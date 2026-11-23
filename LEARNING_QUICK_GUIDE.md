# Learning System: Quick Visual Guide

## 🧠 How the System Learns (3-Minute Overview)

```
TICKET ARRIVES
      ↓
AGENT CLASSIFIES (refunds/billing/shipping/general)
      ↓
AGENT DRAFTS RESPONSE (with confidence score)
      ↓
POLICY GATE CHECKS RULES
      ├─ Confidence too low? → INTERRUPT for human review
      ├─ Refund too high? → INTERRUPT for human review
      └─ All OK? → AUTO-APPROVE
      ↓
IF INTERRUPTED:
  ├─ HUMAN REVIEWS DRAFT
  ├─ HUMAN APPROVES OR EDITS ← 🎓 LEARNING SIGNAL!
  └─ ANY EDIT = OPPORTUNITY TO IMPROVE
      ↓
RESPONSE SENT TO CUSTOMER
      ↓
ENTIRE INTERACTION LOGGED IN traces.jsonl ← 📊 LEARNING DATA
      ↓
ANALYTICS ENGINE ANALYZES PATTERNS
      ├─ Which categories are hard?
      ├─ Are confidence scores accurate?
      ├─ What do humans keep fixing?
      └─ How is the agent improving?
      ↓
IMPROVEMENTS SUGGESTED
      ├─ Update policy_rules.json (thresholds)
      ├─ Update harness/skills/*.md (playbooks)
      └─ Adjust system_prompt.md (instructions)
      ↓
LOOP REPEATS (agent gets better each time)
```

---

## 📊 Learning Signals (What the System Learns From)

### Signal 1: Human Approvals
```
Agent: "I'm 75% confident we should give full refund"
Human: "✅ Yes, approve it"

Learning: Confidence=0.75 is accurate for this category
→ Lower threshold from 0.80 to 0.75 → Faster approvals
```

### Signal 2: Human Rejections
```
Agent: "I'm 95% confident we should give refund"
Human: "❌ No, reject it - policy violation"

Learning: Confidence=0.95 is overconfident for this scenario
→ System prompt needs refinement
```

### Signal 3: Human Edits (Most Important!)
```
Agent draft:  "We can offer $30 store credit for the damaged item"
Human final:  "We're issuing a full $115 refund..."

Learning: 
- Agent was too conservative
- Damage claims need full refunds
- Confidence score was too low
→ Update refunds.md with damage handling rules
```

### Signal 4: Edit Patterns (System-Level Learning)
```
Pattern 1: 23 times human increased refund amounts
  → Agent is too conservative → Raise thresholds

Pattern 2: 12 times human added empathetic language
  → System prompt is too formal → Make it warmer

Pattern 3: 8 times human added next steps
  → Agent forgets to explain what happens next
  → Add reminder to draft prompt
```

---

## 🔄 Three Types of Learning

### Type 1: Confidence Recalibration (Accuracy Learning)

**What it does:**
- Monitors how often high-confidence predictions are correct
- Adjusts confidence thresholds based on approval rates

**Example:**
```
Week 1: min_confidence = 0.80
  → 20 tickets at 0.75-0.79 confidence
  → 19 approved by humans (95% approval rate)
  → Decision: Humans approve 95% → Threshold too high

Week 2: min_confidence = 0.70
  → 25 tickets at 0.70-0.79 confidence
  → 22 approved (88% approval rate)
  → Decision: Good balance, keep it

Week 3: Continue monitoring...
```

### Type 2: Policy Optimization (Efficiency Learning)

**What it does:**
- Tracks which decisions go to human review vs. auto-approved
- Adjusts policy thresholds to maximize auto-approval without losing quality

**Example:**
```
Current policy: max_auto_refund = $50

Observation:
  - Refunds $50-$75: 94% approved by humans
  - Refunds $75-$100: 68% approved
  - Refunds >$100: 12% approved

Decision: Raise max_auto_refund to $75
  - 94% approval rate = good quality
  - Saves ~18% of human review time
  - Customers get faster resolution
```

### Type 3: Playbook Enrichment (Knowledge Learning)

**What it does:**
- Analyzes patterns in human edits
- Identifies gaps in playbooks
- Updates category-specific instructions

**Example:**
```
Detection: Humans frequently edit refunds for "damage claims"

Analysis:
  - 15 customers said "cracked", "broken", "damaged"
  - Agent offered 50% refund each time
  - Human changed to full refund each time
  - Pattern: 100% override rate

Update: Add to harness/skills/refunds.md:
  
  ## Damage Claims
  - Customer reports damage with photo → FULL REFUND
  - Customer reports damage without proof → 50% refund
  - Customer reports defect → FULL REFUND
```

---

## 📈 Learning Over Time (Real Example)

```
                EDIT RATE OVER 3 WEEKS
                (% of tickets edited by humans)

Week 1:    ████████████████████ 44%
            Agent is new, needs learning

Week 2:    ███████████████      31%
            Improvement! Rules updated, playbooks enriched

Week 3:    ████████████         25%
            Continuing to improve

Week 6:    ████████             15% ← Target
            Fully trained agent
```

**What changed:**
- Week 1→2: Updated refunds.md with damage rules → 13% improvement
- Week 2→3: Fixed billing playbook, added empathy to prompt → 6% improvement
- Week 3→6: Continued refinement of all categories → 10% more improvement

---

## 🛠️ How to Use the Learning System

### Step 1: Generate Learning Data
```bash
# Run tickets through the system
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --non-interactive
```
✅ Creates `traces.jsonl` with learning data

### Step 2: Analyze Learning Data
```bash
# See what the system is learning
python -m runtime.learning_analyzer
```

**Output shows:**
```
📊 OVERVIEW
Total tickets processed: 50
Tickets edited by humans: 12
Overall edit rate: 24% ← Target: 15%

📈 PERFORMANCE BY CATEGORY
refunds    ✅ Excellent  Edit rate:   8% (1/12) | Confidence: 0.82
shipping   ✅ Good       Edit rate:  13% (2/15) | Confidence: 0.79
billing    ⚠️  Needs work Edit rate:  27% (3/11) | Confidence: 0.68
general    ❌ Needs work Edit rate:  50% (4/8)  | Confidence: 0.55

🔍 TOP EDIT PATTERNS
• refund_introduced               3 times (25%)
• tone_softened_added_empathy    2 times (17%)
• next_steps_added               2 times (17%)

💡 RECOMMENDATIONS
1. 🔧 BILLING has 27% edit rate. Update harness/skills/billing.md
2. 🎯 25% of edits are "refund_introduced". Fix: Lower refund thresholds
3. ⚠️  Low-confidence predictions are mostly correct. Try lowering threshold to 0.70
```

### Step 3: Apply Improvements
Based on recommendations, update:

**A) Policy Rules** (if recommendations suggest confidence/threshold changes)
```json
{
  "min_confidence": 0.70,  // Was 0.80 - lowered based on 88% approval rate
  "max_auto_refund": 75.00 // Was 50.00 - raised based on success rate
}
```

**B) Playbooks** (if recommendations suggest content updates)
```markdown
# Update harness/skills/billing.md with better examples
```

**C) System Prompt** (if recommendations suggest tone/instruction changes)
```markdown
# Update harness/system_prompt.md with clearer instructions
```

### Step 4: Measure Improvement
```bash
# Run more tickets
python -m runtime.cli_demo --input-file new_batch.json --non-interactive

# Analyze again
python -m runtime.learning_analyzer

# Compare: Did edit rate decrease? Did confidence increase?
```

---

## 🎯 Key Metrics

### Overall Health: Edit Rate
```
< 15% → 🏆 Excellent (agent is well-trained)
15-25% → ✅ Good (normal healthy range)
25-40% → ⚠️ Warning (needs improvement)
> 40% → ❌ Critical (major retraining needed)
```

### Category Health: Edit Rate by Intent
```
refunds   < 15% → Agent understands refund policy well
billing   < 15% → Agent handles billing issues well
shipping  < 15% → Agent resolves shipping issues well
general   < 15% → Agent handles edge cases well
```

### Confidence Quality: Edit Rate by Confidence
```
0.90-1.00 → Should have < 5% edit rate (is agent overconfident?)
0.80-0.90 → Should have < 15% edit rate (reliable range)
0.70-0.80 → May have 20-30% edit rate (uncertain range)
0.60-0.70 → May have > 50% edit rate (should interrupt human)
< 0.60    → Should always go to human (unreliable)
```

---

## 🔮 Learning Signals in Action

### Real Scenario: Learning from Failure

**Ticket 1:**
```
Customer: "My kettle arrived cracked, never used it. Order #4821, $115"
Agent draft: "We can offer a 15% discount ($17) for inconvenience"
Confidence: 0.65

Policy gate: Confidence < 0.80 → INTERRUPT
Human review: "This is damage - full refund!"
Human final: "Full refund of $115 approved."
```

**Signal recorded:** `"refund_too_low"` edit

**Ticket 2 (similar issue):**
```
Customer: "My grinder is broken, never worked properly. Cost $89"
Agent draft: "We're issuing a full refund for the broken grinder."
Confidence: 0.78 → Learned from Ticket 1!

Policy gate: Confidence < 0.80 but close → Might still interrupt
  (If we updated min_confidence to 0.75)

Human review: "✅ Approve" → No edit needed!
```

**Result:** Agent learned and improved on the second similar ticket!

---

## 📚 Learning Data Files

### traces.jsonl (Raw Learning Data)
```json
{"ticket_id": "ticket-abc", "intent": "refunds", "confidence": 0.75, "human_edited": true, ...}
{"ticket_id": "ticket-def", "intent": "billing", "confidence": 0.82, "human_edited": false, ...}
...
```

Each line = one ticket with complete learning information

### policy_rules.json (Learned Rules)
```json
{
  "min_confidence": 0.80,
  "max_auto_refund": 50.00,
  "require_hitl_actions": ["issue_refund_over_limit"]
}
```

Updated based on learning signals

### harness/skills/*.md (Learned Playbooks)
```markdown
# refunds.md - Updated with knowledge from failures

## Damage Claims
- Cracked/broken: Full refund
- Cosmetic damage: 50% refund
- Never used: Full refund
```

Enriched with patterns discovered from traces

---

## 🚀 Starting Your Learning Journey

### Week 1: Establish Baseline
```bash
# Generate initial traces
python -m runtime.cli_demo --input-file large_batch.json --non-interactive

# Analyze
python -m runtime.learning_analyzer

# Note: Initial edit rate will be high (30-50%)
```

### Week 2: First Improvements
```bash
# Apply recommendations from Week 1 analysis
# - Update 1-2 playbooks
# - Maybe adjust 1 policy threshold

# Generate more traces
python -m runtime.cli_demo --input-file another_batch.json --non-interactive

# Analyze
python -m runtime.learning_analyzer

# Should see 10-20% improvement
```

### Week 3+: Continuous Improvement
```bash
# Repeat weekly
# Track trends
# Apply targeted fixes
# Measure impact

# Goal: Reach 15% edit rate and maintain it
```

---

## 🎓 Learning System Checklist

- [ ] Generated initial traces.jsonl
- [ ] Ran learning_analyzer.py
- [ ] Read top recommendations
- [ ] Updated 1-2 playbooks based on patterns
- [ ] Re-ran tickets and re-analyzed
- [ ] Measured improvement in edit rate
- [ ] Tracked which changes had biggest impact
- [ ] Set target edit rate (e.g., 20%)
- [ ] Scheduled weekly analysis reviews
- [ ] Planning continuous improvement process

---

## 💡 Key Insight

**The system doesn't learn automatically — humans make it learn.**

The traces are just data. The learning happens when you:
1. ✅ Analyze the data (learning_analyzer.py)
2. ✅ Understand the patterns (recommendations)
3. ✅ Apply fixes (update playbooks/rules)
4. ✅ Measure the impact (re-analyze)
5. ✅ Repeat

Each iteration makes the agent smarter.

---

**Next Steps:**
1. Run `python -m runtime.learning_analyzer`
2. Read the recommendations
3. Update one playbook based on top pattern
4. Re-run analysis and compare

---

**Learn More:** See `LEARNING_SYSTEM.md` for complete details
