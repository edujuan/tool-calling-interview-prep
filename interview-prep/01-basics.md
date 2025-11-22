# Basics Questions (1-20)

## Basics

### 1. What is an AI agent?

**Answer:**

An AI agent is an AI-driven application that can perform tasks autonomously or semi-autonomously. Unlike a simple chatbot that only generates text responses, an agent can:
- Take actions in the real world (send emails, create files, execute commands)
- Access external information (query databases, call APIs)
- Iterate on tasks until completion
- Make decisions about what steps to take next

**Example:** A customer support agent that can search a knowledge base, query customer records, and create support tickets - not just answer questions.

**Key distinction:** Chatbot responds, Agent acts.

**See also:** [What Are AI Agents?](../docs/01-introduction.md#what-are-ai-agents) for detailed explanation of agent capabilities and limitations.

---

### 2. What is tool-calling?

**Answer:**

Tool-calling is the ability of an AI agent to execute external functions, APIs, or commands to perform tasks beyond text generation.

**Key components:**
1. **Tool Definition:** Specification of what the tool does and what inputs it needs
2. **Tool Discovery:** How the agent learns what tools are available
3. **Tool Selection:** Agent decides which tool to use
4. **Tool Execution:** Agent invokes the tool with appropriate parameters
5. **Result Processing:** Agent interprets the tool's output

**Example:**
```python
# Tool definition
def get_weather(location: str) -> dict:
    """Get current weather for a location"""
    return {"temp": 72, "condition": "sunny"}

# Agent uses it
agent.query("What's the weather in SF?")
# → Agent calls get_weather("San Francisco")
# → Returns: "It's 72°F and sunny in San Francisco"
```

**See also:** [The Solution: Tool-Calling](../docs/01-introduction.md#the-solution-tool-calling) and [Tool Definition](../docs/02-fundamentals.md#1-tool-definition) for detailed implementation.

---

### 3. Why do we need tool-calling? Can't LLMs do everything?

**Answer:**

LLMs have fundamental limitations:

1. **Static Knowledge:** Trained on data up to a cutoff date, can't access real-time information
2. **No Actions:** Can only generate text, cannot execute operations
3. **Hallucination:** May make up answers when uncertain
4. **Limited Reliability:** Poor at precise calculations or structured data processing

**Tool-calling solves this** by letting LLMs delegate to specialized systems:
- Need current weather? → Call weather API
- Need to calculate? → Call calculator
- Need to send email? → Call email service

**Analogy:** Like a manager (LLM) coordinating with specialists (tools) rather than trying to do everything themselves.

**See also:** [The Problem: LLMs Are Limited](../docs/01-introduction.md#the-problem-llms-are-limited) for detailed breakdown of LLM limitations and why agents are necessary.

---

### 4. What's the difference between function-calling and tool-calling?

**Answer:**

**Function-calling** is a specific implementation:
- Term used by OpenAI for their API feature
- LLM outputs structured JSON indicating which function to call
- Model-specific feature (tied to OpenAI, or similar vendors)

**Tool-calling** is the broader concept:
- General term for agents using external capabilities
- Includes functions, APIs, CLIs, databases, etc.
- Protocol-agnostic (can use UTCP, MCP, custom approaches)

**Relationship:** Function-calling is one way to implement tool-calling.

```
Tool-Calling (concept)
├── Function-calling (OpenAI's approach)
├── MCP (protocol)
├── UTCP (protocol)
└── Custom implementations
```

**See also:** [Tool-Calling Fundamentals](../docs/02-fundamentals.md) for terminology and [Protocol Comparison](../docs/06-protocol-comparison.md) for understanding different implementation approaches.

---

### 5. How does an agent know what tools are available?

**Answer:**

**Three common approaches:**

1. **Static Configuration** (Simple)
   ```python
   tools = [calculator, weather_api, email_sender]
   agent = Agent(tools=tools)
   ```
   - Tools hardcoded at startup
   - Simple but inflexible

2. **Dynamic Registry** (Flexible)
   ```python
   registry = ToolRegistry()
   registry.register(calculator)
   registry.register(weather_api)
   agent = Agent(registry=registry)
   ```
   - Tools can be added/removed at runtime
   - Centralized management

3. **Protocol-Based** (Standard)
   - **MCP:** Server advertises tools via `list_tools()` call
   - **UTCP:** Agent loads tool manuals from files/URLs
   - Interoperable across systems

**In practice:** Use static for prototypes, registry for medium systems, protocols for large/enterprise systems.

**See also:** [Tool Discovery](../docs/02-fundamentals.md#2-tool-discovery) for detailed implementation patterns and [Tool Registry architecture](02-architecture.md#25-what-is-a-tool-registry-and-why-use-one) for production systems.

---

### 6. Walk me through what happens when an agent uses a tool.

**Answer:**

**The typical flow:**

```
1. User asks question
      ↓
2. LLM receives: [user question, list of available tools]
      ↓
3. LLM decides: "I need tool X to answer this"
      ↓
4. LLM outputs: {tool: "calculator", args: {"expression": "10*5"}}
      ↓
5. Agent code intercepts this structured output
      ↓
6. Agent executes: calculator(expression="10*5")
      ↓
7. Tool returns: {"result": "50"}
      ↓
8. Result added to conversation context
      ↓
9. LLM receives result and formats answer
      ↓
10. Agent returns: "The answer is 50"
```

**Key points:**
- LLM doesn't execute tools (it just decides and formats)
- Agent code is the bridge between LLM and tools
- Multiple iterations possible for complex tasks

**See also:** [Tool Invocation](../docs/02-fundamentals.md#3-tool-invocation) and [The Tool-Calling Loop](../docs/02-fundamentals.md#the-tool-calling-loop) for detailed step-by-step implementation with code examples.

---

### 7. What information does a tool definition typically include?

**Answer:**

A complete tool definition specifies:

**1. Name** - Identifier for the tool
```python
"name": "get_weather"
```

**2. Description** - What the tool does
```python
"description": "Get current weather conditions for any city"
```

**3. Parameters** - Input schema
```python
"parameters": {
  "location": {
    "type": "string",
    "description": "City name",
    "required": true
  }
}
```

**4. Return Type** - What the tool outputs
```python
"returns": {
  "type": "object",
  "properties": {
    "temperature": {"type": "number"},
    "condition": {"type": "string"}
  }
}
```

**5. Examples** (Optional but helpful)
```python
"examples": [
  {
    "input": {"location": "Paris"},
    "output": {"temperature": 18, "condition": "cloudy"}
  }
]
```

**This is similar to:**
- OpenAPI specs for REST APIs
- Function signatures in programming
- Man pages for CLI tools

**See also:** [Tool Definition](../docs/02-fundamentals.md#1-tool-definition) for detailed schema specifications and [UTCP Tool Schema](../protocols/utcp/specification.md) for protocol-level implementation.

---

### 8. What's the difference between synchronous and asynchronous tool calls?

**Answer:**

**Synchronous (Blocking):**
```python
# Agent waits for tool to complete
result = call_tool("database_query", {"sql": "SELECT ..."})
# Agent can't do anything until this returns
format_response(result)
```

**Asynchronous (Non-blocking):**
```python
# Agent can do other things while waiting
task1 = call_tool_async("weather", {"city": "NYC"})
task2 = call_tool_async("weather", {"city": "LA"})

# Do other work...

# Get results when needed
result1 = await task1
result2 = await task2
```

**Comparison:**

| Aspect | Sync | Async |
|--------|------|-------|
| **Blocking** | Yes | No |
| **Parallel calls** | No | Yes |
| **Complexity** | Lower | Higher |
| **Performance** | Slower | Faster |
| **Best for** | Simple tasks | I/O-heavy workloads |

**When to use async:**
- Multiple independent API calls
- I/O-heavy operations
- Need responsiveness

**See also:** [Asynchronous Tool Execution](../docs/02-fundamentals.md) for implementation patterns and [Concurrent Tool Calls](02-architecture.md#31-how-do-you-handle-concurrent-tool-calls-safely) for production-grade parallel execution.

---

### 9. What is a tool schema and why is it important?

**Answer:**

A **tool schema** defines the structure and validation rules for tool inputs/outputs.

**Purpose:**
1. **Validation** - Ensure correct inputs before calling
2. **LLM Guidance** - Help LLM format requests correctly
3. **Documentation** - Self-describing interface
4. **Type Safety** - Catch errors early

**Example with JSON Schema:**
```json
{
  "name": "send_email",
  "parameters": {
    "type": "object",
    "properties": {
      "to": {
        "type": "string",
        "format": "email",
        "description": "Recipient email"
      },
      "subject": {
        "type": "string",
        "maxLength": 100
      },
      "body": {
        "type": "string"
      }
    },
    "required": ["to", "subject", "body"]
  }
}
```

**Benefits:**
- ✅ Prevents malformed requests
- ✅ Improves LLM accuracy
- ✅ Enables auto-generated documentation
- ✅ Allows validation before expensive API calls

**See also:** [Tool Schemas](../docs/02-fundamentals.md#4-tool-schemas) for JSON Schema fundamentals and [UTCP Parameters Schema](../protocols/utcp/specification.md) for protocol implementation details.

---

### 10. How do you handle tool errors in an agent?

**Answer:**

**Multi-layer error handling:**

**1. Graceful Degradation**
```python
try:
    weather = call_tool("weather_api", {"city": city})
except ToolError:
    # Fall back to cached data or alternative tool
    weather = get_cached_weather(city) or "Weather unavailable"
```

**2. Retry with Backoff**
```python
@retry(max_attempts=3, backoff=exponential)
def call_tool_with_retry(tool, args):
    return call_tool(tool, args)
```

**3. Error Context to LLM**
```python
# Don't just crash - inform the LLM
tool_result = {
    "success": False,
    "error": "API rate limit exceeded",
    "suggestion": "Try again in 60 seconds or use alternate data source"
}
# LLM can adapt its approach
```

**4. Circuit Breaker**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5):
        self.failures = 0
        self.threshold = failure_threshold
        self.state = "closed"  # closed = working
    
    def call(self, func):
        if self.state == "open":
            raise CircuitOpenError("Too many failures, circuit open")
        
        try:
            result = func()
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.state = "open"
            raise
```

**Best Practice:** Always provide context to the LLM about what went wrong and potential alternatives.

**See also:** [Error Handling Example](../examples/python-error-handling/) for production-ready implementation and [Advanced Retry Strategies](02-architecture.md#28-how-do-you-implement-tool-retry-logic) for sophisticated error recovery patterns.

---

### 11. What is the difference between tools, resources, and prompts in agent systems?

**Answer:**

These are three different capabilities an agent might access:

**Tools** - **Actions** the agent can perform
```python
# Tool: Does something
def send_email(to, subject, body):
    # Performs an action
    return {"sent": True, "message_id": "123"}
```

**Resources** - **Data** the agent can read
```python
# Resource: Provides information
def get_documentation():
    # Returns static or dynamic data
    return {"docs": "...", "version": "1.0"}
```

**Prompts** - **Templates** for specialized tasks
```python
# Prompt: Guidance for specific task
CODE_REVIEW_PROMPT = """
You are a code reviewer. Analyze this code for:
- Security issues
- Performance problems
- Best practice violations
"""
```

**In MCP:**
- `list_tools()` - Get available actions
- `list_resources()` - Get available data sources
- `list_prompts()` - Get task templates

**In UTCP:**
- All are modeled as tools (unified interface)

**Example:**
```
Question: "Summarize our Q4 report"

1. Use resource: Get Q4 report data
2. Use prompt: Apply summarization template
3. Use tool: Save summary to file
```

**See also:** [MCP Resources vs Tools](03-protocols.md#52-what-are-mcp-resources-and-how-do-they-differ-from-tools) for detailed implementation and [Protocol Comparison](../docs/06-protocol-comparison.md) for understanding these primitives across protocols.

---

### 12. How does context window size affect tool-calling?

**Answer:**

**Context window** is the total tokens an LLM can process at once.

**Impact on tool-calling:**

**1. Tool Definitions Take Space**
```
Context budget: 8,000 tokens
- System prompt: 500 tokens
- Tool definitions (10 tools): 2,000 tokens
- Conversation history: 3,000 tokens
- Available for response: 2,500 tokens
```

**2. Tool Results Accumulate**
```
Turn 1: Call tool → 500 token result
Turn 2: Call tool → 800 token result
Turn 3: Call tool → 600 token result
Total: 1,900 tokens just from tool outputs
```

**3. Strategies for Large Context:**

**Selective Tool Loading:**
```python
# Don't load all 100 tools at once
relevant_tools = select_tools_for_query(user_query)
# Only load 5-10 relevant ones
```

**Result Summarization:**
```python
# Don't keep full API responses
tool_result = call_api()  # 2000 tokens
summarized = summarize(tool_result)  # 200 tokens
# Use summary in context
```

**Context Sliding:**
```python
# Keep only recent turns
if context_length > MAX_TOKENS:
    context = keep_recent_turns(context, keep=5)
    # Preserve system prompt + recent history
```

**4. Modern Models**
- GPT-4: 8K-128K tokens
- Claude: 200K+ tokens
- Longer context = more tools + history possible

**See also:** [Context Management in Fundamentals](../docs/02-fundamentals.md) and [Emerging Context Challenges](06-advanced.md#94-what-are-the-emerging-challenges-in-ai-agent-systems-as-of-2025) for advanced context optimization techniques.

---

### 13. What is tool chaining and when is it useful?

**Answer:**

**Tool chaining** is when an agent uses multiple tools in sequence, where each tool's output feeds into the next.

**Example:**
```
User: "Find the weather in the capital of France and convert the temperature to Fahrenheit"

Chain:
1. get_capital("France") → "Paris"
2. get_weather("Paris") → {"temp_celsius": 18}
3. convert_temperature(18, "C", "F") → 64.4
4. Format: "The weather in Paris is 64.4°F"
```

**Types:**

**1. Linear Chain** (Sequential)
```
Tool A → Tool B → Tool C → Result
```

**2. Branching Chain** (Conditional)
```
Tool A → if X: Tool B
      → else: Tool C
```

**3. Parallel Chain** (Concurrent)
```
Tool A ↘
Tool B → Combine → Result
Tool C ↗
```

**When useful:**
- ✅ Complex multi-step tasks
- ✅ Data transformation pipelines
- ✅ When single tool insufficient
- ✅ Composing simple tools into complex behavior

**Implementation:**
```python
async def execute_chain(tools, initial_input):
    result = initial_input
    for tool in tools:
        result = await tool(result)
    return result
```

**See also:** [Tool Selection and Chaining](../docs/03-agent-architectures.md#tool-selection-and-chaining) for advanced chaining patterns and [Tool Composition](02-architecture.md#29-what-is-tool-composition-and-how-does-it-work) for building complex tools from simple ones.

---

### 14. How do you prevent an agent from using the wrong tool?

**Answer:**

**Strategies:**

**1. Clear Tool Descriptions**
```python
# Bad
def process(data):
    """Processes data"""

# Good
def calculate_sales_tax(amount: float, state: str) -> float:
    """
    Calculate US state sales tax.
    
    Args:
        amount: Purchase amount in USD
        state: Two-letter state code (e.g., 'CA', 'NY')
    
    Returns:
        Tax amount in USD
        
    Example:
        calculate_sales_tax(100.00, 'CA') → 7.25
    """
```

**2. Tool Categories/Tags**
```python
tools = {
    "weather": ["get_weather", "get_forecast"],
    "math": ["calculate", "convert_units"],
    "data": ["query_db", "search_documents"]
}
# Agent can filter by category
```

**3. Validation Layer**
```python
def validate_tool_selection(query, selected_tool):
    """Verify tool makes sense for query"""
    if "weather" in query and selected_tool not in weather_tools:
        return False, "Query is about weather but tool isn't"
    return True, None
```

**4. Few-Shot Examples**
```python
system_prompt = """
Examples of correct tool usage:
- "What's 2+2?" → use calculator
- "What's the weather?" → use weather_api
- "Send email" → use email_tool

Now handle this query:
"""
```

**5. Constrained Selection**
```python
# For specific task, only allow relevant tools
agent = Agent(
    tools=all_tools,
    allowed_for_query=["weather_api"]  # Restrict choices
)
```

**See also:** [Tool Selection Strategies](../docs/03-agent-architectures.md#tool-selection-and-chaining) for advanced selection patterns and [Anti-Patterns: Tool Overload](../design/anti-patterns.md) for what to avoid.

---

### 15. What are the trade-offs between having many specialized tools vs few general tools?

**Answer:**

**Many Specialized Tools:**

**Pros:**
- ✅ Each tool does one thing well
- ✅ Easier for LLM to choose (clear purpose)
- ✅ Simpler individual implementations
- ✅ Better error messages (specific to task)

**Cons:**
- ❌ Context window fills up faster (more definitions)
- ❌ LLM might struggle to choose from 100+ options
- ❌ More maintenance overhead
- ❌ Higher token costs (listing all tools)

**Example:**
```python
# Specialized
get_current_temperature(city)
get_forecast(city, days)
get_humidity(city)
get_wind_speed(city)
# 4 tools, very specific
```

**Few General Tools:**

**Pros:**
- ✅ Less context window usage
- ✅ Simpler tool selection
- ✅ Fewer definitions to maintain
- ✅ More flexible (handles variations)

**Cons:**
- ❌ Each tool more complex
- ❌ Harder to describe clearly
- ❌ More ways to use incorrectly
- ❌ LLM needs to understand parameters better

**Example:**
```python
# General
get_weather_data(city, metrics=["temp", "forecast", "humidity", "wind"])
# 1 tool, very flexible
```

**Best Practice: Balanced Approach**
```python
# Medium granularity
get_current_weather(city)  # Current conditions
get_forecast(city, days)    # Future predictions
# 2 tools - balance of clarity and simplicity
```

**Rule of thumb:**
- < 20 tools: Can be specialized
- 20-50 tools: Mix of specialized and general
- > 50 tools: Need general tools or dynamic loading

**See also:** [Tool Design Patterns](../design/patterns.md) for best practices and [Tool Granularity in Fundamentals](../docs/02-fundamentals.md) for detailed guidance on tool design.

---

### 16. How do you document tools for an LLM vs for humans?

**Answer:**

**For LLMs: Concise, structured, example-driven**

```json
{
  "name": "search_products",
  "description": "Search product catalog. Returns top 10 matching products.",
  "parameters": {
    "query": {
      "type": "string",
      "description": "Search keywords. Example: 'red shoes' or 'laptop under $1000'"
    },
    "category": {
      "type": "string",
      "enum": ["electronics", "clothing", "home"],
      "description": "Optional category filter"
    }
  },
  "examples": [
    {
      "input": {"query": "wireless headphones", "category": "electronics"},
      "output": {"results": [...], "count": 10}
    }
  ]
}
```

**Key for LLMs:**
- ✅ Clear one-line description
- ✅ Explicit parameter types
- ✅ Examples of valid inputs
- ✅ Expected output structure
- ✅ No ambiguity

**For Humans: Comprehensive, contextual, troubleshooting**

```markdown
# search_products

Search the product catalog with flexible keyword matching.

## Description
Searches across product names, descriptions, and tags using fuzzy matching.
Results are ranked by relevance score.

## Parameters
- `query` (string, required): Search keywords
  - Supports multi-word queries
  - Case-insensitive
  - Uses fuzzy matching (tolerates typos)
- `category` (string, optional): Filter by category
  - Valid values: electronics, clothing, home
  - Default: search all categories

## Returns
```json
{
  "results": [{"id": "...", "name": "...", "price": ...}],
  "count": 10,
  "total_matches": 156
}
```

## Examples
```python
# Simple search
search_products(query="laptop")

# With category filter
search_products(query="laptop", category="electronics")
```

## Error Handling
- Empty query → returns 400 error
- Invalid category → ignored, searches all
- No results → returns empty array

## Performance
- Average response time: 50ms
- Rate limit: 100 requests/minute
```

**Key for Humans:**
- ✅ Full context and use cases
- ✅ Troubleshooting info
- ✅ Performance characteristics
- ✅ Edge cases and error handling
- ✅ Multiple examples

**See also:** [Tool Documentation Best Practices](../docs/02-fundamentals.md) and [UTCP Specification](../protocols/utcp/specification.md) for protocol-level documentation standards.

---

### 17. What is streaming in the context of tool-calling?

**Answer:**

**Streaming** means getting tool results progressively rather than all at once.

**Use cases:**

**1. Long-running operations**
```python
# Non-streaming (blocking)
result = analyze_large_file()  # Wait 30 seconds
print(result)  # All at once

# Streaming
for chunk in analyze_large_file_streaming():
    print(chunk)  # Show progress as it goes
    # "Analyzing... 10%"
    # "Analyzing... 50%"
    # "Complete!"
```

**2. Real-time data**
```python
# Stock price feed
async for price_update in stream_stock_prices("AAPL"):
    agent.process(price_update)
    # Updates flow continuously
```

**3. LLM generation with tools**
```python
# Stream LLM output while it's generating
async for token in llm.generate_stream(prompt):
    print(token, end='')
    
    # Can call tools mid-generation if LLM decides to
    if tool_call_detected(token):
        result = await call_tool()
        continue_generation_with_result(result)
```

**Protocols:**

**Server-Sent Events (SSE):**
```python
# UTCP with SSE
{
  "call_template_type": "sse",
  "url": "https://api.example.com/stream"
}
```

**WebSocket:**
```python
# Bidirectional streaming
async with websocket.connect(url) as ws:
    await ws.send(request)
    async for message in ws:
        process(message)
```

**Benefits:**
- ✅ Better UX (see progress)
- ✅ Can cancel long operations
- ✅ Lower perceived latency
- ✅ Handle large data efficiently

**See also:** [Streaming Example](../examples/python-streaming/) for working implementation and [UTCP Streaming Protocols](../protocols/utcp/specification.md) for SSE and WebSocket support.

---

### 18. How do you handle pagination when a tool returns large datasets?

**Answer:**

**Strategies:**

**1. Automatic Pagination (Agent handles it)**
```python
def search_all_results(query):
    """Tool automatically fetches all pages"""
    all_results = []
    page = 1
    
    while True:
        response = api.search(query, page=page)
        all_results.extend(response.results)
        
        if not response.has_more:
            break
        page += 1
    
    return all_results
```

**Pros:** Simple for agent
**Cons:** Can be slow, wasteful if agent doesn't need all data

**2. Explicit Pagination (Agent controls it)**
```python
# First call
result = search(query="laptop", page=1, per_page=20)
# Returns: {"results": [...], "page": 1, "total_pages": 10}

# Agent decides if it needs more
if need_more_results:
    result2 = search(query="laptop", page=2, per_page=20)
```

**Pros:** Agent controls what to fetch
**Cons:** More complex, requires agent to understand pagination

**3. Cursor-Based Pagination**
```python
# First call
result = search(query="laptop", limit=20)
# Returns: {"results": [...], "next_cursor": "abc123"}

# Next page
result2 = search(query="laptop", cursor="abc123", limit=20)
```

**Pros:** Efficient, consistent results
**Cons:** Can't jump to specific page

**4. Smart Summarization**
```python
def smart_search(query, max_results=50):
    """Fetch limited results + summary of rest"""
    
    full_count = api.count(query)
    results = api.search(query, limit=max_results)
    
    return {
        "results": results,
        "summary": f"Showing top {max_results} of {full_count} total results",
        "has_more": full_count > max_results
    }
```

**Pros:** Gives context without fetching everything
**Cons:** Summary might not be sufficient

**Best Practice:**
```python
# Let LLM decide
result = search(query, page=1)

# LLM sees in system prompt:
"""
If search results show has_more: true, you can call the tool again 
with page=2 to get more results. Only fetch additional pages if 
needed to answer the user's question.
"""
```

**See also:** [Handling Large Datasets](../docs/02-fundamentals.md) for pagination patterns and [Result Processing](03-protocols.md#57-how-do-you-handle-large-payloads-in-mcp-and-utcp) for large payload strategies.

---

### 19. What is tool authentication and how do you handle it securely?

**Answer:**

**Tool authentication** is proving the agent has permission to use a tool.

**Common Methods:**

**1. API Keys**
```python
# DON'T put in tool definition visible to LLM
{
  "name": "send_email",
  "api_key": "secret-key-123"  # ❌ Bad
}

# DO inject at execution time
def call_tool(tool_name, args):
    api_key = os.getenv(f"{tool_name.upper()}_API_KEY")
    return tool_implementation(args, auth=api_key)
```

**2. OAuth Tokens**
```python
# Get user's OAuth token
token = oauth.get_user_token(user_id)

# Use for tool calls
headers = {"Authorization": f"Bearer {token}"}
result = requests.post(tool_url, json=args, headers=headers)
```

**3. Per-User Credentials**
```python
class SecureToolExecutor:
    def __init__(self, user_id):
        self.user_id = user_id
        self.credentials = get_user_credentials(user_id)
    
    def call_tool(self, tool_name, args):
        # Use user's own credentials
        creds = self.credentials[tool_name]
        return execute_with_auth(tool_name, args, creds)
```

**4. Service Accounts**
```python
# Agent uses service account (least privilege)
SERVICE_ACCOUNT = {
    "type": "service_account",
    "permissions": ["read_calendar", "read_email"]  # Limited
}

# Can't do admin operations
```

**Security Principles:**

**✅ DO:**
- Store credentials in environment/secrets manager
- Use least-privilege service accounts
- Inject credentials at runtime (not in prompts)
- Rotate credentials regularly
- Audit all tool calls

**❌ DON'T:**
- Hardcode credentials
- Pass credentials through LLM
- Log credentials
- Give admin access by default
- Share credentials across users

**Architecture:**
```
Agent (no credentials)
  ↓
Tool Executor (has credentials)
  ↓
External API
```

The agent never sees credentials directly.

**See also:** [Security Best Practices](../docs/04-security.md) for comprehensive security guidance, [API Key Management](04-security.md#63-how-should-an-agent-handle-api-keys-and-secrets) for secret storage, and [Protocol Authentication](03-protocols.md#53-how-do-you-handle-authentication-in-utcp-vs-mcp) for UTCP/MCP approaches.

---

### 20. How do you measure the effectiveness of tool-calling in an agent?

**Answer:**

**Key Metrics:**

**1. Tool Selection Accuracy**
```python
# Did agent choose the right tool?
correct_selections = 0
total_queries = 0

for query, expected_tool in test_cases:
    selected_tool = agent.decide_tool(query)
    if selected_tool == expected_tool:
        correct_selections += 1
    total_queries += 1

accuracy = correct_selections / total_queries
# Target: > 95%
```

**2. Task Completion Rate**
```python
# Did agent successfully complete the task?
completed = sum(1 for task in tasks if task.status == "completed")
completion_rate = completed / len(tasks)
# Target: > 90%
```

**3. Efficiency (Steps to Completion)**
```python
# How many tool calls did it take?
optimal_steps = get_optimal_solution(task)
actual_steps = agent.execute(task).steps

efficiency = optimal_steps / actual_steps
# Target: > 0.8 (at most 25% more steps than optimal)
```

**4. Latency**
```python
# Time to complete
start = time.time()
result = agent.execute(task)
latency = time.time() - start

# Target: < 5 seconds for simple tasks
```

**5. Error Rate**
```python
# How often do tool calls fail?
failed_calls = sum(1 for call in calls if call.failed)
error_rate = failed_calls / len(calls)
# Target: < 5%
```

**6. Cost**
```python
# Token usage and API costs
total_tokens = sum(call.tokens for call in calls)
api_costs = sum(call.cost for call in calls)
llm_costs = total_tokens * token_price

total_cost = api_costs + llm_costs
# Track per task
```

**Dashboard Example:**
```python
metrics = {
    "tool_selection_accuracy": 0.96,
    "task_completion_rate": 0.92,
    "avg_steps_to_completion": 3.2,
    "avg_latency_seconds": 4.1,
    "error_rate": 0.03,
    "avg_cost_per_task": 0.015  # USD
}
```

**Continuous Monitoring:**
```python
# Log every tool call
logger.info({
    "query": user_query,
    "tool_selected": tool_name,
    "tool_correct": was_correct,
    "completed": success,
    "steps": num_steps,
    "latency": duration,
    "cost": total_cost
})

# Analyze weekly
generate_report(last_7_days)
```

**See also:** [Production Monitoring Example](../examples/python-production/) for complete observability implementation and [Monitoring Strategies](05-production.md#76-how-do-you-monitor-an-agent-system-in-production) for production-grade metrics collection.

---

**Related Resources:**
- [Architecture Patterns](02-architecture.md) - Agent patterns, tool registries, error handling
- [Protocol Details](03-protocols.md) - UTCP/MCP protocols and resources
- [Security Practices](04-security.md) - Authentication and secure tool execution
- [Production Operations](05-production.md) - Monitoring, deployment, and scaling
- [Advanced Topics](06-advanced.md) - Context management and emerging challenges
- [Full Documentation](../docs/) - Complete guides on agents, protocols, and security
- [Working Examples](../examples/) - Production-ready code examples
- [Back to Main Questions](README.md)
