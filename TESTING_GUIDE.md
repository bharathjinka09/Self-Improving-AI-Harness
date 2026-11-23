# Testing Guide: Error Resilience & Configuration Improvements

## Test Scenarios

Each scenario demonstrates a real-world issue the improvements solve.

---

## 1. Error Resilience Tests

### Test 1.1: Handle Missing Graph Build
**Scenario:** Database connection fails

**Before:** 🔴 Uncaught exception, cryptic traceback
```
Traceback (most recent call last):
  File "runtime/cli_demo.py", line 100, in main
    graph = build_support_graph(use_sqlite=True)
ConnectionError: ...
```

**After:** ✅ Clear error message, exit code 1
```bash
$ python -m runtime.cli_demo --db-type postgres
2024-11-23 20:10:12 - __main__ - ERROR - Failed to build support graph: ConnectionError: Connection refused
$ echo $?
1
```

**How to test:**
```bash
# Stop the database service
# Then run:
python -m runtime.cli_demo --db-type postgres
```

---

### Test 1.2: Handle Missing Interrupt Keys
**Scenario:** Graph returns incomplete state

**Before:** 🔴 KeyError with no context
```
KeyError: 'reason'
```

**After:** ✅ Detailed validation error
```bash
$ python -m runtime.cli_demo
2024-11-23 20:10:15 - __main__ - ERROR - Missing fields in interrupt payload: ['reason', 'intent']
2024-11-23 20:10:15 - __main__ - INFO - Processing complete: 0 succeeded, 1 failed out of 1 total
$ echo $?
1
```

**How to test:**
1. Modify `graph.py` to intentionally return incomplete payload
2. Run: `python -m runtime.cli_demo`
3. Observe: Clear error message instead of crash

---

### Test 1.3: Handle Timeout
**Scenario:** Graph takes too long

**Before:** 🔴 Hangs indefinitely or cryptic timeout error
**After:** ✅ Logs timeout, continues to next ticket

**How to test:**
```bash
# Set very short timeout
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --timeout 1 \
  --non-interactive
```

**Expected output:**
```
--- Processing Ticket 1/5 [ticket-abc123] ---
2024-11-23 20:10:14 - __main__ - ERROR - Timeout processing ticket ticket-abc123: ...
Processing complete: 0 succeeded, 1 failed out of 5 total
```

---

### Test 1.4: Handle Invalid JSON Input File
**Scenario:** Batch input file is malformed

**Before:** 🔴 JSONDecodeError with no guidance
**After:** ✅ Clear error message with file path

**How to test:**
```bash
# Create invalid JSON
echo "{invalid json" > bad_tickets.json

python -m runtime.cli_demo --input-file bad_tickets.json
```

**Expected output:**
```
2024-11-23 20:10:11 - __main__ - ERROR - Invalid JSON in input file: Expecting value: line 1 column 2
```

---

### Test 1.5: Handle Missing Input File
**Scenario:** User provides non-existent file

**Before:** 🔴 FileNotFoundError traceback
**After:** ✅ Clear error message

**How to test:**
```bash
python -m runtime.cli_demo --input-file /nonexistent/path/tickets.json
```

**Expected output:**
```
2024-11-23 20:10:11 - __main__ - ERROR - Input file not found: /nonexistent/path/tickets.json
```

---

### Test 1.6: Handle Invalid Message Structure in Batch
**Scenario:** JSON has wrong format

**Before:** 🔴 KeyError on `msg_obj["customer_msg"]`
**After:** ✅ Logs error, continues to next ticket

**How to test:**
```bash
# Create JSON with invalid structure
cat > bad_format.json << 'EOF'
[
  {"message": "Wrong key name"},
  {"customer_msg": "Valid format"}
]
EOF

python -m runtime.cli_demo --input-file bad_format.json --non-interactive
```

**Expected output:**
```
--- Processing Ticket 1/2 [ticket-abc123] ---
2024-11-23 20:10:11 - __main__ - ERROR - Invalid message object at index 1: {'message': 'Wrong key name'}
--- Processing Ticket 2/2 [ticket-def456] ---
2024-11-23 20:10:12 - __main__ - INFO - Processing ticket ticket-def456
...
Processing complete: 1 succeeded, 1 failed out of 2 total
```

---

### Test 1.7: Handle Very Long Message
**Scenario:** User sends extremely long message

**Before:** 🔴 Out of memory or no validation
**After:** ✅ Rejected with clear reason

**How to test:**
```bash
# Generate 50KB message
python -c "print('x' * 50000)" > long_msg.txt
msg=$(cat long_msg.txt)

python -m runtime.cli_demo --message "$msg"
```

**Expected output:**
```
2024-11-23 20:10:11 - __main__ - ERROR - Invalid message: exceeds maximum length of 10000 characters
```

---

## 2. Configuration Flexibility Tests

### Test 2.1: Custom Message
**Scenario:** Test specific edge case

```bash
python -m runtime.cli_demo \
  --message "My order arrived 3 weeks late" \
  --non-interactive
```

**Verify:** Uses custom message instead of default sample

---

### Test 2.2: Batch Processing with Output
**Scenario:** Process multiple tickets, save results

```bash
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --output-file results.json \
  --non-interactive
```

**Verify:**
```bash
# Check results were saved
ls -la results_ticket-*.json

# View one result
cat results_ticket-abc123.json | python -m json.tool
```

**Expected:** 5 JSON files with complete ticket data

---

### Test 2.3: Non-Interactive Mode (Auto-Approve)
**Scenario:** Run in CI/CD without human input

**Before:** 🔴 Hangs waiting for input, test timeout
**After:** ✅ Auto-approves, completes in seconds

```bash
# Without --non-interactive (would hang)
timeout 10 python -m runtime.cli_demo &
# Process hangs, test fails

# With --non-interactive (completes)
time python -m runtime.cli_demo --non-interactive
# real    0m2.345s
```

---

### Test 2.4: Different Database Backends
**Scenario:** Test with PostgreSQL instead of SQLite

```bash
# Start PostgreSQL
docker run -d -e POSTGRES_PASSWORD=password postgres:15

# Run with PostgreSQL
python -m runtime.cli_demo --db-type postgres
```

**Verify:** Uses PostgreSQL instead of default SQLite

---

### Test 2.5: Debug Logging
**Scenario:** Troubleshoot issue with detailed logs

```bash
python -m runtime.cli_demo \
  --message "Test message" \
  --log-level DEBUG \
  --non-interactive
```

**Expected:** Logs include DEBUG level messages with timestamps:
```
2024-11-23 20:10:13,000 - __main__ - DEBUG - Customer message: Test message
```

---

### Test 2.6: Custom Timeout
**Scenario:** Override default timeout

```bash
# 10 second timeout
python -m runtime.cli_demo --timeout 10 --non-interactive

# Check logs show timeout config
# Expected: "[...] - INFO - Starting support harness CLI demo with config: {'timeout': 10, ...}"
```

---

### Test 2.7: Environment Variable Configuration
**Scenario:** Use env vars instead of CLI args

```bash
export SUPPORT_DB_TYPE=postgres
export SUPPORT_TIMEOUT=600
export SUPPORT_LOG_LEVEL=DEBUG
export SUPPORT_NON_INTERACTIVE=true

python -m runtime.cli_demo
```

**Verify:** Uses environment variables for config

---

### Test 2.8: CLI Args Override Environment Variables
**Scenario:** CLI args have priority

```bash
export SUPPORT_DB_TYPE=postgres

# CLI arg overrides env var
python -m runtime.cli_demo --db-type sqlite --non-interactive

# Check log: "db_type: sqlite" (not postgres)
```

---

## 3. Batch Processing Tests

### Test 3.1: Process Multiple Tickets
**Scenario:** Handle 5 tickets in one run

```bash
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --output-file results/ \
  --non-interactive
```

**Expected output:**
```
--- Processing Ticket 1/5 [ticket-abc123] ---
...
--- Processing Ticket 5/5 [ticket-ijk789] ---
Processing complete: 5 succeeded, 0 failed out of 5 total
```

**Verify:**
```bash
# Count result files
ls results_ticket-*.json | wc -l  # Should be 5
```

---

### Test 3.2: Handle Partial Failures in Batch
**Scenario:** Some tickets succeed, some fail

**How to test:**
1. Create batch file with valid and invalid messages
2. Run batch process
3. Verify success/fail count

```bash
cat > mixed_tickets.json << 'EOF'
[
  {"customer_msg": "Valid message"},
  {"invalid_key": "Missing customer_msg"},
  {"customer_msg": "Another valid"}
]
EOF

python -m runtime.cli_demo \
  --input-file mixed_tickets.json \
  --non-interactive
```

**Expected:**
```
Processing complete: 2 succeeded, 1 failed out of 3 total
```

---

### Test 3.3: Exit Code Reflects Batch Results
**Scenario:** Use exit code in CI/CD

```bash
# Success case
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --non-interactive
echo "Exit code: $?"  # Should be 0

# Failure case  
python -m runtime.cli_demo \
  --input-file bad_format.json
echo "Exit code: $?"  # Should be 1
```

---

## 4. Performance Tests

### Test 4.1: Measure Processing Time
**Scenario:** Track performance

```bash
time python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --non-interactive
```

**Output:**
```
real    0m5.234s
user    0m4.123s
sys     0m1.111s
```

**Verify:** Logs show individual timing for each invocation:
```
Graph invocation completed in 1.05s
Resume invocation completed in 0.42s
```

---

### Test 4.2: Monitor with Different Timeouts
**Scenario:** Ensure timeout feature works

```bash
# Fast timeout (should fail)
python -m runtime.cli_demo --timeout 1 --non-interactive

# Reasonable timeout (should succeed)
python -m runtime.cli_demo --timeout 60 --non-interactive
```

**Expected:** Fast timeout shows error, reasonable timeout completes

---

## 5. Integration Tests

### Test 5.1: CI/CD Pipeline Integration
**Scenario:** Use in CI/CD with failure detection

```bash
#!/bin/bash
set -e  # Exit on error

python -m runtime.cli_demo \
  --input-file tests/tickets.json \
  --non-interactive \
  --log-level INFO

if [ $? -eq 0 ]; then
  echo "✅ All support tickets processed successfully"
  exit 0
else
  echo "❌ Some tickets failed—see logs above"
  exit 1
fi
```

---

### Test 5.2: Local Testing Workflow
**Scenario:** Develop with better feedback

```bash
# 1. Debug with one message
python -m runtime.cli_demo \
  --message "My specific test case" \
  --log-level DEBUG

# 2. Test with batch
python -m runtime.cli_demo \
  --input-file test_cases.json \
  --non-interactive

# 3. Save results
python -m runtime.cli_demo \
  --input-file test_cases.json \
  --output-file results.json \
  --non-interactive
```

---

## Running All Tests

```bash
#!/bin/bash
# Run all test scenarios

echo "=== Test 1: Error Handling ==="
python -m runtime.cli_demo --input-file /nonexistent/file.json

echo -e "\n=== Test 2: Custom Message ==="
python -m runtime.cli_demo \
  --message "Test message" \
  --non-interactive

echo -e "\n=== Test 3: Batch Processing ==="
python -m runtime.cli_demo \
  --input-file example_tickets.json \
  --non-interactive

echo -e "\n=== Test 4: Debug Logging ==="
python -m runtime.cli_demo \
  --message "Debug test" \
  --log-level DEBUG \
  --non-interactive

echo -e "\n=== All Tests Complete ==="
```

---

## Expected Results Summary

| Test | Before | After |
|------|--------|-------|
| Missing file | Crashes | Error message, exit 1 |
| Timeout | Hangs | Logs timeout, continues |
| Malformed JSON | JSONDecodeError | Clear error message |
| Batch processing | Not possible | Works with 100+ tickets |
| Non-interactive | Hangs on input | Auto-approves |
| Performance tracking | None | Detailed timing logs |
| CI/CD integration | Difficult | Easy with exit codes |
| Debugging | Cryptic errors | Detailed logs with levels |
