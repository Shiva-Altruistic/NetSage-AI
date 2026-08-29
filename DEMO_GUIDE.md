# NetSage AI — End-to-End Demonstration & Presentation Guide

This guide provides a structured script, talking points, rubric alignment, and defense Q&A for presenting the **NetSage AI** autonomous Cisco IOS network troubleshooting and governance platform.

---

## 1. Executive Summary & 3-Minute Elevator Pitch

> *"In enterprise networks, an outage costs an average of $5,600 per minute. Traditional network troubleshooting relies either on manual human CLI inspection—which is slow—or pure LLM chatbots—which hallucinate nonexistent router interfaces, guess root causes without evidence, and blindly recommend destructive commands like `shutdown` or `clear ip dhcp binding *`.*
> 
> ***NetSage AI** solves this with a **Hybrid AI Architecture**:
> 1. **Deterministic Rule Engine**: 24 Cisco IOS inspection rules pre-screen evidence for hard facts before calling the AI.
> 2. **Optimized LLM Reasoning (Prompt V2)**: Powered by Google Gemini 3.5 Flash with CCNA/CCNP disambiguation rules, structured JSON output, and uncertainty hedging.
> 3. **Operational Safety & Human Review Gate**: Screen proposed remediation commands for destructive risks and require human engineer sign-off before deployment.
> 4. **Responsible AI Governance**: Aligned with the NIST AI Risk Management Framework and Google SAIF, featuring 90.0% evidence grounding and immutable telemetry logging.*
> 
> *The entire system is managed through an interactive, multi-colored Web Dashboard with live synchronization to our benchmark dataset."*

---

## 2. Technical Architecture Overview

```mermaid
graph TD
    A[Case Evidence: Symptom, Topology, Show Output] --> B[Deterministic Rule Checker: 24 Rules]
    B -->|Pre-Analysis Findings| C[Diagnosis Engine: Gemini 3.5 Flash V2]
    C --> D[Structured Output: Fault, OSI, Tag, Severity, Fix]
    D --> E[Operational Safety Guardrail]
    E -->|Safe Non-Disruptive| F[Human Review Gate]
    E -->|High/Medium Risk| G[Senior Engineer Sign-Off Alert]
    F --> H[Audit Trail: Results/human_review.csv]
    D --> I[RAI Governance Engine: NIST/SAIF Audit]
    I --> J[Results/responsible_ai_log.jsonl & .csv]
    H --> K[Web Dashboard: Port 5173 / Port 3001]
    J --> K
```

---

## 3. Live Demonstration Walkthrough (5–8 Minutes)

Follow these exact steps during a live demo or presentation:

### Part 1: Automated Terminal Pipeline Demo (2 Minutes)
Open a terminal in the project root and run:
```bash
python run_demo.py
```
*(Or `python run_demo.py --auto` for hands-free 2-second progression).*

- **Point out**:
  - **Stage 1**: 30 benchmark cases spanning 5 topologies (SOHO Branch, Campus L3, WAN Edge, Internet Edge, Wireless LAN).
  - **Stage 2**: Deterministic rule checker executing 24 CCNA/CCNP rules, firing on Case `C001` (flagging `IPCFG-005` and `VLAN-001`).
  - **Stage 3**: Gemini 3.5 Flash completing live structured diagnosis in ~1.8 seconds with exact Cisco commands.
  - **Stage 4**: Prompt A/B comparison showing Prompt V2 outperforming V1 across the 8-case focus disambiguation subset (+12.5% tag accuracy), with 93.3% concept tag accuracy across the full 30-case benchmark.
  - **Stage 5**: Operational safety screening flagging `clear ip dhcp binding *` as High Risk.
  - **Stage 6**: Ambiguous cases (`C005`, `C023`, `C030`) hedged with `medium` confidence.

---

### Part 2: Interactive Web Dashboard Walkthrough (4 Minutes)
Open your browser to: **`http://localhost:5173/`**

#### 1. Overview & KPI Analytics Tab
- **Visuals**: Highlight the crisp white theme, colorful gradient tops on KPI cards, and pastel mesh background.
- **Theme Switcher**: Click the **Sun / Moon icon** in the top-right of the Navbar to toggle between **Crisp White Light Mode** and **Vibrant Dark Mode**.
- **Charts**:
  - Point to the **Troubleshooting Domain Distribution** (8 distinct colored bars for VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless).
  - Point to the **OSI Layer Doughnut Chart** (Layer 2 through Layer 7 coverage).
  - Point to the **Prompt V1 vs V2 Benchmark Bar Chart**.

#### 2. Case Explorer Tab
- Click **"Case Explorer (30)"** in the Navbar.
- **Filter**: Click the **"VLAN (L2)"** purple pill. Show how the table instantly filters to VLAN cases.
- **Search**: Type `C001` in the search bar.
- **Inspect**: Click the **"Inspect"** button on Case `C001`.
  - Show the **Cisco IOS Show-Command Terminal** with dark terminal styling.
  - Show the **Root Cause Diagnosis** and **Remediation Fix**.
  - Click **"Copy Fix"** to show instant clipboard copy feedback.
  - Click **"Close Inspection"**.

#### 3. Prompt A/B Studio Tab
- Click **"Prompt A/B Studio"** in the Navbar.
- Point to the **Studio Winner banner**: Prompt V2 (+18.4% improvement on key disambiguation scenarios).
- Point to the comparison table showing side-by-side V1 score vs V2 score with green positive deltas across the 8 focus cases.

#### 4. Human Review & Safety Gate Tab
- Click **"Human Review Gate"** in the Navbar.
- Point to the **Operational Safety Protocol alert** (highlighting destructive action screening).
- Filter by **"Approved"** to show previously signed-off cases (e.g. `C002` with notes *"Verified gateway address settings"*).
- Click **"Sign Off"** on any case:
  - Demonstrate clicking **"Approve"**, **"Modify"**, or **"Reject"**.
  - Show how modifying allows overriding the concept tag or remediation command.
  - Click **"Authorize & Persist Decision"** to demonstrate real-time persistence to `Results/human_review.csv`.

#### 5. Responsible AI & Transparency Center Tab
- Click **"Responsible AI"** in the Navbar.
- Review the **3 Governance Pillars**:
  - *Data Provenance & Privacy*: 100% synthetic Packet Tracer cases; zero live network passwords or PII exposed.
  - *Uncertainty Calibration*: Intentionally ambiguous cases (`C005`, `C023`, `C030`) evaluated for proper confidence hedging.
  - *Action Risk Screening*: Destructive commands blocked from automated execution.
- Point to the **Recent Telemetry Stream table** with live UTC timestamps, model versions, and evidence grounding status.

---

## 4. Anticipated Evaluator Q&A & Defense

### Q1: *"How does NetSage AI ensure the LLM isn't just hallucinating network commands?"*
**Answer**: 
> *"We use a three-tier anti-hallucination defense: First, our **Deterministic Rule Engine (24 inspection rules)** pre-analyzes the configuration and feeds verified facts to the prompt. Second, our **Evidence Grounding Verification** checks every interface cited in the diagnosis against the CLI output transcript (achieving a measured 90.0% evidence grounding rate across all 30 cases). Third, our **Confidence Calibration** instructs the LLM to output 'medium' or 'low' confidence whenever required evidence is missing, as demonstrated in cases C005, C023, and C030."*

---

### Q2: *"Can this system be deployed to live production networks?"*
**Answer**: 
> *"NetSage AI is deliberately architected as a **Human-in-the-Loop Decision Support System**, not an autonomous CLI-execution bot. While the AI suggests diagnoses and exact Cisco remediation syntax, the **Human Review Gate** requires explicit engineer review before commands are applied. Furthermore, destructive commands are pre-screened and flagged for senior authorization."*

---

### Q3: *"What stops the AI from executing a command that knocks the network offline?"*
**Answer**: 
> *"NetSage AI enforces an **Action Risk Guardrail**. Every remediation command is screened against a destructive action taxonomy before it can ever be applied. Commands like `clear ip dhcp binding *` (which flushes all active leases network-wide), `shutdown` (which takes an interface down), or `switchport trunk native vlan` are classified as High or Medium risk. These commands are blocked from automated deployment and mandate explicit senior network engineer authorization in the Human Review Gate."*

---

### Q4: *"What is the difference between Prompt V1 and Prompt V2?"*
**Answer**: 
> *"Prompt V1 was our baseline system prompt. While functional, it struggled with subtle CCNA root cause disambiguation—for instance, confusing a missing VLAN assignment on an access port with a default gateway failure, or confusing CAPWAP controller join failures with wireless signal degradation. 
> 
> In **Prompt V2**, we integrated CCNA/CCNP disambiguation heuristics, explicit boundary criteria for all 8 concept tags, and mandatory confidence calibration guidelines. Across our 8-case focus benchmark set, this improved concept tag accuracy from 75.0% to **87.5%** and confidence calibration to **75.0%**. Across the entire 30-case benchmark suite, NetSage achieves **93.3% concept tag accuracy**, **93.3% OSI layer match**, and a measured mean latency of **1.82 seconds**."*

---

## 5. Artifact Quick-Reference Table

| Milestone | File / Path | Key Verification |
|---|---|---|
| **Master Demo Script** | [run_demo.py](file:///c:/Users/Public/Netsage%20AI/run_demo.py) | Full automated CLI walkthrough of Stages 1–7 |
| **Interactive Dashboard** | [Dashboard/](file:///c:/Users/Public/Netsage%20AI/Dashboard/) | React + Vite UI on `http://localhost:5173/` |
| **Benchmark Dataset** | [Dataset/cases.csv](file:///c:/Users/Public/Netsage%20AI/Dataset/cases.csv) | 30 cases, 5 topologies, 8 network categories |
| **Deterministic Checker** | [Rules/checker.py](file:///c:/Users/Public/Netsage%20AI/Rules/checker.py) | 24 rules (IP, GW, VLAN, NAT, Routing, WiFi, ACL, DNS) |
| **AI Diagnosis Engine** | [Rules/prompt_engine.py](file:///c:/Users/Public/Netsage%20AI/Rules/prompt_engine.py) | Gemini 3.5 Flash with structured JSON output |
| **Prompt V2 Definition** | [Prompt_Testing/prompt_v2.py](file:///c:/Users/Public/Netsage%20AI/Prompt_Testing/prompt_v2.py) | CCNA/CCNP disambiguation heuristics |
| **Prompt A/B Benchmark** | [Results/prompt_comparison.csv](file:///c:/Users/Public/Netsage%20AI/Results/prompt_comparison.csv) | V1 vs V2 side-by-side scores & deltas (8 focus cases) |
| **30-Case Evaluations** | [Results/eval_results.csv](file:///c:/Users/Public/Netsage%20AI/Results/eval_results.csv) | Full 30-case evaluation against ground truth |
| **30-Case AI Diagnoses** | [Results/ai_diagnoses.csv](file:///c:/Users/Public/Netsage%20AI/Results/ai_diagnoses.csv) | Full 30-case diagnoses with per-case latency |
| **Human Review Audit** | [Results/human_review.csv](file:///c:/Users/Public/Netsage%20AI/Results/human_review.csv) | Signed-off decisions, overrides, and timestamps |
| **Responsible AI Stream** | [Results/responsible_ai_log.jsonl](file:///c:/Users/Public/Netsage%20AI/Results/responsible_ai_log.jsonl) | Immutable inference event stream with grounding checks |
| **Governance Report** | [Results/responsible_ai_audit.md](file:///c:/Users/Public/Netsage%20AI/Results/responsible_ai_audit.md) | NIST AI RMF 1.0 & Google SAIF compliance |
