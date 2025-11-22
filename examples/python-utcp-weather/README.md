# UTCP Weather Agent Example (Official v1.0.1 Library)

> **Real-world UTCP v1.0.1 implementation using the actual Python library**

**✅ Updated:** This example uses the official UTCP v1.0.1 Python library (`utcp`, `utcp-http`)

---

## Overview

This example demonstrates **UTCP (Universal Tool Calling Protocol)** - a lightweight approach to tool calling that:

- ✅ **No server required** - Direct API calls
- ✅ **JSON manuals** - Describe APIs declaratively  
- ✅ **Stateless** - No session management
- ✅ **Leverages existing APIs** - Works with any REST API

This agent uses the free OpenWeatherMap API to provide weather information.

---

## What is UTCP?

UTCP is an alternative to MCP (Model Context Protocol) with a simpler architecture:

### MCP vs UTCP

| Feature | MCP | UTCP |
|---------|-----|------|
| **Architecture** | Client-Server | Direct API |
| **State** | Stateful sessions | Stateless |
| **Setup** | Run server process | Load JSON manual |
| **Library** | Custom server code | Official client library |
| **Complexity** | Higher | Lower |
| **Best For** | Complex integrations | Simple API calls |

### This Example Uses

- ✅ Official UTCP v1.0.1 Python library
- ✅ `UtcpClient` for tool execution
- ✅ `CallTemplate` for manual loading
- ✅ Proper async/await patterns

---

## Features

### ✨ Key Capabilities

1. **Current Weather**
   - Temperature, humidity, wind
   - Weather conditions
   - Visibility

2. **5-Day Forecast**
   - 3-hour intervals
   - Temperature ranges
   - Condition predictions

3. **UTCP v1.0.1 Library**
   - Official Python client (`utcp`)
   - HTTP protocol plugin (`utcp-http`)
   - Async tool execution
   - Proper variable substitution (`${VAR}` syntax)

---

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key ([Get one](https://platform.openai.com/api-keys))
- OpenWeatherMap API key ([Get free key](https://openweathermap.org/api))

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY='your-openai-key'
export OPENWEATHER_API_KEY='your-openweather-key'

# Or use .env file
cp .env.example .env
# Edit .env and add your keys
```

---

## Usage

### Run Interactive Mode

```bash
python main.py
```

### Example Queries

```
💬 What's the weather in Tokyo?

[Iteration 1]
  🌤️  Calling UTCP tool: get_current_weather
     Parameters: {"q": "Tokyo", "units": "metric"}
     ✓ Success
       Temperature: 18°C
       Condition: clear sky

AGENT: The current weather in Tokyo is clear with a temperature of 18°C.
```

```
💬 Give me a 3-day forecast for Paris

[Iteration 1]
  🌤️  Calling UTCP tool: get_weather_forecast
     Parameters: {"q": "Paris", "units": "metric", "cnt": 24}
     ✓ Success

AGENT: Here's the 3-day forecast for Paris:

Day 1: 12-16°C, Partly cloudy
Day 2: 13-17°C, Light rain
Day 3: 14-18°C, Clear
```

---

## UTCP Manual Structure (v1.0.1 Format)

### Example: Current Weather Tool

```json
{
  "manual_version": "1.0.0",
  "utcp_version": "1.0.1",
  "info": {
    "title": "OpenWeatherMap Current Weather API",
    "version": "1.0.0",
    "description": "Get current weather conditions"
  },
  "tools": [
    {
      "name": "get_current_weather",
      "description": "Get current weather conditions for any city worldwide",
      "inputs": {
        "type": "object",
        "properties": {
          "q": {
            "type": "string",
            "description": "City name, e.g., 'London' or 'New York,US'"
          },
          "units": {
            "type": "string",
            "description": "Units: metric, imperial, or standard",
            "enum": ["metric", "imperial", "standard"],
            "default": "metric"
          }
        },
        "required": ["q"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "http_method": "GET",
        "query_params": {
          "q": "{{q}}",
          "units": "{{units}}",
          "appid": "${OPENWEATHER_API_KEY}"
        }
      }
    }
  ]
}
```

### Key Components

1. **manual_version** & **utcp_version** - Protocol version info (required)
2. **info** - Manual metadata (title, version, description)
3. **tools** - Array of tool definitions (not single "tool" object!)
4. **inputs** - JSON Schema for tool parameters (not "parameters")
5. **tool_call_template** - How to call the API (not "endpoint")
   - **call_template_type** - Protocol type ("http", "cli", etc.) - REQUIRED
   - **http_method** - HTTP verb (not "method")
   - **query_params** - URL parameters with template substitution

---

## How It Works (UTCP v1.0.1)

**Note:** This example uses the official UTCP v1.0.1 specification format. See the code for the complete implementation.

### 1. Load UTCP Manual

```python
executor = UTCPExecutor()
tool_names = executor.load_manual(WEATHER_UTCP_MANUAL)
# Returns: ['get_current_weather']
```

### 2. Convert to OpenAI Format

```python
tools = executor.get_openai_tools()
# Returns OpenAI function calling format
```

### 3. LLM Decides to Use Tool

```python
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[...],
    tools=tools
)
```

### 4. Execute Tool via UTCP

```python
result = executor.execute(tool_name, parameters)
# Makes direct HTTP request to API
```

### 5. Return Result to LLM

```python
# Add result to conversation
messages.append({
    "role": "tool",
    "content": result
})
```

---

## Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ "What's the weather in Paris?"
       ▼
┌─────────────────────┐
│   Weather Agent     │
│  (OpenAI GPT-4)     │
└──────┬──────────────┘
       │ Analyzes request
       │ Selects tool
       ▼
┌─────────────────────┐
│  UTCP Executor      │
│  - Reads manual     │
│  - Makes HTTP call  │
└──────┬──────────────┘
       │ GET request
       ▼
┌─────────────────────┐
│ OpenWeatherMap API  │
│  (External)         │
└──────┬──────────────┘
       │ JSON response
       ▼
    [Result returned to agent]
```

**No server needed!** Direct API-to-API communication.

---

## Creating Your Own UTCP Tool

### Example: News API (v1.0.1 Format)

```python
NEWS_UTCP_MANUAL = {
    "manual_version": "1.0.0",
    "utcp_version": "1.0.1",
    "info": {
        "title": "News API",
        "version": "1.0.0",
        "description": "Search news articles"
    },
    "tools": [
        {
            "name": "search_news",
            "description": "Search for news articles by keyword",
            "inputs": {
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["q"]
            },
            "tool_call_template": {
                "call_template_type": "http",
                "url": "https://newsapi.org/v2/everything",
                "http_method": "GET",
                "query_params": {
                    "q": "{{q}}",
                    "pageSize": "{{pageSize}}"
                },
                "headers": {
                    "X-Api-Key": "${NEWS_API_KEY}"
                }
            }
        }
    ]
}

# Load and use
tool_names = executor.load_manual(NEWS_UTCP_MANUAL)
result = executor.execute("search_news", {"q": "AI", "pageSize": 5})
```

**Key Differences from Old Format:**
- ✅ Use `"tools": [...]` (array) not `"tool": {...}` (object)
- ✅ Use `"inputs"` not `"parameters"`
- ✅ Use `"tool_call_template"` not `"endpoint"`
- ✅ Use `"http_method"` not `"method"`
- ✅ Include `"call_template_type": "http"` (required!)
- ✅ Auth goes in `headers` or `query_params`, not separate `"authentication"` object

---

## Advantages of UTCP

### ✅ Simplicity

No server to deploy or manage. Just load a JSON file.

```python
# MCP: Must run a server
# > python weather_server.py &

# UTCP: Just load manual
executor.load_manual(WEATHER_MANUAL)
```

### ✅ Portability

UTCP manuals are portable across languages and frameworks.

```python
# Python
executor.load_manual(manual)

# JavaScript
executor.loadManual(manual);

# Go
executor.LoadManual(manual)
```

### ✅ Performance

No intermediate server = faster, lower latency.

```
MCP:  Agent → MCP Client → MCP Server → API
UTCP: Agent → API (direct)
```

### ✅ Existing APIs

Works with any REST API without modification.

```python
# GitHub API
executor.load_manual(GITHUB_MANUAL)

# Stripe API
executor.load_manual(STRIPE_MANUAL)

# Your custom API
executor.load_manual(YOUR_API_MANUAL)
```

---

## Limitations of UTCP

### ❌ No State

UTCP is stateless. Not ideal for:
- Multi-step workflows that need memory
- Session-based operations
- Streaming responses

**Solution:** Use MCP for these cases.

### ❌ No Custom Logic

Can't add business logic in the middle.

**Solution:** Wrap UTCP call in custom function.

### ❌ Limited Error Handling

Can't customize error responses as easily as MCP.

**Solution:** Add retry logic in executor.

---

## When to Use UTCP vs MCP

### Use UTCP When:

- ✅ Calling simple REST APIs
- ✅ No state needed
- ✅ Want minimal setup
- ✅ Performance is critical
- ✅ API already exists

### Use MCP When:

- ✅ Need stateful sessions
- ✅ Complex business logic
- ✅ Custom integrations
- ✅ Streaming required
- ✅ Multiple related operations

### Use Both:

Many agents use a mix:
- UTCP for external APIs (weather, news, etc.)
- MCP for internal tools (database, file system, etc.)

See [Multi-Tool Example](../python-multi-tool/) for hybrid approach.

---

## API Response Examples

### Current Weather Response

```json
{
  "name": "London",
  "sys": {"country": "GB"},
  "main": {
    "temp": 15.2,
    "feels_like": 14.5,
    "humidity": 72
  },
  "weather": [
    {"description": "light rain"}
  ],
  "wind": {"speed": 4.5},
  "visibility": 10000,
  "dt": 1705320000
}
```

### Forecast Response

```json
{
  "city": {"name": "London", "country": "GB"},
  "list": [
    {
      "dt": 1705320000,
      "main": {"temp": 15.2},
      "weather": [{"description": "light rain"}]
    },
    // ... more entries
  ]
}
```

---

## Troubleshooting

### Issue: "API key not found"

**Solution:** Set environment variable:

```bash
export OPENWEATHER_API_KEY='your-key'
```

Or use `.env` file.

### Issue: "401 Unauthorized"

**Solution:** Check that your API key is valid and activated. Free keys may take a few minutes to activate after signup.

### Issue: "City not found"

**Solution:** Try:
- Full city name: "New York" not "NY"
- Add country: "London,GB" or "Paris,FR"
- Check spelling

### Issue: Rate limit exceeded

**Solution:** Free tier allows 60 calls/minute. Add rate limiting:

```python
import time

time.sleep(1)  # Wait 1 second between calls
```

---

## Learn More

### Documentation

- [UTCP Specification](../../protocols/utcp/README.md)
- [MCP vs UTCP Comparison](../../protocols/comparison.md)
- [Tool Calling Fundamentals](../../docs/02-fundamentals.md)

### Other Examples

- [Multi-Tool Agent](../python-multi-tool/) - Hybrid MCP/UTCP
- [ReAct Pattern](../python-react-pattern/) - Tool use pattern
- [Planner-Executor](../python-planner-executor/) - Complex workflows

### External Resources

- [OpenWeatherMap API Docs](https://openweathermap.org/api)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---

## License

MIT License - See [LICENSE](../../LICENSE) for details.

