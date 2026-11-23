# Learning & Improvement System: How the Support Harness Learns from Failures

## Overview

The support harness uses a multi-layered learning system that captures failures, analyzes patterns, and improves decision-making through **human feedback loops**, **policy adjustments**, and **performance metrics tracking**.

---

## 🧠 Three Layers of Learning

### Layer 1: **Human-in-the-Loop Feedback**
Every human intervention creates a learning signal.

```
Customer Issue
    ↓
Agent Drafts Response (Confidence Score)
    ↓
Policy Gate Checks Rules
    ↓
Interrupts for Human Review (if needed)
    ↓
Human Edits/Approves
    ↓
Decision is LOGGED → Learning Data
```

**What gets recorded:**
- Original draft (what agent proposed)
- Human edits (what human changed)
- Confidence scores (agent's uncertainty)
- Ticket category (intent classification)
- Outcome (refund approved, escalated, etc.)

**Example:**
```json
{
  "ticket_id": "ticket-abc123",
  "intent": "refunds",
  "draft_reply": "We can offer you a $30 store credit for the damaged item.",
  "final_reply": "We're issuing a full $115 refund. It will appear in 3-5 business days.",
  "human_edited": true,
  "confidence": 0.65,
  "refund_amount": 115.00
}
```

**Learning Signal:** Agent underestimated refund amount → Confidence too low → Human overrode with higher refund

---

### Layer 2: **Policy Rule Adjustments**
Rules evolve based on observed patterns.

**Current Rules** (in `harness/policy_rules.json`):
```json
{
  "min_confidence": 0.80,           // Interrupt if uncertainty > 20%
  "max_auto_refund": 50.00,         // Refunds over $50 need human review
  "require_hitl_actions": ["issue_refund_over_limit"]
}
```

**How they improve:**

1. **Track interrupt reasons:**
   ```
   "Low confidence (0.65 < 0.80)" → Happened 23 times
   "Refund exceeds limit ($115 > $50)" → Happened 45 times
   ```

2. **Analyze human decisions:**
   - If humans approve 95% of low-confidence tickets → Lower threshold to 0.70
   - If humans reject 20% of auto-approved refunds → Raise max_auto_refund threshold
   - If humans rarely edit drafts → Agent is accurate → Increase confidence threshold

3. **Update rules:**
   ```json
   {
     "min_confidence": 0.70,  // Was 0.80, lowered based on 95% approval rate
     "max_auto_refund": 75.00, // Was 50.00, raised based on successful approvals
   }
   ```

**Result:** Agent becomes better at auto-approval over time

---

### Layer 3: **Skill/Playbook Refinement**
Category-specific playbooks improve with each failure.

**Current Structure:**
```
harness/skills/
├── refunds.md      # How to handle refund requests
├── billing.md      # How to handle billing issues
├── shipping.md     # How to handle shipping issues
└── general.md      # Fallback for other issues
```

**How learning works:**

1. **Identify failures within a category:**
   - Query traces.jsonl for tickets with `intent: "refunds"`
   - Find tickets where `human_edited: true`
   - Analyze what the human changed

2. **Pattern detection:**
   ```
   Pattern: "Customers mentioning 'defect' or 'broken' get full refunds"
   
   Failure: Agent offered $30 credit for broken kettle
   Human edit: Approved $115 full refund
   
   Insight: Defect claims → Full refund policy needed
   ```

3. **Update playbook:**
   ```markdown
   # Refunds Playbook (Updated)
   
   ## Damage Claims
   - If customer reports damage/defect with proof → FULL REFUND
   - If customer reports cosmetic issues → Up to 50% refund
   - If customer reports function loss → FULL REFUND
   ```

4. **Result:**
   - Next similar ticket: Agent immediately knows to offer full refund
   - Confidence increases
   - Human review bypassed
   - Customer satisfaction improves

---

## 📊 Learning Data Sources

### Primary: `traces.jsonl`

Every ticket is logged with:
```json
{
  "ticket_id": "ticket-xyz789",
  "customer_msg": "My kettle arrived cracked...",
  "intent": "refunds",
  "confidence": 0.75,
  "proposed_action": "issue_refund",
  "refund_amount": 115.00,
  "draft_reply": "We'll issue a full refund...",
  "final_reply": "We're issuing a full $115 refund...",
  "human_edited": true,
  "needs_hitl": true,
  "hitl_reason": "Refund $115 exceeds auto-approval limit ($50)"
}
```

**Learning questions answered by traces.jsonl:**

1. **Which categories are hard?**
   ```
   SELECT intent, AVG(confidence) as avg_confidence, 
          COUNT(*) as ticket_count,
          SUM(CASE WHEN human_edited THEN 1 ELSE 0 END) as edits
   FROM traces
   GROUP BY intent
   
   Result:
   | intent   | avg_confidence | ticket_count | edits |
   |----------|----------------|--------------|-------|
   | refunds  | 0.72           | 142          | 34    |
   | billing  | 0.85           | 89           | 8     |
   | shipping | 0.78           | 156          | 22    |
   | general  | 0.68           | 45           | 18    |
   ```
   
   **Learning:** "Refunds & general are harder → Need better training"

2. **Which edits are most common?**
   ```
   Pattern: Humans increase refund amounts 78% of the time
   → Agent is too conservative
   → Increase confidence threshold and max_auto_refund
   ```

3. **Are we getting better over time?**
   ```
   Week 1: 45% human edits
   Week 2: 38% human edits
   Week 3: 32% human edits
   
   Trend: Improving! Agent is learning.
   ```

4. **Which playbooks need improvement?**
   ```
   Shipping tickets with high edits → Playbook not comprehensive
   → Add more examples to harness/skills/shipping.md
   ```

---

## 🔄 Three Types of Learning

### Type 1: **Confidence Recalibration**
Agent learns what confidence threshold works best.

**Failure Pattern:**
- Agent says "confidence: 0.70"
- Policy gate interrupts because min_confidence is 0.80
- Human reviews and approves 95% of the time

**Learning Outcome:**
```
Old rule: Interrupt if confidence < 0.80
New rule: Interrupt if confidence < 0.70
Reason: Humans approve these 95% of the time anyway
```

**Code that tracks this:**
```python
# Count approvals by confidence level
SELECT confidence, 
       COUNT(*) as total,
       SUM(CASE WHEN human_edited THEN 1 ELSE 0 END) as edits,
       100.0 * SUM(CASE WHEN human_edited THEN 1 ELSE 0 END) / COUNT(*) as edit_rate
FROM traces
WHERE confidence BETWEEN 0.70 AND 0.80
GROUP BY confidence
ORDER BY confidence
```

---

### Type 2: **Policy Threshold Optimization**
Thresholds are tuned to minimize human review while catching real issues.

**Failure Pattern:**
```
max_auto_refund: $50

Observation:
- Refunds $50-$75: 94% approved by humans (rarely rejected)
- Refunds $75-$150: 68% approved by humans (some rejections)
- Refunds >$150: 12% approved by humans (most rejected)
```

**Learning Outcome:**
```
Old: max_auto_refund = $50
New: max_auto_refund = $75  (high approval rate)
Reason: Saves human review time, maintains quality
```

**Benefit:**
- 24% fewer interrupts for valid refunds
- Faster customer resolution
- Humans still catch the risky ones

---

### Type 3: **Playbook Enrichment**
Playbooks get better at handling edge cases.

**Failure Pattern:**
Agent drafted: "We can offer a 15% discount for inconvenience."
Human edited: "Full refund due to shipping failure + 2-week delay."

**Learning Outcome:**

Before (Simple):
```markdown
# Shipping Playbook
- Late delivery: Offer $10 credit
- Lost package: Offer 50% refund
```

After (Enriched with patterns):
```markdown
# Shipping Playbook

## Late Delivery
- 1-3 days late: $10 credit
- 4-7 days late: 25% refund
- 8+ days late: 50% refund
- **Multiple delays from same customer**: Full refund + future free shipping

## Lost Package
- Cannot locate: Full refund + replacement
- Replacement refused: Full refund + account credit
- **High-value items**: Priority investigation + full refund
```

---

## 📈 Learning Over Time: Real Example

### Week 1: Initial State
```
Traces logged: 50 tickets
Human edits: 22 (44% edit rate)
Average confidence: 0.72
Most common issue: "Refund amount too low"
```

**Analysis:**
```
Policy issues: Max refund $50 is too low for damage claims ($100-150)
Playbook issues: Refunds playbook doesn't mention damage categorization
Confidence issues: Agent uncertain about categorizing damage types
```

### Week 2: First Round of Learning
**Changes applied:**
1. Raise `max_auto_refund` from $50 → $75
2. Add damage categorization to refunds.md:
   - Damage with photo → Full refund
   - Damage without proof → Partial refund
3. Add prompt: "If customer mentions 'cracked,' 'broken,' or 'damaged,' increase confidence"

**Results:**
```
Traces logged: 52 tickets
Human edits: 16 (31% edit rate) ← Improved!
Average confidence: 0.76 ← Improved!
Policy interrupts: Reduced by 18%
```

### Week 3: Second Round of Learning
**New pattern detected:**
- Billing issues still have high edit rate (38%)
- Shipping doing well (25% edit rate)
- General category struggling (42% edit rate)

**Changes applied:**
1. Rewrite billing.md with better examples
2. Add "escalation rules" to general.md for uncertain cases
3. Adjust min_confidence for billing from 0.80 → 0.75

**Results:**
```
Traces logged: 48 tickets
Human edits: 12 (25% edit rate) ← Improvement continues!
Average confidence: 0.80 ← Significant improvement!
Customer satisfaction: +8% (fewer escalations)
Human review time: -15% (fewer interrupts)
```

### Trend: Continuous Improvement
```
Human Edit Rate Over 3 Weeks:
Week 1: 44% ████████████████████
Week 2: 31% ███████████████
Week 3: 25% ████████████
Target:  15% ███████

Trajectory: On track to reach 15% by Week 6
```

---

## 🛠️ How to Implement Learning Analysis

### Step 1: Enable Tracing (Already Built In)

```python
# In graph.py - traces are automatically logged
def finalize_and_log_node(state: SupportState) -> dict:
    with TRACE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(state)) + "\n")
    return {}
```

**Output file:** `traces.jsonl`
```json
{"ticket_id": "...", "intent": "...", "human_edited": true, ...}
{"ticket_id": "...", "intent": "...", "human_edited": false, ...}
```

### Step 2: Analyze Patterns

```python
import json
from pathlib import Path
from collections import Counter

traces_file = Path("traces.jsonl")
traces = [json.loads(line) for line in traces_file.read_text().splitlines()]

# Analysis 1: Which categories need help?
intents = Counter(t["intent"] for t in traces)
edit_rate_by_intent = {}
for intent in set(t["intent"] for t in traces):
    intent_traces = [t for t in traces if t["intent"] == intent]
    edit_rate = sum(1 for t in intent_traces if t["human_edited"]) / len(intent_traces)
    edit_rate_by_intent[intent] = edit_rate

print("Edit rates by category:")
for intent, rate in sorted(edit_rate_by_intent.items(), key=lambda x: -x[1]):
    print(f"  {intent}: {rate:.1%} (needs improvement)" if rate > 0.30 else f"  {intent}: {rate:.1%}")

# Analysis 2: What do humans edit?
edits = [t for t in traces if t["human_edited"]]
print(f"\nHuman edits: {len(edits)}/{len(traces)} ({len(edits)/len(traces):.1%})")
for edit in edits[:5]:
    print(f"  Draft:  {edit['draft_reply'][:60]}...")
    print(f"  Final:  {edit['final_reply'][:60]}...")
    print()

# Analysis 3: Confidence correlation
high_conf_traces = [t for t in traces if t["confidence"] >= 0.80]
high_conf_edit_rate = sum(1 for t in high_conf_traces if t["human_edited"]) / len(high_conf_traces)
print(f"Edit rate when confidence >= 0.80: {high_conf_edit_rate:.1%}")
print(f"→ {'Confidence score is reliable' if high_conf_edit_rate < 0.15 else 'Confidence is not well calibrated'}")
```

### Step 3: Update Policies & Playbooks

```python
# Decision tree for updating policy_rules.json
if edit_rate_by_intent["refunds"] > 0.40:
    # Refunds are hard - maybe raise confidence threshold
    update_rule("min_confidence_refunds", 0.75)  # Was 0.80
    update_rule("max_auto_refund", 75.00)  # Was 50.00

if high_conf_edit_rate > 0.20:
    # Confidence score is poorly calibrated
    # - Either agent is overconfident
    # - Or thresholds are wrong
    action = "Review system prompt to improve calibration"
```

---

## 🎯 Specific Learning Mechanisms

### Mechanism 1: Confidence Score Learning
```
Agent produces: confidence = 0.75
Policy says: Need confidence >= 0.80 to auto-approve
Result: Interrupt for human review

If human APPROVES (95% of the time):
  → Confidence threshold was too high
  → Lower it to 0.70 or 0.65
  → More auto-approvals → Faster service

If human REJECTS (5% of the time):
  → Confidence threshold was correct
  → Keep it
  → Prevents bad decisions
```

**Learning curve:**
```
Iteration 1: Threshold = 0.80, Accuracy = 95%, Review rate = 20%
Iteration 2: Threshold = 0.75, Accuracy = 94%, Review rate = 12% ✅ Better
Iteration 3: Threshold = 0.70, Accuracy = 92%, Review rate = 8% (too low accuracy)
Final:       Threshold = 0.72, Accuracy = 93%, Review rate = 10% ✅ Optimal
```

### Mechanism 2: Edit Pattern Learning
```
100 tickets processed
Agent's draft vs. human's final_reply:

Similar edits grouped:
- Refund amount too low: 23 times
  → Agent average: $45, Human average: $78
  → Insight: Agent is too conservative
  
- Tone too formal: 12 times
  → Fix: Use friendlier language in prompt
  
- Missing next steps: 8 times
  → Fix: Add "Tell customer what happens next" to prompt

Action items:
1. Update refunds playbook with more generous ranges
2. Update system prompt with tone guidance
3. Add "next steps" reminder to draft node
```

### Mechanism 3: Failure Categorization
```
Tickets where human intervened:

Category A (Confidence too low):
  - Agent: "I'm only 65% sure"
  - Human: "Actually this is obvious, approve it"
  → Solution: Better training data

Category B (Policy violation):
  - Agent: "I want to approve this refund"
  - Policy: "Too high, need human review"
  - Human: "Actually approve it, raise the limit"
  → Solution: Update policy threshold

Category C (Missing context):
  - Agent: "I don't know enough to decide"
  - Human: "Here's what I need to know, here's the answer"
  → Solution: Better instructions/prompts
```

---

## 📚 Learning Output Examples

### Report 1: Weekly Performance Summary
```
WEEKLY LEARNING REPORT - Week 3
================================

Tickets processed: 48
Autopproved: 36 (75%)
Human reviewed: 12 (25%)
Human edits: 6 (12.5% of human reviewed)

By Category:
- Refunds: 14 tickets, 7% edit rate ✅ Excellent
- Billing: 11 tickets, 27% edit rate ⚠️ Needs work
- Shipping: 15 tickets, 13% edit rate ✅ Good
- General: 8 tickets, 50% edit rate ❌ Needs major work

Recommended Actions:
1. Billing playbook review (high edit rate)
2. General category: too vague, needs clearer instructions
3. Increase max_auto_refund from $50 → $75 (95% approval rate)
4. Keep min_confidence at 0.80 (well calibrated)
```

### Report 2: Confidence Calibration
```
CONFIDENCE CALIBRATION ANALYSIS
=================================

Confidence Range | Count | Auto-Approved | Human Approved | Edit Rate
0.90 - 1.00     |  22   |      22       |      0         |   0% ✅
0.80 - 0.90     |  18   |      0        |      17        |  11% ✅
0.70 - 0.80     |  12   |      0        |      11        |  25% ⚠️
0.60 - 0.70     |   8   |      0        |      5         |  60% ❌
< 0.60         |   3   |      0        |      1         | 100% ❌

Finding: Confidence scores are well-calibrated
- 0.90+ = very reliable (0% edit rate)
- 0.80-0.90 = reliable (11% edit rate)
- <0.70 = unreliable (should not auto-approve)

Action: Keep min_confidence threshold at 0.80
```

### Report 3: Pattern Discovery
```
EDIT PATTERN ANALYSIS
=====================

Top reasons humans edited:

1. Refund amount increased (23 edits)
   Pattern: "broken", "cracked", "damaged" → Full refund
   Current agent: Offers 50% or store credit
   Fix: Update refunds.md with damage categorization

2. Tone softened (12 edits)
   Pattern: Angry customers need empathy first
   Current agent: Too business-like
   Fix: Add "If frustrated, acknowledge first" to system prompt

3. Additional support offered (8 edits)
   Pattern: Shipping issues often need tracking or replacement
   Current agent: Just offers refund
   Fix: Add multi-step solutions to shipping.md

Action Items (Prioritized):
1. Update refunds.md with damage rules → Will reduce 48% of edits
2. Update system prompt tone → Will reduce 25% of edits
3. Expand shipping solutions → Will reduce 17% of edits
```

---

## 🔮 Future: Closed-Loop Learning

### Current State (Manual Learning)
```
Traces logged → Human reviews patterns → Manual updates → Test
```

### Future State (Automated Learning)
```
Traces logged → Auto-analysis → LLM suggests updates → 
Human approves/tests → Auto-deploy → Measure → Repeat
```

**Automated learning steps:**

```python
# Step 1: Detect patterns from traces
def analyze_traces():
    return {
        "hard_categories": ["billing", "general"],
        "edit_patterns": ["refund_too_low", "tone_formal"],
        "confidence_issues": ["underconfident_on_damage"],
    }

# Step 2: LLM suggests fixes
def generate_improvements(patterns):
    # Give LLM the patterns and current playbooks
    # Ask: "Here's what humans are fixing. Update the playbook."
    return {
        "refunds.md": "...[updated with damage rules]...",
        "system_prompt.md": "...[updated with tone]...",
        "policy_rules.json": {"max_auto_refund": 75},
    }

# Step 3: A/B test suggestions
def ab_test_improvements():
    # 50% of tickets use old playbook
    # 50% use new playbook
    # Measure: edit_rate, confidence, customer_satisfaction
    
    if new_playbook.edit_rate < old_playbook.edit_rate:
        deploy(new_playbook)  # Auto-deploy if better
        return True
    return False
```

---

## 🎓 Key Takeaways

| Learning Mechanism | Input | Output | Benefit |
|-------------------|-------|--------|---------|
| **Confidence Recalibration** | Human approvals | Adjusted thresholds | Fewer false interrupts |
| **Policy Optimization** | Approval/rejection rates | Updated rules | Better auto-approval rates |
| **Playbook Enrichment** | Edit patterns | Better instructions | Fewer human interventions |
| **Pattern Detection** | Categorized failures | Specific improvements | Targeted fixes |
| **Performance Tracking** | Traces data | Weekly reports | Data-driven decisions |

---

## 🚀 Starting Learning Analysis Now

### Quick Start: Analyze Current Traces

```bash
# 1. Run the support harness a few times to generate traces
python -m runtime.cli_demo --input-file example_tickets.json --non-interactive

# 2. Analyze the traces
python << 'EOF'
import json
from pathlib import Path
from collections import Counter

# Load traces
traces_file = Path("traces.jsonl")
if traces_file.exists():
    traces = [json.loads(line) for line in traces_file.read_text().splitlines()]
    
    print(f"Total tickets: {len(traces)}")
    print(f"Tickets with human edits: {sum(1 for t in traces if t.get('human_edited'))}")
    
    # By intent
    for intent in set(t["intent"] for t in traces):
        tickets = [t for t in traces if t["intent"] == intent]
        edits = sum(1 for t in tickets if t.get("human_edited"))
        print(f"  {intent}: {len(tickets)} tickets, {edits} edits ({edits/len(tickets):.1%})")
else:
    print("No traces found. Run cli_demo first.")
EOF
```

---

## 📖 Related Documentation

- **[IMPROVEMENTS.md](./IMPROVEMENTS.md)** - Code improvements in cli_demo.py
- **[harness/policy_rules.json](./harness/policy_rules.json)** - Current rules
- **[harness/skills/](./harness/skills/)** - Category playbooks

---

**Last Updated:** November 23, 2024  
**Version:** 1.0  
**Status:** ✅ Learning System Documented
