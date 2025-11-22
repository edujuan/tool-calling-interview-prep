# UTCP (Universal Tool Calling Protocol)

A deep dive into the Universal Tool Calling Protocol - a simple, direct approach to AI tool-calling.

## 🎯 Overview

**UTCP** is an open protocol that enables AI agents to call tools directly using their native interfaces (HTTP, CLI, GraphQL, etc.) without requiring intermediary servers.

**Core Philosophy:** "If a human developer can call your API, an AI agent should be able to as well - with the same security and no extra infrastructure."

## 🔑 Key Concepts

### The Manual

The heart of UTCP is the **manual** - a JSON document that describes how to call a tool.

**Think of it as:**
- API documentation, but machine-readable
- A recipe the agent follows to make tool calls
- The "contract" between tool and agent

**Example Manual:**
```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a location",
      "inputs": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name or coordinates"
          },
          "units": {
            "type": "string",
            "enum": ["metric", "imperial"],
            "default": "metric"
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.weather.com/v1/current",
        "http_method": "GET",
        "query_params": {
          "q": "{{location}}",
          "units": "{{units|default:metric}}"
        },
        "headers": {
          "Authorization": "Bearer ${WEATHER_API_KEY}"
        }
      }
    }
  ]
}
```

### Call Templates

UTCP v1.0.1 supports multiple transport types via call templates through a plugin architecture. This flexibility allows UTCP to work with virtually any tool interface, from standard REST APIs to real-time streaming protocols.

**Officially Supported Protocols (v1.0.1):**
- HTTP/REST (`utcp-http`)
- Server-Sent Events (`utcp-http`)
- Streamable HTTP (`utcp-http`)
- Command-Line Interface (`utcp-cli`)
- WebSocket (`utcp-websocket`)
- MCP Integration (`utcp-mcp`)
- Text/Local Files (`utcp-text`)

**Installation:** `pip install utcp` (core) plus protocol plugins as needed

#### 1. HTTP/REST
```json
{
  "call_template_type": "http",
  "url": "https://api.example.com/resource",
  "http_method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body_template": {
    "field": "{{value}}"
  }
}
```

**Installation:** `pip install utcp-http`

#### 2. CLI (Command-Line)
```json
{
  "call_template_type": "cli",
  "command": "curl",
  "args": [
    "-X", "GET",
    "{{url}}",
    "-H", "Authorization: Bearer {{api_key}}"
  ]
}
```

**Installation:** `pip install utcp-cli`

#### 3. WebSocket
```json
{
  "call_template_type": "websocket",
  "url": "wss://api.example.com/stream",
  "message_template": {
    "action": "{{action}}",
    "data": "{{data}}"
  },
  "auth": {
    "type": "token",
    "token": "${WS_TOKEN}"
  }
}
```

**Installation:** `pip install utcp-websocket`

#### 4. Server-Sent Events (SSE)
```json
{
  "call_template_type": "sse",
  "url": "https://api.example.com/events",
  "http_method": "GET",
  "query_params": {
    "channel": "{{channel}}"
  },
  "headers": {
    "Accept": "text/event-stream"
  }
}
```

**Installation:** `pip install utcp-http` (SSE is part of HTTP plugin)

#### 5. Streamable HTTP
```json
{
  "call_template_type": "streamable_http",
  "url": "https://api.example.com/download/{file_id}",
  "http_method": "GET",
  "chunk_size": 4096
}
```

**Installation:** `pip install utcp-http` (Streamable HTTP is part of HTTP plugin)

#### 6. MCP Integration
```json
{
  "call_template_type": "mcp",
  "server_url": "http://internal-mcp:8080",
  "tool_name": "internal_tool"
}
```

**Installation:** `pip install utcp-mcp`  
**Note:** UTCP can call MCP servers, enabling gradual migration from MCP to UTCP.

#### 7. Text/Local Files
```json
{
  "call_template_type": "text",
  "file_path": "/path/to/utcp_manual.json"
}
```

**Installation:** `pip install utcp-text`  
**Use case:** Load UTCP manuals from local files or OpenAPI specifications.

## 🚀 How It Works

### Agent Workflow

```
1. Agent Startup
      ↓
2. Load UTCP Manual(s)
      ↓
3. Parse available tools
      ↓
4. User asks question
      ↓
5. LLM decides to use tool
      ↓
6. UTCP client reads manual
      ↓
7. Constructs native call (HTTP/CLI/etc.)
      ↓
8. Executes directly
      ↓
9. Returns result to LLM
```

### No Server Required

```
Traditional Approach (like MCP):
Agent → Client → Server → Tool
         ↓
    Extra hop, latency

UTCP Approach:
Agent → UTCP Client → Tool
         ↓
    Direct call
```

## 📖 Complete Manual Example

Here's a full UTCP manual with multiple tools:

```json
{
  "manual_version": "2.1.0",
  "utcp_version": "1.0.1",
  "info": {
    "title": "Example Service Tools",
    "version": "2.1.0",
    "description": "Tools for interacting with Example Service"
  },
  "auth": {
    "auth_type": "api_key",
    "var_name": "EXAMPLE_API_KEY",
    "instructions": "Get your API key from https://example.com/keys"
  },
  "tools": [
    {
      "name": "search_locations",
      "description": "Search for locations by name. Returns a list of matching places with coordinates.",
      "tags": ["search", "maps"],
      "inputs": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Location name to search for"
          },
          "limit": {
            "type": "integer",
            "description": "Maximum number of results",
            "default": 5,
            "minimum": 1,
            "maximum": 20
          }
        },
        "required": ["query"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.example.com/v1/locations/search",
        "http_method": "GET",
        "query_params": {
          "q": "{{query}}",
          "limit": "{{limit|default:5}}"
        },
        "headers": {
          "Authorization": "Bearer ${EXAMPLE_API_KEY}",
          "Accept": "application/json"
        }
      },
      "response_schema": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "lat": {"type": "number"},
            "lon": {"type": "number"}
          }
        }
      }
    },
    {
      "name": "get_weather",
      "description": "Get current weather conditions for a specific location",
      "tags": ["weather"],
      "inputs": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name or 'lat,lon' coordinates"
          },
          "units": {
            "type": "string",
            "enum": ["metric", "imperial"],
            "default": "metric",
            "description": "Temperature units"
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.example.com/v1/weather/current",
        "http_method": "GET",
        "query_params": {
          "q": "{{location}}",
          "units": "{{units|default:metric}}"
        },
        "headers": {
          "Authorization": "Bearer ${EXAMPLE_API_KEY}"
        }
      }
    }
  ]
}
```

## 🔐 Authentication

UTCP supports various auth mechanisms:

### 1. API Keys
```json
{
  "auth": {
    "auth_type": "api_key",
    "var_name": "API_KEY",
    "location": "header",  // or "query"
    "key_name": "Authorization"
  },
  "tool_call_template": {
    "headers": {
      "Authorization": "Bearer ${API_KEY}"
    }
  }
}
```

### 2. OAuth 2.0
```json
{
  "auth": {
    "auth_type": "oauth2",
    "token_url": "https://auth.example.com/token",
    "client_id_var": "CLIENT_ID",
    "client_secret_var": "CLIENT_SECRET"
  }
}
```

### 3. Basic Auth
```json
{
  "auth": {
    "auth_type": "basic",
    "username_var": "USERNAME",
    "password_var": "PASSWORD"
  }
}
```

### 4. Custom Headers
```json
{
  "tool_call_template": {
    "headers": {
      "X-API-Key": "${MY_API_KEY}",
      "X-User-ID": "${USER_ID}"
    }
  }
}
```

**Security Note:** Credentials are stored as environment variables, never in the manual itself or prompt.

## 📦 Discovery

UTCP supports flexible tool discovery:

### 1. File-Based
```python
from utcp import UTCPClient

client = UTCPClient()
client.load_manual("./tools/weather.json")
client.load_manual("./tools/maps.json")
```

### 2. URL-Based
```python
client.load_manual("https://api.example.com/utcp-manual.json")
```

### 3. Registry/Directory
```python
registry = UTCPRegistry("https://tool-registry.example.com")
manuals = registry.discover(tags=["weather", "maps"])
for manual_url in manuals:
    client.load_manual(manual_url)
```

### 4. OpenAPI Conversion
```python
from utcp.converters import openapi_to_utcp

# Convert existing OpenAPI spec
utcp_manual = openapi_to_utcp("https://api.example.com/openapi.json")
client.load_manual_dict(utcp_manual)
```

## 🔄 Integration with Frameworks

### LangChain
```python
from langchain.agents import initialize_agent
from utcp.adapters.langchain import UTCPToolkit

# Load UTCP tools
toolkit = UTCPToolkit.from_manual("./tools.json")

# Create agent
agent = initialize_agent(
    toolkit.get_tools(),
    llm,
    agent="zero-shot-react-description"
)

result = agent.run("What's the weather in Paris?")
```

### Direct Usage
```python
from utcp import UTCPClient

client = UTCPClient()
client.load_manual("./weather.json")

# List available tools
tools = client.list_tools()
# ['get_weather', 'search_locations']

# Get tool info
tool_info = client.get_tool_info("get_weather")
print(tool_info.description)
print(tool_info.parameters)

# Call a tool
result = client.call_tool(
    "get_weather",
    {"location": "Paris", "units": "metric"}
)
print(result)  # {"temp": 18, "condition": "cloudy"}
```

## ⚡ Advantages

**1. Performance**
- No proxy overhead (typically 20-40% lower latency than MCP for remote tools)
- Direct protocol usage
- Minimal client-side processing
- Note: Performance gains are most significant for HTTP/REST tools; with MCP's STDIO transport (local), differences are smaller

**2. Simplicity**
- Just a JSON file
- No server to deploy
- No new infrastructure

**3. Flexibility**
- Support for 10+ protocols (HTTP, WebSocket, SSE, gRPC, CLI, GraphQL, and more)
- Works with any API
- Easy OpenAPI conversion
- Streaming support via SSE and WebSocket

**4. Security**
- Uses tool's native authentication
- No credential duplication
- Leverage existing security

**5. Scalability**
- Each tool scales independently
- No central bottleneck
- Built-in semantic search with tags

## ⚠️ Limitations

**1. Stateless**
- No session management
- Each call is independent
- Agent must manage state if needed

**2. No Bidirectional Communication**
- Tools can't call back to agent
- One-way: agent → tool
- No callbacks or notifications

**3. Limited Governance**
- No centralized control point
- Must monitor each tool independently
- Harder to enforce unified policies

**4. Newer Ecosystem**
- Fewer tools with UTCP manuals (vs MCP)
- Community-driven (not corporate-backed)
- Still evolving rapidly

## 🛠️ Tools & Libraries

### Official UTCP Implementations

**Python** (Plugin Architecture)
```bash
# Core library (required)
pip install utcp

# Protocol plugins (install as needed)
pip install utcp-http      # HTTP, SSE, Streamable HTTP
pip install utcp-cli       # Command-line tools
pip install utcp-websocket # WebSocket support
pip install utcp-mcp       # MCP integration
pip install utcp-text      # Local file manuals

# Install all protocols
pip install utcp[all]
```

**TypeScript/JavaScript**
```bash
npm install utcp-js
```

**Go**
```bash
go get github.com/utcp-org/utcp-go
```

### Utilities

**OpenAPI to UTCP Converter**
```bash
utcp convert openapi.json > utcp-manual.json
```

**Manual Validator**
```bash
utcp validate manual.json
```

**Registry Server**
```bash
utcp-registry serve --port 8080
```

## 📚 Best Practices

### ✅ DO:

**1. Write Clear Descriptions**
```json
{
  "description": "Get current weather for a location. Returns temperature, conditions, humidity, and wind speed. Updated every 15 minutes."
}
```

**2. Use Semantic Tags**
```json
{
  "tags": ["weather", "current", "realtime", "outdoor"]
}
```

**3. Provide Examples**
```json
{
  "inputs": {
    "properties": {
      "location": {
        "type": "string",
        "description": "City name (e.g., 'Paris') or coordinates (e.g., '48.8566,2.3522')",
        "examples": ["Paris", "New York", "48.8566,2.3522"]
      }
    }
  }
}
```

**4. Version Your Manuals**
```json
{
  "utcp_version": "1.0.1",
  "manual_version": "2.1.0",
  "metadata": {
    "title": "My Tools"
  }
}
```
*Note: `utcp_version` specifies the protocol version, while `manual_version` specifies your tool manual's version*

**5. Document Response Schemas**
```json
{
  "response_schema": {
    "type": "object",
    "properties": {
      "temp": {"type": "number"},
      "condition": {"type": "string"}
    }
  }
}
```

### ❌ DON'T:

**1. Don't Put Secrets in Manuals**
```json
// BAD
{"api_key": "sk-abc123..."}

// GOOD
{"headers": {"Authorization": "Bearer ${API_KEY}"}}
```

**2. Don't Make Tools Too Complex**
```json
// BAD: 20 parameters
{"parameters": {"p1": ..., "p2": ..., "p3": ..., ...}}

// GOOD: Focused, simple
{"parameters": {"location": ...}}
```

**3. Don't Skip Error Handling**
- Document possible error responses
- Handle timeouts
- Validate inputs

## 🔗 Resources

**Official Documentation:**
- [Official UTCP Specification v1.0.1](https://www.utcp.io/spec) - Complete protocol specification
- [UTCP RFC](https://www.utcp.io/rfc) - Design rationale and philosophy
- [UTCP API Reference](https://www.utcp.io/api) - Implementation guide

**Code & Examples:**
- [UTCP GitHub Organization](https://github.com/utcp-org) - Official implementations
- [Example Manuals](https://github.com/utcp-org/examples) - Real-world UTCP manuals
- [OpenAPI to UTCP Converter](https://github.com/utcp-org/openapi-converter) - Convert existing specs

**Community:**
- [Community Discord](https://discord.gg/utcp) - Discussion and support
- [UTCP Blog](https://www.utcp.io/blog) - Updates and best practices

**Related Standards:**
- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.0) - For REST API documentation
- [JSON Schema](https://json-schema.org/) - For parameter validation

---

**Next Steps:**
- [Try UTCP Example](../../examples/python-utcp-weather/)
- [Compare with MCP](../comparison.md)
- [Read Full Specification](./specification.md)
- [Build Your First UTCP Integration](./tutorial.md)

