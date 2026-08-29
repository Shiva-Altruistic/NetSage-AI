"""NetSage AI Prompt V1 — Baseline.

This file documents the current baseline prompt design.
The authoritative implementation remains: `../Rules/prompt_engine.py`

Baseline evaluation: 62.5% overall.
"""

PROMPT_V1_SPEC = """
Baseline requirements:
1. Evidence-only diagnosis.
2. Use deterministic checker findings as strong signals.
3. Return structured JSON.
4. Select OSI layer 1-7.
5. Select one allowed concept tag.
6. Assign severity and confidence.
7. Recommend one useful next command.
8. Provide a remediation fix.
9. Avoid unsupported evidence.
10. Hedge when evidence is genuinely insufficient.
"""
