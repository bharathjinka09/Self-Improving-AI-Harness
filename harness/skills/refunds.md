# Refunds Playbook

## Eligibility & Auto-Approval
- Damaged, defective, or wrong items reported within 30 days of delivery qualify for a full refund.
- Refunds up to $50.00 can be proposed with `proposed_action="issue_refund"` and normal confidence.
- Refunds strictly above $50.00 can still be drafted with `proposed_action="issue_refund"`, as the deterministic policy gate will automatically route them to a human reviewer.

## Communication Guidelines
- Apologize briefly for the inconvenience.
- Confirm the exact refund amount and note that funds appear on the original payment method within 3–5 business days.
- Do not ask the customer to ship back damaged items under $50.00.
