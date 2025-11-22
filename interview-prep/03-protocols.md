# Protocols Questions (41-54)

## Protocols

### 41. Explain UTCP in simple terms.

**Answer:**

**UTCP (Universal Tool Calling Protocol) is like an instruction manual for tools.**

**Key idea:** Instead of building a server to wrap tools, just publish a JSON file that explains how to call them directly.

**Analogy:** 
- Ordering food: UTCP is like reading the menu and ordering directly from the kitchen
- You don't need a waiter (server) in the middle

**Example UTCP Manual:**
```json
{
  "tools": [{
    "name": "weather",
    "description": "Get current weather",
    "tool_call_template": {
      "call_template_type": "http",
      "url": "https://api.weather.com/current?location={{location}}",
      "http_method": "GET"
    },
    "parameters": {
      "location": {"type": "string"}
    }
  }]
}
```

**Agent's perspective:**
1. Reads manual
2. Sees "to get weather, make GET request to this URL"
3. Makes the request directly
4. Gets result

**Benefits:**
- No server to maintain
- Uses tool's native security
- Lower latency (no middle layer)

---

### 42. Explain MCP in simple terms.

**Answer:**

**MCP (Model Context Protocol) is like having a personal assistant (server) who handles all your tool requests.**

**Key idea:** All tool calls go through a centralized server that manages connections, authentication, and execution.

**Analogy:**
- Ordering food: MCP is like calling a concierge who coordinates with all restaurants for you
- The concierge (MCP server) handles everything

**Architecture:**
```
Agent → MCP Client → MCP Server → Tool
```

**Example:**
```python
# MCP Server code
class MCPServer:
    def list_tools(self):
        return [WeatherTool(), DatabaseTool()]
    
    def call_tool(self, name, args):
        if name == "weather":
            return call_weather_api(args)

# Agent uses it
server = MCPServer()
tools = server.list_tools()
result = server.call_tool("weather", {"location": "Paris"})
```

**Benefits:**
- Centralized control and logging
- Can maintain state across calls
- Unified authentication
- Bidirectional communication

**Trade-off:** More infrastructure, higher latency

---

### 43. When would you choose UTCP over MCP?

**Answer:**

**Choose UTCP when:**

✅ **Performance is critical**
- Real-time applications
- High-frequency operations
- Low-latency requirements
- Example: Trading bot making 1000s of API calls/sec

✅ **You have existing APIs**
- Already have REST APIs
- Have OpenAPI specifications
- Don't want to rewrite integrations
- Example: Integrating 50 public APIs

✅ **Simple, stateless operations**
- One-shot API calls
- Independent tool invocations
- No need for session context
- Example: Weather lookup service

✅ **Rapid prototyping**
- Need to demo quickly
- Don't want infrastructure overhead
- Example: Hackathon project

✅ **Large number of tools**
- 100+ tools to integrate
- Tools from many sources
- Example: API aggregation platform

**Real Example:**
A startup building an AI-powered API testing tool chose UTCP because:
- Needed to call 200+ different APIs
- Required low latency
- Already had OpenAPI specs
- Result: 3-day implementation

---

### 44. When would you choose MCP over UTCP?

**Answer:**

**Choose MCP when:**

✅ **Enterprise governance required**
- Need centralized audit logs
- Compliance requirements
- Unified access control
- Example: Healthcare AI with HIPAA requirements

✅ **Complex stateful workflows**
- Multi-step transactions
- Need to maintain context
- Long-running operations
- Example: Customer service agent maintaining conversation state

✅ **Bidirectional communication needed**
- Tools need to call back to agent
- Interactive workflows
- Example: Approval workflows where tool asks for confirmation

✅ **Centralized management**
- IT department controls all tools
- Want single point of monitoring
- Need consistent policies
- Example: Enterprise with strict IT controls

✅ **Rich feature requirements**
- Need resources (data blobs)
- Need prompt suggestions
- Complex integrations
- Example: IDE integration with code analysis

**Real Example:**
A financial services company chose MCP because:
- Strict compliance (need audit trail)
- Complex customer workflows (stateful)
- IT security requirements (centralized control)
- Result: Passed audit, secure customer data handling

---

### 45. Can you use both UTCP and MCP together?

**Answer:**

**Yes! Hybrid approaches are common and recommended.**

**Use case:** 
- External public APIs → UTCP (fast, simple)
- Internal sensitive tools → MCP (controlled, audited)

**Implementation:**
```python
class HybridAgent:
    def __init__(self):
        self.utcp_client = UTCPClient()
        self.mcp_client = MCPClient()
    
    def call_tool(self, tool_name, args):
        # Route based on tool type
        if tool_name in self.public_tools:
            return self.utcp_client.call(tool_name, args)
        elif tool_name in self.internal_tools:
            return self.mcp_client.call(tool_name, args)
```

**UTCP can even call MCP:**
```json
{
  "tool_call_template": {
    "call_template_type": "mcp",
    "server_url": "http://internal-mcp.company.com"
  }
}
```

**Benefits of hybrid:**
- ✅ Best of both worlds
- ✅ Optimize per tool requirements
- ✅ Gradual migration path
- ✅ Flexibility

**When to use hybrid:**
- Large organizations with varied requirements
- Migrating between protocols
- Different security needs per tool
- Want to optimize each tool independently

---

### 46. What is MCP "sampling" and why is it important?

**Answer:**

**Sampling** is MCP's ability to let servers request that the client's LLM generate text. It's a form of **bidirectional communication** where the tool can call back to the agent.

**Flow:**
```
1. Client calls tool on server
2. Server realizes it needs LLM help
3. Server sends sampling request → Client
4. Client gets user approval
5. Client runs LLM with provided prompt
6. LLM result → Server
7. Server uses result to complete tool
```

**Example Use Cases:**

**1. Interactive Approval:**
```python
# Server asks for confirmation
sampling_result = await server.request_sampling(
    messages=[{
        "role": "user",
        "content": {"type": "text", "text": "Confirm: Delete 500 records? (yes/no)"}
    }]
)
```

**2. Contextual Analysis:**
```python
# Server gives data to LLM for analysis
await server.request_sampling(
    messages=[{
        "role": "user",
        "content": {"type": "text", "text": f"Analyze this error log: {logs}"}
    }],
    system_prompt="You are a debugging expert."
)
```

**Why It's Important:**
- ✅ Enables human-in-the-loop patterns
- ✅ Tools can get clarification
- ✅ Interactive workflows become possible
- ✅ LLM can help tools make decisions

**Security Note:** Client **must** request user approval before executing sampling requests - the server shouldn't have unrestricted access to your LLM.

**Key Differentiator:** UTCP cannot do this - it's one-way (agent → tool). MCP's bidirectional nature is a major advantage for complex workflows.

---

### 47. How do performance differences between MCP and UTCP vary in practice?

**Answer:**

**The simple answer "MCP is 30-40% slower" is misleading.** Performance depends heavily on context:

**Transport Type Matters:**

**MCP with STDIO (local):**
- Overhead: ~10-30ms per call
- Very fast for same-machine tools
- Difference from UTCP is minimal

**MCP with HTTP (remote):**
- Overhead: ~20-100ms per call
- Network latency dominates
- UTCP has clear advantage here

**Workload Type Matters:**

**Real-time systems (100+ calls/sec):**
- UTCP's direct approach wins significantly
- Example: Trading bot, real-time monitoring

**User-facing chatbots:**
- LLM inference (1-3 seconds) dominates latency
- MCP overhead (50ms) is negligible
- Either protocol works fine

**Batch processing:**
- Total time matters, not per-call latency
- MCP overhead acceptable for better governance

**Actual Comparison:**
```
Scenario: Call weather API

UTCP:
- Network to API: 50ms
- Total: 50ms

MCP (STDIO):
- Local MCP overhead: 10ms
- Network to API: 50ms
- Total: 60ms (20% slower)

MCP (HTTP):
- Network to MCP server: 20ms
- Local processing: 10ms
- Network to API: 50ms
- Total: 80ms (60% slower)
```

**Interview Tip:** Don't cite specific percentages. Instead, explain that performance depends on transport, network, and workload, and that for most chatbot use cases, the difference is negligible since LLM latency dominates.

---

### 48. How do you handle the UTCP manual_version field correctly?

**Answer:**

UTCP manuals should include **two version fields**:

**1. `utcp_version`**: The UTCP protocol version
```json
{
  "utcp_version": "1.0.1"  // Protocol spec version
}
```

**2. `manual_version`**: Your tool manual's version
```json
{
  "manual_version": "2.1.0"  // Your manual's version
}
```

**Complete Example:**
```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "metadata": {
    "title": "Weather API Tools",
    "description": "Tools for weather data"
  },
  "tools": [...]
}
```

**Why Both?**
- `utcp_version`: Tells clients which protocol features to expect
- `manual_version`: Tracks changes to your specific tools

**Common Mistake:** Only including `utcp_version` or putting manual version in metadata instead of at root level.

**Versioning Strategy:**
```
manual_version follows semantic versioning:
- 1.0.0 → 1.0.1: Bug fix (patch)
- 1.0.0 → 1.1.0: New tool added (minor)
- 1.0.0 → 2.0.0: Breaking change (major)
```

---

### 49. What protocols does UTCP support for call_template_type?

**Answer:**

UTCP is **transport-agnostic** and supports many protocols:

**1. HTTP/REST** (most common)
```json
{"call_template_type": "http"}
```

**2. WebSocket** (real-time bidirectional)
```json
{"call_template_type": "websocket"}
```

**3. Server-Sent Events** (streaming)
```json
{"call_template_type": "sse"}
```

**4. CLI** (command-line tools)
```json
{"call_template_type": "cli"}
```

**5. gRPC** (high-performance RPC)
```json
{"call_template_type": "grpc"}
```

**6. GraphQL** (graph queries)
```json
{"call_template_type": "graphql"}
```

**7. MCP** (yes, UTCP can call MCP!)
```json
{"call_template_type": "mcp"}
```

**Example: WebSocket Tool**
```json
{
  "name": "live_price_feed",
  "tool_call_template": {
    "call_template_type": "websocket",
    "url": "wss://api.example.com/prices",
    "message_template": {
      "subscribe": "{{symbol}}"
    },
    "auth": {
      "type": "token",
      "token": "${WS_TOKEN}"
    }
  }
}
```

**Example: SSE Streaming**
```json
{
  "name": "live_logs",
  "tool_call_template": {
    "call_template_type": "sse",
    "url": "https://api.example.com/logs/stream",
    "http_method": "GET",
    "headers": {
      "Accept": "text/event-stream"
    }
  }
}
```

**This flexibility is a major UTCP advantage** - it can wrap virtually any interface, not just REST APIs.

---

### 50. How do you convert an OpenAPI spec to a UTCP manual?

**Answer:**

OpenAPI specs can be automatically converted to UTCP manuals.

**OpenAPI Spec:**
```yaml
openapi: 3.0.0
info:
  title: Weather API
  version: 1.0.0
paths:
  /weather:
    get:
      summary: Get weather
      parameters:
        - name: city
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
```

**Converted UTCP Manual:**
```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "metadata": {
    "title": "Weather API",
    "description": "Converted from OpenAPI spec"
  },
  "tools": [{
    "name": "get_weather",
    "description": "Get weather",
    "tool_call_template": {
      "call_template_type": "http",
      "url": "https://api.example.com/weather",
      "http_method": "GET",
      "query_parameters": {
        "city": "{{city}}"
      }
    },
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "City name"
        }
      },
      "required": ["city"]
    }
  }]
}
```

**Automated Conversion:**
```python
def openapi_to_utcp(openapi_spec):
    utcp_manual = {
        "utcp_version": "1.0.1",
        "manual_version": "1.0.0",
        "metadata": {
            "title": openapi_spec["info"]["title"],
            "description": openapi_spec["info"].get("description", "")
        },
        "tools": []
    }
    
    for path, methods in openapi_spec["paths"].items():
        for method, operation in methods.items():
            tool = {
                "name": operation.get("operationId", f"{method}_{path}"),
                "description": operation.get("summary", ""),
                "tool_call_template": {
                    "call_template_type": "http",
                    "url": f"{openapi_spec['servers'][0]['url']}{path}",
                    "http_method": method.upper()
                },
                "parameters": convert_parameters(operation.get("parameters", []))
            }
            utcp_manual["tools"].append(tool)
    
    return utcp_manual
```

---

### 51. What are MCP resources and how do they differ from tools?

**Answer:**

**MCP Resources** are read-only data that the agent can access.

**Resources vs Tools:**

| Aspect | Tools | Resources |
|--------|-------|-----------|
| **Purpose** | Perform actions | Provide data |
| **Mutability** | Can modify state | Read-only |
| **Parameters** | Dynamic (user provides) | Static or predefined |
| **Examples** | send_email, delete_file | documentation, config, file contents |

**MCP Resource Example:**
```python
from mcp.server import Server
from mcp.types import Resource, TextContent

class DocumentationServer(Server):
    async def list_resources(self):
        return [
            Resource(
                uri="docs://api-reference",
                name="API Reference",
                description="Complete API documentation",
                mimeType="text/markdown"
            ),
            Resource(
                uri="docs://examples",
                name="Code Examples",
                description="Usage examples",
                mimeType="text/markdown"
            )
        ]
    
    async def read_resource(self, uri: str):
        if uri == "docs://api-reference":
            content = load_api_docs()
            return [TextContent(
                type="text",
                text=content
            )]
```

**When to use:**
- **Tools:** When agent needs to DO something (send email, query database)
- **Resources:** When agent needs to KNOW something (read docs, get config)

**Advantage:** Resources can be preloaded into context without needing tool calls.

---

### 52. How do you handle authentication in UTCP vs MCP?

**Answer:**

**UTCP Authentication** (Direct to API):
```json
{
  "name": "api_call",
  "tool_call_template": {
    "call_template_type": "http",
    "url": "https://api.example.com/data",
    "http_method": "GET",
    "auth": {
      "type": "bearer",
      "token": "${API_TOKEN}"
    }
  }
}
```

**Token resolution:**
```python
# Agent reads from environment
token = os.getenv("API_TOKEN")
# Injects into request
headers = {"Authorization": f"Bearer {token}"}
```

**MCP Authentication** (Centralized):
```python
class AuthenticatedMCPServer(Server):
    def __init__(self, api_key):
        self.api_key = api_key  # Server holds credentials
    
    async def call_tool(self, name, arguments):
        # Server handles auth automatically
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await make_request(arguments, headers=headers)
```

**Comparison:**

**UTCP:**
- ✅ Agent controls credentials
- ✅ No middleman with access to secrets
- ❌ Agent needs access to all API credentials
- ❌ Harder to centrally manage/rotate

**MCP:**
- ✅ Centralized credential management
- ✅ Server can refresh tokens automatically
- ✅ Easier to audit and rotate
- ❌ Server has access to sensitive credentials
- ❌ Single point of failure

**Best Practice:**
- UTCP: For public APIs or when agent runs in trusted environment
- MCP: For internal APIs or when centralized auth management is required

---

### 53. What is the difference between STDIO and HTTP transport in MCP?

**Answer:**

MCP supports two transport mechanisms:

**STDIO (Standard Input/Output):**

```python
# Server
class MyMCPServer(Server):
    pass

# Run on STDIO
server = MyMCPServer()
server.run_stdio()  # Reads from stdin, writes to stdout

# Client
from mcp.client import MCPClient

async with MCPClient.stdio("./my_server.py") as client:
    result = await client.call_tool("my_tool", {})
```

**Characteristics:**
- ✅ Very fast (no network overhead)
- ✅ Simple setup
- ✅ Good for local tools
- ❌ Must be on same machine
- ❌ Process per connection

**HTTP/SSE Transport:**

```python
# Server
from mcp.server.http import HTTPServer

server = HTTPServer(MyMCPServer())
server.run(host="0.0.0.0", port=8080)

# Client
async with MCPClient.http("http://localhost:8080") as client:
    result = await client.call_tool("my_tool", {})
```

**Characteristics:**
- ✅ Works over network
- ✅ Multiple clients can connect
- ✅ Can be load balanced
- ❌ Network latency
- ❌ Requires network infrastructure

**When to use:**

| Use Case | Transport |
|----------|-----------|
| Local development | STDIO |
| Production single-machine | STDIO |
| Remote tools | HTTP |
| Multiple clients | HTTP |
| Cloud deployment | HTTP |
| Low latency critical | STDIO |

**Hybrid:**
```python
# Local tools via STDIO
local_client = MCPClient.stdio("./local_tools.py")

# Remote tools via HTTP
remote_client = MCPClient.http("https://api.company.com/mcp")
```

---

### 54. What are MCP prompts and when should you use them?

**Answer:**

**MCP Prompts** are pre-defined prompt templates that servers can offer to clients.

**Example:**
```python
from mcp.types import Prompt, PromptMessage

class CodeReviewServer(Server):
    async def list_prompts(self):
        return [
            Prompt(
                name="code_review",
                description="Review code for issues",
                arguments=[
                    {"name": "language", "description": "Programming language", "required": True},
                    {"name": "code", "description": "Code to review", "required": True}
                ]
            ),
            Prompt(
                name="security_audit",
                description="Security-focused code review",
                arguments=[
                    {"name": "code", "description": "Code to audit", "required": True}
                ]
            )
        ]
    
    async def get_prompt(self, name, arguments):
        if name == "code_review":
            return [
                PromptMessage(
                    role="system",
                    content={
                        "type": "text",
                        "text": f"""You are an expert {arguments['language']} code reviewer.
                        Analyze this code for:
                        - Bugs and logical errors
                        - Performance issues
                        - Code style and best practices
                        - Potential improvements"""
                    }
                ),
                PromptMessage(
                    role="user",
                    content={
                        "type": "text",
                        "text": f"Review this code:\n\n```{arguments['language']}\n{arguments['code']}\n```"
                    }
                )
            ]
```

**Client Usage:**
```python
# List available prompts
prompts = await client.list_prompts()

# Get a prompt
prompt_messages = await client.get_prompt("code_review", {
    "language": "python",
    "code": "def foo():\n    return bar"
})

# Use with LLM
response = await llm.generate(prompt_messages)
```

**When to use:**
- ✅ Domain-specific tasks (code review, data analysis)
- ✅ Consistent prompt engineering across users
- ✅ Complex multi-step prompts
- ✅ When server has domain expertise

**Benefits:**
- Centralized prompt management
- Domain experts create prompts
- Easy to update/improve
- Consistent results

**UTCP Equivalent:**
UTCP doesn't have built-in prompt support, but you could model it as a tool:
```json
{
  "name": "get_code_review_prompt",
  "description": "Get optimized prompt for code review",
  "returns_prompt": true
}
```

---

**Related Resources:**
- [Protocol Comparison](../docs/06-protocol-comparison.md)
- [UTCP Tutorial](../protocols/utcp/tutorial.md)
- [MCP Tutorial](../protocols/mcp/tutorial.md)
- [Back to Main Questions](README.md)
