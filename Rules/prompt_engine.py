#!/usr/bin/env python3
"""NetSage AI — LLM-powered network fault diagnosis engine.

Builds structured prompts from case evidence + deterministic checker findings,
sends them to Google Gemini, and parses structured JSON diagnoses.

Usage:
    # As a library (called by run_diagnosis.py):
    engine = DiagnosisEngine(api_key="...")
    diagnosis = engine.diagnose(case_row, checker_findings)

    # Dry-run (no API key needed — prints the prompt that *would* be sent):
    engine = DiagnosisEngine(api_key=None)
    prompt = engine.build_prompt(case_row, checker_findings)
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── Structured output ────────────────────────────────────────────────────────

@dataclass
class Diagnosis:
    """Structured AI diagnosis returned by the engine."""
    fault: str = ""
    osi_layer: int = 0
    concept_tag: str = ""
    severity: str = ""
    confidence: str = ""
    next_command: str = ""
    fix: str = ""
    reasoning: str = ""
    raw_response: str = field(default="", repr=False)


# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are **NetSage AI**, a senior CCNA/CCNP-level network troubleshooting \
assistant. Your job is to diagnose network faults from Cisco IOS evidence.

═══════════════════════════════════════════════════════
RULES — read carefully before every diagnosis
═══════════════════════════════════════════════════════

1. **Evidence-only diagnosis.** Base your diagnosis *exclusively* on the \
   symptom description, topology note, and show-command output provided. \
   Never invent evidence that is not shown.

2. **Pre-Analysis findings.** A deterministic rule checker has already \
   analysed the same evidence. Its findings are supplied in a \
   "PRE-ANALYSIS" section. Use them as strong signals — if a rule reports \
   FAIL, that finding is factual. Do NOT contradict a FAIL finding unless \
   you can cite specific evidence that the rule misinterpreted.

3. **Structured JSON output.** You MUST respond with a single JSON object \
   (no markdown fences, no explanation outside the JSON) containing exactly \
   these keys:

   {
     "fault": "<one-paragraph root-cause explanation>",
     "osi_layer": <integer 1-7>,
     "concept_tag": "<one of: vlan, gateway, dhcp, dns, routing, acl, nat, wireless>",
     "severity": "<high | medium | low>",
     "confidence": "<high | medium | low>",
     "next_command": "<the single most useful next show/debug command>",
     "fix": "<step-by-step remediation>",
     "reasoning": "<brief chain-of-thought explaining how you arrived at the diagnosis>"
   }

4. **OSI layer mapping guidance:**
   - Layer 1: physical, cables, power, wireless signal strength
   - Layer 2: VLANs, trunking, STP, MAC tables, wireless SSID mapping
   - Layer 3: IP addressing, subnetting, routing (static/OSPF/EIGRP), \
     gateways, NAT, ACLs
   - Layer 4: port-based ACLs (TCP/UDP port filtering)
   - Layer 7: DHCP, DNS, application-layer services

5. **Responsible AI guardrails:**
   - If the evidence is genuinely insufficient to confirm a single root \
     cause, set confidence to "low" and say so explicitly in the fault \
     description. Do NOT force a confident diagnosis.
   - Never recommend disabling security controls (ACLs, firewalls) as a \
     permanent fix — only as a temporary diagnostic step, clearly labeled.
   - If multiple plausible faults exist, mention them and explain which \
     is most likely given the evidence.

6. **Concept tag must be exactly one of:** vlan, gateway, dhcp, dns, \
   routing, acl, nat, wireless. Pick the tag that best matches the \
   *primary* root cause.

═══════════════════════════════════════════════════════
WORKED EXAMPLE
═══════════════════════════════════════════════════════

**Symptom:** PC on VLAN 20 cannot reach its gateway.
**Topology:** Router-on-a-stick, VLAN 20 gateway is 10.10.20.1.
**Show output:** Access port is in VLAN 10, PC has IP 10.10.10.45/24, \
gateway set to 10.10.20.1.
**Pre-Analysis:** VLAN-001 FAIL — port is VLAN 10 but intended VLAN is 20. \
IPCFG-005 FAIL — gateway 10.10.20.1 is outside subnet 10.10.10.0/24.

**Correct response:**
{
  "fault": "Access port Fa0/5 is assigned to VLAN 10 instead of VLAN 20. The PC receives a VLAN 10 address (10.10.10.45) but its gateway is set for VLAN 20 (10.10.20.1), which is unreachable from VLAN 10.",
  "osi_layer": 2,
  "concept_tag": "vlan",
  "severity": "high",
  "confidence": "high",
  "next_command": "show running-config interface fa0/5",
  "fix": "On SW1: interface fa0/5 / switchport access vlan 20. Verify with show vlan brief.",
  "reasoning": "Checker flagged VLAN mismatch (port in VLAN 10, intended 20) and gateway outside subnet. Both findings align with a single root cause: wrong access VLAN."
}
"""


# ── Prompt builder ───────────────────────────────────────────────────────────

def _format_findings(findings: list[dict]) -> str:
    """Format checker findings into a readable pre-analysis block."""
    if not findings:
        return "No deterministic findings available."

    lines = []
    # Sort: FAILs first, then WARNINGs, then everything else
    priority = {"FAIL": 0, "WARNING": 1, "PASS": 2, "NOT_APPLICABLE": 3}
    sorted_findings = sorted(findings, key=lambda f: priority.get(f.get("status", ""), 4))

    for f in sorted_findings:
        status = f.get("status", "?")
        rule_id = f.get("rule_id", "?")
        message = f.get("message", "")
        evidence = f.get("evidence", "")

        # Skip NOT_APPLICABLE findings to keep the prompt concise
        if status == "NOT_APPLICABLE":
            continue

        icon = {"FAIL": "❌", "WARNING": "⚠️", "PASS": "✅"}.get(status, "ℹ️")
        line = f"  {icon} [{rule_id}] {status}: {message}"
        if evidence:
            line += f"\n     Evidence: {evidence}"
        lines.append(line)

    if not lines:
        return "All deterministic checks returned NOT_APPLICABLE (no relevant evidence found)."

    return "\n".join(lines)


def build_user_prompt(case: dict, findings: list[dict]) -> str:
    """Build the per-case user prompt with evidence and pre-analysis."""
    symptom = case.get("symptom", "").replace("\\n", "\n")
    topology = case.get("topology_note", "").replace("\\n", "\n")
    show_output = case.get("show_output", "").replace("\\n", "\n")
    case_id = case.get("case_id", "unknown")

    pre_analysis = _format_findings(findings)

    prompt = f"""\
══════════════════════════════════════════════════════
CASE {case_id}
══════════════════════════════════════════════════════

▸ SYMPTOM
{symptom}

▸ TOPOLOGY
{topology}

▸ SHOW-COMMAND OUTPUT
{show_output}

▸ PRE-ANALYSIS (deterministic rule checker results)
{pre_analysis}

══════════════════════════════════════════════════════
Diagnose this case. Respond with a single JSON object.
══════════════════════════════════════════════════════
"""
    return prompt


# ── LLM caller ───────────────────────────────────────────────────────────────

def _parse_osi_layer(value) -> int:
    """Robustly extract an OSI layer integer from various LLM formats.

    Handles: 2, "2", "Layer 2", "layer 2", "L2", etc.
    """
    if isinstance(value, int):
        return value
    s = str(value).strip()
    # Try direct int parse first
    try:
        return int(s)
    except ValueError:
        pass
    # Extract digits from strings like "Layer 2", "L3", etc.
    m = re.search(r'(\d+)', s)
    if m:
        return int(m.group(1))
    return 0


def _parse_diagnosis(raw: str) -> Diagnosis:
    """Parse a JSON response string into a Diagnosis dataclass."""
    cleaned = raw.strip()

    # 1. Extract from ```json ... ``` code block if present
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned, re.I)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    else:
        # 2. Extract outermost curly braces
        brace_match = re.search(r"(\{[\s\S]*\})", cleaned)
        if brace_match:
            cleaned = brace_match.group(1).strip()
        else:
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    data = None
    try:
        data = json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        # Fallback: remove trailing commas before closing braces
        fixed = re.sub(r",\s*([\]}])", r"\1", cleaned)
        try:
            data = json.loads(fixed, strict=False)
        except json.JSONDecodeError:
            pass

    if not isinstance(data, dict):
        return Diagnosis(
            fault=f"[PARSE ERROR] Could not parse LLM response as JSON.",
            reasoning=raw[:500],
            raw_response=raw,
        )

    return Diagnosis(
        fault=str(data.get("fault", "")),
        osi_layer=_parse_osi_layer(data.get("osi_layer", 0)),
        concept_tag=str(data.get("concept_tag", "")).lower().strip(),
        severity=str(data.get("severity", "")).lower().strip(),
        confidence=str(data.get("confidence", "")).lower().strip(),
        next_command=str(data.get("next_command", "")),
        fix=str(data.get("fix", "")),
        reasoning=str(data.get("reasoning", "")),
        raw_response=raw,
    )


DEFAULT_API_KEY = os.environ.get("GEMINI_API_KEY", "")


class DiagnosisEngine:
    """Manages LLM-based network fault diagnosis."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.5-flash-lite",
                 system_prompt: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
        self.model_name = model
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self._client = None
        self._initialized = False

    def _init_model(self):
        """Lazy-init the Gemini client (avoids import errors if not installed)."""
        if self._initialized:
            return
        if not self.api_key:
            raise RuntimeError(
                "No Gemini API key provided. Pass --api-key or set GEMINI_API_KEY.\n"
                "Get a free key at: https://aistudio.google.com/apikey"
            )
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise RuntimeError(
                "google-genai package not installed.\n"
                "Run: pip install google-genai"
            )

        self._client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(timeout=25000),
        )
        self._initialized = True

    def build_prompt(self, case: dict, findings: list[dict]) -> str:
        """Build the full user prompt (useful for dry-run / inspection)."""
        return build_user_prompt(case, findings)

    def diagnose(self, case: dict, findings: list[dict],
                 retry_attempts: int = 2, retry_delay: float = 2.0) -> Diagnosis:
        """Send a case to the LLM and return a structured Diagnosis."""
        self._init_model()
        prompt = self.build_prompt(case, findings)

        from google.genai import types

        last_error = None
        for attempt in range(1, retry_attempts + 2):
            try:
                # Suppress the AFC deprecation warning printed by google-genai
                # (it writes to stderr via print, not via warnings.warn).
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                try:
                    response = self._client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=self.system_prompt,
                            temperature=0.2,
                            response_mime_type="application/json",
                        ),
                    )
                finally:
                    sys.stderr = old_stderr
                raw = response.text
                return _parse_diagnosis(raw)
            except Exception as e:
                last_error = e
                if attempt <= retry_attempts:
                    time.sleep(retry_delay * attempt)
                    continue

        return Diagnosis(
            fault=f"[API ERROR] {last_error}",
            raw_response=str(last_error),
        )

    def diagnose_dry_run(self, case: dict, findings: list[dict]) -> str:
        """Return the prompt that would be sent, without calling the API."""
        prompt = self.build_prompt(case, findings)
        sp = self.system_prompt
        header = f"=== SYSTEM PROMPT ({len(sp)} chars) ===\n{sp}\n\n"
        return header + f"=== USER PROMPT ({len(prompt)} chars) ===\n{prompt}"


# ── CLI for quick testing ────────────────────────────────────────────────────

def main():
    import argparse
    import csv
    from pathlib import Path

    # Import checker from same directory
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from checker import check_case, Finding
    from dataclasses import asdict as _asdict

    parser = argparse.ArgumentParser(description="NetSage AI prompt engine — test a single case")
    parser.add_argument("--csv", required=True, help="Path to cases.csv")
    parser.add_argument("--case-id", help="Specific case to test (default: first case)")
    parser.add_argument("--api-key", default=None, help="Gemini API key")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without calling API")
    args = parser.parse_args()

    # Load cases
    with open(args.csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cases = list(reader)

    # Find target case
    if args.case_id:
        target = next((c for c in cases if c["case_id"] == args.case_id), None)
        if not target:
            raise SystemExit(f"Case {args.case_id} not found in CSV.")
    else:
        target = cases[0]

    print(f"[>] Case: {target['case_id']}")
    print(f"[>] Symptom: {target['symptom'][:100]}...")

    # Run checker
    checker_findings = check_case(target)
    findings_dicts = [_asdict(f) for f in checker_findings]

    engine = DiagnosisEngine(api_key=args.api_key)

    if args.dry_run:
        print("\n" + engine.diagnose_dry_run(target, findings_dicts))
    else:
        print("[*] Calling Gemini...")
        diagnosis = engine.diagnose(target, findings_dicts)
        print(f"\n{'=' * 60}")
        print(f"  Fault:       {diagnosis.fault}")
        print(f"  OSI Layer:   {diagnosis.osi_layer}")
        print(f"  Concept:     {diagnosis.concept_tag}")
        print(f"  Severity:    {diagnosis.severity}")
        print(f"  Confidence:  {diagnosis.confidence}")
        print(f"  Next Cmd:    {diagnosis.next_command}")
        print(f"  Fix:         {diagnosis.fix}")
        print(f"  Reasoning:   {diagnosis.reasoning}")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
