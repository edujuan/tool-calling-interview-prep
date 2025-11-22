# MCP File Operations Example

> **Complete MCP server/client implementation for file system operations**

---

## Overview

This example demonstrates the **Model Context Protocol (MCP)** with a real-world use case: file system operations.

### What is MCP?

MCP is a standardized protocol for connecting AI agents to external tools and data sources. It uses:

- **Client-Server Architecture** - Agents connect to MCP servers
- **JSON-RPC 2.0** - Standard request/response format
- **Tool Discovery** - Servers advertise their capabilities
- **Multiple Transports** - STDIO, HTTP/SSE

---

## Architecture

```
┌─────────────────┐
│   AI Agent      │
│  (OpenAI GPT)   │
└────────┬────────┘
         │ "List all Python files"
         ▼
┌─────────────────┐
│   MCP Client    │
│  (This code)    │
└────────┬────────┘
         │ JSON-RPC over STDIO
         ▼
┌─────────────────┐
│   MCP Server    │
│ (File Ops)      │
└────────┬────────┘
         │ Safe file system access
         ▼
    [File System]
```

### Key Components

1. **MCP Server** (`mcp_server.py`)
   - Implements JSON-RPC 2.0
   - Provides file operation tools
   - Sandboxed to workspace directory
   - Security: Path validation, no directory traversal

2. **MCP Client** (`mcp_client.py`)
   - Connects to server via STDIO
   - Discovers available tools
   - Translates to OpenAI format
   - Routes tool calls to server

3. **AI Agent**
   - Uses OpenAI's function calling
   - Decides when to use tools
   - Processes tool results

---

## Features

### Available Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write content to file |
| `list_directory` | List files in directory |
| `search_files` | Search with glob patterns |
| `get_file_info` | Get file metadata |
| `create_directory` | Create new directory |

### Security Features

✅ **Sandboxed** - Operations limited to workspace directory
✅ **Path Validation** - Prevents directory traversal attacks
✅ **Error Handling** - Graceful failure messages
✅ **Read-Only Option** - Can restrict to read-only mode

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
python mcp_client.py
```

The client will automatically:
1. Start the MCP server
2. Initialize connection
3. Discover tools
4. Launch interactive mode

### Example Interactions

#### Example 1: List Files

```
You: List all files in the current directory

[Iteration 1]
  📁 Calling MCP tool: list_directory
     Arguments: {"path": "."}
     ✓ Success

AGENT: Here are the files in the current directory:

- mcp_server.py (file, 8.5 KB)
- mcp_client.py (file, 6.2 KB)
- README.md (file, 4.1 KB)
- requirements.txt (file, 0.1 KB)
```

#### Example 2: Create and Write File

```
You: Create a file called 'notes.txt' with the content 'MCP is awesome!'

[Iteration 1]
  📁 Calling MCP tool: write_file
     Arguments: {
       "path": "notes.txt",
       "content": "MCP is awesome!"
     }
     ✓ Success

AGENT: I've created the file 'notes.txt' with your content!
```

#### Example 3: Search Files

```
You: Find all Python files

[Iteration 1]
  📁 Calling MCP tool: search_files
     Arguments: {"pattern": "*.py"}
     ✓ Success

AGENT: I found 2 Python files:

1. mcp_server.py (8.5 KB)
2. mcp_client.py (6.2 KB)
```

#### Example 4: File Metadata

```
You: Get information about README.md

[Iteration 1]
  📁 Calling MCP tool: get_file_info
     Arguments: {"path": "README.md"}
     ✓ Success

AGENT: Here's the information for README.md:

- Type: file
- Size: 4,123 bytes
- Created: 2024-01-15 10:30:00
- Modified: 2024-01-15 14:22:13
- Permissions: 644
```

---

## How It Works

### 1. Server Startup

```python
# Client starts server
process = subprocess.Popen(
    ["python3", "mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)
```

### 2. Initialization

Client sends `initialize` request:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {
      "name": "file-operations-client",
      "version": "1.0.0"
    }
  }
}
```

Server responds:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {
      "name": "file-operations-server",
      "version": "1.0.0"
    }
  }
}
```

### 3. Tool Discovery

Client requests `tools/list`:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

Server returns available tools:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "read_file",
        "description": "Read the contents of a file",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": {"type": "string", "description": "..."}
          },
          "required": ["path"]
        }
      },
      // ... more tools
    ]
  }
}
```

### 4. Tool Invocation

When agent wants to use a tool:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "example.txt"
    }
  }
}
```

Server executes and responds:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"path\": \"example.txt\", \"content\": \"...\"}"
      }
    ]
  }
}
```

---

## Security

### Path Validation

The server validates all file paths to prevent directory traversal:

```python
def _validate_path(self, path: str) -> Path:
    """Prevent access outside workspace"""
    full_path = (self.workspace / path).resolve()
    
    try:
        full_path.relative_to(self.workspace)
    except ValueError:
        raise PermissionError("Access denied: path outside workspace")
    
    return full_path
```

### Attack Prevention

❌ **Blocked**: `../../../etc/passwd`
❌ **Blocked**: `/absolute/path/to/file`
✅ **Allowed**: `./subdir/file.txt`
✅ **Allowed**: `notes.txt`

### Best Practices

1. **Always validate paths** before file operations
2. **Sandbox to workspace** directory
3. **Log all operations** for audit trail
4. **Limit file sizes** for read operations
5. **Use read-only mode** when write access not needed

---

## Extending the Server

### Add Custom Tool

```python
def my_custom_tool(self, arg1: str, arg2: int) -> Dict:
    """Your tool implementation"""
    # ... logic here
    return {"result": "success"}

# Register in __init__
self.register_tool(
    name="my_custom_tool",
    description="What it does",
    parameters={
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "..."},
            "arg2": {"type": "integer", "description": "..."}
        },
        "required": ["arg1", "arg2"]
    },
    handler=self.my_custom_tool
)
```

### Example: Text Search Tool

```python
def search_in_files(self, pattern: str, query: str) -> Dict:
    """Search for text within files"""
    results = []
    
    for file_path in self.workspace.glob(pattern):
        if file_path.is_file():
            content = file_path.read_text()
            if query.lower() in content.lower():
                # Find line numbers
                lines = content.split('\n')
                matches = [
                    (i+1, line) 
                    for i, line in enumerate(lines) 
                    if query.lower() in line.lower()
                ]
                
                results.append({
                    "file": str(file_path.relative_to(self.workspace)),
                    "matches": len(matches),
                    "lines": [m[0] for m in matches[:5]]  # First 5
                })
    
    return {
        "query": query,
        "pattern": pattern,
        "files_found": len(results),
        "results": results
    }
```

---

## Comparison: MCP vs UTCP

| Feature | MCP (This Example) | UTCP |
|---------|-------------------|------|
| **Setup** | Start server process | Load JSON manual |
| **State** | Stateful (can maintain context) | Stateless |
| **Flexibility** | Custom logic possible | Limited to API spec |
| **Performance** | Extra hop (client→server→resource) | Direct (client→API) |
| **Use Case** | Complex integrations, custom tools | Simple API wrappers |

**When to use MCP:**
- Need custom business logic
- State management required
- Complex multi-step operations
- Internal tools (file system, database, etc.)

**When to use UTCP:**
- Simple REST API calls
- No state needed
- Performance critical
- External public APIs

---

## Troubleshooting

### Issue: "Server closed connection"

**Cause:** Server crashed or failed to start

**Solution:**
```bash
# Test server independently
python mcp_server.py

# Check for Python errors
python -c "import json; import sys"
```

### Issue: "Tool not found"

**Cause:** Server didn't register tool properly

**Solution:** Check server logs (stderr):
```bash
python mcp_server.py 2> server.log
```

### Issue: "Access denied: path outside workspace"

**Cause:** Trying to access file outside workspace

**Solution:** Use relative paths only:
```
✅ "notes.txt"
✅ "./subdir/file.txt"
❌ "../outside.txt"
❌ "/absolute/path"
```

---

## Advanced Topics

### HTTP/SSE Transport

Instead of STDIO, use HTTP with Server-Sent Events:

```python
# Server (using Flask)
@app.route('/mcp', methods=['POST'])
def handle_request():
    request_data = request.json
    response = server.handle_request(request_data)
    return jsonify(response)

# Client
response = requests.post(
    'http://localhost:5000/mcp',
    json=request_data
)
```

### Multiple Servers

Connect to multiple MCP servers:

```python
file_client = MCPClient(['python', 'file_server.py'])
db_client = MCPClient(['python', 'db_server.py'])

# Combine tools
all_tools = (
    file_client.get_openai_tools() +
    db_client.get_openai_tools()
)
```

### Resources and Prompts

MCP also supports:
- **Resources**: Exposed data (files, URLs, etc.)
- **Prompts**: Pre-defined prompt templates

See [MCP Specification](../../protocols/mcp/specification.md) for details.

---

## Learn More

### Documentation

- [MCP Specification](../../protocols/mcp/specification.md)
- [MCP Tutorial](../../protocols/mcp/tutorial.md)
- [MCP vs UTCP Comparison](../../protocols/comparison.md)

### Other Examples

- [UTCP Weather](../python-utcp-weather/) - UTCP approach
- [Multi-Tool Agent](../python-multi-tool/) - Hybrid MCP/UTCP
- [Security Best Practices](../../docs/04-security.md)

### External Resources

- [MCP Official Docs](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

---

## License

MIT License - See [LICENSE](../../LICENSE) for details.


