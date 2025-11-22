# Error Handling Showcase

> **Comprehensive error handling patterns for production AI agents**

---

## Overview

This example demonstrates production-grade error handling strategies for AI agents:

- **Retry Logic** with exponential backoff
- **Circuit Breaker Pattern** to prevent cascading failures
- **Input Validation** and sanitization
- **Timeout Handling** for long-running operations
- **Graceful Degradation** with fallback strategies
- **Error Logging** and monitoring

---

## What You'll Learn

✅ How to handle API failures gracefully  
✅ When and how to retry operations  
✅ Circuit breaker pattern for resilient systems  
✅ Input validation to prevent security issues  
✅ Error recovery strategies  
✅ Production-ready error handling patterns

---

## Prerequisites

- Python 3.10+
- OpenAI API key (optional for tool-only demos)

---

## Setup

```bash
# 1. Navigate to this directory
cd examples/python-error-handling

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Set up API key for full demo
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

---

## Running the Example

### With API Key (Full Demo)

```bash
python main.py
```

### Without API Key (Tool Demos Only)

```bash
# The example will automatically run tool demos if no API key is found
python main.py
```

---

## Error Handling Patterns Demonstrated

### 1. Retry with Exponential Backoff

**Problem:** Network calls and external APIs can fail temporarily.

**Solution:** Automatically retry with increasing delays between attempts.

```python
@retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
def calculate_with_retry(expression: str):
    # Will retry up to 3 times with delays: 1s, 2s, 4s
    result = eval(expression)
    return result
```

**When to Use:**
- API calls to external services
- Database queries
- File operations on network drives
- Any operation that might fail temporarily

**Benefits:**
- Handles transient failures automatically
- Exponential backoff prevents overwhelming failing services
- Configurable retry strategy

---

### 2. Circuit Breaker Pattern

**Problem:** Calling a failing service repeatedly can:
- Waste resources
- Cause cascading failures
- Prevent recovery

**Solution:** "Open the circuit" after threshold failures, preventing calls until recovery.

```python
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

result = circuit_breaker.call(api_function, endpoint)
```

**States:**
- **CLOSED**: Normal operation, calls go through
- **OPEN**: Too many failures, block all calls
- **HALF_OPEN**: Testing recovery, allow one call

**When to Use:**
- External API integrations
- Database connections
- Microservice communication
- Any dependency that might fail

---

### 3. Input Validation

**Problem:** Invalid or malicious input can cause:
- Security vulnerabilities (path traversal, injection)
- Application crashes
- Incorrect results

**Solution:** Validate and sanitize all inputs before processing.

```python
validator = InputValidator()

# Validate string length and characters
text = validator.validate_string(
    user_input,
    min_length=1,
    max_length=1000
)

# Validate numeric ranges
amount = validator.validate_number(
    value,
    min_value=0,
    max_value=1000000
)

# Sanitize file paths
safe_path = validator.sanitize_path(user_path)
```

**Validation Types Demonstrated:**
- String length constraints
- Allowed character sets
- Numeric range checks
- Path sanitization (prevent directory traversal)

---

### 4. Timeout Handling

**Problem:** Operations can hang indefinitely, blocking the agent.

**Solution:** Set maximum execution time for operations.

```python
with timeout(5.0):
    result = long_running_operation()
# Raises ToolTimeoutError if exceeds 5 seconds
```

**When to Use:**
- Network operations
- File I/O
- External process execution
- Any potentially long-running operation

---

### 5. Graceful Degradation

**Problem:** When a service fails, the entire agent shouldn't crash.

**Solution:** Provide fallback behavior or cached data.

```python
try:
    result = circuit_breaker.call(fetch_live_data)
except CircuitBreakerOpen:
    # Circuit is open, use cached data instead
    result = get_cached_data()
```

**Strategies:**
- Use cached/stale data
- Return partial results
- Provide default values
- Inform user of degraded service

---

## Code Structure

### Error Types

```python
ToolError                # Base exception
├── ToolTimeoutError     # Operation timeout
├── ToolValidationError  # Invalid input
└── CircuitBreakerOpen   # Circuit is open
```

### Components

**CircuitBreaker**
- Tracks failure count
- Opens circuit after threshold
- Attempts recovery after timeout
- Transitions: CLOSED → OPEN → HALF_OPEN → CLOSED

**InputValidator**
- String validation (length, characters)
- Number validation (range)
- Path sanitization (security)

**ResilientTools**
- Calculator with retry logic
- API call with circuit breaker
- File operation with validation

**ResilientAgent**
- Full agent with error-resilient LLM calls
- Safe tool execution
- Error logging and recovery

---

## Example Scenarios

### Scenario 1: Handling API Failures

```
You: Call the weather API

Agent calls API → Fails (simulated 30% failure rate)
↓
Retry with backoff: 1s delay
↓
Retry again: 2s delay
↓
Success on 3rd attempt
↓
Agent: "The weather is sunny, 72°F"
```

### Scenario 2: Circuit Breaker Protection

```
You: Call the weather API repeatedly

Call 1: Fails
Call 2: Fails  
Call 3: Fails (circuit opens)
↓
Circuit Breaker: OPEN
↓
Call 4: Blocked (circuit open)
Call 5: Blocked (circuit open)
↓
Wait 30 seconds...
↓
Call 6: Allowed (circuit half-open)
↓
If succeeds → Circuit CLOSED (normal operation)
If fails → Circuit OPEN again
```

### Scenario 3: Input Validation

```
You: Write to ../etc/passwd

Agent validates path → Security violation detected
↓
Error: "Path cannot contain '..'"
↓
Agent: "I cannot write to that location for security reasons."
```

---

## Best Practices Demonstrated

### ✅ DO:

1. **Validate All Inputs**
   ```python
   # Always validate before processing
   validated_input = validator.validate_string(user_input, max_length=1000)
   ```

2. **Use Retry for Transient Failures**
   ```python
   @retry_with_backoff(max_retries=3)
   def api_call():
       return requests.get(url)
   ```

3. **Implement Circuit Breakers for External Services**
   ```python
   result = circuit_breaker.call(external_api_function)
   ```

4. **Log All Errors**
   ```python
   logger.error(f"Operation failed: {error}")
   self.error_log.append(error_details)
   ```

5. **Provide Meaningful Error Messages**
   ```python
   return {
       "success": False,
       "error": "Connection timeout after 30s",
       "error_type": "timeout",
       "suggested_action": "Please try again later"
   }
   ```

### ❌ DON'T:

1. **Don't Retry Indefinitely**
   ```python
   # BAD: Could retry forever
   while True:
       try:
           result = operation()
           break
       except:
           time.sleep(1)
   ```

2. **Don't Ignore Errors Silently**
   ```python
   # BAD: Hides problems
   try:
       critical_operation()
   except:
       pass  # Silent failure!
   ```

3. **Don't Trust User Input**
   ```python
   # BAD: Security vulnerability
   filepath = user_input  # Could be "../../../etc/passwd"
   with open(filepath, 'w') as f:
       f.write(content)
   ```

4. **Don't Let Operations Run Forever**
   ```python
   # BAD: Could hang indefinitely
   result = external_api_call()  # No timeout!
   ```

---

## Error Recovery Strategies

| Error Type | Strategy | Example |
|------------|----------|---------|
| Transient Network | Retry with backoff | API timeout → Retry 3x |
| Service Down | Circuit breaker | API fails 5x → Open circuit |
| Invalid Input | Validate & reject | Path with ".." → Reject |
| Timeout | Set limits | Operation > 30s → Cancel |
| Permanent Error | Fail fast | Invalid API key → Don't retry |

---

## Monitoring and Observability

### Error Logging

The example includes comprehensive logging:

```python
# Logs include:
- Timestamp
- Error type
- Error message
- Context (what was being attempted)
- Stack traces (for debugging)
```

### Error Metrics

Track:
- **Error Rate**: Errors per time period
- **Retry Success Rate**: % of retries that succeed
- **Circuit Breaker State**: Time in each state
- **Common Failure Modes**: Most frequent errors

### View Error Log

```python
agent.show_error_log()
```

Output:
```
📊 Error Log:
==========================================

1. 2024-01-15T10:30:00
   Message: Calculate invalid expression
   Error: ToolValidationError: Invalid expression

2. 2024-01-15T10:31:00
   Message: Write to protected path
   Error: Path validation failed
```

---

## Production Considerations

### 1. Logging

Use structured logging:
```python
logger.info("Operation started", extra={
    "operation": "api_call",
    "endpoint": "/weather",
    "user_id": user_id
})
```

### 2. Monitoring

Integrate with monitoring systems:
- Sentry for error tracking
- Prometheus for metrics
- ELK stack for log aggregation

### 3. Alerting

Set up alerts for:
- High error rates
- Circuit breakers opening
- Timeout frequency
- Validation failures (potential attacks)

### 4. Testing

Test error scenarios:
```python
def test_retry_logic():
    # Simulate 2 failures then success
    mock_api.side_effect = [Exception(), Exception(), {"data": "success"}]
    result = calculate_with_retry("2+2")
    assert result["success"] == True
```

---

## Configuration

### Retry Settings

```python
retry_with_backoff(
    max_retries=3,        # Max attempts
    initial_delay=1.0,    # First retry delay (seconds)
    backoff_factor=2.0    # Delay multiplier
)
# Delays: 1s, 2s, 4s
```

### Circuit Breaker Settings

```python
CircuitBreaker(
    failure_threshold=5,   # Failures before opening
    recovery_timeout=60.0  # Seconds before retry
)
```

### Validation Settings

```python
validate_string(
    value,
    min_length=1,
    max_length=1000,
    allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789"
)
```

---

## Common Errors and Solutions

### Error: "Circuit breaker is OPEN"

**Cause:** Too many failures detected  
**Solution:** Wait for recovery timeout, then try again

### Error: "ToolValidationError: String too long"

**Cause:** Input exceeds max_length  
**Solution:** Reduce input size or increase limit

### Error: "Path cannot contain '..'"

**Cause:** Security protection against directory traversal  
**Solution:** Use relative paths within allowed directory

### Error: "Operation timed out"

**Cause:** Operation exceeded time limit  
**Solution:** Optimize operation or increase timeout

---

## Extending the Example

### Add Custom Validation

```python
class CustomValidator(InputValidator):
    @staticmethod
    def validate_email(email: str) -> str:
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(pattern, email):
            raise ToolValidationError("Invalid email format")
        return email
```

### Add Custom Error Types

```python
class RateLimitError(ToolError):
    """API rate limit exceeded"""
    pass

class AuthenticationError(ToolError):
    """Authentication failed"""
    pass
```

### Integrate with External Monitoring

```python
import sentry_sdk

sentry_sdk.init(dsn="your-sentry-dsn")

try:
    result = operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

---

## Learn More

- [Fundamentals](../../docs/02-fundamentals.md)
- [Security Guide](../../docs/04-security.md)
- [Design Patterns](../../design/patterns.md)
- [Anti-Patterns](../../design/anti-patterns.md)

---

## Key Takeaways

✅ **Always validate input** - Prevent security issues and crashes  
✅ **Retry transient failures** - Exponential backoff handles temporary issues  
✅ **Use circuit breakers** - Prevent cascading failures  
✅ **Set timeouts** - Don't let operations hang  
✅ **Log everything** - You can't fix what you can't see  
✅ **Fail gracefully** - Provide fallbacks when possible  
✅ **Test error scenarios** - Don't wait for production to find issues

---

**Production-ready error handling is not optional - it's essential for reliable AI agents!** 🛡️

