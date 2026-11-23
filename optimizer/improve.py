import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from optimizer.eval_gate import run_eval_gate

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
TRACE_LOG = ROOT_DIR / "traces.jsonl"
HARNESS_DIR = ROOT_DIR / "harness"
GOLDEN_PATH = ROOT_DIR / "evals" / "golden_tickets.jsonl"


class SkillPatch(BaseModel):
    diagnosis: str
    updated_markdown: str


def append_new_regression_cases(edited_traces: list[dict]) -> None:
    existing_ids = set()
    if GOLDEN_PATH.exists():
        for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing_ids.add(json.loads(line)["id"])

    with GOLDEN_PATH.open("a", encoding="utf-8") as f:
        for t in edited_traces:
            if t["ticket_id"] not in existing_ids:
                record = {
                    "id": t["ticket_id"],
                    "intent": t["intent"],
                    "customer_msg": t["customer_msg"],
                    "expected_action": t["proposed_action"],
                    "expected_criteria": f"Align with approved human response: {t['final_reply']}",
                }
                f.write(json.dumps(record) + "\n")


def optimize_skill(intent: str, min_edits: int = 3) -> bool:
    if not TRACE_LOG.exists():
        print("No traces.jsonl found yet. Run runtime.cli_demo first.")
        return False

    traces = [
        json.loads(line)
        for line in TRACE_LOG.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    failures = [t for t in traces if t.get("intent") == intent and t.get("human_edited")]

    if len(failures) < min_edits:
        print(f"Found {len(failures)} human-edited traces for '{intent}' (need {min_edits}). Skipping.")
        return False

    skill_path = HARNESS_DIR / "skills" / f"{intent}.md"
    current_skill = skill_path.read_text(encoding="utf-8")

    # Promote recent human corrections into the permanent regression suite
    append_new_regression_cases(failures[-10:])

    optimizer_model = os.getenv("OPTIMIZER_MODEL", "o3")
    optimizer_llm = ChatOpenAI(model=optimizer_model).with_structured_output(SkillPatch)

    patch = optimizer_llm.invoke([
        SystemMessage(content=(
            "You improve modular customer support playbooks based on human agent corrections. "
            "Identify the recurring gap between draft_reply and final_reply, and update the Markdown playbook "
            "with concise, generalizable rules. Never hardcode customer names, order numbers, or override policy limits."
        )),
        HumanMessage(content=(
            f"Current Playbook ({intent}.md):\n{current_skill}\n\n"
            f"Recent Human Corrections:\n{json.dumps(failures[-10:], indent=2)}"
        )),
    ])

    print(f"\nProposed Diagnosis: {patch.diagnosis}")
    print("Running offline regression eval gate...")

    if run_eval_gate(target_intent=intent, candidate_skill_md=patch.updated_markdown):
        skill_path.write_text(patch.updated_markdown, encoding="utf-8")
        print(f"SUCCESS: Eval gate passed. Updated {skill_path}")
        return True

    print("BLOCKED: Candidate playbook failed regression checks. No changes written.")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize a support skill playbook from HITL traces.")
    parser.add_argument("--intent", default="refunds", choices=["refunds", "billing", "shipping", "general"])
    parser.add_argument("--min-edits", type=int, default=3)
    args = parser.parse_args()
    optimize_skill(intent=args.intent, min_edits=args.min_edits)
