# UTCP Weather Agent Example

> **Real-world UTCP implementation with OpenWeatherMap API**

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
| **Transport** | STDIO/SSE | HTTP/S |
| **Complexity** | Higher | Lower |
| **Best For** | Complex integrations | Simple API calls |

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

3. **UTCP Manual Format**
   - Declarative API definitions
   - Built-in authentication
   - Parameter validation

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

## UTCP Manual Structure

### Example: Current Weather Tool

```json
{
  "protocol": "utcp",
  "version": "1.0",
  "tool": {
    "name": "get_current_weather",
    "description": "Get current weather conditions for any city worldwide",
    "endpoint": {
      "url": "https://api.openweathermap.org/data/2.5/weather",
      "method": "GET"
    },
    "authentication": {
      "type": "api_key",
      "location": "query",
      "param_name": "appid",
      "env_var": "OPENWEATHER_API_KEY"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "q": {
          "type": "string",
          "description": "City name",
          "required": true
        },
        "units": {
          "type": "string",
          "description": "Units: metric, imperial, or standard",
          "default": "metric"
        }
      }
    }
  }
}
```

### Key Components

1. **Endpoint** - URL and HTTP method
2. **Authentication** - How to authenticate (API key, bearer token, etc.)
3. **Parameters** - What inputs the tool accepts
4. **Response** - What the tool returns

---

## How It Works

### 1. Load UTCP Manual

```python
executor = UTCPExecutor()
executor.load_manual(WEATHER_UTCP_MANUAL)
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

### Example: News API

```python
NEWS_UTCP_MANUAL = {
    "protocol": "utcp",
    "version": "1.0",
    "tool": {
        "name": "search_news",
        "description": "Search for news articles",
        "endpoint": {
            "url": "https://newsapi.org/v2/everything",
            "method": "GET"
        },
        "authentication": {
            "type": "api_key",
            "location": "header",
            "param_name": "X-Api-Key",
            "env_var": "NEWS_API_KEY"
        },
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Search query",
                    "required": true
                },
                "pageSize": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 10
                }
            }
        }
    }
}

# Load and use
executor.load_manual(NEWS_UTCP_MANUAL)
result = executor.execute("search_news", {"q": "AI", "pageSize": 5})
```

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

