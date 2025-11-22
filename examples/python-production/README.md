# Production-Ready AI Agent

> **Enterprise-grade patterns for deploying AI agents in production**

---

## Overview

This example demonstrates production-ready patterns for deploying AI agents with comprehensive monitoring, logging, and observability.

**Production Features:**
- ✅ Structured logging with audit trail
- ✅ Metrics collection and aggregation
- ✅ Request tracing for debugging
- ✅ Rate limiting and throttling
- ✅ Cost tracking and monitoring
- ✅ Health checks and status monitoring
- ✅ Error tracking and alerting

---

## Why Production Patterns Matter

| Development | Production |
|-------------|------------|
| `print()` debug statements | Structured logging |
| No metrics | Comprehensive metrics |
| Hope it works | Health monitoring |
| Pay whatever | Cost tracking |
| Handle all requests | Rate limiting |
| Guess what failed | Request tracing |

**Production-ready means observable, maintainable, and reliable!**

---

## Prerequisites

- Python 3.10+
- OpenAI API key

---

## Setup

```bash
# 1. Navigate to directory
cd examples/python-production

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

---

## Running the Example

```bash
python main.py
```

### Output

```
🏭 Production-Ready AI Agent Demo
==========================================

✅ Production agent initialized

Running example requests...

──────────────────────────────────────────
Request 1/3
──────────────────────────────────────────
Message: What is machine learning?

✅ Response: Machine learning is a subset of artificial intelligence...

📊 Metadata:
   duration_ms: 1245.3
   tokens: 156
   cost_usd: 0.000234
   model: gpt-3.5-turbo

📊 PRODUCTION AGENT DASHBOARD
==========================================

✅ Status: HEALTHY

📈 Request Metrics:
  Total Requests: 3
  Error Rate: 0.00%
  Avg Duration: 1156.23ms
  Avg Tokens: 148

💰 Cost Metrics:
  Total Cost: $0.0007
    gpt-3.5-turbo: $0.0007

==========================================
```

---

## Production Components

### 1. Structured Logging

**Problem:** `print()` statements are hard to search and analyze.

**Solution:** Structured logging with context.

```python
logger = StructuredLogger("ProductionAgent", log_file="agent.log")

logger.info(
    "Request received",
    request_id=request_id,
    user_id=user_id,
    message_length=len(message)
)
```

**Log Output:**
```
2024-01-15 10:30:00 - ProductionAgent - INFO - Request received {"request_id": "a1b2c3d4", "user_id": "user_123", "message_length": 45}
```

**Benefits:**
- Easy to search and filter
- Contains context for debugging
- Machine-readable for log aggregation
- Audit trail for compliance

---

### 2. Metrics Collection

**Problem:** Can't measure what you don't track.

**Solution:** Comprehensive metrics collection.

```python
@dataclass
class RequestMetrics:
    request_id: str
    timestamp: datetime
    duration_ms: float
    token_count: int
    cost_usd: float
    success: bool
```

**Tracked Metrics:**
- Request count
- Error rate
- Average duration
- Token usage
- Cost per request
- Tool usage frequency

**Why It Matters:**
- Identify performance issues
- Track costs
- Capacity planning
- SLA monitoring

---

### 3. Request Tracing

**Problem:** Hard to debug multi-step operations.

**Solution:** Distributed tracing.

```python
tracer.start_trace(request_id)

span = tracer.start_span(request_id, "llm_call", model="gpt-3.5-turbo")
# ... do work ...
span.finish()
```

**Trace Output:**
```
📊 Trace for Request a1b2c3d4
==========================================

✅ rate_limiting (2.34ms)

✅ llm_call (1245.67ms)
   model: gpt-3.5-turbo
   tokens: 156

✅ cost_calculation (0.12ms)
   cost_usd: 0.000234
```

**Benefits:**
- See exactly what happened
- Identify bottlenecks
- Debug production issues
- Performance optimization

---

### 4. Rate Limiting

**Problem:** Uncontrolled request rate can overwhelm system.

**Solution:** Token bucket rate limiter.

```python
rate_limiter = RateLimiter(requests_per_minute=60)

if not rate_limiter.consume():
    wait_time = rate_limiter.wait_time()
    return {"error": "Rate limit exceeded", "retry_after": wait_time}
```

**How It Works:**
1. Start with N tokens (capacity)
2. Each request consumes 1 token
3. Tokens refill continuously
4. Block when no tokens available

**Benefits:**
- Prevent API quota exhaustion
- Protect downstream services
- Fair resource allocation
- Predictable behavior

---

### 5. Cost Tracking

**Problem:** Surprise API bills.

**Solution:** Real-time cost tracking.

```python
cost_tracker = CostTracker()

cost = cost_tracker.calculate_cost(
    model="gpt-3.5-turbo",
    input_tokens=100,
    output_tokens=50
)
```

**Tracks:**
- Cost per request
- Cost per model
- Total spend
- Cost trends

**Use Cases:**
- Budget alerts
- Cost attribution
- Optimization opportunities
- Billing reconciliation

---

### 6. Health Monitoring

**Problem:** Don't know when system is degraded.

**Solution:** Health checks with status levels.

```python
health = agent.get_health()

# Returns:
{
    "status": "healthy",  # healthy, warning, degraded, critical
    "error_rate": 2.5,
    "total_requests": 1000,
    "timestamp": "2024-01-15T10:30:00"
}
```

**Status Levels:**
- **healthy**: Error rate < 5%
- **warning**: Error rate 5-20%
- **degraded**: Error rate 20-50%
- **critical**: Error rate > 50%

**Integration:**
- Load balancer health checks
- Monitoring dashboards
- Alert triggers
- Auto-scaling decisions

---

## Monitoring Dashboard

The example includes a real-time dashboard:

```
📊 PRODUCTION AGENT DASHBOARD
==========================================

✅ Status: HEALTHY

📈 Request Metrics:
  Total Requests: 156
  Error Rate: 1.28%
  Avg Duration: 1245.67ms
  Avg Tokens: 142

💰 Cost Metrics:
  Total Cost: $0.0234
    gpt-3.5-turbo: $0.0234

🔧 Tool Usage:
    search_documents: 23
    calculate: 12
    
==========================================
```

**View Dashboard:**
```python
# In interactive mode, type: stats
You: stats
```

---

## Integration Patterns

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

request_counter = Counter('agent_requests_total', 'Total requests')
request_duration = Histogram('agent_request_duration_seconds', 'Request duration')
error_rate = Gauge('agent_error_rate', 'Current error rate')

def chat_with_metrics(message):
    request_counter.inc()
    
    with request_duration.time():
        result = agent.chat(message)
    
    error_rate.set(agent.metrics.get_stats()['error_rate'])
    
    return result
```

### Sentry Error Tracking

```python
import sentry_sdk

sentry_sdk.init(dsn="your-sentry-dsn")

try:
    result = agent.chat(message)
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

### DataDog APM

```python
from ddtrace import tracer

@tracer.wrap(service="ai-agent", resource="chat")
def chat_with_tracing(message):
    span = tracer.current_span()
    span.set_tag("message.length", len(message))
    
    result = agent.chat(message)
    
    span.set_metric("tokens.used", result['metadata']['tokens'])
    span.set_metric("cost.usd", result['metadata']['cost_usd'])
    
    return result
```

---

## Production Checklist

### Before Deployment

- [ ] Enable structured logging
- [ ] Set up metrics collection
- [ ] Configure health checks
- [ ] Implement rate limiting
- [ ] Add request tracing
- [ ] Set up error tracking
- [ ] Configure alerts
- [ ] Load test the system
- [ ] Document runbooks
- [ ] Set up monitoring dashboard

### Monitoring Setup

- [ ] CPU/Memory monitoring
- [ ] Request rate tracking
- [ ] Error rate alerts
- [ ] Cost alerts
- [ ] Latency percentiles (p50, p95, p99)
- [ ] Uptime monitoring
- [ ] API quota tracking

### Alerting Rules

```yaml
alerts:
  - name: High Error Rate
    condition: error_rate > 10%
    duration: 5 minutes
    severity: warning
  
  - name: Critical Error Rate
    condition: error_rate > 25%
    duration: 2 minutes
    severity: critical
  
  - name: High Cost
    condition: hourly_cost > $10
    severity: warning
  
  - name: Rate Limit Approaching
    condition: requests_per_minute > 50
    severity: info
```

---

## Best Practices

### Logging

✅ **DO:**
- Use structured logging
- Include request IDs
- Log at appropriate levels
- Sanitize sensitive data
- Include context in logs

❌ **DON'T:**
- Use print() in production
- Log sensitive user data
- Log excessively (performance impact)
- Use unclear log messages

### Metrics

✅ **DO:**
- Track business metrics
- Monitor error rates
- Measure latency percentiles
- Track resource usage
- Set up dashboards

❌ **DON'T:**
- Track everything (be selective)
- Ignore cost metrics
- Skip health checks
- Forget to alert on metrics

### Error Handling

✅ **DO:**
- Log all errors with context
- Return meaningful error messages
- Track error rates
- Set up error alerts
- Have fallback strategies

❌ **DON'T:**
- Silently fail
- Expose stack traces to users
- Ignore transient errors
- Lack error recovery

---

## Performance Optimization

### Reduce Latency

1. **Use Faster Models**
   ```python
   model="gpt-3.5-turbo"  # Faster than GPT-4
   ```

2. **Enable Streaming**
   ```python
   stream=True  # Start showing results immediately
   ```

3. **Cache Common Responses**
   ```python
   cache = {}
   if message in cache:
       return cache[message]
   ```

4. **Optimize Prompts**
   ```python
   # Shorter prompts = faster responses
   ```

### Reduce Costs

1. **Use Cheaper Models**
   ```python
   # gpt-3.5-turbo is 10-30x cheaper than GPT-4
   ```

2. **Reduce Token Usage**
   ```python
   max_tokens=150  # Limit response length
   ```

3. **Cache Responses**
   ```python
   # Don't regenerate same responses
   ```

4. **Batch Requests**
   ```python
   # Process multiple at once when possible
   ```

---

## Troubleshooting

### High Error Rate

**Symptoms:** Error rate > 10%

**Possible Causes:**
- API quota exceeded
- Invalid API key
- Network issues
- Rate limiting

**Solutions:**
1. Check API quota/billing
2. Verify API key
3. Add retry logic
4. Implement backoff
5. Check network connectivity

### High Latency

**Symptoms:** p95 latency > 5s

**Possible Causes:**
- Using slow model (GPT-4)
- Long prompts/responses
- Network latency
- Rate limiting delays

**Solutions:**
1. Switch to faster model
2. Reduce max_tokens
3. Enable streaming
4. Add caching
5. Optimize prompts

### High Costs

**Symptoms:** Costs exceeding budget

**Possible Causes:**
- Using expensive models
- High token counts
- No caching
- Unnecessary requests

**Solutions:**
1. Use cheaper models
2. Implement caching
3. Reduce max_tokens
4. Set cost alerts
5. Review usage patterns

---

## Deployment Patterns

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["python", "main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: production-agent
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: agent
        image: production-agent:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## Learn More

- [Error Handling](../python-error-handling/)
- [Streaming Responses](../python-streaming/)
- [Security Guide](../../docs/04-security.md)
- [Design Patterns](../../design/patterns.md)

---

## Key Takeaways

✅ **Structured logging** - Essential for debugging and audit trails  
✅ **Metrics collection** - Can't improve what you don't measure  
✅ **Request tracing** - Debug production issues effectively  
✅ **Rate limiting** - Protect your system and budget  
✅ **Cost tracking** - No surprise bills  
✅ **Health monitoring** - Know when something's wrong  
✅ **Production readiness** - Difference between demo and production

---

**Production-ready isn't optional - it's the difference between a demo and a reliable service!** 🏭

