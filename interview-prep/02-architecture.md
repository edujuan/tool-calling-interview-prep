# Architecture Questions (21-40)

## Architecture

### 21. What are the main agent architecture patterns?

**Answer:**

**1. Reactive (ReAct Pattern)**
```
Loop: Think → Act → Observe → Think → ...
```
- Agent decides one step at a time
- Simple but can be inefficient
- Used in: LangChain agents, many chatbots

**2. Planner-Executor**
```
Phase 1: Plan (list all steps)
Phase 2: Execute (do each step)
```
- More efficient for multi-step tasks
- Can revise plan if step fails
- Used in: AutoGPT-style agents

**3. Multi-Agent**
```
Manager Agent ← → Worker Agents
```
- Multiple agents with different roles
- Can work in parallel
- Used in: Enterprise systems, complex workflows

**When to use:**
- ReAct: Simple, single-purpose agents
- Planner: Complex tasks with dependencies
- Multi-Agent: Very complex or parallel workloads

**See:** [Agent Architectures Guide](../docs/03-agent-architectures.md), [ReAct Example](../examples/python-react-pattern/), [Planner Example](../examples/python-planner-executor/), [Multi-Agent Example](../examples/python-multi-agent/)

---

### 22. Explain the ReAct pattern.

**Answer:**

**ReAct = Reasoning + Acting**

The agent alternates between:
- **Thought:** Reasoning about what to do next
- **Action:** Using a tool
- **Observation:** Seeing the tool's result

**Example Flow:**
```
User: "What's the weather in Paris and London?"

Thought: I need weather data for Paris first
Action: weather_api(location="Paris")
Observation: {"temp": 18, "condition": "cloudy"}

Thought: Now I need London's weather
Action: weather_api(location="London")
Observation: {"temp": 15, "condition": "rainy"}

Thought: I have all the information
Final Answer: "Paris is 18°C and cloudy, London is 15°C and rainy"
```

**Advantages:**
- Simple to implement
- Flexible (can adapt on the fly)
- Interpretable (can see agent's reasoning)

**Disadvantages:**
- Can be inefficient (doesn't plan ahead)
- Might get stuck in loops
- Token usage grows with iterations

**See:** [ReAct Pattern Deep Dive](../docs/03-agent-architectures.md#pattern-1-reactive-agents-react), [ReAct Example Code](../examples/python-react-pattern/)

---

### 23. How would you prevent an agent from getting stuck in a loop?

**Answer:**

**Multiple strategies:**

**1. Iteration Limit**
```python
MAX_ITERATIONS = 10

for i in range(MAX_ITERATIONS):
    action = agent.decide()
    if action == "final_answer":
        break
    execute(action)
else:
    return "Agent reached max iterations without answering"
```

**2. State Tracking**
```python
seen_states = set()

while True:
    state = agent.get_state()
    if state in seen_states:
        return "Agent is repeating itself - stopping"
    seen_states.add(state)
    agent.step()
```

**3. Progress Detection**
```python
history = []

def is_making_progress():
    # Check if recent actions are productive
    recent = history[-5:]
    if len(set(recent)) == 1:  # Same action 5 times
        return False
    return True
```

**4. Explicit Loop Prevention in Prompt**
```
Instructions to LLM:
- If you've tried an approach twice with no progress, try a different approach
- If stuck, say "I'm unable to complete this task" instead of repeating
```

**5. Timeout**
```python
import time
START_TIME = time.time()
TIMEOUT = 60  # seconds

while time.time() - START_TIME < TIMEOUT:
    agent.step()
```

**Best practice:** Combine multiple approaches.

**See:** [Loop Prevention in ReAct](../docs/03-agent-architectures.md#where-react-struggles), [Infinite Loop Anti-Pattern](../design/anti-patterns.md#-anti-pattern-5-infinite-loop-trap)

---

### 27. What is the Observer pattern in agent systems?

**Answer:**

The **Observer pattern** allows components to watch and react to agent events.

**Use cases:**
- Logging
- Monitoring
- Debugging
- Analytics

**Implementation:**
```python
class AgentObserver:
    def on_tool_call(self, tool_name, args):
        pass
    
    def on_tool_result(self, tool_name, result):
        pass
    
    def on_error(self, error):
        pass

class LoggingObserver(AgentObserver):
    def on_tool_call(self, tool_name, args):
        logger.info(f"Calling {tool_name} with {args}")
    
    def on_tool_result(self, tool_name, result):
        logger.info(f"{tool_name} returned {result}")

class MetricsObserver(AgentObserver):
    def on_tool_call(self, tool_name, args):
        metrics.increment(f"tool.{tool_name}.calls")
    
    def on_error(self, error):
        metrics.increment("agent.errors")

# Agent with observers
agent = Agent(
    tools=tools,
    observers=[LoggingObserver(), MetricsObserver()]
)
```

**Benefits:**
- ✅ Separation of concerns
- ✅ Easy to add monitoring
- ✅ Non-invasive (doesn't change agent logic)

**See:** [Design Patterns](../design/patterns.md) - Observer and monitoring patterns

---

### 28. How do you implement tool retry logic?

**Answer:**

**Basic Retry:**
```python
def call_tool_with_retry(tool, args, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return tool(args)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(1)  # Wait before retry
```

**Exponential Backoff:**
```python
import time
from random import random

def exponential_backoff_retry(tool, args, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return tool(args)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            # Wait: 1s, 2s, 4s, 8s, 16s (with jitter)
            delay = (2 ** attempt) + random()
            time.sleep(delay)
```

**Smart Retry (Different errors):**
```python
def smart_retry(tool, args, max_attempts=3):
    retryable_errors = [TimeoutError, ConnectionError, RateLimitError]
    
    for attempt in range(max_attempts):
        try:
            return tool(args)
        except Exception as e:
            # Don't retry on permanent errors
            if type(e) not in retryable_errors:
                raise
            
            if attempt == max_attempts - 1:
                raise
            
            # Different strategies by error type
            if isinstance(e, RateLimitError):
                time.sleep(e.retry_after or 60)
            elif isinstance(e, TimeoutError):
                time.sleep(5)
            else:
                time.sleep(2 ** attempt)
```

**Decorator Approach:**
```python
from functools import wraps

def retry(max_attempts=3, backoff=exponential):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(backoff(attempt))
        return wrapper
    return decorator

@retry(max_attempts=5)
def call_api(endpoint, data):
    return requests.post(endpoint, json=data)
```

**Best Practice:** Combine backoff + jitter + error-type awareness

**See:** [Retry with Exponential Backoff Pattern](../design/patterns.md#pattern-7-retry-with-exponential-backoff)

---

### 29. What is tool composition and how does it work?

**Answer:**

**Tool composition** is building complex tools from simpler ones.

**Example:**
```python
# Simple tools
def get_user_id(email):
    return db.query("SELECT id FROM users WHERE email=?", email)

def get_user_orders(user_id):
    return db.query("SELECT * FROM orders WHERE user_id=?", user_id)

def calculate_total(orders):
    return sum(order.amount for order in orders)

# Composed tool
def get_customer_lifetime_value(email):
    """Composite tool using 3 simple tools"""
    user_id = get_user_id(email)
    orders = get_user_orders(user_id)
    total = calculate_total(orders)
    return total
```

**Approaches:**

**1. Function Composition:**
```python
from functools import reduce

def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)

# Usage
process = compose(format_output, calculate, fetch_data)
result = process(input)
```

**2. Pipeline Pattern:**
```python
class ToolPipeline:
    def __init__(self):
        self.steps = []
    
    def add_step(self, tool):
        self.steps.append(tool)
        return self
    
    def execute(self, input):
        result = input
        for step in self.steps:
            result = step(result)
        return result

# Usage
pipeline = ToolPipeline()
    .add_step(fetch_data)
    .add_step(transform)
    .add_step(validate)
    .add_step(save)

result = pipeline.execute(user_query)
```

**3. Agent-Directed Composition:**
```python
# Let agent decide composition
tools = [get_user_id, get_orders, calculate_total]
agent = Agent(tools=tools)

# Agent figures out to call them in sequence
agent.query("What's the lifetime value of user@example.com?")
```

**Benefits:**
- ✅ Reusable building blocks
- ✅ Easier testing (test pieces separately)
- ✅ More maintainable
- ✅ Flexible (different compositions for different tasks)

**See:** [Tool Composition Pattern](../design/patterns.md#pattern-3-tool-composition)

---

### 31. How do you handle concurrent tool calls safely?

**Answer:**

**Challenges:**
- Race conditions
- Resource contention
- Partial failures
- Result ordering

**Strategies:**

**1. Async/Await Pattern:**
```python
import asyncio

async def call_tools_concurrently(tool_calls):
    """Execute multiple tools in parallel"""
    tasks = [
        asyncio.create_task(tool.execute(args))
        for tool, args in tool_calls
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle failures
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Tool {i} failed: {result}")
    
    return results
```

**2. Resource Locking:**
```python
from threading import Lock

class SharedResourceTool:
    def __init__(self):
        self.lock = Lock()
        self.resource = SharedResource()
    
    def execute(self, args):
        with self.lock:
            # Only one tool can access resource at a time
            return self.resource.process(args)
```

**3. Connection Pooling:**
```python
from concurrent.futures import ThreadPoolExecutor

class ToolExecutor:
    def __init__(self, max_workers=10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.connection_pool = ConnectionPool(size=max_workers)
    
    def execute_concurrent(self, tool_calls):
        futures = []
        for tool, args in tool_calls:
            future = self.executor.submit(
                self.execute_with_connection,
                tool, args
            )
            futures.append(future)
        
        return [f.result() for f in futures]
    
    def execute_with_connection(self, tool, args):
        with self.connection_pool.get_connection() as conn:
            return tool.execute(args, connection=conn)
```

**4. Rate Limiting (Concurrent):**
```python
import asyncio
from asyncio import Semaphore

class ConcurrentRateLimiter:
    def __init__(self, max_concurrent=5):
        self.semaphore = Semaphore(max_concurrent)
    
    async def execute(self, tool, args):
        async with self.semaphore:
            # At most 5 tools executing at once
            return await tool.execute(args)
```

**5. Transaction Management:**
```python
class TransactionalExecutor:
    async def execute_batch(self, tool_calls):
        """All succeed or all fail"""
        transaction = Transaction()
        results = []
        
        try:
            for tool, args in tool_calls:
                result = await tool.execute(args, transaction=transaction)
                results.append(result)
            
            transaction.commit()
            return results
        
        except Exception:
            transaction.rollback()
            raise
```

**Best Practices:**
- ✅ Use connection pools
- ✅ Implement timeouts
- ✅ Handle partial failures gracefully
- ✅ Log concurrency issues
- ✅ Test under load

**See:** [Parallel Tool Execution](../docs/03-agent-architectures.md#tool-chaining-patterns)

---

### 35. How would you implement a plugin system for agent tools?

**Answer:**

A **plugin system** allows third-parties to add tools to your agent.

**Architecture:**

**1. Plugin Interface:**
```python
from abc import ABC, abstractmethod

class ToolPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    def get_tools(self) -> list:
        """Return list of tools provided by this plugin"""
        pass
    
    @abstractmethod
    def initialize(self, config: dict):
        """Setup plugin with configuration"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources"""
        pass
```

**2. Plugin Implementation:**
```python
class WeatherPlugin(ToolPlugin):
    @property
    def name(self):
        return "weather_plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    def initialize(self, config):
        self.api_key = config.get("api_key")
    
    def get_tools(self):
        return [
            {
                "name": "get_weather",
                "description": "Get current weather",
                "execute": self.get_weather
            },
            {
                "name": "get_forecast",
                "description": "Get weather forecast",
                "execute": self.get_forecast
            }
        ]
    
    def get_weather(self, location):
        # Implementation
        pass
    
    def cleanup(self):
        # Close connections, etc.
        pass
```

**3. Plugin Manager:**
```python
import importlib
import os

class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = plugin_dir
        self.plugins = {}
    
    def discover_plugins(self):
        """Find all plugins in plugin directory"""
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py"):
                module_name = filename[:-3]
                self.load_plugin(module_name)
    
    def load_plugin(self, module_name):
        """Dynamically import and instantiate plugin"""
        try:
            module = importlib.import_module(f"plugins.{module_name}")
            
            # Find ToolPlugin subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, ToolPlugin) and 
                    attr != ToolPlugin):
                    
                    plugin = attr()
                    self.plugins[plugin.name] = plugin
                    logger.info(f"Loaded plugin: {plugin.name}")
        
        except Exception as e:
            logger.error(f"Failed to load plugin {module_name}: {e}")
    
    def initialize_all(self, config):
        """Initialize all plugins"""
        for plugin in self.plugins.values():
            plugin_config = config.get(plugin.name, {})
            plugin.initialize(plugin_config)
    
    def get_all_tools(self):
        """Collect tools from all plugins"""
        tools = []
        for plugin in self.plugins.values():
            tools.extend(plugin.get_tools())
        return tools
```

**4. Security Sandboxing:**
```python
class SafePluginExecutor:
    """Execute plugins in restricted environment"""
    
    def execute_plugin_tool(self, plugin, tool_name, args):
        # Set resource limits
        with ResourceLimits(
            max_memory=100 * 1024 * 1024,  # 100MB
            max_cpu_time=5,  # 5 seconds
            no_network=True  # Disable network for untrusted plugins
        ):
            tool = plugin.get_tool(tool_name)
            return tool.execute(args)
```

**5. Plugin Marketplace Integration:**
```python
class PluginMarketplace:
    def search_plugins(self, query):
        """Search marketplace for plugins"""
        return requests.get(f"{MARKETPLACE_URL}/search?q={query}")
    
    def install_plugin(self, plugin_name):
        """Download and install plugin"""
        plugin_package = self.download_plugin(plugin_name)
        
        # Verify signature
        if not self.verify_signature(plugin_package):
            raise SecurityError("Plugin signature invalid")
        
        # Install
        self.extract_to_plugin_dir(plugin_package)
        self.plugin_manager.load_plugin(plugin_name)
```

**Best Practices:**
- ✅ Validate plugin security before loading
- ✅ Run plugins in sandboxes
- ✅ Version plugin API
- ✅ Provide plugin development docs
- ✅ Allow plugin configuration
- ✅ Handle plugin failures gracefully

**See:** [Tool Factory Pattern](../design/patterns.md#pattern-2-tool-factory) for dynamic tool creation patterns

---

### 36. What is the role of prompt engineering in agent architectures?

**Answer:**

**Prompt engineering** is critical for agent behavior even with the same tools.

**Key Aspects:**

**1. System Prompt Sets Agent Behavior:**
```python
# Cautious agent
CAUTIOUS_PROMPT = """
You are a careful assistant. Before using any tool:
1. Explain what you're about to do
2. Ask for confirmation if the action is irreversible
3. Validate all inputs carefully
"""

# Efficient agent
EFFICIENT_PROMPT = """
You are an efficient assistant. When given a task:
1. Plan the minimum steps needed
2. Execute tools in parallel when possible
3. Avoid redundant tool calls
"""
```

**2. Tool Selection Guidance:**
```python
TOOL_SELECTION_PROMPT = """
Available tools:
- calculator: For math operations (ONLY for calculations, not general questions)
- search: For finding information online
- email: For sending emails

Examples:
Q: "What's 5 + 3?" → Use calculator
Q: "What's the capital of France?" → Use search (it's a fact, not a calculation)
Q: "Send status update to team" → Use email
"""
```

**3. Error Recovery Instructions:**
```python
ERROR_HANDLING_PROMPT = """
If a tool call fails:
1. Check if you used the wrong tool → try a different one
2. Check if parameters were wrong → retry with corrected params
3. If tool is unavailable → inform user and suggest alternatives
4. After 3 failures → stop and ask user for help

Never get stuck in a loop of retrying the same failed call.
"""
```

**4. Output Formatting:**
```python
OUTPUT_FORMAT_PROMPT = """
Always structure your responses as:
1. **What I did**: List tools called and why
2. **Results**: Summarize findings
3. **Answer**: Direct answer to user's question

Example:
**What I did**: Called weather_api("Paris") to get current conditions
**Results**: Temperature is 18°C, condition is cloudy
**Answer**: It's currently 18°C and cloudy in Paris.
```

**5. Multi-Turn Context:**
```python
CONTEXT_AWARENESS_PROMPT = """
You maintain context across conversation:
- Remember previous tool calls
- Reference earlier results without re-calling tools
- Build on previous answers

Example:
User: "What's the weather in Paris?"
You: "It's 18°C and cloudy"

User: "And in London?"
You: "London is 15°C and rainy" (Don't repeat Paris info)

User: "Which is warmer?"
You: "Paris is warmer" (Use remembered data, don't call tools again)
"""
```

**6. Few-Shot Examples:**
```python
FEW_SHOT_PROMPT = """
Here are examples of good tool usage:

Example 1:
User: "Book a flight to NYC"
Assistant: I'll help book a flight. First I need some details:
- What date?
- Departing from where?
- Preferred airline?
(DON'T call booking tool without required info)

Example 2:
User: "What's the stock price?"
Assistant: Which stock? Please provide the ticker symbol.
(DON'T guess or use arbitrary stock)

Now handle this query:
"""
```

**Impact on Architecture:**
- Different prompts = different agent behavior
- Same tools + different prompts = different agents
- Prompts can encode domain knowledge
- Easier to iterate than changing code

**See:** [Prompt Engineering for Agents](../docs/03-agent-architectures.md#prompt-engineering-for-agents)

---

### 37. How do you implement graceful degradation when tools fail?

**Answer:**

**Graceful degradation** means maintaining functionality even when tools fail.

**Strategies:**

**1. Fallback Tools:**
```python
class FallbackToolExecutor:
    def __init__(self):
        self.primary_tools = {...}
        self.fallback_tools = {
            "weather_api": ["weather_api_backup", "weather_scraper"],
            "database": ["cache", "readonly_replica"]
        }
    
    def execute(self, tool_name, args):
        try:
            return self.primary_tools[tool_name].execute(args)
        except Exception as e:
            logger.warning(f"{tool_name} failed: {e}. Trying fallbacks...")
            
            for fallback_name in self.fallback_tools.get(tool_name, []):
                try:
                    return self.fallback_tools[fallback_name].execute(args)
                except Exception:
                    continue
            
            # All failed
            raise AllToolsFailedError(f"All versions of {tool_name} failed")
```

**2. Cached Results:**
```python
class CachedToolExecutor:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    def execute(self, tool_name, args):
        cache_key = f"{tool_name}:{hash(frozenset(args.items()))}"
        
        # Try fresh result
        try:
            result = self.tool.execute(args)
            self.cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
            return result
        
        except Exception:
            # Fall back to cache
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                age = time.time() - cached["timestamp"]
                logger.warning(f"Using cached result (age: {age}s)")
                return {
                    **cached["result"],
                    "_cached": True,
                    "_age_seconds": age
                }
            raise
```

**3. Partial Results:**
```python
async def fetch_multiple_sources(sources):
    """Get data from multiple sources, return what succeeds"""
    results = []
    errors = []
    
    tasks = [fetch_source(source) for source in sources]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    
    for source, outcome in zip(sources, outcomes):
        if isinstance(outcome, Exception):
            errors.append({"source": source, "error": str(outcome)})
        else:
            results.append(outcome)
    
    if not results:
        raise AllSourcesFailedError(errors)
    
    # Return partial success
    return {
        "results": results,
        "errors": errors,
        "success_rate": len(results) / len(sources)
    }
```

**4. Degraded Functionality:**
```python
class DegradedAgent:
    def query(self, user_query):
        # Try full functionality
        try:
            return self.full_pipeline(user_query)
        except ToolFailure:
            # Fall back to limited functionality
            logger.warning("Tool failed, using degraded mode")
            return self.limited_pipeline(user_query)
    
    def full_pipeline(self, query):
        # Uses all tools including external APIs
        data = self.call_tool("external_api", {...})
        enriched = self.call_tool("enrichment", data)
        return self.format(enriched)
    
    def limited_pipeline(self, query):
        # Uses only local/cached data
        data = self.call_tool("local_cache", {...})
        return self.format(data)
```

**5. User Communication:**
```python
def execute_with_transparency(tool, args):
    try:
        return tool.execute(args)
    
    except RateLimitError:
        return {
            "error": True,
            "message": "Service is rate-limited. Using cached data from 1 hour ago.",
            "degraded": True
        }
    
    except ServiceUnavailableError:
        return {
            "error": True,
            "message": "Service is down. I can try an alternative source or wait for it to recover.",
            "suggested_actions": ["use_fallback", "retry_later"]
        }
```

**6. Circuit Breaker Pattern:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "closed"  # closed = normal, open = failing
        self.opened_at = None
    
    def call(self, func, *args):
        if self.state == "open":
            # Check if enough time has passed to retry
            if time.time() - self.opened_at > self.timeout:
                self.state = "half_open"
            else:
                # Use fallback instead
                return self.fallback()
        
        try:
            result = func(*args)
            if self.state == "half_open":
                # Success! Close circuit
                self.state = "closed"
                self.failure_count = 0
            return result
        
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                self.opened_at = time.time()
            
            # Use fallback
            return self.fallback()
```

**See:** [Circuit Breaker Pattern](../design/patterns.md#pattern-6-circuit-breaker), [Error Handling Patterns](../design/patterns.md#error-handling-patterns)

---

### 38. What debugging strategies work well for agent systems?

**Answer:**

Debugging agents is challenging because of:
- Non-deterministic LLM behavior
- Multiple tool calls
- Complex state

**Strategies:**

**1. Detailed Logging:**
```python
import logging
from datetime import datetime

class AgentLogger:
    def log_tool_call(self, tool_name, args, result, error=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool_call",
            "tool": tool_name,
            "arguments": args,
            "result": result if not error else None,
            "error": str(error) if error else None,
            "success": error is None
        }
        logging.info(json.dumps(log_entry))
    
    def log_llm_call(self, prompt, response, tokens_used):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "llm_call",
            "prompt_preview": prompt[:200],
            "response_preview": response[:200],
            "tokens": tokens_used
        }
        logging.info(json.dumps(log_entry))
```

**2. Execution Trace:**
```python
class ExecutionTracer:
    def __init__(self):
        self.trace = []
    
    def record_step(self, step_type, data):
        self.trace.append({
            "step": len(self.trace) + 1,
            "type": step_type,
            "data": data,
            "timestamp": time.time()
        })
    
    def visualize(self):
        for step in self.trace:
            print(f"Step {step['step']}: {step['type']}")
            print(f"  Data: {step['data']}")
            print()
```

**3. Replay System:**
```python
class AgentReplayer:
    """Replay agent execution for debugging"""
    
    def record_session(self, session_id):
        """Save all inputs/outputs"""
        self.sessions[session_id] = {
            "user_query": ...,
            "tool_calls": [...],
            "llm_calls": [...],
            "final_response": ...
        }
    
    def replay(self, session_id, stop_at_step=None):
        """Replay session, optionally stopping mid-way"""
        session = self.sessions[session_id]
        
        for i, step in enumerate(session["tool_calls"]):
            if stop_at_step and i >= stop_at_step:
                breakpoint()  # Debugging hook
            
            print(f"Replaying step {i}: {step['tool']}")
            # Could use cached results instead of re-calling
            result = step["cached_result"]
```

**4. Assertion Checks:**
```python
class ValidatedAgent:
    def call_tool(self, tool_name, args):
        # Pre-condition
        assert self.validate_args(tool_name, args), "Invalid arguments"
        
        result = self.executor.execute(tool_name, args)
        
        # Post-condition
        assert result is not None, "Tool returned None"
        assert self.validate_result(result), "Invalid result format"
        
        return result
```

**5. Test Mode:**
```python
class DebuggableAgent:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
    
    def execute(self, query):
        if self.debug_mode:
            # Pause before each tool call
            tool_name = self.llm.decide_tool(query)
            print(f"About to call: {tool_name}")
            input("Press Enter to continue...")
        
        return self.normal_execution(query)
```

**6. Visualization:**
```python
class AgentVisualizer:
    """Generate visual diagrams of agent execution"""
    
    def generate_flowchart(self, execution_trace):
        """Create flowchart of agent's decision path"""
        import graphviz
        
        dot = graphviz.Digraph()
        
        for i, step in enumerate(execution_trace):
            dot.node(str(i), step["description"])
            if i > 0:
                dot.edge(str(i-1), str(i))
        
        dot.render("agent_execution")
```

**See:** [Production Agent Example](../examples/python-production/) with logging and debugging features

**7. Comparison Testing:**
```python
def compare_agent_versions(query, agent_v1, agent_v2):
    """Compare two agent versions side-by-side"""
    
    result_v1 = agent_v1.execute(query)
    result_v2 = agent_v2.execute(query)
    
    return {
        "query": query,
        "v1": {
            "result": result_v1,
            "tools_used": agent_v1.get_tools_used(),
            "steps": agent_v1.get_step_count()
        },
        "v2": {
            "result": result_v2,
            "tools_used": agent_v2.get_tools_used(),
            "steps": agent_v2.get_step_count()
        },
        "differences": diff(result_v1, result_v2)
    }
```

---

### 39. How do you optimize agent performance?

**Answer:**

**Performance bottlenecks:**
- LLM inference latency
- Tool execution time
- Context window limitations
- Token costs

**Optimization Strategies:**

**1. Caching LLM Responses:**
```python
from functools import lru_cache
import hashlib

class CachedLLM:
    def __init__(self):
        self.cache = {}
    
    def generate(self, prompt):
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        response = self.llm.generate(prompt)
        self.cache[cache_key] = response
        return response
```

**2. Parallel Tool Execution:**
```python
import asyncio

async def execute_independent_tools_parallel(tool_calls):
    """Execute non-dependent tools in parallel"""
    
    # Identify which tools can run in parallel
    dependency_graph = build_dependency_graph(tool_calls)
    independent_groups = find_independent_groups(dependency_graph)
    
    results = {}
    for group in independent_groups:
        # Execute group in parallel
        tasks = [execute_tool(call) for call in group]
        group_results = await asyncio.gather(*tasks)
        results.update(group_results)
    
    return results
```

**3. Streaming Responses:**
```python
async def stream_agent_response(query):
    """Stream response as it's generated"""
    
    # Start thinking
    async for thought in llm.stream_thinking(query):
        yield {"type": "thinking", "content": thought}
    
    # Execute tools as decided
    for tool_call in llm.get_tool_calls():
        yield {"type": "tool_call", "tool": tool_call.name}
        result = await execute_tool(tool_call)
        yield {"type": "tool_result", "result": result}
    
    # Final answer
    async for token in llm.stream_final_answer():
        yield {"type": "answer", "content": token}
```

**4. Context Compression:**
```python
class ContextCompressor:
    def compress_history(self, conversation_history):
        """Reduce token usage while preserving key info"""
        
        # Keep first message (usually system prompt)
        compressed = [conversation_history[0]]
        
        # Summarize middle messages
        if len(conversation_history) > 10:
            middle = conversation_history[1:-5]
            summary = self.llm.summarize(middle)
            compressed.append({
                "role": "system",
                "content": f"Previous conversation summary: {summary}"
            })
        
        # Keep recent messages verbatim
        compressed.extend(conversation_history[-5:])
        
        return compressed
```

**5. Batch Processing:**
```python
class BatchAgent:
    def process_batch(self, queries):
        """Process multiple queries efficiently"""
        
        # Batch LLM calls
        prompts = [self.build_prompt(q) for q in queries]
        responses = self.llm.batch_generate(prompts)  # Single API call
        
        # Extract tool calls from all responses
        all_tool_calls = []
        for response in responses:
            all_tool_calls.extend(extract_tool_calls(response))
        
        # Batch execute tools
        tool_results = self.batch_execute_tools(all_tool_calls)
        
        # Continue processing...
        return results
```

**6. Model Selection:**
```python
class MultiModelAgent:
    """Use appropriate model for each task"""
    
    def __init__(self):
        self.fast_model = GPT35()  # Cheap, fast
        self.smart_model = GPT4()  # Expensive, capable
    
    def execute(self, query, complexity="auto"):
        if complexity == "auto":
            complexity = self.assess_complexity(query)
        
        if complexity == "simple":
            # Use fast model for simple tasks
            return self.fast_model.generate(query)
        else:
            # Use powerful model for complex tasks
            return self.smart_model.generate(query)
```

**7. Early Stopping:**
```python
class EarlyStoppingAgent:
    def execute(self, query, max_iterations=10):
        for i in range(max_iterations):
            action = self.decide_next_action()
            
            if action.type == "answer":
                return action.content  # Done!
            
            if self.confidence(action) < 0.3:
                # Agent is floundering
                return "I'm not sure how to complete this task"
            
            self.execute_action(action)
```

**Metrics to Track:**
- Latency (time to first token, total time)
- Token usage (input + output)
- Tool call count
- Cache hit rate
- Cost per query

**See:** [Performance Optimization Techniques](../docs/03-agent-architectures.md#real-world-performance-differences), [Streaming Example](../examples/python-streaming/)

---

### 40. What are common anti-patterns in agent architecture?

**Answer:**

**1. Tool Overload:**
```python
# ❌ BAD: Giving agent 200 tools at once
agent = Agent(tools=all_200_tools)

# ✅ GOOD: Selective tool loading
relevant_tools = select_tools_for_domain(query)
agent = Agent(tools=relevant_tools)
```

**2. No Error Handling:**
```python
# ❌ BAD: Crashes on any tool failure
result = call_tool(name, args)

# ✅ GOOD: Graceful error handling
try:
    result = call_tool(name, args)
except ToolError as e:
    result = fallback_handler(e)
```

**3. Stateful Tools Without Cleanup:**
```python
# ❌ BAD: Resources leak
class DatabaseTool:
    def execute(self, query):
        conn = create_connection()
        result = conn.execute(query)
        return result  # Connection never closed!

# ✅ GOOD: Proper resource management
class DatabaseTool:
    def execute(self, query):
        with create_connection() as conn:
            return conn.execute(query)
```

**4. Infinite Loops:**
```python
# ❌ BAD: No iteration limit
while not agent.has_answer():
    agent.step()  # Could loop forever!

# ✅ GOOD: Bounded iterations
for i in range(MAX_ITERATIONS):
    if agent.has_answer():
        break
    agent.step()
```

**5. Exposing Secrets to LLM:**
```python
# ❌ BAD: API key in prompt
prompt = f"Use this key: {API_KEY}"

# ✅ GOOD: Inject secrets at execution
def execute_tool(name, args):
    return tool(args, auth=get_secret(name))
```

**6. No Validation:**
```python
# ❌ BAD: Trust LLM output blindly
tool_call = llm.decide_tool()
execute(tool_call)  # Could be malformed!

# ✅ GOOD: Validate before executing
tool_call = llm.decide_tool()
if validate_tool_call(tool_call):
    execute(tool_call)
```

**7. Tight Coupling:**
```python
# ❌ BAD: Agent knows tool implementation details
class Agent:
    def get_weather(self, city):
        return requests.get(f"https://api.../weather?city={city}")

# ✅ GOOD: Agent only knows interface
class Agent:
    def get_weather(self, city):
        return self.tools["weather"].execute({"city": city})
```

**8. Synchronous Everything:**
```python
# ❌ BAD: Sequential when parallel possible
weather_nyc = get_weather("NYC")  # Wait...
weather_la = get_weather("LA")    # Wait...

# ✅ GOOD: Parallel execution
results = await asyncio.gather(
    get_weather("NYC"),
    get_weather("LA")
)
```

**9. Verbose Tool Definitions:**
```python
# ❌ BAD: Wastes context window
{
    "name": "calculator",
    "description": "This tool provides mathematical calculation capabilities including but not limited to addition, subtraction, multiplication, division, and various other arithmetic operations..."
}

# ✅ GOOD: Concise and clear
{
    "name": "calculator",
    "description": "Evaluate mathematical expressions. Example: '2+2' returns 4"
}
```

**10. No Monitoring:**
```python
# ❌ BAD: No visibility
agent.execute(query)  # Hope it works!

# ✅ GOOD: Comprehensive logging
with AgentMonitor() as monitor:
    result = agent.execute(query)
    monitor.log_metrics()
```

**See:** [Complete Anti-Patterns Guide](../design/anti-patterns.md), [Design Patterns](../design/patterns.md)

---

**Related Resources:**
- [Agent Architectures Deep Dive](../docs/03-agent-architectures.md)
- [Design Patterns](../design/patterns.md)
- [Design Anti-Patterns](../design/anti-patterns.md)
- [Back to Main Questions](README.md)
