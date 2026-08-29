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
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

# Force UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


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
    evidence_grounded: bool = True
    latency_sec: float = 0.0
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


import os
import json
import time

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("\"'")
            if k and k not in os.environ:
                os.environ[k] = v

_SYNONYMS = {
    "reconfigure": "configure",
    "update": "configure",
    "modify": "configure",
    "change": "configure",
    "set": "configure",
    "assign": "configure",
    "incorrect": "wrong",
    "mismatch": "wrong",
    "mismatched": "wrong",
    "invalid": "wrong",
    "non-existent": "missing",
    "nonexistent": "missing",
    "sub-interface": "subinterface",
    "sub-interfaces": "subinterface",
    "subinterfaces": "subinterface",
    "default-gateway": "gateway",
    "gw": "gateway",
}


def normalize_cisco_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"\bgigabitethernet\b", "gi", t)
    t = re.sub(r"\bfastethernet\b", "fa", t)
    t = re.sub(r"\bserial\b", "se", t)
    t = re.sub(r"\binterface\s+fa\b", "fa", t)
    t = re.sub(r"\binterface\s+gi\b", "gi", t)
    return t


def _tokenize_cisco(text: str) -> list[str]:
    text = normalize_cisco_text(text)
    tokens = re.findall(r"[a-z0-9]+(?:[.\-/][a-z0-9]+)*", text)
    result = []
    for t in tokens:
        if t in _STOPWORDS or len(t) < 2:
            continue
        mapped = _SYNONYMS.get(t, t)
        result.append(mapped)
    return result


def extract_cisco_entities(text: str) -> set[str]:
    text = normalize_cisco_text(text)
    entities = set()
    for ip in re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?\b", text):
        entities.add(ip)
    for vlan in re.findall(r"\bvlan\s*(\d+)\b", text):
        entities.add(f"vlan{vlan}")
    for iface in re.findall(r"\b(?:gi|fa|se)\d[0-9/.]*\b", text):
        entities.add(iface)
    for dev in re.findall(r"\b(?:pc-[a-z0-9]+|sw\d*|r\d*-[a-z0-9]+|ap\d+|wlc\d+)\b", text):
        entities.add(dev)
    return entities


def semantic_technical_similarity(gt_text: str, pred_text: str) -> float:
    """Compute semantic technical similarity between reference and prediction.

    Prevents underscoring correct technical solutions by evaluating:
    1. Technical Entity Match (IPs, VLANs, interfaces, devices)
    2. Concept Recall (ground truth required technical information present in prediction)
    3. Phrasing & Command Sequence Match
    """
    toks_gt = _tokenize_cisco(gt_text)
    toks_pred = _tokenize_cisco(pred_text)
    if not toks_gt or not toks_pred:
        return 0.0

    set_gt = set(toks_gt)
    set_pred = set(toks_pred)
    intersection = set_gt & set_pred

    recall = len(intersection) / len(set_gt)

    ents_gt = extract_cisco_entities(gt_text)
    ents_pred = extract_cisco_entities(pred_text)
    if ents_gt:
        ent_match = len(ents_gt & ents_pred) / len(ents_gt)
    else:
        ent_match = recall

    def get_bigrams(tokens):
        return set(zip(tokens[:-1], tokens[1:])) if len(tokens) > 1 else set()

    bg_gt = get_bigrams(toks_gt)
    bg_pred = get_bigrams(toks_pred)
    bg_match = (len(bg_gt & bg_pred) / len(bg_gt)) if bg_gt else recall

    score = (0.40 * recall) + (0.35 * ent_match) + (0.25 * bg_match)
    return round(min(1.0, max(0.0, score)), 4)


def batch_llm_judge(
    cases: list[dict],
    diagnoses: list[dict],
    api_key: str | None = None,
) -> dict[str, tuple[float, float]]:
    """Run an LLM-as-a-judge pass using Gemini to evaluate technical equivalence."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return {}

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
    except Exception:
        return {}

    diag_lookup = {d.get("case_id"): d for d in diagnoses}
    judgments: dict[str, tuple[float, float]] = {}

    batch_size = 10
    for i in range(0, len(cases), batch_size):
        batch = cases[i:i + batch_size]
        items = []
        for c in batch:
            cid = c.get("case_id", "")
            d = diag_lookup.get(cid, {})
            items.append({
                "case_id": cid,
                "ref_fault": c.get("expected_fault", ""),
                "pred_fault": d.get("fault", ""),
                "ref_fix": c.get("expected_fix", ""),
                "pred_fix": d.get("fix", ""),
            })

        prompt = f"""You are an objective Cisco CCNA/CCNP technical evaluation judge.
Compare each predicted AI diagnosis against the ground truth reference.
Score each dimension from 0.0 to 1.0:
- fault_similarity: Does the predicted fault identify the same technical root cause and mechanism?
- fix_similarity: Does the predicted remediation provide a correct, working Cisco fix matching the required corrective actions?

Rate strictly on technical validity, not wording overlap. Minor wording differences, synonyms, or additional helpful explanation should NOT be penalized.

Cases:
{json.dumps(items, indent=2)}

Return a JSON array of objects:
[
  {{"case_id": "C...", "fault_similarity": <float 0.0-1.0>, "fix_similarity": <float 0.0-1.0>}}, ...
]
"""
        try:
            resp = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(resp.text)
            for row in data:
                judgments[row["case_id"]] = (
                    round(float(row.get("fault_similarity", 0.0)), 4),
                    round(float(row.get("fix_similarity", 0.0)), 4),
                )
            time.sleep(1.5)
        except Exception:
            pass

    return judgments


# ── Scoring logic ────────────────────────────────────────────────────────────

# Cases known to have intentionally insufficient evidence
UNCERTAIN_CASES = {"C005", "C023", "C030"}


def score_case(
    case: dict,
    diagnosis,
    latency_sec: float = 0.0,
    fault_sim: float | None = None,
    fix_sim: float | None = None,
) -> CaseScore:
    """Score a single AI diagnosis against ground truth.

    Args:
        case: row from cases.csv (with ground-truth fields)
        diagnosis: Diagnosis dataclass from prompt_engine
        latency_sec: Wall-clock latency for the diagnosis in seconds
        fault_sim: Pre-computed fault similarity (e.g. from LLM judge)
        fix_sim: Pre-computed fix similarity (e.g. from LLM judge)
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

    # --- Semantic text similarity (prevents underscoring correct answers) ---
    if fault_sim is None:
        fault_sim = semantic_technical_similarity(gt_fault, ai_fault)

    if fix_sim is None:
        fix_sim = semantic_technical_similarity(gt_fix, ai_fix)

    # --- Confidence appropriateness ---
    # For uncertain cases, the AI should NOT say "high" confidence
    if case_id in UNCERTAIN_CASES:
        confidence_ok = ai_confidence in ("low", "medium")
    else:
        confidence_ok = ai_confidence == "high"

    # --- Evidence grounding (Interface check against show output) ---
    all_evidence = f"{case.get('symptom', '')} {case.get('topology_note', '')} {case.get('show_output', '')}"
    cited_interfaces = re.findall(
        r"\b(?:[A-Z][a-z0-9/.]*Ethernet\d[0-9/.]*|Fa\d[0-9/.]*|Gi\d[0-9/.]*|Se\d[0-9/.]*|Vlan\d+)\b",
        f"{ai_fault} {ai_fix}",
        re.I,
    )
    grounded = True
    for iface in cited_interfaces:
        if iface.lower() in ("ethernet", "fastethernet", "gigabitethernet", "serial"):
            continue
        if iface.lower() not in all_evidence.lower():
            grounded = False
            break

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
        evidence_grounded=grounded,
        latency_sec=round(latency_sec, 2),
        overall_score=round(overall, 4),
    )


# ── Report generation ────────────────────────────────────────────────────────

def generate_eval_csv(scores: list[CaseScore], output_path: Path):
    """Write per-case evaluation results to CSV."""
    fieldnames = [
        "case_id", "osi_layer_match", "concept_tag_match", "severity_match",
        "fault_similarity", "fix_similarity", "confidence_appropriate",
        "evidence_grounded", "latency_sec", "overall_score"
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
            row["evidence_grounded"] = int(row["evidence_grounded"])
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
    grounded_acc = sum(s.evidence_grounded for s in scores) / n
    latencies = [s.latency_sec for s in scores if s.latency_sec > 0]
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

    # Per-category breakdown
    case_lookup = {c["case_id"]: c for c in cases}
    cat_scores: dict[str, list[float]] = defaultdict(list)
    for s in scores:
        tag = case_lookup.get(s.case_id, {}).get("concept_tag", "unknown")
        cat_scores[tag].append(s.overall_score)

    # Build report
    lines = [
        "# NetSage AI — Evaluation Report\n",
        f"**Cases evaluated:** {n} (Full Benchmark Suite)",
        f"**Average overall score:** {avg_overall:.1%}",
        f"**Mean inference latency:** {avg_latency:.2f}s\n",
        "## Accuracy Breakdown\n",
        "| Metric | Score | Measurement Method |",
        "|---|---|---|",
        f"| OSI Layer (exact match) | {osi_acc:.1%} | Exact numeric layer match |",
        f"| Concept Tag (exact match) | {tag_acc:.1%} | Ground truth CCNA category match |",
        f"| Severity (exact match) | {sev_acc:.1%} | Ground truth severity match |",
        f"| Fault Description (semantic similarity) | {avg_fault_sim:.1%} | Technical root-cause semantic equivalence |",
        f"| Fix Quality (semantic similarity) | {avg_fix_sim:.1%} | Working Cisco remediation equivalence |",
        f"| Confidence Appropriateness | {conf_acc:.1%} | Hedging on ambiguous cases |",
        f"| Evidence Grounding Rate | {grounded_acc:.1%} | Cited interfaces verified in transcript |",
        f"| Mean Inference Latency | {avg_latency:.2f}s | Wall-clock API response time |",
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
    """Score all diagnoses in Results/ai_diagnoses.csv against Dataset/cases.csv."""
    cases_path = Path(__file__).resolve().parent.parent / "Dataset" / "cases.csv"
    diags_path = Path(__file__).resolve().parent.parent / "Results" / "ai_diagnoses.csv"
    results_dir = Path(__file__).resolve().parent.parent / "Results"

    if not cases_path.exists() or not diags_path.exists():
        print(f"[!] Missing required data file: {cases_path} or {diags_path}")
        return 1

    with cases_path.open("r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    with diags_path.open("r", encoding="utf-8") as f:
        diags = list(csv.DictReader(f))

    print(f">> NetSage AI Evaluator: Evaluating {len(diags)} diagnoses across {len(cases)} cases...")
    print(">> Running batch LLM-as-a-judge pass for technical semantic equivalence...")
    judgments = batch_llm_judge(cases, diags)
    if judgments:
        print(f"   [+] Technical judgments obtained for {len(judgments)} cases.")
    else:
        print("   [!] API key not available; falling back to entity-aware semantic similarity.")

    case_map = {c["case_id"]: c for c in cases}
    scores: list[CaseScore] = []

    for d in diags:
        cid = d.get("case_id", "")
        c = case_map.get(cid)
        if not c:
            continue
        lat = float(d.get("latency_sec", 0.0) or 0.0)
        f_sim, x_sim = judgments.get(cid, (None, None))

        class MockDiag:
            pass
        m = MockDiag()
        for k, v in d.items():
            setattr(m, k, v)

        score = score_case(c, m, latency_sec=lat, fault_sim=f_sim, fix_sim=x_sim)
        scores.append(score)

    eval_csv = results_dir / "eval_results.csv"
    eval_rep = results_dir / "eval_report.md"

    generate_eval_csv(scores, eval_csv)
    generate_eval_report(scores, cases, eval_rep)

    avg_score = sum(s.overall_score for s in scores) / len(scores)
    osi_acc = sum(s.osi_layer_match for s in scores) / len(scores)
    tag_acc = sum(s.concept_tag_match for s in scores) / len(scores)
    sev_acc = sum(s.severity_match for s in scores) / len(scores)
    avg_f = sum(s.fault_similarity for s in scores) / len(scores)
    avg_x = sum(s.fix_similarity for s in scores) / len(scores)

    print(f"\n{'=' * 60}")
    print(f"  REGENERATED EVALUATION SUMMARY ({len(scores)} cases)")
    print(f"{'=' * 60}")
    print(f"  Overall Score:           {avg_score:.1%}")
    print(f"  OSI Layer Match:         {osi_acc:.1%}")
    print(f"  Concept Tag Match:       {tag_acc:.1%}")
    print(f"  Severity Match:          {sev_acc:.1%}")
    print(f"  Fault Technical Match:   {avg_f:.1%}")
    print(f"  Fix Technical Match:     {avg_x:.1%}")
    print(f"{'=' * 60}")
    print(f"[>] Saved eval CSV:    {eval_csv}")
    print(f"[>] Saved eval report: {eval_rep}\n")
    return 0


if __name__ == "__main__":
    main()
