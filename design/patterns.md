# Design Patterns for AI Agents

> **Proven patterns for building reliable, maintainable AI agents**

---

## Table of Contents

- [Tool Design Patterns](#tool-design-patterns)
- [Agent Design Patterns](#agent-design-patterns)
- [Error Handling Patterns](#error-handling-patterns)
- [State Management Patterns](#state-management-patterns)
- [Security Patterns](#security-patterns)
- [Testing Patterns](#testing-patterns)

---

## Tool Design Patterns

### Pattern 1: Tool Wrapper

**Problem**: Raw tools may not be safe or have the right interface for agents.

**Solution**: Wrap tools with validation, error handling, and formatting.

```python
class ToolWrapper:
    """Wraps a tool with common functionality"""
    
    def __init__(self, func, name: str, description: str, 
                 schema: dict, timeout: int = 30):
        self.func = func
        self.name = name
        self.description = description
        self.schema = schema
        self.timeout = timeout
    
    def __call__(self, **kwargs):
        """Execute tool with validation and error handling"""
        # 1. Validate inputs
        self._validate_inputs(kwargs)
        
        # 2. Execute with timeout
        try:
            result = self._execute_with_timeout(kwargs)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _validate_inputs(self, kwargs):
        """Validate against JSON schema"""
        from jsonschema import validate, ValidationError
        try:
            validate(instance=kwargs, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e.message}")
    
    def _execute_with_timeout(self, kwargs):
        """Execute with timeout protection"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Tool {self.name} exceeded {self.timeout}s timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout)
        
        try:
            result = self.func(**kwargs)
            signal.alarm(0)  # Cancel alarm
            return result
        except Exception as e:
            signal.alarm(0)
            raise

# Usage
def raw_calculator(expression: str) -> float:
    return eval(expression)

calculator = ToolWrapper(
    func=raw_calculator,
    name="calculator",
    description="Evaluates mathematical expressions",
    schema={
        "type": "object",
        "properties": {
            "expression": {"type": "string"}
        },
        "required": ["expression"]
    },
    timeout=5
)

result = calculator(expression="2 + 2")  # Validated, timeout-protected
```

**Benefits**:
- ✅ Consistent error handling
- ✅ Input validation
- ✅ Timeout protection
- ✅ Easy to test

---

### Pattern 2: Tool Factory

**Problem**: Creating many similar tools is repetitive.

**Solution**: Use a factory to generate tools from configurations.

```python
class ToolFactory:
    """Factory for creating tools from configurations"""
    
    @staticmethod
    def create_api_tool(name: str, url: str, method: str = "GET",
                       headers: dict = None, description: str = None):
        """Create a tool that calls an HTTP API"""
        
        import requests
        
        def api_tool(**kwargs):
            response = requests.request(
                method=method,
                url=url.format(**kwargs),  # URL templating
                headers=headers or {},
                json=kwargs if method in ["POST", "PUT"] else None,
                params=kwargs if method == "GET" else None,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        api_tool.__name__ = name
        api_tool.__doc__ = description or f"Calls {url}"
        
        return api_tool
    
    @staticmethod
    def create_file_tool(operation: str, base_path: str = "."):
        """Create a file operation tool"""
        import os
        
        if operation == "read":
            def read_file(path: str) -> str:
                full_path = os.path.join(base_path, path)
                if not full_path.startswith(base_path):
                    raise ValueError("Path outside allowed directory")
                with open(full_path, 'r') as f:
                    return f.read()
            return read_file
        
        elif operation == "write":
            def write_file(path: str, content: str) -> str:
                full_path = os.path.join(base_path, path)
                if not full_path.startswith(base_path):
                    raise ValueError("Path outside allowed directory")
                with open(full_path, 'w') as f:
                    f.write(content)
                return f"Wrote {len(content)} characters"
            return write_file

# Usage
weather_tool = ToolFactory.create_api_tool(
    name="get_weather",
    url="https://api.weather.com/v1/current?location={location}",
    method="GET",
    description="Gets current weather for a location"
)

read_tool = ToolFactory.create_file_tool(
    operation="read",
    base_path="/safe/directory"
)
```

**Benefits**:
- ✅ DRY (Don't Repeat Yourself)
- ✅ Consistent tool interface
- ✅ Easy to add new tools
- ✅ Configuration-driven

---

### Pattern 3: Tool Composition

**Problem**: Complex operations require multiple tools.

**Solution**: Create composite tools from simpler ones.

```python
class CompositeTool:
    """Combines multiple tools into a workflow"""
    
    def __init__(self, name: str, steps: List[dict]):
        self.name = name
        self.steps = steps
    
    def __call__(self, **initial_inputs):
        """Execute tool chain"""
        context = initial_inputs.copy()
        
        for step in self.steps:
            tool = step['tool']
            input_mapping = step.get('input_mapping', {})
            output_key = step.get('output_key', 'result')
            
            # Map inputs from context
            tool_inputs = {}
            for param, source in input_mapping.items():
                if source.startswith('$'):
                    # Reference to context variable
                    tool_inputs[param] = context[source[1:]]
                else:
                    tool_inputs[param] = source
            
            # Execute tool
            result = tool(**tool_inputs)
            
            # Store result in context
            context[output_key] = result
        
        return context

# Example: Weather comparison tool
weather_compare = CompositeTool(
    name="compare_weather",
    steps=[
        {
            'tool': get_weather,
            'input_mapping': {'location': '$location1'},
            'output_key': 'weather1'
        },
        {
            'tool': get_weather,
            'input_mapping': {'location': '$location2'},
            'output_key': 'weather2'
        },
        {
            'tool': calculator,
            'input_mapping': {
                'expression': "$weather1[temp] - $weather2[temp]"
            },
            'output_key': 'temp_diff'
        }
    ]
)

result = weather_compare(location1="Paris", location2="London")
# Returns: {'location1': 'Paris', 'location2': 'London', 
#           'weather1': {...}, 'weather2': {...}, 'temp_diff': 3}
```

**Benefits**:
- ✅ Reusable workflows
- ✅ Declarative composition
- ✅ Easy to test individual steps
- ✅ Clear data flow

---

## Agent Design Patterns

### Pattern 4: Strategy Pattern for Agent Behavior

**Problem**: Need different agent behaviors for different scenarios.

**Solution**: Use strategy pattern to swap agent logic.

```python
from abc import ABC, abstractmethod

class AgentStrategy(ABC):
    """Base strategy for agent behavior"""
    
    @abstractmethod
    def decide_action(self, state: dict) -> dict:
        """Decide what action to take"""
        pass

class ReflexiveStrategy(AgentStrategy):
    """Simple reflex agent - immediate response"""
    
    def decide_action(self, state: dict) -> dict:
        query = state['query']
        
        # Simple keyword matching
        if 'weather' in query.lower():
            return {'action': 'get_weather', 'inputs': {'location': 'parsed_location'}}
        elif 'calculate' in query.lower() or any(op in query for op in ['+', '-', '*', '/']):
            return {'action': 'calculator', 'inputs': {'expression': query}}
        else:
            return {'action': 'respond', 'inputs': {'message': "I'm not sure how to help"}}

class ReasoningStrategy(AgentStrategy):
    """Agent that reasons before acting"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def decide_action(self, state: dict) -> dict:
        # Use LLM to reason about best action
        prompt = f"""
        Query: {state['query']}
        Available tools: {state['available_tools']}
        
        What should I do? Respond with JSON: {{"action": "...", "inputs": {{...}}}}
        """
        
        response = self.llm.generate(prompt)
        return json.loads(response)

class Agent:
    """Agent that uses pluggable strategies"""
    
    def __init__(self, strategy: AgentStrategy, tools: dict):
        self.strategy = strategy
        self.tools = tools
    
    def run(self, query: str):
        state = {
            'query': query,
            'available_tools': list(self.tools.keys())
        }
        
        # Strategy decides action
        decision = self.strategy.decide_action(state)
        
        # Execute action
        if decision['action'] in self.tools:
            return self.tools[decision['action']](**decision['inputs'])
        
        return "Unknown action"

# Usage - switch strategies easily
agent = Agent(
    strategy=ReflexiveStrategy(),  # Fast, no LLM calls
    tools={'get_weather': weather_tool, 'calculator': calc_tool}
)

# Or use reasoning strategy
agent.strategy = ReasoningStrategy(llm=openai_client)
```

**Benefits**:
- ✅ Flexible behavior
- ✅ Easy to test different strategies
- ✅ Clean separation of concerns
- ✅ Can switch at runtime

---

### Pattern 5: Chain of Responsibility for Tool Selection

**Problem**: Multiple ways to handle a query, need to try them in order.

**Solution**: Chain of handlers that pass query along if they can't handle it.

```python
class ToolHandler(ABC):
    """Base handler in the chain"""
    
    def __init__(self):
        self.next_handler: Optional[ToolHandler] = None
    
    def set_next(self, handler: 'ToolHandler'):
        self.next_handler = handler
        return handler  # Allow chaining
    
    def handle(self, query: str, context: dict):
        if self.can_handle(query, context):
            return self.process(query, context)
        elif self.next_handler:
            return self.next_handler.handle(query, context)
        else:
            return {"error": "No handler could process this query"}
    
    @abstractmethod
    def can_handle(self, query: str, context: dict) -> bool:
        pass
    
    @abstractmethod
    def process(self, query: str, context: dict):
        pass

class MathHandler(ToolHandler):
    """Handles math queries"""
    
    def can_handle(self, query: str, context: dict) -> bool:
        return any(op in query for op in ['+', '-', '*', '/', 'calculate'])
    
    def process(self, query: str, context: dict):
        # Extract expression and calculate
        return {"type": "math", "result": "calculation_result"}

class WeatherHandler(ToolHandler):
    """Handles weather queries"""
    
    def can_handle(self, query: str, context: dict) -> bool:
        return 'weather' in query.lower()
    
    def process(self, query: str, context: dict):
        return {"type": "weather", "result": "weather_data"}

class GeneralHandler(ToolHandler):
    """Fallback handler using LLM"""
    
    def __init__(self, llm):
        super().__init__()
        self.llm = llm
    
    def can_handle(self, query: str, context: dict) -> bool:
        return True  # Always handles as fallback
    
    def process(self, query: str, context: dict):
        response = self.llm.generate(query)
        return {"type": "general", "result": response}

# Build chain
math_handler = MathHandler()
weather_handler = WeatherHandler()
general_handler = GeneralHandler(llm)

math_handler.set_next(weather_handler).set_next(general_handler)

# Use chain
result = math_handler.handle("What's 2 + 2?", {})  # MathHandler processes
result = math_handler.handle("Weather in Paris?", {})  # WeatherHandler processes
result = math_handler.handle("Tell me a joke", {})  # GeneralHandler processes
```

**Benefits**:
- ✅ Flexible request handling
- ✅ Easy to add/remove handlers
- ✅ Priority-based processing
- ✅ Fallback mechanism

---

## Error Handling Patterns

### Pattern 6: Circuit Breaker

**Problem**: Failing tool can slow down entire agent.

**Solution**: Circuit breaker pattern to fail fast.

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Protects against cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, 
                 timeout: int = 60, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        # Check if circuit should change state
        self._update_state()
        
        if self.state == CircuitState.OPEN:
            raise Exception(f"Circuit breaker OPEN. Tool unavailable.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _update_state(self):
        """Update circuit state based on time and failures"""
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
    
    def _on_success(self):
        """Called on successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.failure_count = 0
    
    def _on_failure(self):
        """Called on failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
class ResilientTool:
    """Tool with circuit breaker"""
    
    def __init__(self, func):
        self.func = func
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60
        )
    
    def __call__(self, **kwargs):
        try:
            return self.circuit_breaker.call(self.func, **kwargs)
        except Exception as e:
            # Log, alert, use fallback, etc.
            return {"error": str(e), "circuit_state": self.circuit_breaker.state.value}

# Wrap unreliable tool
unreliable_api = ResilientTool(some_flaky_api_call)

# Will automatically stop trying if it keeps failing
result = unreliable_api(query="test")
```

**Benefits**:
- ✅ Fail fast when tool is down
- ✅ Automatic recovery attempts
- ✅ Prevents resource waste
- ✅ Better user experience

---

### Pattern 7: Retry with Exponential Backoff

**Problem**: Transient failures should be retried, but not too aggressively.

**Solution**: Retry with exponentially increasing delays.

```python
import time
from functools import wraps

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0,
                       max_delay: float = 60.0, exponential_base: float = 2.0):
    """Decorator for retrying with exponential backoff"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Last attempt, re-raise
                        raise
                    
                    # Log retry
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    
                    # Wait with exponential backoff
                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)
            
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3, base_delay=1.0)
def call_flaky_api(endpoint: str):
    """API call that might fail transiently"""
    response = requests.get(endpoint, timeout=10)
    response.raise_for_status()
    return response.json()

# Automatically retries with: 1s, 2s, 4s delays
result = call_flaky_api("https://api.example.com/data")
```

**Benefits**:
- ✅ Handles transient failures
- ✅ Doesn't overwhelm failing service
- ✅ Configurable retry strategy
- ✅ Simple to apply

---

## State Management Patterns

### Pattern 8: Memento (Save/Restore State)

**Problem**: Need to save and restore agent state (for debugging, rollback).

**Solution**: Memento pattern to capture and restore state.

```python
from dataclasses import dataclass, field
from typing import List, Any
from copy import deepcopy

@dataclass
class AgentMemento:
    """Saved state of agent"""
    conversation_history: List[dict]
    context: dict
    iteration: int
    timestamp: float
    
class StatefulAgent:
    """Agent that can save/restore state"""
    
    def __init__(self):
        self.conversation_history: List[dict] = []
        self.context: dict = {}
        self.iteration: int = 0
        self.mementos: List[AgentMemento] = []
    
    def save_state(self) -> AgentMemento:
        """Create memento of current state"""
        memento = AgentMemento(
            conversation_history=deepcopy(self.conversation_history),
            context=deepcopy(self.context),
            iteration=self.iteration,
            timestamp=time.time()
        )
        self.mementos.append(memento)
        return memento
    
    def restore_state(self, memento: AgentMemento):
        """Restore from memento"""
        self.conversation_history = deepcopy(memento.conversation_history)
        self.context = deepcopy(memento.context)
        self.iteration = memento.iteration
    
    def rollback(self, steps: int = 1):
        """Rollback N steps"""
        if len(self.mementos) >= steps:
            memento = self.mementos[-(steps + 1)]
            self.restore_state(memento)
            # Remove later mementos
            self.mementos = self.mementos[:-(steps)]

# Usage
agent = StatefulAgent()

# Do some work
agent.step("query 1")
agent.save_state()  # Checkpoint 1

agent.step("query 2")
agent.save_state()  # Checkpoint 2

agent.step("query 3")  # Oops, this went wrong

# Rollback to checkpoint 2
agent.rollback(steps=1)
```

**Benefits**:
- ✅ Easy debugging
- ✅ Can replay agent execution
- ✅ Support for "undo"
- ✅ State inspection

---

## Security Patterns

### Pattern 9: Allowlist Pattern

**Problem**: Agent might call unauthorized tools or access forbidden resources.

**Solution**: Explicit allowlist of permitted operations.

```python
class AllowlistEnforcer:
    """Enforces allowlist for tools and resources"""
    
    def __init__(self):
        self.allowed_tools: Set[str] = set()
        self.allowed_paths: Set[str] = set()
        self.allowed_domains: Set[str] = set()
    
    def allow_tool(self, tool_name: str):
        """Add tool to allowlist"""
        self.allowed_tools.add(tool_name)
    
    def allow_path(self, path: str):
        """Add file path to allowlist"""
        self.allowed_paths.add(os.path.abspath(path))
    
    def allow_domain(self, domain: str):
        """Add domain to allowlist"""
        self.allowed_domains.add(domain)
    
    def check_tool(self, tool_name: str) -> bool:
        """Check if tool is allowed"""
        if tool_name not in self.allowed_tools:
            raise SecurityError(f"Tool '{tool_name}' not in allowlist")
        return True
    
    def check_path(self, path: str) -> bool:
        """Check if path access is allowed"""
        abs_path = os.path.abspath(path)
        if not any(abs_path.startswith(allowed) for allowed in self.allowed_paths):
            raise SecurityError(f"Path '{path}' not in allowlist")
        return True
    
    def check_url(self, url: str) -> bool:
        """Check if URL domain is allowed"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain not in self.allowed_domains:
            raise SecurityError(f"Domain '{domain}' not in allowlist")
        return True

class SecureAgent:
    """Agent with enforced security policies"""
    
    def __init__(self, enforcer: AllowlistEnforcer):
        self.enforcer = enforcer
        self.tools = {}
    
    def call_tool(self, tool_name: str, **kwargs):
        """Call tool with security checks"""
        # Check tool is allowed
        self.enforcer.check_tool(tool_name)
        
        # Check arguments for paths/URLs
        for key, value in kwargs.items():
            if 'path' in key.lower() and isinstance(value, str):
                self.enforcer.check_path(value)
            elif 'url' in key.lower() and isinstance(value, str):
                self.enforcer.check_url(value)
        
        # Execute if all checks pass
        return self.tools[tool_name](**kwargs)

# Usage
enforcer = AllowlistEnforcer()
enforcer.allow_tool("calculator")
enforcer.allow_tool("read_file")
enforcer.allow_path("/home/user/documents")
enforcer.allow_domain("api.trusted-service.com")

agent = SecureAgent(enforcer)
agent.call_tool("calculator", expression="2+2")  # ✅ Allowed
agent.call_tool("delete_database")  # ❌ SecurityError
```

**Benefits**:
- ✅ Explicit security policy
- ✅ Fail-secure (deny by default)
- ✅ Easy to audit
- ✅ Prevents unauthorized access

---

## Testing Patterns

### Pattern 10: Test Double for Tools

**Problem**: Testing agents that call external APIs is slow and expensive.

**Solution**: Use test doubles (mocks/stubs) for tools.

```python
from unittest.mock import Mock
from typing import Protocol

class WeatherTool(Protocol):
    """Protocol for weather tools"""
    def __call__(self, location: str) -> dict:
        ...

class RealWeatherTool:
    """Real implementation calling external API"""
    def __call__(self, location: str) -> dict:
        response = requests.get(f"https://api.weather.com?loc={location}")
        return response.json()

class MockWeatherTool:
    """Mock for testing"""
    def __init__(self):
        self.call_count = 0
        self.last_location = None
    
    def __call__(self, location: str) -> dict:
        self.call_count += 1
        self.last_location = location
        
        # Return predictable test data
        return {
            "location": location,
            "temp": 20,
            "condition": "sunny"
        }

# In production
agent = Agent(tools={"weather": RealWeatherTool()})

# In tests
def test_agent_uses_weather_tool():
    mock_weather = MockWeatherTool()
    agent = Agent(tools={"weather": mock_weather})
    
    agent.run("What's the weather in Paris?")
    
    assert mock_weather.call_count == 1
    assert mock_weather.last_location == "Paris"
```

**Benefits**:
- ✅ Fast tests
- ✅ No external dependencies
- ✅ Predictable results
- ✅ Easy to test error cases

---

## Summary

**Key Takeaways:**

1. **Use wrappers** for consistent tool interfaces
2. **Factory patterns** reduce boilerplate
3. **Strategy patterns** enable flexible behavior
4. **Circuit breakers** protect from cascading failures
5. **Retry patterns** handle transient errors
6. **Mementos** enable state management
7. **Allowlists** enforce security
8. **Test doubles** enable fast testing

**When to Apply:**

- Start simple, add patterns as needed
- Patterns solve specific problems - don't over-engineer
- Combine patterns for robust systems

---

**See Also:**
- [Anti-Patterns](anti-patterns.md) - What NOT to do
- [Architecture Guide](../docs/03-agent-architectures.md)
- [Security Best Practices](../docs/04-security.md)

