# CLI Demo - Quick Reference Card

## 🚀 Common Commands

### Single Ticket (Interactive)
```bash
python -m runtime.cli_demo
```
✅ Processes sample ticket with human review prompt

### Single Ticket (Auto-Approve)
```bash
python -m runtime.cli_demo --non-interactive
```
✅ No manual input needed - useful for testing

### Custom Message
```bash
python -m runtime.cli_demo --message "Your message here"
```
✅ Test specific scenarios without editing code

### Batch Processing
```bash
python -m runtime.cli_demo \
  --input-file tickets.json \
  --non-interactive
```
✅ Process 5+ tickets in one run, auto-approve all

### Save Results
```bash
python -m runtime.cli_demo \
  --input-file tickets.json \
  --output-file results/ \
  --non-interactive
```
✅ Results saved as `results_ticket-*.json`

### Debug Mode
```bash
python -m runtime.cli_demo \
  --message "My issue" \
  --log-level DEBUG
```
✅ Detailed logging with timestamps for troubleshooting

### Production Setup
```bash
python -m runtime.cli_demo \
  --db-type postgres \
  --timeout 600 \
  --input-file tickets.json \
  --non-interactive
```
✅ Use PostgreSQL, 10-min timeout, batch processing

---

## 🔧 All Options

```
--message TEXT              Custom customer message
--input-file PATH           JSON file with batch tickets
--output-file PATH          Save results to JSON
--non-interactive          Auto-approve (no human review)
--db-type {sqlite,postgres,memory}  Database (default: sqlite)
--timeout SECONDS          Graph timeout (default: 300)
--log-level {DEBUG,INFO,WARNING,ERROR}  Log verbosity
--help                     Show help
```

---

## 🌍 Environment Variables

```bash
export SUPPORT_DB_TYPE=postgres           # Database type
export SUPPORT_TIMEOUT=600                # Timeout in seconds
export SUPPORT_LOG_LEVEL=DEBUG            # Logging level
export SUPPORT_INTERACTIVE=false          # Non-interactive mode
export SUPPORT_INPUT_FILE=tickets.json    # Input batch file
export SUPPORT_OUTPUT_FILE=results.json   # Output file
```

Then run:
```bash
python -m runtime.cli_demo
```

---

## ✅ Error Handling

| Scenario | Before | After |
|----------|--------|-------|
| Missing file | Crashes | Error message, exit 1 |
| Timeout | Hangs | Logs timeout, continues |
| Bad JSON | JSONDecodeError | Clear error message |
| Missing fields | KeyError | Reports specific keys |
| Invalid message | No validation | Rejected with reason |

---

## 📊 Exit Codes

```bash
python -m runtime.cli_demo
echo $?
# 0 = Success
# 1 = Failure
```

Use in scripts:
```bash
python -m runtime.cli_demo || exit 1
if [ $? -eq 0 ]; then echo "Success!"; fi
```

---

## 📝 Input File Format

Create `tickets.json`:
```json
[
  {"customer_msg": "Issue 1"},
  {"customer_msg": "Issue 2"},
  {"customer_msg": "Issue 3"}
]
```

Then:
```bash
python -m runtime.cli_demo --input-file tickets.json --non-interactive
```

**Output:**
```
Processing complete: 3 succeeded, 0 failed out of 3 total
```

---

## 📂 Output File Format

Result per ticket: `results_ticket-abc123.json`

```json
{
  "ticket_id": "ticket-abc123",
  "human_edited": false,
  "final_reply": "Thank you for contacting us..."
}
```

---

## ⏱️ Logging Levels

```bash
# Most detailed - debugging only
--log-level DEBUG

# Standard - shows operations
--log-level INFO

# Warnings only
--log-level WARNING

# Errors only
--log-level ERROR
```

---

## 🔄 Workflow Examples

### Local Testing
```bash
python -m runtime.cli_demo \
  --message "Test case" \
  --log-level DEBUG
```
👉 Requires human input for review

### Automated Testing
```bash
python -m runtime.cli_demo \
  --input-file tests.json \
  --non-interactive \
  --output-file test_results/ \
  || exit 1
```
👉 Auto-approves, fails pipeline if issues

### Production Batch
```bash
python -m runtime.cli_demo \
  --db-type postgres \
  --input-file daily_tickets.json \
  --output-file results/ \
  --non-interactive \
  --timeout 600
```
👉 Production database, 10-min timeout, batch processing

### Quick Single Test
```bash
python -m runtime.cli_demo --non-interactive
```
👉 No input needed, processes sample ticket

---

## 🐛 Troubleshooting

### Script hangs waiting for input
❌ **Problem:** No `--non-interactive` flag
✅ **Solution:** Add `--non-interactive`

### "File not found" error
❌ **Problem:** Wrong file path
✅ **Solution:** Check file exists and path is correct

### Timeout errors
❌ **Problem:** Default timeout too short
✅ **Solution:** Use `--timeout 600` or higher

### Can't see what's happening
❌ **Problem:** Default logging is INFO only
✅ **Solution:** Use `--log-level DEBUG`

### Need different database
❌ **Problem:** Default uses SQLite
✅ **Solution:** Use `--db-type postgres`

---

## 📚 Documentation Map

| File | Purpose | Read Time |
|------|---------|-----------|
| QUICKSTART.md | Get started quickly | 5 min |
| BEFORE_AFTER.md | See what improved | 10 min |
| IMPROVEMENTS.md | Learn all features | 20 min |
| TESTING_GUIDE.md | Validate functionality | 30 min |
| ENHANCEMENT_INDEX.md | Find anything | 2 min |
| REFERENCE_CARD.md | Quick lookup (this) | 2 min |

---

## 🎯 Cheat Sheet

**I want to:**

| Goal | Command |
|------|---------|
| Run with no input | Add `--non-interactive` |
| Test multiple tickets | Add `--input-file tickets.json` |
| See detailed logs | Add `--log-level DEBUG` |
| Use PostgreSQL | Add `--db-type postgres` |
| Save results | Add `--output-file results/` |
| Custom test message | Add `--message "text"` |
| Longer timeout | Add `--timeout 600` |
| Check exit status | Add `; echo $?` |

---

## 💡 Pro Tips

1. **Combine flags** - Use multiple flags together:
   ```bash
   python -m runtime.cli_demo \
     --input-file tickets.json \
     --output-file results/ \
     --non-interactive \
     --log-level INFO
   ```

2. **Use environment for defaults**:
   ```bash
   export SUPPORT_NON_INTERACTIVE=true
   python -m runtime.cli_demo  # Uses env defaults
   ```

3. **Override env with CLI args**:
   ```bash
   export SUPPORT_DB_TYPE=postgres
   python -m runtime.cli_demo --db-type sqlite  # Uses sqlite
   ```

4. **Check help anytime**:
   ```bash
   python -m runtime.cli_demo --help
   ```

5. **Pipe to file for analysis**:
   ```bash
   python -m runtime.cli_demo \
     --input-file tickets.json \
     --log-level DEBUG \
     > batch_run.log 2>&1
   ```

---

## 🚨 Common Mistakes

| ❌ Mistake | ✅ Fix |
|-----------|--------|
| `python cli_demo.py` | Use `python -m runtime.cli_demo` |
| Hardcoding config | Use CLI args or env vars |
| Forgetting `--non-interactive` | Add flag for automation |
| Running without `--input-file` | Add flag for batch mode |
| Using short timeout | Try `--timeout 600` |
| Missing JSON keys | Check format: `{"customer_msg": "..."}` |

---

## 📋 Setup Checklist

- [ ] Python 3.8+ installed
- [ ] Required packages installed (see requirements.txt)
- [ ] Can run: `python -m runtime.cli_demo --help`
- [ ] Can run: `python -m runtime.cli_demo --non-interactive`
- [ ] Can run batch: `python -m runtime.cli_demo --input-file example_tickets.json --non-interactive`

---

**Last Updated:** November 23, 2024  
**Version:** 1.0  
**Status:** ✅ Ready to Use
