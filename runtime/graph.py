import json
import os
import sqlite3
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field

load_dotenv()

HARNESS_DIR = Path(__file__).resolve().parent.parent / "harness"
TRACE_LOG = Path(__file__).resolve().parent.parent / "traces.jsonl"
CHECKPOINT_DB = Path(__file__).resolve().parent.parent / "checkpoints.sqlite"


class RouteDecision(BaseModel):
    intent: Literal["refunds", "billing", "shipping", "general"]
    confidence: float = Field(ge=0.0, le=1.0)


class AgentDraft(BaseModel):
    proposed_action: Literal["none", "issue_refund", "update_address"]
    refund_amount: float = 0.0
    draft_reply: str
    confidence: float = Field(ge=0.0, le=1.0)


class SupportState(TypedDict):
    ticket_id: str
    customer_msg: str
    intent: str
    proposed_action: str
    refund_amount: float
    draft_reply: str
    confidence: float
    needs_hitl: bool
    hitl_reason: str
    final_reply: str
    human_edited: bool


def get_llm() -> ChatOpenAI:
    model_name = os.getenv("SUPPORT_AGENT_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model_name, temperature=0)


def load_harness_prompt(intent: str, override_skill_md: str | None = None) -> str:
    base_prompt = (HARNESS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    if override_skill_md is not None:
        skill_text = override_skill_md
    else:
        skill_path = HARNESS_DIR / "skills" / f"{intent}.md"
        skill_text = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
    return f"{base_prompt}\n\n## Active Playbook ({intent})\n{skill_text}"


def classify_node(state: SupportState) -> dict:
    router = get_llm().with_structured_output(RouteDecision)
    res = router.invoke([
        SystemMessage(content="Classify the customer support ticket into refunds, billing, shipping, or general."),
        HumanMessage(content=state["customer_msg"]),
    ])
    return {"intent": res.intent, "confidence": res.confidence}


def draft_node(state: SupportState) -> dict:
    system_prompt = load_harness_prompt(state["intent"])
    drafter = get_llm().with_structured_output(AgentDraft)
    res = drafter.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["customer_msg"]),
    ])
    return {
        "proposed_action": res.proposed_action,
        "refund_amount": res.refund_amount,
        "draft_reply": res.draft_reply,
        "confidence": min(state["confidence"], res.confidence),
    }


def policy_gate_node(state: SupportState) -> dict:
    rules = json.loads((HARNESS_DIR / "policy_rules.json").read_text(encoding="utf-8"))
    if state["confidence"] < rules["min_confidence"]:
        return {
            "needs_hitl": True,
            "hitl_reason": f"Low confidence ({state['confidence']:.2f} < {rules['min_confidence']:.2f})",
        }
    if state["proposed_action"] == "issue_refund" and state["refund_amount"] > rules["max_auto_refund"]:
        return {
            "needs_hitl": True,
            "hitl_reason": f"Refund ${state['refund_amount']:.2f} exceeds auto-approval limit (${rules['max_auto_refund']:.2f})",
        }
    return {
        "needs_hitl": False,
        "hitl_reason": "",
        "final_reply": state["draft_reply"],
        "human_edited": False,
    }


def human_review_node(state: SupportState) -> dict:
    human_decision = interrupt({
        "ticket_id": state["ticket_id"],
        "intent": state["intent"],
        "reason": state["hitl_reason"],
        "proposed_action": state["proposed_action"],
        "refund_amount": state["refund_amount"],
        "draft_reply": state["draft_reply"],
    })
    final_reply = human_decision.get("final_reply", state["draft_reply"])
    edited = final_reply.strip() != state["draft_reply"].strip()
    return {"final_reply": final_reply, "human_edited": edited}


def finalize_and_log_node(state: SupportState) -> dict:
    # Execute external side effects (e.g., Stripe refund API) strictly after approval
    with TRACE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(state)) + "\n")
    return {}


def build_support_graph(use_sqlite: bool = True):
    builder = StateGraph(SupportState)
    builder.add_node("classify", classify_node)
    builder.add_node("draft", draft_node)
    builder.add_node("policy_gate", policy_gate_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("finalize", finalize_and_log_node)

    builder.add_edge(START, "classify")
    builder.add_edge("classify", "draft")
    builder.add_edge("draft", "policy_gate")
    builder.add_conditional_edges(
        "policy_gate",
        lambda s: "human_review" if s["needs_hitl"] else "finalize",
    )
    builder.add_edge("human_review", "finalize")
    builder.add_edge("finalize", END)

    if use_sqlite:
        conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()
