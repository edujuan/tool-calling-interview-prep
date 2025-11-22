# Universal Tool Calling Protocol (UTCP) - Complete Specification

> **Deep dive into UTCP architecture, manual structure, and implementation**

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Manual Structure](#manual-structure)
- [Tool Definitions](#tool-definitions)
- [Call Templates](#call-templates)
- [Variable Substitution](#variable-substitution)
- [Authentication](#authentication)
- [Protocol Plugins](#protocol-plugins)
- [Client Implementation](#client-implementation)
- [Best Practices](#best-practices)

---

## Overview

The **Universal Tool Calling Protocol (UTCP)** is an open standard for enabling AI agents to call tools directly using their native protocols (HTTP, CLI, WebSocket, etc.) without requiring intermediary servers.

### Key Concepts

```
┌─────────────────┐
│   AI AGENT      │  ← AI Application (e.g., LangChain, Custom Agent)
│  (Host App)     │
└────────┬────────┘
         │
         │ Uses
         ▼
┌─────────────────┐
│  UTCP CLIENT    │  ← Library that reads manuals and makes calls
│  (In Agent)     │
└────────┬────────┘
         │
         │ Direct Call (HTTP/CLI/etc.)
         ▼
┌─────────────────┐
│   TOOL/API      │  ← Actual service (no wrapper needed)
└─────────────────┘
```

**Design Philosophy**: "If a human developer can call your API, an AI agent should be able to as well - with the same security and no extra infrastructure."

---

## Architecture

### Two-Layer Model

#### Layer 1: UTCP Client

The **client** is a library that reads UTCP manuals and executes tool calls.

**Responsibilities**:
- Load and parse UTCP manuals
- Extract tool definitions
- Perform variable substitution
- Execute calls using appropriate protocol plugins
- Handle authentication
- Return results to agent

**Code Example**:
```python
from utcp import UTCPClient

class Agent:
    """AI agent using UTCP"""
    
    def __init__(self, llm):
        self.llm = llm
        self.utcp_client = UTCPClient()
    
    async def setup_tools(self):
        """Load UTCP manuals"""
        # Load from file
        await self.utcp_client.register_manual_from_file("./tools/weather.json")
        
        # Load from URL
        await self.utcp_client.register_manual_from_url(
            "https://api.example.com/utcp-manual.json"
        )
    
    async def run(self, query: str):
        """Run agent with UTCP tools"""
        
        # Get available tools
        tools = await self.utcp_client.get_tools()
        
        # LLM decides which tool to use
        decision = await self.llm.decide(query, available_tools=tools)
        
        if decision['action'] == 'use_tool':
            # Call tool directly via UTCP
            result = await self.utcp_client.call_tool(
                decision['tool_name'],
                decision['arguments']
            )
            
            return result
```

#### Layer 2: Tools/APIs

The **tools** are existing services that need no modification to work with UTCP.

**Key Point**: Unlike MCP, UTCP does not require building a server. You just create a manual describing how to call your existing API.

---

## Manual Structure

A UTCP manual is a JSON document that describes available tools and how to call them.

### Required Fields

```typescript
interface UTCPManual {
  utcp_version: string;       // Protocol version (e.g., "1.0.1")
  manual_version: string;     // Manual version (e.g., "1.0.0")
  tools: Tool[];              // Array of tool definitions
}
```

### Optional Fields

```typescript
interface UTCPManual {
  info?: {
    title: string;           // API/service name
    version: string;         // API version
    description: string;     // Service description
  };
  auth?: AuthConfig;         // Shared authentication config
  metadata?: {               // Custom metadata
    [key: string]: any;
  };
}
```

### Complete Example

```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "info": {
    "title": "Weather Service API",
    "version": "2.5.0",
    "description": "Current weather and forecast data"
  },
  "auth": {
    "auth_type": "api_key",
    "api_key": "${WEATHER_API_KEY}",
    "var_name": "appid",
    "location": "query"
  },
  "tools": [
    {
      "name": "get_current_weather",
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
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "http_method": "GET",
        "query_params": {
          "q": "${location}",
          "units": "${units}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    }
  ]
}
```

---

## Tool Definitions

Each tool in the manual describes a single capability.

### Tool Schema

```typescript
interface Tool {
  name: string;                    // Unique tool identifier
  description: string;             // What the tool does
  inputs: JSONSchema;              // Input parameters (JSON Schema)
  tool_call_template: CallTemplate; // How to execute the tool
  outputs?: JSONSchema;            // Expected output structure (optional)
  tags?: string[];                 // Categorization tags (optional)
}
```

### Input Schema (JSON Schema)

```json
{
  "name": "search_database",
  "description": "Search customer database with filters",
  "inputs": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query",
        "examples": ["John Doe", "user@example.com"]
      },
      "filters": {
        "type": "object",
        "properties": {
          "status": {
            "type": "string",
            "enum": ["active", "inactive", "pending"],
            "description": "Filter by customer status"
          },
          "created_after": {
            "type": "string",
            "format": "date",
            "description": "ISO 8601 date"
          }
        }
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 10
      }
    },
    "required": ["query"]
  },
  "tool_call_template": {
    "call_template_type": "http",
    "url": "https://api.example.com/customers/search",
    "http_method": "POST",
    "body_template": {
      "query": "${query}",
      "filters": "${filters}",
      "limit": "${limit}"
    }
  }
}
```

### Output Schema (Optional)

```json
{
  "outputs": {
    "type": "object",
    "properties": {
      "results": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "status": {"type": "string"}
          }
        }
      },
      "total": {"type": "integer"}
    }
  }
}
```

---

## Call Templates

Call templates specify how to execute a tool using a specific protocol.

### Call Template Types

UTCP v1.0.1 supports multiple protocol plugins:

| Protocol | Plugin | Use Case |
|----------|--------|----------|
| HTTP | `utcp-http` | REST APIs, webhooks |
| CLI | `utcp-cli` | Command-line tools, scripts |
| WebSocket | `utcp-websocket` | Real-time bidirectional communication |
| SSE | `utcp-http` | Server-sent events, streaming |
| Streamable HTTP | `utcp-http` | Large file downloads, chunked responses |
| MCP | `utcp-mcp` | Integration with MCP servers |
| Text | `utcp-text` | Local file-based manuals |

### HTTP Call Template

```json
{
  "call_template_type": "http",
  "url": "https://api.example.com/resource/{id}",
  "http_method": "GET",
  "headers": {
    "Authorization": "Bearer ${API_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "UTCP-Client/1.0"
  },
  "query_params": {
    "format": "json",
    "include": "${include_fields}"
  },
  "body_template": {
    "data": "${payload}"
  },
  "timeout": 30
}
```

**Supported HTTP Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS

### CLI Call Template

```json
{
  "call_template_type": "cli",
  "commands": [
    {
      "command": "git clone UTCP_ARG_repo_url_UTCP_END",
      "working_dir": "/tmp",
      "append_to_final_output": false
    },
    {
      "command": "cd $CMD_0_OUTPUT && npm install",
      "append_to_final_output": false
    },
    {
      "command": "npm test",
      "append_to_final_output": true
    }
  ],
  "env_vars": {
    "NODE_ENV": "test",
    "API_KEY": "${API_KEY}"
  },
  "timeout": 300
}
```

**Key Features**:
- Multi-command sequences
- Command output referencing (`$CMD_0_OUTPUT`, `$CMD_1_OUTPUT`)
- Argument placeholders (`UTCP_ARG_name_UTCP_END`)
- Environment variables
- Working directory control

### WebSocket Call Template

```json
{
  "call_template_type": "websocket",
  "url": "wss://api.example.com/stream",
  "message_template": {
    "action": "${action}",
    "data": "${data}"
  },
  "auth": {
    "auth_type": "api_key",
    "api_key": "${WS_TOKEN}",
    "var_name": "token",
    "location": "header"
  },
  "timeout": 60
}
```

### SSE (Server-Sent Events) Call Template

```json
{
  "call_template_type": "sse",
  "url": "https://api.example.com/events",
  "http_method": "GET",
  "query_params": {
    "channel": "${channel}"
  },
  "headers": {
    "Accept": "text/event-stream",
    "Authorization": "Bearer ${TOKEN}"
  },
  "timeout": 300
}
```

**Use Cases**:
- Real-time notifications
- Live data feeds
- Progress updates
- Event streams

### Streamable HTTP Call Template

```json
{
  "call_template_type": "streamable_http",
  "url": "https://api.example.com/download/{file_id}",
  "http_method": "GET",
  "headers": {
    "Authorization": "Bearer ${TOKEN}"
  },
  "chunk_size": 8192,
  "timeout": 600
}
```

**Use Cases**:
- Large file downloads
- Chunked responses
- Incremental data processing

### MCP Call Template

```json
{
  "call_template_type": "mcp",
  "server_url": "http://internal-mcp:8080",
  "tool_name": "internal_tool",
  "transport": "stdio"
}
```

**Use Case**: Call existing MCP servers from UTCP clients for gradual migration.

### Text Call Template

```json
{
  "call_template_type": "text",
  "file_path": "/path/to/manual.json"
}
```

**Use Case**: Load UTCP manuals from local files or mounted volumes.

---

## Variable Substitution

UTCP uses a powerful variable substitution system to inject dynamic values into call templates.

### Syntax

Variables are denoted with `${VARIABLE_NAME}` syntax.

### Variable Sources

#### 1. Tool Arguments

```json
{
  "tool_call_template": {
    "url": "https://api.example.com/users/${user_id}",
    "query_params": {
      "format": "${output_format}"
    }
  }
}
```

When calling: `call_tool("get_user", {"user_id": "123", "output_format": "json"})`

Becomes: `https://api.example.com/users/123?format=json`

#### 2. Environment Variables

```json
{
  "headers": {
    "Authorization": "Bearer ${API_TOKEN}",
    "X-Custom-Header": "${CUSTOM_VALUE}"
  }
}
```

Loaded from environment: `export API_TOKEN=abc123`

#### 3. Configuration Variables

```python
client = UTCPClient(
    variables={
        "base_url": "https://api.staging.example.com",
        "timeout": "30"
    }
)
```

```json
{
  "url": "${base_url}/endpoint",
  "timeout": "${timeout}"
}
```

### Path Parameters

```json
{
  "url": "https://api.example.com/users/{user_id}/posts/{post_id}"
}
```

The `{parameter}` syntax is also supported for path parameters (alternative to `${parameter}`).

### Default Values

```json
{
  "query_params": {
    "limit": "${limit|default:10}",
    "units": "${units|default:metric}"
  }
}
```

### CLI Argument Substitution

CLI templates use a special syntax:

```json
{
  "command": "curl -X POST UTCP_ARG_url_UTCP_END -d UTCP_ARG_data_UTCP_END"
}
```

Called as: `call_tool("curl_post", {"url": "https://...", "data": "{...}"})`

### Command Output References

```json
{
  "commands": [
    {"command": "echo 'output1'", "append_to_final_output": false},
    {"command": "echo 'output2'", "append_to_final_output": false},
    {"command": "echo Previous: $CMD_0_OUTPUT and $CMD_1_OUTPUT", "append_to_final_output": true}
  ]
}
```

---

## Authentication

UTCP supports multiple authentication mechanisms.

### Authentication Types

#### 1. API Key

```json
{
  "auth": {
    "auth_type": "api_key",
    "api_key": "${API_KEY}",
    "var_name": "X-API-Key",
    "location": "header"
  }
}
```

**Locations**: `header`, `query`, `cookie`

**Example (Query Parameter)**:
```json
{
  "auth": {
    "auth_type": "api_key",
    "api_key": "${API_KEY}",
    "var_name": "api_key",
    "location": "query"
  }
}
```

#### 2. Basic Auth

```json
{
  "auth": {
    "auth_type": "basic",
    "username": "${USERNAME}",
    "password": "${PASSWORD}"
  }
}
```

Automatically encodes to `Authorization: Basic base64(username:password)`

#### 3. OAuth2

```json
{
  "auth": {
    "auth_type": "oauth2",
    "client_id": "${CLIENT_ID}",
    "client_secret": "${CLIENT_SECRET}",
    "token_url": "https://auth.example.com/token",
    "scopes": ["read", "write"]
  }
}
```

**Features**:
- Automatic token acquisition
- Token caching (by client_id)
- Token refresh

#### 4. Bearer Token

```json
{
  "auth": {
    "auth_type": "api_key",
    "api_key": "${TOKEN}",
    "var_name": "Authorization",
    "location": "header"
  }
}
```

Or directly in headers:
```json
{
  "headers": {
    "Authorization": "Bearer ${TOKEN}"
  }
}
```

### Tool-Level vs Manual-Level Auth

**Manual-Level** (applies to all tools):
```json
{
  "utcp_version": "1.0.1",
  "auth": {
    "auth_type": "api_key",
    "api_key": "${API_KEY}",
    "var_name": "X-API-Key",
    "location": "header"
  },
  "tools": [...]
}
```

**Tool-Level** (overrides manual-level):
```json
{
  "tools": [
    {
      "name": "special_tool",
      "tool_call_template": {
        "call_template_type": "http",
        "url": "...",
        "auth": {
          "auth_type": "basic",
          "username": "${SPECIAL_USER}",
          "password": "${SPECIAL_PASS}"
        }
      }
    }
  ]
}
```

---

## Protocol Plugins

UTCP v1.0.1 uses a plugin architecture for extensibility.

### Installation

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

### Plugin Discovery

UTCP automatically discovers and loads installed protocol plugins.

```python
from utcp import UTCPClient

client = UTCPClient()

# List available protocols
protocols = client.get_available_protocols()
print(protocols)
# Output: ['http', 'sse', 'streamable_http', 'cli', 'websocket', 'mcp', 'text']
```

### Creating Custom Plugins

You can create custom protocol plugins by implementing the `CommunicationProtocol` interface:

```python
from utcp.interfaces import CommunicationProtocol
from utcp.data import CallTemplate

class CustomProtocol(CommunicationProtocol):
    """Custom protocol implementation"""
    
    @property
    def protocol_name(self) -> str:
        return "custom"
    
    async def call(
        self,
        call_template: CallTemplate,
        tool_args: dict
    ) -> dict:
        """Execute tool call using custom protocol"""
        # Implementation here
        pass
    
    def validate_call_template(self, call_template: CallTemplate):
        """Validate call template structure"""
        # Validation logic
        pass
```

---

## Client Implementation

### Basic Client Usage

```python
import asyncio
import os
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.data.call_template import CallTemplate

async def main():
    # Create client with configuration
    config = UtcpClientConfig(
        manual_call_templates=[
            CallTemplate(
                name="weather_manual",
                call_template_type="text",
                file_path="./weather.json"
            )
        ],
        variables={"WEATHER_API_KEY": os.getenv("WEATHER_API_KEY")}
    )
    
    client = await UtcpClient.create(config=config)
    print("✓ Client created successfully")
    
    # Get all tools
    tools = await client.get_tools()
    print(f"Available tools: {[t.name for t in tools]}")
    
    # Get specific tool info
    tool = await client.get_tool("get_current_weather")
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Inputs: {tool.inputs}")
    
    # Call tool
    result = await client.call_tool(
        "get_current_weather",
        {"location": "Paris", "units": "metric"}
    )
    print(f"Result: {result}")

asyncio.run(main())
```

### Loading from URL

```python
from utcp.data.call_template import CallTemplate

# Configure client to load manual from HTTP endpoint
config = UtcpClientConfig(
    manual_call_templates=[
        CallTemplate(
            name="remote_manual",
            call_template_type="http",
            url="https://api.example.com/utcp-manual.json",
            http_method="GET"
        )
    ]
)

client = await UtcpClient.create(config=config)
```

### Loading Multiple Manuals

```python
from utcp.data.call_template import CallTemplate

# Configure client with multiple manuals
config = UtcpClientConfig(
    manual_call_templates=[
        CallTemplate(
            name="weather",
            call_template_type="text",
            file_path="./weather.json"
        ),
        CallTemplate(
            name="maps",
            call_template_type="text",
            file_path="./maps.json"
        ),
        CallTemplate(
            name="database",
            call_template_type="http",
            url="https://api.db.com/manual.json",
            http_method="GET"
        )
    ]
)

client = await UtcpClient.create(config=config)

# Get all tools from all manuals
all_tools = await client.get_tools()
print(f"Total tools available: {len(all_tools)}")
```

### Variable Configuration

```python
import os

# Set variables at client level via config
config = UtcpClientConfig(
    manual_call_templates=[...],
    variables={
        "API_KEY": "abc123",
        "BASE_URL": "https://api.staging.example.com"
    }
)

client = await UtcpClient.create(config=config)

# Or load from environment
config = UtcpClientConfig(
    manual_call_templates=[...],
    variables={
        "API_KEY": os.getenv("API_KEY"),
        "TIMEOUT": os.getenv("TIMEOUT", "30")
    }
)

client = await UtcpClient.create(config=config)
```

### Error Handling

```python
try:
    result = await client.call_tool("get_weather", {"location": "Paris"})
except KeyError as e:
    print(f"Tool not found: {e}")
except ValueError as e:
    print(f"Invalid arguments: {e}")
except Exception as e:
    print(f"Error: {e}")
```

### Agent Integration

#### LangChain Integration

```python
from langchain.agents import initialize_agent
from langchain.tools import Tool as LangChainTool
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.data.call_template import CallTemplate

async def setup_langchain_agent(llm):
    # Create UTCP client
    config = UtcpClientConfig(
        manual_call_templates=[
            CallTemplate(
                name="tools",
                call_template_type="text",
                file_path="./tools.json"
            )
        ]
    )
    
    client = await UtcpClient.create(config=config)
    
    # Convert UTCP tools to LangChain tools
    utcp_tools = await client.get_tools()
    langchain_tools = []
    
    for tool in utcp_tools:
        async def tool_func(tool_input, tool_name=tool.name):
            return await client.call_tool(tool_name, tool_input)
        
        langchain_tools.append(
            LangChainTool(
                name=tool.name,
                description=tool.description,
                func=tool_func
            )
        )
    
    # Create agent
    agent = initialize_agent(
        langchain_tools,
        llm,
        agent="zero-shot-react-description"
    )
    
    return agent

# Usage
agent = await setup_langchain_agent(llm)
result = agent.run("What's the weather in Paris?")
```

#### Custom Agent Loop

```python
from utcp.utcp_client import UtcpClient

async def agent_loop(client: UtcpClient, llm, query: str):
    """Simple agent loop with UTCP"""
    
    # Get available tools
    tools = await client.get_tools()
    
    # Format tools for LLM
    tool_descriptions = [
        f"{t.name}: {t.description}" for t in tools
    ]
    
    # LLM decides which tool to use
    decision = await llm.decide(
        query=query,
        tools=tool_descriptions
    )
    
    if decision.action == "use_tool":
        # Execute tool
        result = await client.call_tool(
            decision.tool_name,
            decision.arguments
        )
        
        # LLM processes result
        answer = await llm.respond(
            query=query,
            tool_result=result
        )
        
        return answer
```

---

## Best Practices

### 1. Manual Design

✅ **DO:**

**Write Clear Descriptions**
```json
{
  "description": "Get current weather for a location. Returns temperature, humidity, wind speed, and conditions. Data is updated every 15 minutes from weather stations worldwide."
}
```

**Use Semantic Tags**
```json
{
  "tags": ["weather", "current", "realtime", "outdoor", "temperature"]
}
```

**Provide Examples**
```json
{
  "inputs": {
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or coordinates",
        "examples": ["Paris", "New York", "48.8566,2.3522"]
      }
    }
  }
}
```

**Version Your Manuals**
```json
{
  "utcp_version": "1.0.1",
  "manual_version": "2.1.0",
  "info": {
    "title": "Weather API",
    "version": "2.5.0"
  }
}
```

❌ **DON'T:**

**Don't Put Secrets in Manuals**
```json
// BAD
{"headers": {"Authorization": "Bearer sk-abc123secret"}}

// GOOD
{"headers": {"Authorization": "Bearer ${API_TOKEN}"}}
```

**Don't Make Tools Too Complex**
```json
// BAD: 20 parameters
{"inputs": {"properties": {"p1": ..., "p2": ..., "p3": ..., /* 17 more */}}}

// GOOD: Focused, simple
{"inputs": {"properties": {"location": ..., "units": ...}}}
```

### 2. Security

✅ **DO:**

**Use Environment Variables**
```bash
export API_KEY=your_secret_key
export DATABASE_URL=postgresql://...
```

**Validate Inputs**
```json
{
  "inputs": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "pattern": "^[0-9]+$",
        "minLength": 1,
        "maxLength": 20
      }
    }
  }
}
```

**Use HTTPS**
```json
{
  "url": "https://api.example.com/endpoint"
}
```

**Set Timeouts**
```json
{
  "timeout": 30
}
```

❌ **DON'T:**

**Don't Expose Internal Paths**
```json
// BAD
{"url": "http://192.168.1.100:8080/internal/admin"}

// GOOD
{"url": "https://api.example.com/public/endpoint"}
```

**Don't Allow Arbitrary Commands**
```json
// BAD (CLI)
{"command": "${user_command}"}

// GOOD
{"command": "safe_script.sh UTCP_ARG_param_UTCP_END"}
```

### 3. Performance

✅ **DO:**

**Cache Manuals**
```python
# Load manual once
await client.register_manual_from_file("./tools.json")

# Reuse for multiple calls
await client.call_tool("tool1", args1)
await client.call_tool("tool2", args2)
```

**Set Appropriate Timeouts**
```json
{
  "timeout": 5  // Fast API
}

{
  "timeout": 300  // Long-running operation
}
```

**Use Streaming for Large Data**
```json
{
  "call_template_type": "streamable_http",
  "chunk_size": 8192
}
```

### 4. Error Handling

✅ **DO:**

**Document Error Responses**
```json
{
  "outputs": {
    "oneOf": [
      {
        "type": "object",
        "properties": {"result": {"type": "string"}}
      },
      {
        "type": "object",
        "properties": {
          "error": {"type": "string"},
          "code": {"type": "integer"}
        }
      }
    ]
  }
}
```

**Handle Timeouts**
```python
try:
    result = await client.call_tool("slow_tool", args)
except asyncio.TimeoutError:
    # Handle timeout
    pass
```

### 5. Tool Organization

✅ **DO:**

**Group Related Tools**
```
weather/
  ├── current.json      # Current weather
  ├── forecast.json     # Forecasts
  └── alerts.json       # Weather alerts

maps/
  ├── geocoding.json    # Address to coordinates
  └── directions.json   # Route planning
```

**Use Consistent Naming**
```
get_current_weather
get_weather_forecast
get_weather_alerts

search_location
get_directions
```

---

## Summary

**UTCP provides:**
- ✅ Direct protocol access (HTTP, CLI, WebSocket, etc.)
- ✅ No server infrastructure required
- ✅ JSON manual-based tool definition
- ✅ Powerful variable substitution
- ✅ Multiple authentication methods
- ✅ Plugin architecture for extensibility
- ✅ Native tool performance

**Best for:**
- Direct API integration
- Minimal infrastructure
- High performance requirements
- Existing services (no modification needed)
- Rapid prototyping

**Trade-offs:**
- Stateless (no server-side state)
- One-way communication (agent → tool)
- No bidirectional callbacks
- Manual distribution needed

---

**Official Resources:**
- [Official UTCP Specification v1.0.1](https://www.utcp.io/spec) - Complete protocol specification
- [UTCP RFC](https://www.utcp.io/rfc) - Design rationale and philosophy
- [UTCP API Reference](https://www.utcp.io/api) - Implementation guide

**Code & Examples:**
- [UTCP GitHub Organization](https://github.com/universal-tool-calling-protocol) - Official implementations
- [Example Manuals](https://github.com/universal-tool-calling-protocol/examples) - Real-world UTCP manuals
- [OpenAPI to UTCP Converter](https://github.com/universal-tool-calling-protocol/openapi-converter) - Convert existing specs

**Community:**
- [UTCP Blog](https://www.utcp.io/blog) - Updates and best practices

**Related Standards:**
- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.0) - For REST API documentation
- [JSON Schema](https://json-schema.org/) - For parameter validation

---

**Next Steps:**
- [Try UTCP Tutorial](./tutorial.md)
- [Compare with MCP](../comparison.md)
- [Read UTCP README](./README.md)

