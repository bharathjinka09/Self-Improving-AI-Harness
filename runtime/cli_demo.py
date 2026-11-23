import uuid
from langgraph.types import Command
from runtime.graph import build_support_graph


def main():
    graph = build_support_graph(use_sqlite=True)
    ticket_id = f"ticket-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": ticket_id}}

    sample_msg = (
        "Hi, my ceramic pour-over kettle arrived cracked today (Order #4821). "
        "It cost $115—can I please get a full refund?"
    )
    print(f"\n--- Incoming Ticket [{ticket_id}] ---")
    print(f"Customer: {sample_msg}\n")

    result = graph.invoke(
        {"ticket_id": ticket_id, "customer_msg": sample_msg},
        config=config,
    )

    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("=== PAUSED FOR HUMAN-IN-THE-LOOP REVIEW ===")
        print(f"Reason          : {payload['reason']}")
        print(f"Intent          : {payload['intent']}")
        print(f"Proposed Action : {payload['proposed_action']} (${payload['refund_amount']:.2f})")
        print(f"Agent Draft     :\n{payload['draft_reply']}\n")

        edited = input("Press Enter to approve draft, or type an edited reply:\n> ").strip()
        final_reply = edited if edited else payload["draft_reply"]

        final_state = graph.invoke(
            Command(resume={"final_reply": final_reply}),
            config=config,
        )
        print("\n=== TICKET COMPLETED & LOGGED TO traces.jsonl ===")
        print(f"Human Edited : {final_state['human_edited']}")
        print(f"Final Reply  : {final_state['final_reply']}")
    else:
        print("=== AUTO-APPROVED & COMPLETED ===")
        print(f"Final Reply  : {result['final_reply']}")


if __name__ == "__main__":
    main()
