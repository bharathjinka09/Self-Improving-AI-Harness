# Self-Improving Customer Support Agent Harness (OpenAI + LangGraph)

A production-ready agent with **human-in-the-loop (HITL) customer support agent** built with **OpenAI** and **LangGraph** that safely improves its own playbooks over time without modifying locked security rules or evaluation suites.

---

## Architecture Overview

```text
support-harness/
├── harness/                  # Editable, version-controlled agent surfaces
│   ├── system_prompt.md      # Global tone, safety guardrails, and escalation rules
│   ├── skills/               # Modular intent playbooks (loaded dynamically)
│   │   ├── refunds.md
│   │   ├── billing.md
│   │   ├── shipping.md
│   │   └── general.md
│   └── policy_rules.json     # Locked deterministic thresholds (refund caps, confidence)
├── runtime/                  # Immutable execution engine (never edited by optimizer)
│   ├── __init__.py
│   ├── graph.py              # LangGraph workflow with SqliteSaver & native interrupt()
│   └── cli_demo.py           # Interactive CLI demo showing HITL pause & resume
├── optimizer/                # Offline self-improvement & regression gating
│   ├── __init__.py
│   ├── eval_gate.py          # OpenAI Structured Output regression judge
│   └── improve.py            # Clusters human edits -> proposes skill diffs -> gates promotion
├── evals/                    # Read-only regression test suite
│   └── golden_tickets.jsonl  # Historical benchmark & regression tickets
├── .env.example              # Environment variable template
├── .gitignore
└── requirements.txt
```

### How the Self-Improvement Loop Works
1. **Route & Draft (`runtime/graph.py`):** Incoming tickets are classified by intent so only the relevant playbook (`harness/skills/<intent>.md`) is loaded—preventing prompt bloat.
2. **Deterministic Policy Gate:** If confidence falls below `min_confidence` or a refund exceeds `max_auto_refund`, LangGraph triggers `interrupt()` and persists state via `SqliteSaver`.
3. **Human-in-the-Loop Review:** A support agent reviews the draft, edits it if needed, and resumes execution via `Command(resume=...)`. All traces are appended to `traces.jsonl`.
4. **Offline Optimization & Eval Gate (`optimizer/improve.py`):** A scheduled job inspects traces where `human_edited == True`, uses a reasoning model (`o3` / `gpt-4.1`) to propose a generalized update to that intent's skill file, and runs `optimizer/eval_gate.py` against `evals/golden_tickets.jsonl` before writing changes.

---

## Quickstart for New Developers

### 1. Clone & Create a Virtual Environment
```bash
git clone <your-repo-url>
cd support-harness
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 4. Run the Interactive HITL Demo
Test a ticket that triggers a human-in-the-loop pause (e.g., a refund over $50) and approve/edit the draft reply in your terminal:
```bash
python -m runtime.cli_demo
```
This creates `checkpoints.sqlite` (LangGraph state persistence) and appends execution logs to `traces.jsonl`.

### 5. Run the Regression Evaluation Suite
Verify the current harness against the golden ticket dataset:
```bash
python -m optimizer.eval_gate
```

### 6. Run the Offline Self-Improvement Optimizer
Once you have collected human-edited traces in `traces.jsonl` (default threshold: `min_edits=3`), run the optimizer to propose, evaluate, and apply a skill patch:
```bash
python -m optimizer.improve --intent refunds --min-edits 1
```

---

## Safety & Governance Best Practices
* **Keep `policy_rules.json` locked:** Financial limits and escalation triggers are enforced in deterministic Python code, not editable prompts.
* **Promote via Pull Requests in Production:** In CI/CD, run `python -m optimizer.improve` in a GitHub Action that opens a PR whenever `eval_gate.py` passes, requiring a support lead's approval before merging.
* **Post-Interrupt Side Effects:** External API calls (Stripe refunds, CRM updates) belong strictly in `finalize_and_log_node` *after* `human_review_node` so interrupted nodes never double-execute on resume.
