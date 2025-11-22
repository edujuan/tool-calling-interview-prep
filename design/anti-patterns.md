# Anti-Patterns: What NOT to Do

> **Learn from common mistakes in AI agent development**

---

## Table of Contents

- [Tool Design Anti-Patterns](#tool-design-anti-patterns)
- [Agent Architecture Anti-Patterns](#agent-architecture-anti-patterns)
- [Security Anti-Patterns](#security-anti-patterns)
- [Performance Anti-Patterns](#performance-anti-patterns)
- [Testing Anti-Patterns](#testing-anti-patterns)

---

## Tool Design Anti-Patterns

### ❌ Anti-Pattern 1: God Tool

**Problem**: One tool that does everything.[[34]](https://en.wikipedia.org/wiki/God_object)

**Bad Example**:
```python
def do_everything(action: str, **kwargs):
    """Does any action based on action parameter"""
    if action == "weather":
        return get_weather(**kwargs)
    elif action == "calculate":
        return calculate(**kwargs)
    elif action == "search":
        return search_web(**kwargs)
    # ... 50 more actions
```

**Why It's Bad**:
- Impossible for LLM to understand all capabilities
- Hard to test and maintain[[35]](https://en.wikipedia.org/wiki/God_object)
- Security nightmare (one tool = all permissions)
- Poor error messages[[36]](https://en.wikipedia.org/wiki/God_object)

**Better Approach**:
```python
# Separate, focused tools
def get_weather(location: str) -> dict:
    """Gets current weather for location"""
    return weather_api.get(location)

def calculator(expression: str) -> float:
    """Evaluates mathematical expression"""
    return eval_math(expression)

def search_web(query: str) -> list:
    """Searches web and returns top results"""
    return search_api.search(query)
```

---

### ❌ Anti-Pattern 2: Silent Failures

**Problem**: Tool fails but returns successful-looking result. This violates the principle that errors should never pass silently.

**Bad Example**:
```python
def get_user_data(user_id: str):
    """Get user data"""
    try:
        return database.query(user_id)
    except Exception:
        return {}  # ❌ Looks like user with no data!
```

**Why It's Bad**:
- Agent thinks operation succeeded
- Continues with bad data
- Hard to debug
- Can make decisions on wrong information

**Better Approach**:
```python
def get_user_data(user_id: str):
    """Get user data"""
    try:
        result = database.query(user_id)
        return {"success": True, "data": result}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "database_error"
        }
```

---

### ❌ Anti-Pattern 3: Overly Complex Parameters

**Problem**: Tool requires too many parameters or nested structures. Complex interfaces are error-prone and harder to use.

**Bad Example**:
```python
def complex_tool(param1, param2, param3, param4, param5, 
                 config: dict, options: dict, metadata: dict):
    """Does something with 8+ parameters"""
    pass
```

**Why It's Bad**:
- LLM struggles to provide all parameters correctly
- High chance of errors
- Poor user experience
- Hard to prompt engineer

**Better Approach**:
```python
# Split into simpler tools
def simple_tool(primary_param: str, optional_setting: str = "default"):
    """Does one thing well with 1-2 parameters"""
    pass

# Or use a config object with sensible defaults
@dataclass
class ToolConfig:
    setting1: str = "default"
    setting2: int = 10
    # ... with defaults

def flexible_tool(input: str, config: ToolConfig = None):
    config = config or ToolConfig()
    # Use config.setting1, etc.
```

---

### ❌ Anti-Pattern 4: Undocumented Tools

**Problem**: Tool has no description or unclear documentation.[[13]](https://docs.fireworks.ai/guides/function-calling)

**Bad Example**:
```python
def process(data):
    # What does this do? What format is data?
    return do_something(data)
```

**Why It's Bad**:
- LLM doesn't know when to use it
- LLM can't provide correct inputs
- Results in trial-and-error
- Wastes tokens and money

**Better Approach**:
```python
def process_customer_feedback(feedback_text: str, 
                              sentiment_threshold: float = 0.5) -> dict:
    """
    Analyzes customer feedback and extracts sentiment and key issues.
    
    Args:
        feedback_text: Raw customer feedback text (any length)
        sentiment_threshold: Minimum score (0-1) to flag as negative (default: 0.5)
    
    Returns:
        dict with keys:
            - sentiment: "positive" | "negative" | "neutral"
            - score: float 0-1
            - key_issues: list of identified issues
            - summary: brief summary of feedback
    
    Example:
        process_customer_feedback("Product is great but shipping was slow")
        => {"sentiment": "positive", "score": 0.7, 
            "key_issues": ["shipping delay"], ...}
    """
    pass
```

---

## Agent Architecture Anti-Patterns

### ❌ Anti-Pattern 5: Infinite Loop Trap

**Problem**: Agent can get stuck in loops with no escape mechanism. This is a known issue in autonomous agent systems that lack proper stopping criteria.

**Bad Example**:
```python
def agent_loop(query):
    while True:  # ❌ No exit condition!
        action = llm.decide_action(query)
        result = execute(action)
        if "final answer" in result:
            return result
        # What if LLM never says "final answer"?
```

**Why It's Bad**:
- Can run forever
- Wastes API credits
- Poor user experience
- Hard to debug when it happens

**Better Approach**:
```python
def agent_loop(query, max_iterations=10):
    for i in range(max_iterations):
        action = llm.decide_action(query)
        result = execute(action)
        
        if "final answer" in result:
            return result
        
        # Detect loops
        if is_repeating(action, history):
            return "Agent is stuck in a loop, stopping"
    
    return "Reached maximum iterations without completing"
```

---

### ❌ Anti-Pattern 6: Prompt Soup

**Problem**: Massive, unstructured prompts with everything thrown in.[[37]](https://www.lakera.ai/blog/guide-to-prompt-injection)

**Bad Example**:
```python
prompt = f"""
You are helpful. Use tools. Tools are {tools}. 
User said {query}. History: {history}. 
Format: JSON or maybe text. Do what the user wants.
Tools: {tools_again}. Remember context {context}.
Be nice. Output should be... 
{more_rambling_instructions}
"""
```

**Why It's Bad**:
- LLM gets confused
- Wastes tokens
- Inconsistent results
- Hard to maintain

**Better Approach**:
```python
def build_structured_prompt(query, tools, history):
    sections = [
        "# ROLE",
        "You are a helpful AI assistant with access to tools.",
        "",
        "# AVAILABLE TOOLS",
        format_tools(tools),
        "",
        "# FORMAT",
        "Respond using: Thought → Action → Action Input",
        "",
        "# CONVERSATION HISTORY",
        format_history(history),
        "",
        "# CURRENT QUERY",
        query
    ]
    return "\n".join(sections)
```

---

### ❌ Anti-Pattern 7: Stateful Chaos

**Problem**: State scattered everywhere with no clear ownership. Global state makes debugging hard and prevents proper state management.

**Bad Example**:
```python
# Global state - disaster waiting to happen
current_user = None
conversation_history = []
tool_results = {}
agent_state = {}

def agent_step(query):
    global current_user, conversation_history  # ❌
    # Modify multiple global states
    conversation_history.append(query)
    # What if another request comes in?
```

**Why It's Bad**:
- Race conditions in concurrent scenarios
- Hard to test
- Difficult to debug
- Can't run multiple agents simultaneously

**Better Approach**:
```python
@dataclass
class AgentState:
    """Encapsulated agent state"""
    user_id: str
    conversation_history: List[dict] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    iteration: int = 0

class Agent:
    def __init__(self, user_id: str):
        self.state = AgentState(user_id=user_id)
    
    def step(self, query: str):
        # All state in self.state
        self.state.conversation_history.append({"query": query})
        self.state.iteration += 1
```

---

## Security Anti-Patterns

### ❌ Anti-Pattern 8: Credentials in Prompts

**Problem**: Putting API keys or secrets in LLM prompts.[[38]](https://www.guidepointsecurity.com/blog/prompt-injection-the-ai-vulnerability-we-still-cant-fix/)[[39]](https://www.guidepointsecurity.com/blog/prompt-injection-the-ai-vulnerability-we-still-cant-fix/)

**Bad Example**:
```python
prompt = f"""
Use this API key to call the service: {API_KEY}
Call endpoint with key {SECRET_KEY}
"""
```

**Why It's Bad**:
- LLM might output the credential
- Credentials in logs
- Violation of security best practices
- Credentials in LLM training data (if they train on API calls)

**Better Approach**:
```python
# Tools handle credentials internally
class SecureAPITool:
    def __init__(self):
        self._api_key = os.getenv("API_KEY")  # Never exposed to LLM
    
    def call(self, endpoint: str):
        # Inject credential at call time
        headers = {"Authorization": f"Bearer {self._api_key}"}
        return requests.get(endpoint, headers=headers)

# Prompt never mentions credentials
prompt = """You can use api_tool to call endpoints."""
```

---

### ❌ Anti-Pattern 9: eval() for Everything

**Problem**: Using eval() to execute arbitrary code.[[40]](https://dilankam.medium.com/the-god-object-anti-pattern-in-software-architecture-b2b7782d6997)

**Bad Example**:
```python
def calculator(expression: str):
    """Calculate anything"""
    return eval(expression)  # ❌ DANGEROUS!

# Agent could execute:
# calculator("__import__('os').system('rm -rf /')")
```

**Why It's Bad**:
- **CRITICAL SECURITY VULNERABILITY**
- Can execute arbitrary code
- Delete files, access network, steal data
- **NEVER DO THIS IN PRODUCTION**

**Better Approach**:
```python
# Option 1: Safe math parser
import ast
import operator

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

def safe_calculator(expression: str):
    """Safely evaluate math expressions"""
    try:
        node = ast.parse(expression, mode='eval')
        return safe_eval(node.body)
    except:
        raise ValueError("Invalid expression")

def safe_eval(node):
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        return OPERATORS[type(node.op)](left, right)
    else:
        raise ValueError("Unsupported operation")

# Option 2: Use a library
from simpleeval import simple_eval
def calculator(expression: str):
    return simple_eval(expression)  # Much safer
```

---

### ❌ Anti-Pattern 10: No Input Validation

**Problem**: Trusting LLM output without validation.[[41]](https://docs.fireworks.ai/guides/function-calling)[[42]](https://genai.owasp.org/llmrisk2023-24/llm01-24-prompt-injection/)

**Bad Example**:
```python
def delete_file(path: str):
    """Delete a file"""
    os.remove(path)  # ❌ No validation!

# Agent could call: delete_file("/etc/passwd")
```

**Why It's Bad**:
- LLM can make mistakes
- Prompt injection can manipulate agent
- Destructive actions need safeguards
- No undo once executed

**Better Approach**:
```python
def delete_file(path: str):
    """Delete a file (only in allowed directories)"""
    # 1. Validate path format
    if not isinstance(path, str) or len(path) > 500:
        raise ValueError("Invalid path")
    
    # 2. Resolve to absolute path
    abs_path = os.path.abspath(path)
    
    # 3. Check against allowlist
    ALLOWED_DIRS = ["/tmp", "/home/user/documents"]
    if not any(abs_path.startswith(d) for d in ALLOWED_DIRS):
        raise PermissionError(f"Cannot delete outside allowed dirs")
    
    # 4. Additional checks
    if os.path.isdir(abs_path):
        raise ValueError("Cannot delete directories, only files")
    
    # 5. Require confirmation for important files
    if os.path.getsize(abs_path) > 1_000_000:  # > 1MB
        raise ValueError("File too large, requires manual confirmation")
    
    # 6. Finally, delete
    os.remove(abs_path)
    
    # 7. Log the action
    logger.info(f"Deleted file: {abs_path}")
```

---

## Performance Anti-Patterns

### ❌ Anti-Pattern 11: Sequential When Could Parallelize

**Problem**: Calling tools one-by-one when they could run in parallel. Parallelizing independent tasks can yield significant performance improvements.

**Bad Example**:
```python
def get_all_weather(cities):
    results = []
    for city in cities:  # ❌ Sequential
        weather = get_weather(city)  # Each takes 1 second
        results.append(weather)
    return results  # Takes 10 seconds for 10 cities
```

**Why It's Bad**:
- Slow for users
- Wastes time
- Doesn't scale
- Poor resource utilization

**Better Approach**:
```python
import asyncio

async def get_all_weather(cities):
    # Run all calls in parallel
    tasks = [get_weather_async(city) for city in cities]
    results = await asyncio.gather(*tasks)
    return results  # Takes 1 second for 10 cities!
```

---

### ❌ Anti-Pattern 12: Recomputing Everything

**Problem**: Calling tools repeatedly for same result. Caching or memoization avoids redundant computations and improves performance.

**Bad Example**:
```python
def agent_step(query):
    current_time = get_current_time()  # Called
    # ... some processing
    time_again = get_current_time()  # Called again!
    # ... more processing
    yet_another_time = get_current_time()  # And again!
```

**Why It's Bad**:
- Unnecessary API calls (costs money)
- Slower execution
- Might hit rate limits
- Wasteful

**Better Approach**:
```python
class AgentWithCache:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {}  # Time-to-live per key
    
    def get_cached_or_fetch(self, key, fetch_func, ttl=60):
        """Cache with expiration"""
        now = time.time()
        
        if key in self.cache:
            if now - self.cache_ttl[key] < ttl:
                return self.cache[key]  # Still fresh
        
        # Fetch and cache
        result = fetch_func()
        self.cache[key] = result
        self.cache_ttl[key] = now
        return result

# Usage
current_time = agent.get_cached_or_fetch(
    "current_time",
    lambda: get_current_time(),
    ttl=60  # Cache for 1 minute
)
```

---

## Testing Anti-Patterns

### ❌ Anti-Pattern 13: Testing in Production

**Problem**: Only testing with real APIs and real data. Proper testing requires staging environments to catch issues before production.

**Bad Example**:
```python
def test_agent():
    """Test by running against production!"""
    agent = Agent(tools={
        "send_email": real_email_sender,  # ❌ Sends real emails!
        "charge_card": real_payment_processor,  # ❌ Charges real money!
    })
    
    agent.run("Send invoice and charge customer")  # Hope this works!
```

**Why It's Bad**:
- Expensive (API costs, actual charges)
- Dangerous (real emails sent, real data modified)
- Slow
- Can't test error scenarios

**Better Approach**:
```python
def test_agent():
    """Test with mocks"""
    mock_email = Mock(return_value={"sent": True})
    mock_payment = Mock(return_value={"charged": True, "transaction_id": "test123"})
    
    agent = Agent(tools={
        "send_email": mock_email,
        "charge_card": mock_payment,
    })
    
    result = agent.run("Send invoice and charge customer")
    
    # Verify behavior
    assert mock_email.called
    assert mock_payment.called
    assert "transaction_id" in result
```

---

### ❌ Anti-Pattern 14: No Error Case Testing

**Problem**: Only testing happy path. Testing best practices emphasize the importance of testing not only expected behavior but also error conditions.

**Bad Example**:
```python
def test_agent():
    """Test that it works"""
    result = agent.run("What's 2 + 2?")
    assert result == "4"  # Only tests success case
```

**Why It's Bad**:
- Real-world has failures
- Agent should handle errors gracefully
- No confidence in reliability
- Surprises in production

**Better Approach**:
```python
def test_agent_success():
    """Test successful execution"""
    result = agent.run("What's 2 + 2?")
    assert result == "4"

def test_agent_tool_failure():
    """Test when tool fails"""
    agent.tools["calculator"] = lambda x: raise Exception("API down")
    result = agent.run("What's 2 + 2?")
    assert "error" in result.lower()
    assert "try again" in result.lower()

def test_agent_invalid_input():
    """Test with malformed input"""
    result = agent.run("")  # Empty query
    assert result is not None

def test_agent_timeout():
    """Test timeout handling"""
    def slow_tool(**kwargs):
        time.sleep(100)  # Simulate slow tool
    
    agent.tools["slow"] = slow_tool
    result = agent.run("Use slow tool", timeout=5)
    assert "timeout" in result.lower()

def test_agent_max_iterations():
    """Test loop protection"""
    result = agent.run("Impossible task", max_iterations=3)
    assert "maximum iterations" in result.lower()
```

---

## Summary

### Top Anti-Patterns to Avoid

1. ❌ **God Tools** - Keep tools focused and single-purpose
2. ❌ **Silent Failures** - Always return success/error clearly
3. ❌ **eval()** - Never use for user/agent input
4. ❌ **Credentials in Prompts** - Keep secrets out of LLM context
5. ❌ **No Validation** - Validate all inputs, especially destructive ones
6. ❌ **Infinite Loops** - Always have max iteration limits
7. ❌ **Testing in Production** - Use mocks and test environments
8. ❌ **No Error Testing** - Test failures, not just success
9. ❌ **Undocumented Tools** - LLM needs clear descriptions
10. ❌ **Sequential Operations** - Parallelize when possible

### Quick Checklist

Before deploying an agent, ask:

- [ ] Are all tools focused and well-documented?
- [ ] Do tools return clear success/failure indicators?
- [ ] Are credentials handled securely?
- [ ] Is there input validation on all tools?
- [ ] Are there max iteration limits?
- [ ] Have I tested error cases?
- [ ] Can operations run in parallel where appropriate?
- [ ] Is there caching for expensive operations?
- [ ] Are there no eval() calls on untrusted input?
- [ ] Is state managed cleanly?

---

**See Also:**
- [Design Patterns](patterns.md) - What TO do
- [Security Best Practices](../docs/04-security.md)
- [Testing Guide](../docs/testing.md)

