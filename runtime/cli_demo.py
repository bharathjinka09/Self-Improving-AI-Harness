import argparse
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from time import time

from langgraph.types import Command
from runtime.graph import build_support_graph

logger = logging.getLogger(__name__)


class CLIDemoConfig:
    """Configuration management for CLI demo."""

    def __init__(
        self,
        db_type: str = "sqlite",
        interactive: bool = True,
        timeout: int = 300,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        log_level: str = "INFO",
        custom_message: Optional[str] = None,
    ):
        self.db_type = db_type
        self.interactive = interactive
        self.timeout = timeout
        self.input_file = input_file
        self.output_file = output_file
        self.log_level = log_level
        self.custom_message = custom_message

    @classmethod
    def from_env(cls) -> "CLIDemoConfig":
        """Load configuration from environment variables."""
        return cls(
            db_type=os.getenv("SUPPORT_DB_TYPE", "sqlite"),
            interactive=os.getenv("SUPPORT_INTERACTIVE", "true").lower() == "true",
            timeout=int(os.getenv("SUPPORT_TIMEOUT", "300")),
            input_file=os.getenv("SUPPORT_INPUT_FILE"),
            output_file=os.getenv("SUPPORT_OUTPUT_FILE"),
            log_level=os.getenv("SUPPORT_LOG_LEVEL", "INFO"),
        )


def setup_logging(log_level: str) -> None:
    """Configure logging for the CLI demo."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def validate_message(msg: str) -> bool:
    """Validate customer message format and content."""
    if not msg or not isinstance(msg, str):
        logger.error("Invalid message: must be a non-empty string")
        return False
    if len(msg) > 10000:
        logger.error("Invalid message: exceeds maximum length of 10000 characters")
        return False
    return True


def validate_result_state(result: Dict[str, Any], stage: str = "initial") -> bool:
    """Validate result state structure and required keys."""
    if not isinstance(result, dict):
        logger.error(f"Invalid result type at {stage}: expected dict, got {type(result)}")
        return False

    if stage == "initial":
        if "__interrupt__" not in result and "final_reply" not in result:
            logger.error(f"Invalid result at {stage}: missing '__interrupt__' or 'final_reply'")
            return False
    elif stage == "resume":
        required_keys = ["human_edited", "final_reply"]
        missing = [k for k in required_keys if k not in result]
        if missing:
            logger.error(f"Invalid result at {stage}: missing keys {missing}")
            return False
    return True


def process_ticket(
    graph: Any,
    ticket_id: str,
    customer_msg: str,
    config: Dict[str, Any],
    cfg: CLIDemoConfig,
) -> Optional[Dict[str, Any]]:
    """Process a support ticket through the graph."""
    try:
        logger.info(f"Processing ticket {ticket_id}")
        logger.debug(f"Customer message: {customer_msg}")

        start_time = time()
        result = graph.invoke(
            {"ticket_id": ticket_id, "customer_msg": customer_msg},
            config=config,
        )
        elapsed = time() - start_time
        logger.info(f"Graph invocation completed in {elapsed:.2f}s")

        if not validate_result_state(result, stage="initial"):
            return None

        return result

    except TimeoutError as e:
        logger.error(f"Timeout processing ticket {ticket_id}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Missing key in result: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing ticket {ticket_id}: {type(e).__name__}: {e}")
        return None


def handle_human_review(
    graph: Any,
    result: Dict[str, Any],
    config: Dict[str, Any],
    cfg: CLIDemoConfig,
) -> Optional[Dict[str, Any]]:
    """Handle human-in-the-loop review stage."""
    if "__interrupt__" not in result:
        return None

    try:
        payload = result["__interrupt__"][0].value

        required_fields = ["reason", "intent", "proposed_action", "refund_amount", "draft_reply"]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            logger.error(f"Missing fields in interrupt payload: {missing}")
            return None

        print("\n" + "=" * 60)
        print("=== PAUSED FOR HUMAN-IN-THE-LOOP REVIEW ===")
        print("=" * 60)
        print(f"Reason          : {payload['reason']}")
        print(f"Intent          : {payload['intent']}")
        print(f"Proposed Action : {payload['proposed_action']} (${payload['refund_amount']:.2f})")
        print(f"\nAgent Draft:\n{payload['draft_reply']}\n")

        if not cfg.interactive:
            logger.info("Non-interactive mode: auto-approving draft")
            final_reply = payload["draft_reply"]
        else:
            edited = input("Press Enter to approve draft, or type an edited reply:\n> ").strip()
            final_reply = edited if edited else payload["draft_reply"]

        logger.debug(f"Final reply determined: {len(final_reply)} chars")

        start_time = time()
        final_state = graph.invoke(
            Command(resume={"final_reply": final_reply}),
            config=config,
        )
        elapsed = time() - start_time
        logger.info(f"Resume invocation completed in {elapsed:.2f}s")

        if not validate_result_state(final_state, stage="resume"):
            return None

        return final_state

    except KeyError as e:
        logger.error(f"Missing key in interrupt payload: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in human review: {type(e).__name__}: {e}")
        return None


def save_result(result: Dict[str, Any], output_file: Optional[str]) -> bool:
    """Save result to output file (JSON format)."""
    if not output_file:
        return True

    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Result saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save result to {output_file}: {type(e).__name__}: {e}")
        return False


def load_messages_from_file(input_file: str) -> Optional[list]:
    """Load messages from JSON file. Format: [{"customer_msg": "..."}]"""
    try:
        with open(input_file, "r") as f:
            messages = json.load(f)
        if not isinstance(messages, list):
            logger.error("Input file must contain a JSON array")
            return None
        logger.info(f"Loaded {len(messages)} messages from {input_file}")
        return messages
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading input file: {type(e).__name__}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Support harness CLI demo with error resilience and configuration flexibility"
    )
    parser.add_argument(
        "--db-type",
        choices=["sqlite", "postgres", "memory"],
        default="sqlite",
        help="Database backend type (default: sqlite)",
    )
    parser.add_argument(
        "--message",
        type=str,
        help="Custom customer message (overrides default sample)",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="JSON file with messages to process (batch mode, non-interactive)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Save final result to JSON file",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without interactive human review (auto-approve)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Graph invocation timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    cfg = CLIDemoConfig(
        db_type=args.db_type,
        interactive=not args.non_interactive,
        timeout=args.timeout,
        input_file=args.input_file,
        output_file=args.output_file,
        log_level=args.log_level,
        custom_message=args.message,
    )

    setup_logging(cfg.log_level)
    logger.info(f"Starting support harness CLI demo with config: {cfg.__dict__}")

    try:
        logger.info(f"Building support graph with db_type={cfg.db_type}")
        graph = build_support_graph(use_sqlite=(cfg.db_type == "sqlite"))
    except Exception as e:
        logger.error(f"Failed to build support graph: {type(e).__name__}: {e}")
        return 1

    messages_to_process = []

    if cfg.input_file:
        logger.info(f"Batch mode: loading messages from {cfg.input_file}")
        loaded = load_messages_from_file(cfg.input_file)
        if not loaded:
            logger.error("Failed to load input file")
            return 1
        messages_to_process = loaded
    else:
        default_msg = (
            "Hi, my ceramic pour-over kettle arrived cracked today (Order #4821). "
            "It cost $115—can I please get a full refund?"
        )
        messages_to_process = [{"customer_msg": cfg.custom_message or default_msg}]

    success_count = 0
    error_count = 0

    for idx, msg_obj in enumerate(messages_to_process, 1):
        if not isinstance(msg_obj, dict) or "customer_msg" not in msg_obj:
            logger.error(f"Invalid message object at index {idx}: {msg_obj}")
            error_count += 1
            continue

        customer_msg = msg_obj["customer_msg"]

        if not validate_message(customer_msg):
            error_count += 1
            continue

        ticket_id = f"ticket-{uuid.uuid4().hex[:6]}"
        config = {"configurable": {"thread_id": ticket_id}}

        print(f"\n--- Processing Ticket {idx}/{len(messages_to_process)} [{ticket_id}] ---")
        print(f"Customer: {customer_msg}\n")

        result = process_ticket(graph, ticket_id, customer_msg, config, cfg)
        if not result:
            error_count += 1
            continue

        if "__interrupt__" in result:
            final_state = handle_human_review(graph, result, config, cfg)
            if not final_state:
                error_count += 1
                continue
            result = final_state

        print("\n" + "=" * 60)
        print("=== TICKET COMPLETED & LOGGED TO traces.jsonl ===")
        print("=" * 60)
        print(f"Human Edited : {result.get('human_edited', 'N/A')}")
        print(f"Final Reply  : {result.get('final_reply', 'N/A')}")

        if cfg.output_file:
            save_result(result, cfg.output_file.replace(".json", f"_{ticket_id}.json"))

        success_count += 1

    logger.info(
        f"Processing complete: {success_count} succeeded, {error_count} failed "
        f"out of {len(messages_to_process)} total"
    )

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
