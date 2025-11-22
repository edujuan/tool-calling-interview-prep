# Design Patterns and Architecture

This directory contains architectural diagrams, design patterns, and anti-patterns for building AI agents with tool-calling capabilities.

## 📐 Contents

### Core Documents
- [**Design Patterns**](patterns.md) - Proven patterns for agent systems
- [**Anti-Patterns**](anti-patterns.md) - Common mistakes and how to avoid them
- [**Architecture Diagrams**](diagrams/) - Visual representations of systems
- [**Design Decisions**](design-decisions.md) - How to make architectural choices

### Diagrams
- [Agent Architecture Patterns](diagrams/agent-architectures.png)
- [UTCP vs MCP Comparison](diagrams/protocol-comparison.png)
- [Security Layers](diagrams/security-architecture.png)
- [Deployment Patterns](diagrams/deployment.png)

## 🎨 Design Patterns

### Pattern 1: Command Pattern for Tools

**Problem:** Need consistent interface for diverse tools (APIs, CLIs, functions)

**Solution:** Wrap all tools with a command interface

```python
class ToolCommand:
    def execute(self, args):
        raise NotImplementedError
    
    def validate(self, args):
        raise NotImplementedError

class WeatherCommand(ToolCommand):
    def execute(self, args):
        return call_weather_api(args["location"])
    
    def validate(self, args):
        if "location" not in args:
            raise ValueError("location required")

# Usage
tools = [WeatherCommand(), CalculatorCommand(), EmailCommand()]
for tool in tools:
    tool.validate(args)
    result = tool.execute(args)
```

**Benefits:**
- ✅ Uniform interface
- ✅ Easy to add new tools
- ✅ Centralized validation
- ✅ Testable

---

### Pattern 2: Circuit Breaker for Unreliable Tools

**Problem:** External API fails repeatedly, agent wastes time retrying

**Solution:** Circuit breaker pattern - stop calling failing services

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise ServiceUnavailableError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise

# Usage
weather_breaker = CircuitBreaker()

def call_weather_tool(location):
    return weather_breaker.call(weather_api.get, location)
```

**Benefits:**
- ✅ Fail fast instead of wasting time
- ✅ Automatic recovery attempts
- ✅ Protects downstream services
- ✅ Better user experience (quick error vs timeout)

---

### Pattern 3: Cache Pattern for Expensive Tools

**Problem:** Same tool called multiple times with same args (wasteful, slow)

**Solution:** Cache tool results

```python
from functools import lru_cache
import hashlib
import json

class ToolCache:
    def __init__(self, ttl=300):  # 5 minute TTL
        self.cache = {}
        self.ttl = ttl
    
    def get_key(self, tool_name, args):
        # Create cache key from tool name and args
        args_str = json.dumps(args, sort_keys=True)
        return f"{tool_name}:{hashlib.md5(args_str.encode()).hexdigest()}"
    
    def get(self, tool_name, args):
        key = self.get_key(tool_name, args)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            del self.cache[key]
        return None
    
    def set(self, tool_name, args, result):
        key = self.get_key(tool_name, args)
        self.cache[key] = (result, time.time())

# Usage
cache = ToolCache(ttl=300)

def call_tool_with_cache(tool_name, args):
    # Check cache first
    cached = cache.get(tool_name, args)
    if cached is not None:
        return cached
    
    # Call tool
    result = execute_tool(tool_name, args)
    
    # Cache result
    cache.set(tool_name, args, result)
    return result
```

**Benefits:**
- ✅ Faster responses
- ✅ Reduced API costs
- ✅ Less load on external services
- ✅ Better user experience

---

### Pattern 4: Retry with Exponential Backoff

**Problem:** Temporary failures shouldn't stop agent

**Solution:** Retry failed calls with increasing delays

```python
import time
from random import random

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """
    Retry function with exponential backoff
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Last attempt, give up
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random()
            time.sleep(delay)
    
# Usage
def call_unreliable_api():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

result = retry_with_backoff(call_unreliable_api, max_retries=3)
```

**Benefits:**
- ✅ Handles transient failures
- ✅ Avoids thundering herd (jitter)
- ✅ Configurable retry policy
- ✅ Eventually fails gracefully

---

### Pattern 5: Adapter Pattern for Multiple Protocols

**Problem:** Want to support both UTCP and MCP tools seamlessly

**Solution:** Adapter pattern to normalize interfaces

```python
class ToolAdapter:
    def call(self, tool_name, args):
        raise NotImplementedError

class UTCPAdapter(ToolAdapter):
    def __init__(self, client):
        self.client = client
    
    def call(self, tool_name, args):
        return self.client.call_tool(tool_name, args)

class MCPAdapter(ToolAdapter):
    def __init__(self, client):
        self.client = client
    
    async def call(self, tool_name, args):
        return await self.client.call_tool(tool_name, args)

class Agent:
    def __init__(self):
        self.adapters = {
            "weather": UTCPAdapter(utcp_client),
            "database": MCPAdapter(mcp_client)
        }
    
    def use_tool(self, tool_name, args):
        adapter = self.adapters[tool_name]
        return adapter.call(tool_name, args)
```

**Benefits:**
- ✅ Protocol-agnostic agent code
- ✅ Easy to switch protocols
- ✅ Can use multiple protocols
- ✅ Testable with mock adapters

---

## 🚫 Anti-Patterns

### Anti-Pattern 1: Tool Overloading

**❌ Bad:**
```python
def super_tool(action, data, mode, options, config):
    """
    A tool that does everything!
    Can search, can calculate, can send emails...
    """
    if action == "search":
        # 100 lines of search logic
    elif action == "calculate":
        # 100 lines of calculation logic
    elif action == "email":
        # 100 lines of email logic
    ...
```

**✅ Good:**
```python
def search_tool(query):
    """Focused tool that only searches"""
    return perform_search(query)

def calculator_tool(expression):
    """Focused tool that only calculates"""
    return evaluate(expression)

def email_tool(to, subject, body):
    """Focused tool that only sends emails"""
    return send_email(to, subject, body)
```

**Why it's bad:**
- LLM confused about when to use it
- Hard to maintain
- Can't optimize individually
- Complex error handling

**Rule:** One tool, one purpose

---

### Anti-Pattern 2: Hardcoded Tool Logic in Agent

**❌ Bad:**
```python
class Agent:
    def process(self, query):
        if "weather" in query:
            # Weather API logic hardcoded here
            response = requests.get(f"https://api.weather.com?q={query}")
            return response.json()
        elif "calculate" in query:
            # Calculator logic hardcoded here
            ...
```

**✅ Good:**
```python
class Agent:
    def __init__(self, tools):
        self.tools = tools  # Tools injected
    
    def process(self, query):
        # Let LLM decide which tool
        tool_choice = self.llm.decide(query, self.tools)
        return self.tools[tool_choice].execute(...)
```

**Why it's bad:**
- Can't add tools without changing agent code
- No separation of concerns
- Hard to test
- Doesn't scale

**Rule:** Tools are plugins, not part of agent core

---

### Anti-Pattern 3: Ignoring Tool Errors

**❌ Bad:**
```python
try:
    result = call_tool(name, args)
except:
    pass  # Ignore errors, continue
```

**✅ Good:**
```python
try:
    result = call_tool(name, args)
except ToolNotFoundError:
    return f"Tool {name} doesn't exist"
except ValidationError as e:
    return f"Invalid arguments: {e}"
except TimeoutError:
    return f"Tool {name} timed out - trying alternative"
except Exception as e:
    logger.error(f"Tool error: {e}")
    return f"Tool {name} failed: {e}"
```

**Why it's bad:**
- Agent doesn't know tool failed
- Can't recover or try alternatives
- Poor user experience
- No visibility into issues

**Rule:** Every error is information

---

## 📊 Architecture Decision Records

### ADR-001: Choosing Between UTCP and MCP

**Status:** Accepted

**Context:**
Need to integrate 20+ tools for our AI assistant. Mix of internal and external APIs.

**Decision:**
Use hybrid approach:
- UTCP for external public APIs (faster, simpler)
- MCP for internal database/auth tools (controlled, audited)

**Consequences:**
- **Positive:** Best of both worlds, optimized per tool
- **Negative:** More complexity, two systems to maintain
- **Mitigation:** Shared adapter layer abstracts differences

---

### ADR-002: Agent Architecture Pattern

**Status:** Accepted

**Context:**
Building customer support agent. Needs to search KB, query CRM, create tickets.

**Decision:**
Use Plan-and-Execute pattern instead of pure ReAct.

**Reasoning:**
- Tasks often have clear steps (search → query → create)
- Planning reduces API calls (more efficient)
- Easier to show user what agent will do

**Consequences:**
- **Positive:** More efficient, predictable
- **Negative:** Less flexible for unexpected paths
- **Mitigation:** Allow re-planning if step fails

---

## 🔗 Related Resources

- [System Design Primer](https://github.com/donnemartin/system-design-primer)
- [Design Patterns (Gang of Four)](https://en.wikipedia.org/wiki/Design_Patterns)
- [Cloud Design Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/)

---

**Want to contribute a pattern?** See [CONTRIBUTING.md](../CONTRIBUTING.md)

