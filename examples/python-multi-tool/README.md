# Multi-Tool Agent Example

> **Demonstrates intelligent use of multiple tools from different sources**

---

## Overview

This example showcases an AI agent that can use tools from multiple sources:

- **Native Python functions**: Calculator, file operations, time
- **External APIs**: Weather, news, translation (mocked)
- **MCP Server**: Database operations (simulated)

The agent intelligently selects and chains tools to accomplish complex tasks.

---

## Features

### ✨ Key Capabilities

1. **Unified Tool Registry**
   - Central registry for all tools
   - Supports multiple tool sources (native, API, MCP)
   - Automatic tool discovery and registration

2. **Intelligent Tool Selection**
   - LLM automatically picks the right tool for the task
   - Can chain multiple tools together
   - Handles tool dependencies

3. **Comprehensive Error Handling**
   - Graceful failure handling
   - Error messages returned as tool results
   - Retry logic built-in

4. **Tool Usage Analytics**
   - Track which tools are used
   - Measure execution time
   - View usage statistics

---

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY='your-key-here'

# Or use .env file
cp .env.example .env
# Edit .env and add your key
```

---

## Usage

### Run Interactive Mode

```bash
python main.py
```

### Example Interactions

#### Example 1: Tool Chaining

```
You: What's the weather in Paris? Translate the result to Spanish.

Agent:
[Iteration 1]
  🔧 Calling tool: get_weather
     Arguments: {"city": "Paris"}
     Result: {"city":"Paris","temperature":72,"condition":"Sunny"...}

[Iteration 2]
  🔧 Calling tool: translate_text
     Arguments: {"text": "Sunny, 72°F", "target_language": "es"}
     Result: {"translated": "[ES] Sunny, 72°F"...}

Agent: The weather in Paris is currently sunny with a temperature of 72°F. 
In Spanish: "Soleado, 72°F"
```

#### Example 2: Database + Calculation

```
You: Query all users from the database and calculate the average of their IDs.

Agent:
[Iteration 1]
  🔧 Calling tool: query_database
     Arguments: {"table": "users"}
     Result: {"results": [{"id": 1, ...}, {"id": 2, ...}]}

[Iteration 2]
  🔧 Calling tool: calculator
     Arguments: {"expression": "(1 + 2) / 2"}
     Result: {"result": 1.5}

Agent: I found 2 users in the database. The average of their IDs is 1.5.
```

#### Example 3: File Operations

```
You: Get the current time and save it to a file called 'timestamp.txt'

Agent:
[Iteration 1]
  🔧 Calling tool: current_time
     Result: {"time": "2024-01-15T10:30:00", ...}

[Iteration 2]
  🔧 Calling tool: write_file
     Arguments: {"filepath": "timestamp.txt", "content": "2024-01-15T10:30:00"}
     Result: {"success": true, "bytes_written": 19}

Agent: I've saved the current time (2024-01-15T10:30:00) to 'timestamp.txt'
```

---

## Architecture

### Tool Registry Pattern

```python
ToolRegistry
├── Native Tools (Python functions)
│   ├── calculator
│   ├── read_file
│   ├── write_file
│   └── current_time
├── API Tools (External services)
│   ├── get_weather
│   ├── search_news
│   └── translate_text
└── MCP Tools (Database server)
    ├── query_database
    └── insert_record
```

### Agent Flow

```
User Input
    ↓
[Agent: Analyze request]
    ↓
[Agent: Select tool(s) needed]
    ↓
[Execute tools]
    ↓
[Agent: Process results]
    ↓
[Need more tools?]
    ├─ Yes → Loop back
    └─ No  → Return final answer
```

---

## Available Tools

### Native Tools (4)

| Tool | Description |
|------|-------------|
| `calculator` | Evaluate mathematical expressions |
| `read_file` | Read file contents |
| `write_file` | Write content to file |
| `current_time` | Get current timestamp |

### API Tools (3)

| Tool | Description |
|------|-------------|
| `get_weather` | Get weather for a city |
| `search_news` | Search news articles |
| `translate_text` | Translate text to another language |

### MCP Tools (2)

| Tool | Description |
|------|-------------|
| `query_database` | Query database tables |
| `insert_record` | Insert record into database |

---

## Adding Custom Tools

### 1. Define Tool Function

```python
def my_custom_tool(param1: str, param2: int) -> str:
    """Your tool implementation"""
    result = do_something(param1, param2)
    return json.dumps({"result": result})
```

### 2. Create Tool Object

```python
custom_tool = Tool(
    name="my_custom_tool",
    description="What this tool does",
    parameters={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "First parameter"
            },
            "param2": {
                "type": "integer",
                "description": "Second parameter"
            }
        },
        "required": ["param1", "param2"]
    },
    function=my_custom_tool,
    source="native"  # or "api", "mcp"
)
```

### 3. Register Tool

```python
agent.registry.register(custom_tool)
```

---

## Tool Usage Statistics

The agent tracks tool usage:

```python
agent.show_tool_usage_stats()
```

Output:
```
📊 Tool Usage Statistics
========================================

Total tool calls: 8
Unique tools used: 5

Breakdown by tool:
  • calculator (native): 2 calls, avg 0.003s
  • get_weather (api): 2 calls, avg 0.150s
  • query_database (mcp): 1 call, avg 0.002s
  • translate_text (api): 2 calls, avg 0.120s
  • write_file (native): 1 call, avg 0.001s
```

---

## Best Practices

### ✅ DO:

1. **Use descriptive tool names**
   ```python
   # Good
   name="query_database"
   
   # Bad
   name="db_q"
   ```

2. **Provide clear descriptions**
   ```python
   description="Query database tables. Available tables: users, products. Can filter by key-value pairs."
   ```

3. **Validate inputs**
   ```python
   def my_tool(param: str) -> str:
       if not param:
           return json.dumps({"error": "Parameter required"})
       # ... rest of implementation
   ```

4. **Return JSON**
   ```python
   return json.dumps({
       "success": True,
       "data": result
   })
   ```

5. **Handle errors gracefully**
   ```python
   try:
       result = risky_operation()
       return json.dumps({"result": result})
   except Exception as e:
       return json.dumps({"error": str(e)})
   ```

### ❌ DON'T:

1. **Don't use side effects without documenting**
2. **Don't return raw strings (use JSON)**
3. **Don't ignore errors**
4. **Don't create tools with overlapping functionality**
5. **Don't forget parameter descriptions**

---

## Comparison with Other Patterns

| Feature | Multi-Tool | ReAct | Planner-Executor |
|---------|------------|-------|------------------|
| Tool Selection | Automatic | Manual loop | Planned upfront |
| Tool Chaining | Automatic | Manual | Explicit in plan |
| Flexibility | High | Medium | Low |
| Complexity | Medium | Low | High |
| Best For | Diverse tools | Simple tasks | Complex workflows |

---

## Extending to Real APIs

### Weather API (OpenWeatherMap)

```python
import requests

def get_weather(city: str) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    return json.dumps({
        "city": city,
        "temperature": data['main']['temp'],
        "condition": data['weather'][0]['description'],
        "humidity": data['main']['humidity']
    })
```

### News API

```python
def search_news(query: str, limit: int = 5) -> str:
    api_key = os.getenv("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    
    response = requests.get(url)
    data = response.json()
    
    articles = [
        {
            "title": a['title'],
            "source": a['source']['name'],
            "published": a['publishedAt']
        }
        for a in data['articles'][:limit]
    ]
    
    return json.dumps({"articles": articles, "query": query})
```

---

## Troubleshooting

### Issue: "Tool not found"

**Solution:** Make sure tool is registered:

```python
agent.registry.register(your_tool)
```

### Issue: Tool fails silently

**Solution:** Check error handling in tool function. Always return JSON:

```python
try:
    result = tool_logic()
    return json.dumps({"result": result})
except Exception as e:
    return json.dumps({"error": str(e)})
```

### Issue: Agent doesn't use tools

**Solution:** 
- Check tool descriptions are clear
- Verify OpenAI API key is valid
- Try a more explicit user request

---

## Learn More

- [Agent Architectures](../../docs/03-agent-architectures.md)
- [Tool Calling Fundamentals](../../docs/02-fundamentals.md)
- [Design Patterns](../../design/patterns.md)

---

## License

MIT License - See [LICENSE](../../LICENSE) for details.



