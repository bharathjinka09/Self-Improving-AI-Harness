import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from runtime.graph import AgentDraft, get_llm, load_harness_prompt

load_dotenv()

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "evals" / "golden_tickets.jsonl"


class JudgeVerdict(BaseModel):
    passed: bool
    reason: str = Field(description="Brief explanation of why the draft met or violated expectations.")


def run_eval_gate(
    target_intent: str | None = None,
    candidate_skill_md: str | None = None,
) -> bool:
    if not GOLDEN_PATH.exists():
        print("No golden_tickets.jsonl found; skipping eval gate.")
        return True

    tickets = [
        json.loads(line)
        for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if target_intent:
        tickets = [t for t in tickets if t["intent"] == target_intent]

    if not tickets:
        print(f"No golden tickets for intent '{target_intent}'.")
        return True

    drafter = get_llm().with_structured_output(AgentDraft)
    judge = get_llm().with_structured_output(JudgeVerdict)

    passed_count = 0
    for ticket in tickets:
        override = candidate_skill_md if ticket["intent"] == target_intent else None
        sys_prompt = load_harness_prompt(ticket["intent"], override_skill_md=override)

        draft = drafter.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=ticket["customer_msg"]),
        ])

        verdict = judge.invoke([
            SystemMessage(content=(
                "You are a strict QA evaluator for customer support responses. "
                "Verify whether the agent's proposed_action, refund_amount, and draft_reply "
                "satisfy the expected criteria without hallucinating policies."
            )),
            HumanMessage(content=json.dumps({
                "customer_msg": ticket["customer_msg"],
                "expected_action": ticket["expected_action"],
                "expected_criteria": ticket["expected_criteria"],
                "actual_action": draft.proposed_action,
                "actual_refund_amount": draft.refund_amount,
                "actual_reply": draft.draft_reply,
            }, indent=2)),
        ])

        status = "PASS" if verdict.passed else "FAIL"
        print(f"[{status}] {ticket['id']} ({ticket['intent']}): {verdict.reason}")
        if verdict.passed:
            passed_count += 1

    pass_rate = passed_count / len(tickets)
    print(f"Eval Summary: {passed_count}/{len(tickets)} passed ({pass_rate:.0%})")
    return passed_count == len(tickets)


if __name__ == "__main__":
    ok = run_eval_gate()
    raise SystemExit(0 if ok else 1)
