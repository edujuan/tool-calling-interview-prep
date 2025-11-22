# Fundamentals of Tool Use

Now that you understand *why* tool-calling matters (from the Introduction), let's dive into *how* it actually works. This chapter breaks down the mechanics that power every tool-calling agent, from the simplest calculator bot to complex multi-agent systems.

Think of this as learning the grammar before writing sentences. Once you understand these fundamentals, the agent architectures and patterns in later chapters will make much more sense.

## Core Concepts

Before an agent can use a tool, it needs to understand three things: what the tool is called, what it does, and what information it needs. Let's start with how tools are defined.

### 1. Tool Definition

A **tool** is any capability that an AI agent can invoke. It has three key components:

```python
{
    "name": "calculator",           # Unique identifier
    "description": "Performs...",   # What it does (for LLM)
    "parameters": {...}             # Input schema (what it needs)
}
```

**Example Tool Definition:**

```python
calculator_tool = {
    "name": "calculator",
    "description": "Evaluates mathematical expressions. Use for any calculation.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A valid Python mathematical expression (e.g., '2 + 2' or '10 * 5')"
            }
        },
        "required": ["expression"]
    }
}
```

So that's how you define a single tool. But a real agent has access to many tools - dozens or even hundreds. This raises an important question: how does the agent learn what tools exist and what they do?

### 2. Tool Discovery

**How does an agent know what tools are available?**

Imagine walking into a workshop full of tools. Before you can fix anything, you need to know what's in your toolbox. Same with AI agents - they need a way to discover their capabilities.

```
┌─────────────────┐
│  Agent Startup  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ List Available  │  ← Query: "What tools exist?"
│     Tools       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tool Registry  │  ← Returns: [calculator, weather_api, email_sender, ...]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent Memory   │  ← Stores tool capabilities
└─────────────────┘
```

**Three Discovery Approaches:**

1. **Static Configuration** (Simple)
   - Tools defined in code or config file
   - Agent loads them at startup
   - Best for: Small, fixed toolsets

2. **Dynamic Registry** (Flexible)
   - Tools registered with a central service
   - Agent queries registry at runtime
   - Best for: Large, changing toolsets

3. **Protocol-Based** (Standard)
   - MCP: Server advertises tools via `tools/list`[[6]](https://www.anthropic.com/news/model-context-protocol)
   - UTCP: Agent loads tool manuals from URLs/files[[8]](https://www.utcp.io/)
   - Best for: Interoperable systems

Discovery tells the agent what tools exist. But knowing about a tool isn't the same as using it. Let's see what happens when an agent actually invokes a tool.

### 3. Tool Invocation

**The complete flow:**

This is where the magic happens - the LLM decides a tool is needed, the agent executes it, and the result comes back to inform the next step.

```python
# 1. LLM decides to use a tool
llm_decision = {
    "action": "use_tool",
    "tool": "calculator",
    "arguments": {"expression": "25 * 4"}
}

# 2. Agent executes the tool
result = execute_tool(
    name="calculator",
    args={"expression": "25 * 4"}
)
# Returns: {"result": "100"}

# 3. Result goes back to LLM
llm_continues_with(result)
# LLM: "The answer is 100."
```

### 4. Tool Schemas

For all this to work, the LLM needs to understand what each tool expects as input. This is where schemas come in - they're like type hints that tell the LLM exactly what format the arguments should take.

Tools use **JSON Schema** to describe their inputs:[[9]](https://docs.fireworks.ai/guides/function-calling)

```json
{
  "type": "object",
  "properties": {
    "temperature": {
      "type": "number",
      "description": "Temperature in Celsius"
    },
    "unit": {
      "type": "string",
      "enum": ["C", "F"],
      "description": "Temperature unit"
    }
  },
  "required": ["temperature"]
}
```

**Why schemas matter:**
- LLMs understand what arguments to provide
- Validation prevents errors
- Documentation is built-in

Now that we understand tools, discovery, invocation, and schemas, let's see how these pieces fit together in an agent's operation. This is the fundamental loop that powers almost every tool-calling agent.

## The Tool-Calling Loop

Most agents follow this pattern:[[11]](https://docs.fireworks.ai/guides/function-calling)

This loop is the heartbeat of an agent. It continues cycling - thinking, acting, observing - until the task is complete.

```
1. Receive user input
      ↓
2. LLM analyzes → Decides: Answer directly OR use tool?
      ↓
3. If tool needed → LLM outputs: tool name + arguments
      ↓
4. Agent executes tool → Gets result
      ↓
5. Result added to context
      ↓
6. Loop back to step 2 (with new context)
      ↓
7. Final answer when no more tools needed
```

### Example: Multi-Step Task

**Task**: "Email my manager the current weather in San Francisco"

```
Step 1: User request received
  ↓
Step 2: LLM thinks: "I need weather data first"
  → Uses: weather_api(location="San Francisco")
  → Result: {"temp": 18, "condition": "foggy"}
  ↓
Step 3: LLM thinks: "Now I can compose and send email"
  → Uses: email_sender(
       to="manager@company.com",
       subject="SF Weather",
       body="Current weather: 18°C, foggy"
     )
  → Result: {"status": "sent", "id": "msg_123"}
  ↓
Step 4: LLM responds: "I've sent the email with the current weather!"
```

The loop above assumes tools execute immediately and return results quickly. But what if a tool takes 10 seconds? Or needs to run in parallel with others? This is where execution modes come in.

## Tool Execution Modes

How you execute tools affects your agent's performance and responsiveness. There are three main approaches, each with different trade-offs:

### 1. Synchronous (Wait for Result)

```python
def call_tool_sync(tool_name, args):
    """Wait for tool to complete before continuing"""
    result = execute(tool_name, args)  # Blocks here
    return result

# Usage
result = call_tool_sync("weather_api", {"location": "Paris"})
# Agent waits for API response
```

**Best for**: Fast tools (< 1 second), simple workflows

### 2. Asynchronous (Non-Blocking)

```python
async def call_tool_async(tool_name, args):
    """Don't wait - continue with other work"""
    task = execute_async(tool_name, args)  # Returns immediately
    # Agent can do other things
    result = await task  # Get result when ready
    return result

# Usage
task1 = call_tool_async("weather_api", {"location": "Paris"})
task2 = call_tool_async("weather_api", {"location": "London"})
results = await asyncio.gather(task1, task2)  # Parallel execution
```

**Best for**: Slow tools, parallel execution, responsiveness

### 3. Streaming (Progressive Results)

```python
def call_tool_streaming(tool_name, args):
    """Get results progressively as they come"""
    stream = execute_streaming(tool_name, args)
    for chunk in stream:
        yield chunk  # Process each piece as it arrives

# Usage
for data_chunk in call_tool_streaming("large_query", {...}):
    process(data_chunk)  # Show progress to user
```

**Best for**: Large data transfers, progress updates, long-running tasks

No matter which execution mode you choose, there's one constant: things will go wrong. APIs fail, networks timeout, arguments are invalid. The difference between a toy agent and a production-ready one is often just error handling.

## Error Handling

Tools can fail! Robust agents handle errors gracefully:

Understanding what can go wrong is the first step to building resilient agents.

### Common Error Types

```python
class ToolError:
    # 1. Tool doesn't exist
    ToolNotFoundError
    
    # 2. Invalid arguments
    InvalidArgumentsError
    
    # 3. Tool execution failed
    ExecutionError
    
    # 4. Timeout
    TimeoutError
    
    # 5. Permission denied
    PermissionError
```

### Error Handling Strategy

```python
def safe_tool_call(tool_name, args):
    """Execute tool with error handling"""
    try:
        # Validate tool exists
        if tool_name not in available_tools:
            return {"error": "Tool not found", "available": list(available_tools.keys())}
        
        # Validate arguments
        tool = available_tools[tool_name]
        validate_args(tool.schema, args)
        
        # Execute with timeout
        result = execute_with_timeout(tool, args, timeout=30)
        
        return {"success": True, "data": result}
        
    except ValidationError as e:
        return {"error": "Invalid arguments", "details": str(e)}
    
    except TimeoutError:
        return {"error": "Tool took too long to respond"}
    
    except Exception as e:
        return {"error": "Tool execution failed", "details": str(e)}
```

**What should the agent do with errors?**

1. **Retry**: Try again (maybe with different arguments)
2. **Fallback**: Use an alternative tool
3. **Inform**: Tell the user what went wrong
4. **Abort**: Give up and return error

With error handling in place, your agent can reliably use individual tools. But the real power comes from combining tools - using outputs from one as inputs to another, or running multiple tools simultaneously.

## Tool Composition

Complex tasks often require multiple tools working together. There are two primary patterns:

**Chaining**: Use output of one tool as input to another

This creates a pipeline where each tool builds on the previous one's work.

```python
# Step 1: Get data
data = search_tool(query="Python tutorials")

# Step 2: Summarize results
summary = summarize_tool(text=data)

# Step 3: Save to file
save_tool(content=summary, filename="summary.txt")
```

**Parallel Execution**: Run multiple tools simultaneously

```python
import asyncio

# Run three tools at once
results = await asyncio.gather(
    weather_tool(location="NYC"),
    weather_tool(location="LA"),
    weather_tool(location="Chicago")
)
```

You now understand the mechanics of tool-calling. But knowing how something works doesn't automatically mean you'll build it well. Let's cover the dos and don'ts learned from real-world agent development.

## Best Practices

### ✅ DO:

1. **Write clear descriptions**
   ```python
   # Good
   "Search the web for current information. Returns top 10 results."
   
   # Bad
   "Search"
   ```

2. **Validate inputs**
   ```python
   def tool(email: str):
       if not is_valid_email(email):
           raise ValueError("Invalid email format")
   ```

3. **Handle errors gracefully**
   ```python
   try:
       result = risky_operation()
   except Exception as e:
       return {"error": str(e), "suggestion": "Try with different parameters"}
   ```

4. **Set timeouts**
   ```python
   result = execute_with_timeout(tool, args, timeout=30)
   ```

5. **Log all tool calls**
   ```python
   logger.info(f"Calling {tool_name} with {args}")
   ```

### ❌ DON'T:

1. **Don't expose dangerous operations without safeguards**
   ```python
   # BAD - no restrictions!
   def run_shell_command(cmd: str):
       return os.system(cmd)
   ```

2. **Don't ignore errors**
   ```python
   # BAD
   try:
       result = tool()
   except:
       pass  # Silent failure!
   ```

3. **Don't hardcode credentials**
   ```python
   # BAD
   API_KEY = "sk-abc123..."  # Exposed!
   
   # GOOD
   API_KEY = os.environ.get("API_KEY")
   ```

4. **Don't make tools too complex**
   ```python
   # BAD - too many parameters
   def complex_tool(arg1, arg2, arg3, arg4, arg5, arg6):
       ...
   
   # GOOD - focused purpose
   def simple_tool(data: dict):
       ...
   ```

## Key Terminology

| Term | Definition |
|------|------------|
| **Tool** | A capability an agent can invoke (function, API, command) |
| **Schema** | JSON Schema defining tool inputs/outputs |
| **Discovery** | Process of finding available tools |
| **Invocation** | Executing a tool with specific arguments |
| **Result** | Data returned by a tool |
| **Chaining** | Using output of one tool as input to another |
| **Registry** | Central database of available tools |
| **Protocol** | Standard way to define and call tools (MCP, UTCP) |

## Summary

You've just learned the grammar of tool-calling. These aren't abstract concepts - they're the building blocks that every agent uses, whether it's a simple calculator bot or a complex multi-agent system.

**Core Principles:**

1. Tools extend LLM capabilities with actions and real-time data
2. Tools have names, descriptions, and parameter schemas
3. Agents discover, select, and invoke tools in a loop
4. Error handling is critical for reliability
5. Tools can be chained or parallelized for complex workflows

**What's Next:**

With these fundamentals in place, you're ready to see how they come together in actual agent architectures. How do you structure the loop? When do you plan vs react? How do multiple agents coordinate?

- **Beginner path**: Jump straight to [Building Your First Agent](07-first-agent.md) to apply these concepts hands-on
- **Architectural path**: Explore [Agent Architectures](03-agent-architectures.md) to see different design patterns
- **Protocol deep-dive**: Learn about [MCP vs UTCP](06-protocol-comparison.md) for standardized tool-calling

---

**Previous**: [← Introduction](01-introduction.md) | **Next**: [Agent Architectures →](03-agent-architectures.md)

