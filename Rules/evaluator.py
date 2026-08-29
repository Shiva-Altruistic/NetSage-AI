#!/usr/bin/env python3
"""NetSage AI — Automated evaluation of AI diagnoses against ground truth.

Compares LLM-generated diagnoses to the expected_fault, osi_layer,
concept_tag, severity, and expected_fix fields from cases.csv.

Produces:
  - eval_results.csv   — per-case scoring breakdown
  - eval_report.md     — human-readable summary report
"""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional


# ── Scoring dataclass ────────────────────────────────────────────────────────

@dataclass
class CaseScore:
    case_id: str
    osi_layer_match: bool = False
    concept_tag_match: bool = False
    severity_match: bool = False
    fault_similarity: float = 0.0
    fix_similarity: float = 0.0
    confidence_appropriate: bool = False
    overall_score: float = 0.0


# ── Text similarity (TF-IDF cosine, stdlib-only) ────────────────────────────

_STOPWORDS = frozenset(
    "a an the is are was were be been being have has had do does did will "
    "would shall should may might must can could of to in for on with at by "
    "from as into through during before after above below between out off "
    "over under again further then once here there when where why how all "
    "each every both few more most other some such no nor not only own same "
    "so than too very and but if or because it its this that these those i "
    "me my we our you your he him his she her they them their what which who".split()
)


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip non-alpha, remove stopwords."""
    tokens = re.findall(r"[a-z0-9]+(?:[.\-/][a-z0-9]+)*", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _build_tfidf(docs: list[list[str]]) -> list[dict[str, float]]:
    """Build TF-IDF vectors for a list of tokenized documents."""
    # Document frequency
    df: Counter = Counter()
    for doc in docs:
        df.update(set(doc))

    n = len(docs)
    vectors = []
    for doc in docs:
        tf: Counter = Counter(doc)
        total = len(doc) if doc else 1
        vec = {}
        for term, count in tf.items():
            idf = math.log((n + 1) / (df[term] + 1)) + 1  # smoothed IDF
            vec[term] = (count / total) * idf
        vectors.append(vec)
    return vectors


def _cosine_sim(v1: dict[str, float], v2: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    if not v1 or not v2:
        return 0.0
    common = set(v1.keys()) & set(v2.keys())
    dot = sum(v1[k] * v2[k] for k in common)
    mag1 = math.sqrt(sum(x * x for x in v1.values()))
    mag2 = math.sqrt(sum(x * x for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def text_similarity(text_a: str, text_b: str) -> float:
    """Compute TF-IDF cosine similarity between two text strings."""
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    vectors = _build_tfidf([tokens_a, tokens_b])
    return round(_cosine_sim(vectors[0], vectors[1]), 4)


def keyword_overlap(text_a: str, text_b: str) -> float:
    """Compute Jaccard-style keyword overlap between two texts."""
    set_a = set(_tokenize(text_a))
    set_b = set(_tokenize(text_b))
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return round(len(intersection) / len(union), 4)


# ── Scoring logic ────────────────────────────────────────────────────────────

# Cases known to have intentionally insufficient evidence
UNCERTAIN_CASES = {"C005", "C023", "C030"}


def score_case(case: dict, diagnosis) -> CaseScore:
    """Score a single AI diagnosis against ground truth.

    Args:
        case: row from cases.csv (with ground-truth fields)
        diagnosis: Diagnosis dataclass from prompt_engine
    """
    case_id = case.get("case_id", "?")

    # Extract ground truth
    gt_fault = case.get("expected_fault", "")
    gt_osi = case.get("osi_layer", "")
    gt_tag = case.get("concept_tag", "").lower().strip()
    gt_severity = case.get("severity", "").lower().strip()
    gt_fix = case.get("expected_fix", "")

    # Extract AI predictions
    ai_fault = getattr(diagnosis, "fault", "")
    ai_osi = getattr(diagnosis, "osi_layer", 0)
    ai_tag = getattr(diagnosis, "concept_tag", "").lower().strip()
    ai_severity = getattr(diagnosis, "severity", "").lower().strip()
    ai_fix = getattr(diagnosis, "fix", "")
    ai_confidence = getattr(diagnosis, "confidence", "").lower().strip()

    # --- Exact matches ---
    try:
        osi_match = int(gt_osi) == int(ai_osi)
    except (ValueError, TypeError):
        osi_match = False

    tag_match = gt_tag == ai_tag
    sev_match = gt_severity == ai_severity

    # --- Text similarity ---
    # Use the higher of cosine and keyword overlap for robustness
    fault_cosine = text_similarity(gt_fault, ai_fault)
    fault_keyword = keyword_overlap(gt_fault, ai_fault)
    fault_sim = max(fault_cosine, fault_keyword)

    fix_cosine = text_similarity(gt_fix, ai_fix)
    fix_keyword = keyword_overlap(gt_fix, ai_fix)
    fix_sim = max(fix_cosine, fix_keyword)

    # --- Confidence appropriateness ---
    # For uncertain cases, the AI should NOT say "high" confidence
    if case_id in UNCERTAIN_CASES:
        confidence_ok = ai_confidence in ("low", "medium")
    else:
        confidence_ok = ai_confidence == "high"

    # --- Overall weighted score ---
    overall = (
        0.30 * fault_sim +
        0.15 * (1.0 if osi_match else 0.0) +
        0.15 * (1.0 if tag_match else 0.0) +
        0.10 * (1.0 if sev_match else 0.0) +
        0.20 * fix_sim +
        0.10 * (1.0 if confidence_ok else 0.0)
    )

    return CaseScore(
        case_id=case_id,
        osi_layer_match=osi_match,
        concept_tag_match=tag_match,
        severity_match=sev_match,
        fault_similarity=fault_sim,
        fix_similarity=fix_sim,
        confidence_appropriate=confidence_ok,
        overall_score=round(overall, 4),
    )


# ── Report generation ────────────────────────────────────────────────────────

def generate_eval_csv(scores: list[CaseScore], output_path: Path):
    """Write per-case evaluation results to CSV."""
    fieldnames = [
        "case_id", "osi_layer_match", "concept_tag_match", "severity_match",
        "fault_similarity", "fix_similarity", "confidence_appropriate", "overall_score"
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in scores:
            row = asdict(s)
            row["osi_layer_match"] = int(row["osi_layer_match"])
            row["concept_tag_match"] = int(row["concept_tag_match"])
            row["severity_match"] = int(row["severity_match"])
            row["confidence_appropriate"] = int(row["confidence_appropriate"])
            writer.writerow(row)


def generate_eval_report(
    scores: list[CaseScore],
    cases: list[dict],
    output_path: Path,
):
    """Write a human-readable evaluation report in Markdown."""
    n = len(scores)
    if n == 0:
        output_path.write_text("# Evaluation Report\n\nNo cases evaluated.\n", encoding="utf-8")
        return

    # Aggregate metrics
    avg_overall = sum(s.overall_score for s in scores) / n
    osi_acc = sum(s.osi_layer_match for s in scores) / n
    tag_acc = sum(s.concept_tag_match for s in scores) / n
    sev_acc = sum(s.severity_match for s in scores) / n
    avg_fault_sim = sum(s.fault_similarity for s in scores) / n
    avg_fix_sim = sum(s.fix_similarity for s in scores) / n
    conf_acc = sum(s.confidence_appropriate for s in scores) / n

    # Per-category breakdown
    case_lookup = {c["case_id"]: c for c in cases}
    cat_scores: dict[str, list[float]] = defaultdict(list)
    for s in scores:
        tag = case_lookup.get(s.case_id, {}).get("concept_tag", "unknown")
        cat_scores[tag].append(s.overall_score)

    # Build report
    lines = [
        "# NetSage AI — Evaluation Report\n",
        f"**Cases evaluated:** {n}",
        f"**Average overall score:** {avg_overall:.1%}\n",
        "## Accuracy Breakdown\n",
        "| Metric | Score |",
        "|---|---|",
        f"| OSI Layer (exact match) | {osi_acc:.1%} |",
        f"| Concept Tag (exact match) | {tag_acc:.1%} |",
        f"| Severity (exact match) | {sev_acc:.1%} |",
        f"| Fault Description (text similarity) | {avg_fault_sim:.1%} |",
        f"| Fix Quality (text similarity) | {avg_fix_sim:.1%} |",
        f"| Confidence Appropriateness | {conf_acc:.1%} |",
        "",
        "## Per-Category Scores\n",
        "| Category | Cases | Avg Score |",
        "|---|---|---|",
    ]
    for cat in sorted(cat_scores.keys()):
        cat_avg = sum(cat_scores[cat]) / len(cat_scores[cat])
        lines.append(f"| {cat} | {len(cat_scores[cat])} | {cat_avg:.1%} |")

    # Top & bottom cases
    sorted_scores = sorted(scores, key=lambda s: s.overall_score, reverse=True)
    lines.extend([
        "",
        "## Best Performing Cases\n",
        "| Case | Score | OSI | Tag | Severity |",
        "|---|---|---|---|---|",
    ])
    for s in sorted_scores[:5]:
        lines.append(
            f"| {s.case_id} | {s.overall_score:.1%} | "
            f"{'✅' if s.osi_layer_match else '❌'} | "
            f"{'✅' if s.concept_tag_match else '❌'} | "
            f"{'✅' if s.severity_match else '❌'} |"
        )

    lines.extend([
        "",
        "## Cases Needing Improvement\n",
        "| Case | Score | OSI | Tag | Severity |",
        "|---|---|---|---|---|",
    ])
    for s in sorted_scores[-5:]:
        lines.append(
            f"| {s.case_id} | {s.overall_score:.1%} | "
            f"{'✅' if s.osi_layer_match else '❌'} | "
            f"{'✅' if s.concept_tag_match else '❌'} | "
            f"{'✅' if s.severity_match else '❌'} |"
        )

    # Responsible AI check
    uncertain_scores = [s for s in scores if s.case_id in UNCERTAIN_CASES]
    lines.extend([
        "",
        "## Responsible AI — Uncertain Cases\n",
        f"Cases with intentionally insufficient evidence: {sorted(UNCERTAIN_CASES)}\n",
    ])
    for s in uncertain_scores:
        status = "✅ Appropriately hedged" if s.confidence_appropriate else "⚠️ Over-confident"
        lines.append(f"- **{s.case_id}**: {status} (score: {s.overall_score:.1%})")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    """Quick standalone test — score a mock diagnosis."""
    print("Evaluator module loaded successfully.")
    print("Use via: from evaluator import score_case, generate_eval_csv, generate_eval_report")

    # Demo: score two identical strings
    sim = text_similarity(
        "Access port is in wrong VLAN, should be VLAN 20 not VLAN 10",
        "The access port Fa0/5 is assigned to VLAN 10 instead of the intended VLAN 20"
    )
    print(f"\nDemo text similarity: {sim:.4f}")

    kw = keyword_overlap(
        "Access port is in wrong VLAN, should be VLAN 20 not VLAN 10",
        "The access port Fa0/5 is assigned to VLAN 10 instead of the intended VLAN 20"
    )
    print(f"Demo keyword overlap: {kw:.4f}")


if __name__ == "__main__":
    main()
