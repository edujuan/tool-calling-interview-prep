# Fundamentals of Tool Use

This chapter covers the core concepts you need to understand before building tool-calling agents.

## Core Concepts

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

### 2. Tool Discovery

**How does an agent know what tools are available?**

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
   - MCP: Server advertises tools via `tools/list`
   - UTCP: Agent loads tool manuals from URLs/files
   - Best for: Interoperable systems

### 3. Tool Invocation

**The complete flow:**

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

Tools use **JSON Schema** to describe their inputs:

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

## The Tool-Calling Loop

Most agents follow this pattern:

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

## Tool Execution Modes

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

## Error Handling

Tools can fail! Robust agents handle errors gracefully:

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

## Tool Composition

**Chaining**: Use output of one tool as input to another

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

**Core Principles:**

1. Tools extend LLM capabilities with actions and real-time data
2. Tools have names, descriptions, and parameter schemas
3. Agents discover, select, and invoke tools in a loop
4. Error handling is critical for reliability
5. Tools can be chained or parallelized for complex workflows

**What's Next:**

Now that you understand the fundamentals, let's explore:
- How agents are architectured ([Agent Architectures](03-agent-architectures.md))
- Specific protocols like MCP and UTCP ([Protocol docs](04-mcp-overview.md))
- Building your first agent ([First Agent Tutorial](07-first-agent.md))

---

**Previous**: [← Introduction](01-introduction.md) | **Next**: [Agent Architectures →](03-agent-architectures.md)

