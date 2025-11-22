# Production Questions (76, 81)

## Production

### 76. How do you monitor an agent system in production?

**Answer:**

> **See:** [Production Agent Example](../examples/python-production/main.py) for a complete implementation with metrics collection, logging, and health monitoring.

**Key Monitoring Areas:**

**1. Performance Metrics:**
```python
class AgentMetrics:
    def track_request(self, start_time, end_time, success):
        latency = end_time - start_time
        
        metrics.record({
            "latency_ms": latency * 1000,
            "success": success,
            "timestamp": datetime.now()
        })
        
        # Track percentiles
        metrics.histogram("agent.latency", latency)
        metrics.increment("agent.requests.total")
        if success:
            metrics.increment("agent.requests.success")
        else:
            metrics.increment("agent.requests.failed")
```

**2. Tool Usage Tracking:**
```python
def monitor_tool_usage(tool_name, duration, error=None):
    metrics.increment(f"tools.{tool_name}.calls")
    metrics.histogram(f"tools.{tool_name}.duration", duration)
    
    if error:
        metrics.increment(f"tools.{tool_name}.errors")
        alert_if_threshold_exceeded(tool_name)
```

**3. Cost Monitoring:**
```python
class CostTracker:
    def track_llm_call(self, model, input_tokens, output_tokens):
        cost = calculate_cost(model, input_tokens, output_tokens)
        
        metrics.increment("llm.tokens.input", input_tokens)
        metrics.increment("llm.tokens.output", output_tokens)
        metrics.increment("llm.cost.total", cost)
        
        # Alert on unusual spending
        if cost > COST_THRESHOLD:
            alert_finance_team(f"High cost call: ${cost}")
```

**4. Quality Metrics:**
```python
class QualityMonitor:
    def track_completion(self, task, completed, iterations):
        metrics.record({
            "task_completed": completed,
            "iterations_needed": iterations,
            "task_type": task.type
        })
        
        # Track completion rate
        completion_rate = self.get_completion_rate(window="1h")
        if completion_rate < 0.9:
            alert_team("Completion rate dropped below 90%")
```

**5. Dashboard Example:**
```python
# Using Grafana/Datadog
dashboard = {
    "panels": [
        {"title": "Requests/sec", "metric": "agent.requests.rate"},
        {"title": "P95 Latency", "metric": "agent.latency.p95"},
        {"title": "Error Rate", "metric": "agent.errors.rate"},
        {"title": "Cost per Hour", "metric": "llm.cost.hourly"},
        {"title": "Tool Success Rate", "metric": "tools.success.rate"},
        {"title": "Active Users", "metric": "agent.users.active"}
    ]
}
```

---

### 81. How do you optimize costs in production agent systems?

**Answer:**

> **See:** [Cost Tracking Implementation](../examples/python-production/main.py#L330-L371) for a working cost tracker with token pricing and monitoring.

**Cost Optimization Strategies:**

**1. Model Selection:**
```python
class CostOptimizedAgent:
    def __init__(self):
        self.fast_model = "gpt-3.5-turbo"  # $0.002/1K tokens
        self.smart_model = "gpt-4"  # $0.03/1K tokens
    
    def choose_model(self, query):
        """Use cheaper model when possible"""
        complexity = self.assess_complexity(query)
        
        if complexity < 0.5:
            return self.fast_model
        else:
            return self.smart_model
    
    def assess_complexity(self, query):
        """Determine if query needs powerful model"""
        indicators = {
            "length": len(query.split()) > 100,
            "tools_needed": self.count_tools_needed(query) > 3,
            "reasoning_required": self.needs_complex_reasoning(query)
        }
        
        return sum(indicators.values()) / len(indicators)
```

**2. Caching:**
```python
class ResponseCache:
    def get_or_compute(self, query_hash, compute_fn):
        """Cache expensive LLM calls"""
        cached = self.cache.get(query_hash)
        
        if cached:
            logger.info(f"Cache hit, saved ${self.estimate_cost(query_hash)}")
            metrics.increment("cost.saved.cache")
            return cached
        
        result = compute_fn()
        self.cache.set(query_hash, result, ttl=3600)
        
        return result
```

**3. Prompt Optimization:**
```python
class PromptOptimizer:
    def optimize_prompt(self, prompt):
        """Reduce token usage without losing functionality"""
        
        # Remove unnecessary whitespace
        optimized = " ".join(prompt.split())
        
        # Use abbreviations for common terms
        replacements = {
            "Please provide": "Provide",
            "I would like you to": "Please",
            "Additionally": "Also"
        }
        
        for old, new in replacements.items():
            optimized = optimized.replace(old, new)
        
        tokens_saved = self.count_tokens(prompt) - self.count_tokens(optimized)
        logger.info(f"Saved {tokens_saved} tokens")
        
        return optimized
```

**4. Batch Processing:**
```python
class BatchProcessor:
    def process_batch(self, queries, batch_size=10):
        """Process multiple queries in one LLM call"""
        
        batched_prompt = "\n\n".join([
            f"Query {i+1}: {q}"
            for i, q in enumerate(queries[:batch_size])
        ])
        
        # One API call instead of N
        response = llm.generate(batched_prompt)
        
        # Parse individual responses
        return self.parse_batch_response(response)
```

**5. Rate Limit Optimization:**
```python
class RateLimitOptimizer:
    def optimize_api_usage(self):
        """Maximize API usage without hitting rate limits"""
        
        # Track API usage
        current_rate = metrics.get("api.calls.per_minute")
        api_limit = 100  # calls per minute
        
        # Adaptive throttling
        if current_rate > api_limit * 0.9:
            # Near limit, slow down
            time.sleep(0.1)
        elif current_rate < api_limit * 0.5:
            # Under-utilizing, can speed up
            pass
```

**6. Tool Cost Tracking:**
```python
class ToolCostTracker:
    def __init__(self):
        self.tool_costs = {
            "gpt4_call": 0.03,  # per 1K tokens
            "database_query": 0.001,  # per query
            "api_call": 0.01  # per call
        }
    
    def track_costs(self, tool_name, usage):
        cost = self.tool_costs.get(tool_name, 0) * usage
        
        metrics.increment("cost.total", cost)
        metrics.increment(f"cost.{tool_name}", cost)
        
        # Alert on expensive operations
        if cost > 1.0:  # > $1
            logger.warning(f"Expensive operation: {tool_name} cost ${cost}")
```

---

**Related Resources:**
- [Production Example](../examples/python-production/)
- [Security Questions](04-security.md)
- [Back to Main Questions](README.md)
