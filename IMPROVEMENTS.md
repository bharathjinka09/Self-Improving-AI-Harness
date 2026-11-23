# CLI Demo Improvements: Error Resilience & Configuration Flexibility

## Overview
The enhanced `cli_demo.py` provides production-ready error handling, flexible configuration, and batch processing capabilities while maintaining backward compatibility with the original single-ticket workflow.

## Key Improvements

### 1. **Error Resilience & Robustness**

#### Comprehensive Error Handling
- **Try-catch blocks** around all graph invocations, file I/O, and state transitions
- **Specific exception types** (TimeoutError, KeyError, FileNotFoundError, JSONDecodeError) for targeted recovery
- **State validation** at each stage to catch malformed results early
- **Graceful degradation** with meaningful error logging and exit codes

#### Input Validation
```python
# Validates customer messages before processing
validate_message(msg: str) -> bool
# - Ensures non-empty string
# - Enforces maximum length (10,000 chars) to prevent abuse
```

#### State Validation
```python
# Validates result structure at each stage
validate_result_state(result: Dict, stage: str) -> bool
# - Checks initial result for __interrupt__ or final_reply
# - Checks resume result for human_edited and final_reply
# - Reports missing keys with clear error messages
```

#### Interrupt Payload Validation
- Validates all required fields in human-review payloads before accessing
- Prevents AttributeError/KeyError when payload structure is unexpected

#### Timing & Performance Tracking
- Logs graph invocation duration in seconds
- Helps identify bottlenecks in resume vs. initial processing
- Useful for SLA monitoring

---

### 2. **CLI Configuration Flexibility**

#### Command-Line Arguments
```bash
# Custom message
python -m runtime.cli_demo --message "My order is broken"

# Batch processing
python -m runtime.cli_demo --input-file tickets.json --output-file results.json

# Non-interactive mode (auto-approve drafts)
python -m runtime.cli_demo --non-interactive

# Different database backends
python -m runtime.cli_demo --db-type postgres

# Control logging verbosity
python -m runtime.cli_demo --log-level DEBUG

# Set graph timeout
python -m runtime.cli_demo --timeout 60
```

#### Environment Variable Support
```bash
export SUPPORT_DB_TYPE=postgres
export SUPPORT_INTERACTIVE=false
export SUPPORT_TIMEOUT=600
export SUPPORT_INPUT_FILE=tickets.json
export SUPPORT_OUTPUT_FILE=results.json
export SUPPORT_LOG_LEVEL=DEBUG

python -m runtime.cli_demo
```

#### Configuration Object
- `CLIDemoConfig` class encapsulates all settings
- Loads from CLI args, environment variables, or defaults
- Easy to extend with new parameters

#### Batch Processing
- Load multiple tickets from JSON file
- Process all tickets in one run
- Track success/failure counts
- Save individual results with ticket IDs

---

## Usage Examples

### Single Interactive Ticket (Default)
```bash
python -m runtime.cli_demo
```
**Output:**
- Prompts for human review
- Allows editing agent draft
- Logs to console and traces.jsonl

---

### Single Ticket, Auto-Approved (Non-Interactive)
```bash
python -m runtime.cli_demo --non-interactive
```
**Use case:** Automated testing, CI/CD pipelines, low-confidence scenarios

---

### Custom Message
```bash
python -m runtime.cli_demo --message "My product arrived damaged"
```
**Use case:** Testing specific edge cases

---

### Batch Processing from File
**tickets.json:**
```json
[
  {"customer_msg": "Order arrived cracked, requesting refund"},
  {"customer_msg": "Delivery was 5 days late"},
  {"customer_msg": "Wrong item received"}
]
```

**Command:**
```bash
python -m runtime.cli_demo \
  --input-file tickets.json \
  --output-file results.json \
  --non-interactive
```

**Output:**
- `results_ticket-abc123.json`: Full result for ticket 1
- `results_ticket-def456.json`: Full result for ticket 2
- `results_ticket-ghi789.json`: Full result for ticket 3
- Console summary: `3 succeeded, 0 failed`

---

### Debug Mode with PostgreSQL
```bash
python -m runtime.cli_demo \
  --db-type postgres \
  --log-level DEBUG
```

**Output:**
- Detailed logs of all operations
- Stack traces on errors
- State snapshots at each stage

---

## Error Handling Scenarios

### Scenario 1: Invalid Graph Build
```python
# Before: Crashes with no error message
# After: Logs error and returns exit code 1
logger.error("Failed to build support graph: TimeoutError: Connection refused")
```

### Scenario 2: Malformed Interrupt Payload
```python
# Before: KeyError on payload['reason']
# After: Validates payload structure and logs missing keys
logger.error("Missing fields in interrupt payload: ['reason', 'intent']")
```

### Scenario 3: Input File Corruption
```python
# Before: JSON decode exception, unclear error
# After: Clear error message with file path
logger.error("Invalid JSON in input file: Expecting value: line 1 column 2")
```

### Scenario 4: Timeout During Processing
```bash
python -m runtime.cli_demo --timeout 10
# Timeout in graph invocation → logs and continues to next ticket
logger.error("Timeout processing ticket ticket-abc123: ...")
```

---

## Logging Output

All operations are logged with timestamps and levels:

```
2024-11-23 20:10:11,000 - __main__ - INFO - Starting support harness CLI demo with config: {...}
2024-11-23 20:10:12,000 - __main__ - INFO - Building support graph with db_type=sqlite
2024-11-23 20:10:13,000 - __main__ - INFO - Processing ticket ticket-abc123
2024-11-23 20:10:14,500 - __main__ - INFO - Graph invocation completed in 1.50s
2024-11-23 20:10:15,000 - __main__ - INFO - Resume invocation completed in 0.45s
2024-11-23 20:10:15,100 - __main__ - INFO - Result saved to results_ticket-abc123.json
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tickets processed successfully |
| 1 | One or more tickets failed |

**Usage in scripts:**
```bash
python -m runtime.cli_demo || echo "Demo failed!"
if [ $? -eq 0 ]; then echo "All tickets approved"; fi
```

---

## Backward Compatibility

The original usage still works:
```bash
# Single sample ticket, interactive
python -m runtime.cli_demo
```

All original functionality is preserved while adding optional CLI args.

---

## Testing the Improvements

### Test 1: Error Handling
```bash
# Should handle gracefully (non-zero exit)
python -m runtime.cli_demo --input-file nonexistent.json
```

### Test 2: Batch Processing
```bash
echo '[{"customer_msg": "Test 1"}, {"customer_msg": "Test 2"}]' > test.json
python -m runtime.cli_demo --input-file test.json --non-interactive
# Should output: "2 succeeded, 0 failed"
```

### Test 3: Configuration Priority
```bash
# CLI args override environment variables
export SUPPORT_DB_TYPE=postgres
python -m runtime.cli_demo --db-type sqlite  # Uses sqlite
```

### Test 4: Timeout Handling
```bash
# Should timeout and report
python -m runtime.cli_demo --timeout 1
```

---

## Migration Guide

**For existing scripts:**
- No changes needed; default behavior is identical
- Add `--non-interactive` for automation
- Add `--input-file` for batch processing

**For new workflows:**
- Use `--log-level DEBUG` for troubleshooting
- Use `--output-file` to persist results
- Use `--db-type postgres` for production scale

---

## Future Enhancements

Potential additions (non-breaking):
- Retry logic with exponential backoff
- Metrics export (Prometheus format)
- Multi-threading for batch processing
- Result aggregation and reporting
- Integration with external logging services
