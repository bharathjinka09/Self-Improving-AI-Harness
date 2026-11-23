# Quick Start: Enhanced CLI Demo

## What Changed?

The `cli_demo.py` now has:
- ✅ **Robust error handling** - Won't crash on edge cases
- ✅ **CLI arguments** - Flexible configuration without code changes
- ✅ **Batch processing** - Handle multiple tickets in one run
- ✅ **Structured logging** - Detailed debugging info
- ✅ **State validation** - Catch data issues early

## Run It Now

### Option 1: Single Ticket (Interactive)
```bash
python -m runtime.cli_demo
```
Works exactly like before—processes sample ticket with human review.

### Option 2: Batch Processing (Auto-Approve)
```bash
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --output-file results.json \
  --non-interactive
```

**Output:**
```
--- Processing Ticket 1/5 [ticket-abc123] ---
Customer: Hi, my ceramic pour-over kettle arrived cracked today...

============================================================
=== TICKET COMPLETED & LOGGED TO traces.jsonl ===
============================================================
Human Edited : False
Final Reply  : We understand your frustration. We're issuing a full refund immediately...

--- Processing Ticket 2/5 [ticket-def456] ---
...
```

### Option 3: Debug Mode
```bash
python -m runtime.cli_demo \
  --message "My order never arrived" \
  --non-interactive \
  --log-level DEBUG
```

Outputs detailed logs for troubleshooting.

## Command Reference

```bash
python -m runtime.cli_demo [OPTIONS]

Options:
  --message TEXT              Custom customer message
  --input-file PATH           JSON file with batch tickets
  --output-file PATH          Save results to JSON
  --non-interactive           Auto-approve (no human review)
  --db-type {sqlite,postgres,memory}  Database backend (default: sqlite)
  --timeout SECONDS           Graph invocation timeout (default: 300)
  --log-level {DEBUG,INFO,WARNING,ERROR}  Logging verbosity
  --help                      Show this help
```

## Examples

### Process 5 tickets in batch, save results
```bash
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --output-file results/ \
  --non-interactive
```

### Test with custom timeout (useful for CI/CD)
```bash
python -m runtime.cli_demo --non-interactive --timeout 60
```

### Enable debugging for a specific message
```bash
python -m runtime.cli_demo \
  --message "Issue description here" \
  --log-level DEBUG
```

## What Improvements Help?

| Scenario | Improvement |
|----------|-------------|
| **Production crashes** | ✅ Error handling catches exceptions, doesn't crash |
| **Need to test multiple messages** | ✅ Batch mode processes JSON file |
| **Can't sit and approve each draft** | ✅ `--non-interactive` auto-approves |
| **Graph hangs unexpectedly** | ✅ `--timeout` parameter with logging |
| **Finding bugs** | ✅ `--log-level DEBUG` with timestamps |
| **Different databases** | ✅ `--db-type postgres` etc. |
| **CI/CD integration** | ✅ Exit codes + non-interactive mode |

## Exit Codes

```bash
python -m runtime.cli_demo
echo $?  # Returns 0 if all succeeded, 1 if any failed
```

Use in shell scripts:
```bash
if python -m runtime.cli_demo --input-file tickets.json; then
  echo "All tickets processed!"
else
  echo "Some tickets failed—check logs"
fi
```

## Errors Are Now Helpful

**Before:**
```
KeyError: 'reason'
```

**After:**
```
2024-11-23 20:10:15 - __main__ - ERROR - Missing fields in interrupt payload: ['reason', 'intent']
2024-11-23 20:10:15 - __main__ - INFO - Processing complete: 0 succeeded, 1 failed out of 1 total
```

## Tips

1. **Testing**: Use `--non-interactive` and `example_tickets.json` to test without manual input
2. **Debugging**: Add `--log-level DEBUG` to see all state transitions
3. **Production**: Use `--db-type postgres` and `--timeout 600` for stability
4. **CI/CD**: Use exit codes to fail builds on errors:
   ```bash
   python -m runtime.cli_demo --input-file tests.json || exit 1
   ```

## See Full Docs

For complete details, see [IMPROVEMENTS.md](./IMPROVEMENTS.md)
