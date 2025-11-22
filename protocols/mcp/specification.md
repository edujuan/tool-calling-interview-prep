# Model Context Protocol (MCP) - Complete Specification

> **Deep dive into MCP architecture, lifecycle, and implementation**

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Protocol Lifecycle](#protocol-lifecycle)
- [Message Format](#message-format)
- [Tool System](#tool-system)
- [Resources and Prompts](#resources-and-prompts)
- [Transport Layers](#transport-layers)
- [Implementation Guide](#implementation-guide)
- [Best Practices](#best-practices)

---

## Overview

The **Model Context Protocol (MCP)** is an open standard introduced by Anthropic in late 2024 for connecting AI applications to external systems. MCP provides a standardized way for AI agents to:

- Discover available tools
- Execute tool calls
- Access contextual resources
- Use pre-defined prompts
- Maintain stateful sessions

### Key Concepts

```
┌─────────────────┐
│   MCP HOST      │  ← AI Application (e.g., Claude Desktop, IDE)
│  (Agent App)    │
└────────┬────────┘
         │
         │ Uses
         ▼
┌─────────────────┐
│   MCP CLIENT    │  ← Library that speaks MCP protocol
│  (In Host)      │
└────────┬────────┘
         │
         │ Connects to (JSON-RPC)
         ▼
┌─────────────────┐
│   MCP SERVER    │  ← Exposes tools and resources
│  (Service)      │
└────────┬────────┘
         │
         │ Wraps
         ▼
┌─────────────────┐
│   TOOLS/APIs    │  ← Actual implementations
└─────────────────┘
```

**Design Philosophy**: "USB-C port for AI" - one protocol to connect to many services

---

## Architecture

### Three-Layer Model

#### Layer 1: MCP Host

The **host** is the AI application that wants to use tools.

**Responsibilities**:
- Runs the LLM
- Manages MCP client connections
- Presents tools to the LLM
- Coordinates multiple MCP servers

**Examples**:
- Claude Desktop app
- VS Code with AI extension
- Custom AI agent application

**Code Example**:
```python
class MCPHost:
    """AI application using MCP"""
    
    def __init__(self, llm):
        self.llm = llm
        self.clients = {}  # server_name -> MCPClient
    
    async def connect_to_server(self, server_url: str, name: str):
        """Connect to an MCP server"""
        client = MCPClient(server_url)
        await client.connect()
        
        # Discover tools
        tools = await client.list_tools()
        
        # Store client
        self.clients[name] = {
            'client': client,
            'tools': tools
        }
        
        return tools
    
    async def run_agent(self, query: str):
        """Run agent with MCP tools"""
        
        # Get all available tools
        all_tools = []
        for server in self.clients.values():
            all_tools.extend(server['tools'])
        
        # LLM decides which tool to use
        decision = await self.llm.decide(query, available_tools=all_tools)
        
        if decision['action'] == 'use_tool':
            # Find which server has this tool
            tool_name = decision['tool']
            server = self._find_server_with_tool(tool_name)
            
            # Execute via MCP
            result = await server['client'].call_tool(
                tool_name,
                decision['arguments']
            )
            
            return result
```

#### Layer 2: MCP Client

The **client** is a library that implements the MCP protocol on the host side.

**Responsibilities**:
- Establish connection to servers
- Send JSON-RPC requests
- Handle responses and errors
- Manage connection lifecycle

**Standard Operations**:
```python
class MCPClient:
    """MCP client library"""
    
    async def connect(self):
        """Establish connection to server"""
        pass
    
    async def initialize(self) -> dict:
        """Initialize session, exchange capabilities"""
        response = await self.request("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "my-client",
                "version": "1.0.0"
            }
        })
        return response
    
    async def list_tools(self) -> list:
        """Get list of available tools"""
        response = await self.request("tools/list", {})
        return response['tools']
    
    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool"""
        response = await self.request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        return response
    
    async def request(self, method: str, params: dict) -> dict:
        """Send JSON-RPC request"""
        message = {
            "jsonrpc": "2.0",
            "id": self._generate_id(),
            "method": method,
            "params": params
        }
        
        response = await self._send(message)
        return response['result']
```

#### Layer 3: MCP Server

The **server** exposes tools and resources via the MCP protocol.

**Responsibilities**:
- Implement JSON-RPC handlers
- Register tools and resources
- Execute tool logic
- Manage authentication and permissions

**Example Implementation**:
```python
from mcp import Server, Tool
from mcp.types import TextContent, ImageContent

class WeatherMCPServer(Server):
    """MCP server for weather tools"""
    
    def __init__(self):
        super().__init__("weather-server")
    
    @self.list_tools()
    async def handle_list_tools(self) -> list[Tool]:
        """Return available tools"""
        return [
            Tool(
                name="get_weather",
                description="Get current weather for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or zip code"
                        },
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            )
        ]
    
    @self.call_tool()
    async def handle_call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Execute tool"""
        if name == "get_weather":
            # Call actual weather API
            weather_data = await self._fetch_weather(
                arguments['location'],
                arguments.get('units', 'celsius')
            )
            
            # Return result as TextContent
            return [
                TextContent(
                    type="text",
                    text=f"Weather in {arguments['location']}: "
                         f"{weather_data['temp']}° {weather_data['condition']}"
                )
            ]
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def _fetch_weather(self, location: str, units: str) -> dict:
        """Actual weather API call"""
        # Implementation here
        pass

# Run server
server = WeatherMCPServer()
await server.run()
```

---

## Protocol Lifecycle

### Connection Flow

```
CLIENT                                SERVER
  |                                     |
  |-------- initialize request ------->|
  |                                     |
  |<------- initialize response -------|
  |        (server capabilities)       |
  |                                     |
  |-------- tools/list request ------->|
  |                                     |
  |<------- tools/list response -------|
  |        (available tools)           |
  |                                     |
  |-------- tools/call request ------->|
  |        (tool_name, args)           |
  |                                     |
  |<------- tools/call response -------|
  |        (result)                    |
  |                                     |
  |-------- [more tool calls] -------->|
  |                                     |
  |-------- disconnect --------------->|
  |                                     |
```

### 1. Initialization Phase

**Client → Server: initialize**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {
        "listChanged": true
      },
      "sampling": {}
    },
    "clientInfo": {
      "name": "example-client",
      "version": "1.0.0"
    }
  }
}
```

**Server → Client: response**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {
        "subscribe": true,
        "listChanged": true
      },
      "prompts": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "weather-server",
      "version": "1.0.0"
    }
  }
}
```

### 2. Discovery Phase

**Client → Server: tools/list**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Server → Client: response**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": {"type": "string"},
            "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
          },
          "required": ["location"]
        }
      }
    ]
  }
}
```

### 3. Execution Phase

**Client → Server: tools/call**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "location": "Paris",
      "units": "celsius"
    }
  }
}
```

**Server → Client: response**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Weather in Paris: 18°C, Cloudy"
      }
    ]
  }
}
```

---

## Message Format

### JSON-RPC 2.0

MCP uses **JSON-RPC 2.0** for all communication.

#### Request Format

```json
{
  "jsonrpc": "2.0",
  "id": <number | string>,
  "method": "<method_name>",
  "params": {
    // Method-specific parameters
  }
}
```

#### Response Format (Success)

```json
{
  "jsonrpc": "2.0",
  "id": <matching request id>,
  "result": {
    // Method-specific result
  }
}
```

#### Response Format (Error)

```json
{
  "jsonrpc": "2.0",
  "id": <matching request id>,
  "error": {
    "code": <error code>,
    "message": "<error message>",
    "data": {
      // Optional additional error info
    }
  }
}
```

#### Notification (No Response Expected)

```json
{
  "jsonrpc": "2.0",
  "method": "<method_name>",
  "params": {
    // Parameters
  }
  // No "id" field = notification
}
```

### Standard Error Codes

| Code | Meaning | Usage |
|------|---------|-------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid request | Missing required fields |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Wrong parameter types |
| -32603 | Internal error | Server error |
| -32000 to -32099 | Server errors | Custom server errors |

---

## Tool System

### Tool Definition Schema

```typescript
interface Tool {
  name: string;              // Unique identifier
  description: string;        // What the tool does
  inputSchema: JSONSchema;    // JSON Schema for arguments
}
```

**Example: Complex Tool**

```json
{
  "name": "search_database",
  "description": "Search customer database with filters",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "filters": {
        "type": "object",
        "properties": {
          "status": {
            "type": "string",
            "enum": ["active", "inactive", "pending"]
          },
          "created_after": {
            "type": "string",
            "format": "date"
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
  }
}
```

### Tool Response Types

MCP supports multiple content types in responses:

#### Text Content

```json
{
  "content": [
    {
      "type": "text",
      "text": "The result is 42"
    }
  ]
}
```

#### Image Content

```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64-encoded-image>",
      "mimeType": "image/png"
    }
  ]
}
```

#### Resource Content

```json
{
  "content": [
    {
      "type": "resource",
      "resource": {
        "uri": "file:///path/to/file.txt",
        "mimeType": "text/plain",
        "text": "File contents here"
      }
    }
  ]
}
```

---

## Resources and Prompts

MCP servers can provide more than just tools:

### Resources

**Resources** are data that the server can provide (files, database records, etc.)

**List Resources:**

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/list",
  "params": {}
}

// Response
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "resources": [
      {
        "uri": "file:///workspace/README.md",
        "name": "README.md",
        "mimeType": "text/markdown",
        "description": "Project readme file"
      }
    ]
  }
}
```

**Read Resource:**

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "file:///workspace/README.md"
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "contents": [
      {
        "uri": "file:///workspace/README.md",
        "mimeType": "text/markdown",
        "text": "# My Project\n\nDescription here..."
      }
    ]
  }
}
```

### Prompts

**Prompts** are pre-defined prompt templates that servers can provide.

```json
// List prompts
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/list",
  "params": {}
}

// Response
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "prompts": [
      {
        "name": "code_review",
        "description": "Review code for issues",
        "arguments": [
          {
            "name": "code",
            "description": "Code to review",
            "required": true
          }
        ]
      }
    ]
  }
}
```

---

## Bidirectional Communication & Sampling

One of MCP's most powerful features is **bidirectional communication** - the ability for servers to initiate requests back to the client. This enables interactive workflows and human-in-the-loop patterns.

### Sampling: Server → Client Requests

**Sampling** allows an MCP server to request that the client (agent) generate text via its LLM. This is useful when a tool needs:
- Clarification from the user
- Additional context to complete an operation
- LLM assistance to process results
- Interactive decision-making

**Key Concept:** The server can ask the agent "please have your LLM generate a response to this prompt."

### Sampling Flow

```
1. Client calls tool on server
      ↓
2. Server realizes it needs more info
      ↓
3. Server sends sampling request → Client
      ↓
4. Client presents to user (with approval)
      ↓
5. User approves request
      ↓
6. Client calls LLM with provided prompt
      ↓
7. LLM generates response
      ↓
8. Client returns result → Server
      ↓
9. Server uses result to complete tool
      ↓
10. Server returns final result → Client
```

### Sampling Request Format

**Server → Client: sampling/createMessage**

```json
{
  "jsonrpc": "2.0",
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Based on the analysis results, should we proceed with the migration? Consider these factors: ..."
        }
      }
    ],
    "modelPreferences": {
      "hints": [
        {
          "name": "claude-3-5-sonnet-20241022"
        }
      ],
      "intelligenceLevel": 0.5,
      "costLevel": 0.5
    },
    "systemPrompt": "You are an expert database administrator evaluating migration plans.",
    "maxTokens": 1000
  }
}
```

**Client → Server: sampling response**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "model": "claude-3-5-sonnet-20241022",
    "role": "assistant",
    "content": {
      "type": "text",
      "text": "Based on the analysis, I recommend proceeding with the migration because..."
    },
    "stopReason": "end_turn"
  }
}
```

### Server-Side Implementation

```python
from mcp.server import Server
from mcp.types import SamplingRequest, TextContent

class InteractiveMCPServer(Server):
    """MCP server that uses sampling for interactive workflows"""
    
    async def call_tool_impl(self, name: str, arguments: dict):
        if name == "deploy_changes":
            # Analyze deployment risks
            risks = self._analyze_deployment(arguments)
            
            if risks['severity'] == 'high':
                # Ask LLM to help decide
                sampling_result = await self.request_sampling(
                    messages=[{
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Deployment has high-risk changes: {risks['details']}. "
                                   f"Should we proceed? Provide reasoning."
                        }
                    }],
                    system_prompt="You are a cautious DevOps engineer.",
                    max_tokens=500
                )
                
                decision_text = sampling_result.content.text
                
                # Parse LLM decision
                if "proceed" in decision_text.lower():
                    result = self._execute_deployment(arguments)
                    return [TextContent(
                        type="text",
                        text=f"Deployment executed. LLM reasoning: {decision_text}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Deployment cancelled based on LLM analysis: {decision_text}"
                    )]
            
            # Low risk - proceed automatically
            result = self._execute_deployment(arguments)
            return [TextContent(type="text", text=f"Deployed: {result}")]
```

### Client-Side Handling

```python
from mcp.client import Client

class MCPClientWithSampling(Client):
    """MCP client that handles sampling requests"""
    
    def __init__(self, llm_client, user_approval_callback):
        super().__init__()
        self.llm_client = llm_client
        self.user_approval = user_approval_callback
    
    async def handle_sampling_request(self, request: dict):
        """Handle server-initiated sampling request"""
        
        # Extract sampling parameters
        messages = request['params']['messages']
        system_prompt = request['params'].get('systemPrompt', '')
        max_tokens = request['params'].get('maxTokens', 1000)
        
        # Security: Request user approval first
        approved = await self.user_approval(
            f"Server wants to use your LLM with prompt: {messages[0]['content']['text']}"
        )
        
        if not approved:
            return {
                "jsonrpc": "2.0",
                "id": request['id'],
                "error": {
                    "code": -32000,
                    "message": "User denied sampling request"
                }
            }
        
        # Call LLM
        llm_response = await self.llm_client.generate(
            messages=messages,
            system=system_prompt,
            max_tokens=max_tokens
        )
        
        # Return result to server
        return {
            "jsonrpc": "2.0",
            "id": request['id'],
            "result": {
                "model": llm_response.model,
                "role": "assistant",
                "content": {
                    "type": "text",
                    "text": llm_response.text
                },
                "stopReason": llm_response.stop_reason
            }
        }
```

### Use Cases for Bidirectional Communication

**1. Interactive Approvals**
```python
# Server requests approval for sensitive operation
sampling_result = await server.request_sampling(
    messages=[{"role": "user", "content": {"type": "text", "text": "Confirm: Delete production database 'users'? (yes/no)"}}],
    max_tokens=10
)
```

**2. Contextual Analysis**
```python
# Server provides data, asks LLM to analyze
await server.request_sampling(
    messages=[{
        "role": "user", 
        "content": {"type": "text", "text": f"Here's the log data: {logs}. What caused the error?"}
    }],
    system_prompt="You are a debugging expert."
)
```

**3. Dynamic Tool Selection**
```python
# Server asks which approach to use
await server.request_sampling(
    messages=[{
        "role": "user",
        "content": {"type": "text", "text": "We have 3 backup strategies: A (fast, risky), B (balanced), C (slow, safe). Which should we use given: ..."}
    }]
)
```

**4. Progressive Refinement**
```python
# Server iteratively refines output with LLM help
draft = initial_draft()
for iteration in range(3):
    feedback = await server.request_sampling(
        messages=[{"role": "user", "content": {"type": "text", "text": f"Improve this: {draft}"}}]
    )
    draft = feedback.content.text
```

### Security Considerations

**⚠️ Critical: Sampling requires user approval**

```python
# Client MUST request user permission
async def safe_sampling_handler(request):
    # Show user what the server is requesting
    print(f"⚠️  Server wants to use your LLM:")
    print(f"Prompt: {request['params']['messages']}")
    print(f"Cost estimate: ~{estimate_cost(request)} tokens")
    
    approval = input("Allow? (yes/no): ")
    
    if approval.lower() != 'yes':
        return {"error": {"code": -32000, "message": "User denied"}}
    
    # Only then proceed with LLM call
    return await call_llm(request)
```

**Why approval is needed:**
- Sampling uses client's LLM (costs money)
- Server could inject malicious prompts
- User should control what their LLM sees
- Prevents prompt injection via server

### Comparison: MCP vs UTCP

| Feature | MCP | UTCP |
|---------|-----|------|
| **Server → Client calls** | ✅ Yes (sampling) | ❌ No |
| **Interactive workflows** | ✅ Native support | ⚠️ Manual implementation |
| **Human-in-the-loop** | ✅ Built-in pattern | ⚠️ Agent must handle |
| **Tool callbacks** | ✅ Yes | ❌ One-way only |

**This is a key differentiator:** MCP's bidirectional communication enables workflows that would be difficult with stateless protocols like UTCP.

---

## Transport Layers

MCP supports two main transport mechanisms:

### 1. STDIO Transport

**Use case**: Local servers, same machine as client

**How it works**:
- Server runs as subprocess
- Communication via stdin/stdout
- Client launches server process
- Low latency, no network overhead

**Example (Client side)**:

```python
import subprocess
import json

class StdioMCPClient:
    """MCP client using STDIO transport"""
    
    def __init__(self, server_command: list):
        # Launch server as subprocess
        self.process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    def send_request(self, method: str, params: dict) -> dict:
        """Send JSON-RPC request via stdin"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params
        }
        
        # Write to stdin
        json_str = json.dumps(request) + "\n"
        self.process.stdin.write(json_str)
        self.process.stdin.flush()
        
        # Read response from stdout
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)
        
        return response
    
    def close(self):
        """Terminate server process"""
        self.process.terminate()
        self.process.wait()

# Usage
client = StdioMCPClient(["python", "my_mcp_server.py"])
tools = client.send_request("tools/list", {})
```

### 2. HTTP/SSE Transport

**Use case**: Remote servers, cloud services

**How it works**:
- Server runs as HTTP service
- Client connects via HTTP
- Server-Sent Events (SSE) for server→client messages
- Network-based, can be remote

**Example (Server side with FastAPI)**:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """Handle MCP JSON-RPC requests"""
    
    method = request['method']
    params = request.get('params', {})
    
    if method == "tools/list":
        result = {
            "tools": [
                {
                    "name": "example_tool",
                    "description": "An example tool",
                    "inputSchema": {"type": "object"}
                }
            ]
        }
    elif method == "tools/call":
        # Execute tool
        result = {
            "content": [
                {"type": "text", "text": "Tool executed successfully"}
            ]
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": request['id'],
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }
    
    return {
        "jsonrpc": "2.0",
        "id": request['id'],
        "result": result
    }

@app.get("/mcp/sse")
async def sse_endpoint():
    """Server-Sent Events for server→client notifications"""
    
    async def event_generator():
        # Send periodic updates
        while True:
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            await asyncio.sleep(30)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### Transport Comparison

| Feature | STDIO | HTTP/SSE |
|---------|-------|----------|
| **Latency** | Very Low (~1ms) | Low (~10-50ms) |
| **Location** | Same machine only | Can be remote |
| **Setup** | Simple subprocess | Requires server setup |
| **Firewall** | No issues | May need ports open |
| **Scalability** | 1:1 client-server | Many clients → 1 server |
| **Use Case** | Local tools, IDE plugins | Cloud services, shared tools |

---

## Implementation Guide

### Building an MCP Server

**Step-by-step guide to creating your first MCP server:**

#### Step 1: Install MCP SDK

```bash
pip install mcp
```

#### Step 2: Create Server Class

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

class CalculatorServer(Server):
    """Simple calculator MCP server"""
    
    def __init__(self):
        super().__init__("calculator-server")
    
    async def list_tools_impl(self) -> list[Tool]:
        """Define available tools"""
        return [
            Tool(
                name="add",
                description="Add two numbers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            ),
            Tool(
                name="multiply",
                description="Multiply two numbers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            )
        ]
    
    async def call_tool_impl(
        self,
        name: str,
        arguments: dict
    ) -> list[TextContent]:
        """Execute tool logic"""
        
        if name == "add":
            result = arguments['a'] + arguments['b']
            return [TextContent(
                type="text",
                text=f"Result: {result}"
            )]
        
        elif name == "multiply":
            result = arguments['a'] * arguments['b']
            return [TextContent(
                type="text",
                text=f"Result: {result}"
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")

# Run server
async def main():
    server = CalculatorServer()
    
    # Run with STDIO transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 3: Test Server

```python
# test_server.py
from mcp.client import Client
import asyncio

async def test_calculator_server():
    """Test the calculator server"""
    
    # Connect to server
    client = Client()
    await client.connect_stdio(["python", "calculator_server.py"])
    
    # List tools
    tools = await client.list_tools()
    print(f"Available tools: {[t.name for t in tools]}")
    
    # Call tool
    result = await client.call_tool("add", {"a": 5, "b": 3})
    print(f"5 + 3 = {result.content[0].text}")
    
    # Cleanup
    await client.disconnect()

asyncio.run(test_calculator_server())
```

---

## Best Practices

### 1. Tool Design

✅ **DO:**
- Keep tools focused (single responsibility)
- Provide clear, detailed descriptions
- Use JSON Schema for validation
- Return structured content

❌ **DON'T:**
- Create "god tools" that do everything
- Use vague descriptions
- Skip input validation
- Return unstructured strings

### 2. Error Handling

✅ **DO:**
```python
async def call_tool_impl(self, name: str, arguments: dict):
    try:
        # Validate inputs
        self._validate_arguments(name, arguments)
        
        # Execute with timeout
        result = await asyncio.wait_for(
            self._execute_tool(name, arguments),
            timeout=30.0
        )
        
        return result
        
    except ValidationError as e:
        raise MCPError(
            code=-32602,
            message="Invalid arguments",
            data={"details": str(e)}
        )
    except TimeoutError:
        raise MCPError(
            code=-32000,
            message="Tool execution timeout"
        )
```

### 3. Resource Management

✅ **DO:**
- Use async/await properly
- Close connections in finally blocks
- Implement proper cleanup
- Handle server shutdown gracefully

### 4. Security

✅ **DO:**
- Validate all inputs
- Implement authentication
- Use TLS for HTTP transport
- Sandbox tool execution
- Log all tool calls

❌ **DON'T:**
- Trust client input blindly
- Expose internal paths
- Allow arbitrary code execution
- Skip authorization checks

### 5. Performance

✅ **DO:**
- Cache expensive operations
- Use connection pooling
- Implement timeouts
- Monitor performance metrics

---

## Summary

**MCP provides:**
- ✅ Standardized protocol for tool use
- ✅ Client-server architecture
- ✅ JSON-RPC 2.0 messaging
- ✅ Tools, resources, and prompts
- ✅ Multiple transport options
- ✅ Stateful sessions
- ✅ Bidirectional communication

**Best for:**
- Enterprise environments
- Complex workflows
- Centralized control
- Stateful interactions

**Trade-offs:**
- More infrastructure needed
- Higher latency than direct calls
- Requires server maintenance
- Learning curve for implementation

---

**Official Resources:**
- [Official MCP Documentation](https://modelcontextprotocol.io/) - Complete documentation
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Protocol specification (latest: 2024-11-05)
- [Anthropic MCP Announcement](https://www.anthropic.com/news/model-context-protocol) - Original announcement and vision
- [MCP GitHub Repository](https://github.com/modelcontextprotocol) - SDKs and examples

**Learning Resources:**
- [MCP Quickstart Guide](https://modelcontextprotocol.io/quickstart) - Get started in 10 minutes
- [Building MCP Servers Tutorial](https://modelcontextprotocol.io/tutorials/building-servers) - Step-by-step guide
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) - Debugging tool
- [Hugging Face MCP Course](https://huggingface.co/learn/cookbook/mcp) - Comprehensive learning path

**Next Steps:**
- [MCP vs UTCP Comparison](../comparison.md)
- [Build Your First MCP Server](./tutorial.md)
- [MCP Example: File Operations](../../examples/python-mcp-files/)

