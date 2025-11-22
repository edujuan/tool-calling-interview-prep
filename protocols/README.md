# Protocols for AI Tool-Calling

This directory contains detailed information about the two major protocols for AI tool-calling: **UTCP** and **MCP**.

## 📋 Contents

### Core Documentation
- [**UTCP Overview**](utcp/README.md) - Universal Tool Calling Protocol
- [**MCP Overview**](mcp/README.md) - Model Context Protocol  
- [**UTCP vs MCP Comparison**](comparison.md) - When to use which

### Protocol Details
- [UTCP Specification Deep Dive](utcp/specification.md)
- [MCP Specification Deep Dive](mcp/specification.md)
- [Protocol Interoperability](interoperability.md)

## 🎯 Quick Comparison

| Aspect | UTCP | MCP |
|--------|------|-----|
| **Philosophy** | Direct & Simple | Centralized & Controlled |
| **Architecture** | Stateless, direct calls | Client-Server with state |
| **Setup** | JSON manual file | Server process required |
| **Latency** | Lower (no proxy) | Higher (extra hop) |
| **Governance** | Native tool security | Centralized control point |
| **Learning Curve** | Easier (standard web tech) | Steeper (new concepts) |
| **Best For** | Quick integrations, performance | Enterprise governance, complex workflows |

## 🚀 When to Choose UTCP

Choose UTCP when you need:

- ✅ **Low latency** - Direct API calls without intermediaries
- ✅ **Quick integration** - Existing APIs with OpenAPI specs
- ✅ **Flexibility** - Support for HTTP, CLI, GraphQL, gRPC, etc.
- ✅ **Simplicity** - No server infrastructure to maintain
- ✅ **Scale** - Hundreds or thousands of tools
- ✅ **Native security** - Leverage existing API authentication

**Example Use Cases:**
- Public API integration (weather, maps, search)
- Microservices architectures
- Developer tools and CLIs
- High-performance applications

## 🏢 When to Choose MCP

Choose MCP when you need:

- ✅ **Centralized control** - Single point for authentication and policies
- ✅ **Stateful sessions** - Maintain context across multiple calls
- ✅ **Rich features** - Resources, prompts, and bidirectional communication
- ✅ **Enterprise governance** - Unified logging, monitoring, and access control
- ✅ **Complex workflows** - Multi-step operations with maintained state
- ✅ **Vendor support** - Backed by Anthropic with growing ecosystem

**Example Use Cases:**
- Enterprise internal tools
- Long-running agent sessions
- Tools requiring complex state management
- Environments needing strict compliance and auditing

## 📖 Learning Path

### Beginner
1. Read [UTCP Overview](utcp/README.md) first (simpler concept)
2. Try the [Basic UTCP Example](../examples/utcp-basic/)
3. Read [MCP Overview](mcp/README.md)
4. Try the [Basic MCP Example](../examples/mcp-basic/)
5. Review [Comparison](comparison.md) to understand trade-offs

### Intermediate
1. Study [UTCP Specification](utcp/specification.md)
2. Study [MCP Specification](mcp/specification.md)
3. Explore [Protocol Interoperability](interoperability.md)
4. Build projects using both protocols

### Advanced
1. Implement custom UTCP manuals
2. Build custom MCP servers
3. Create hybrid systems using both protocols
4. Contribute to protocol specifications

## 🔧 Quick Start Examples

### UTCP Example

```python
from utcp import UTCPClient

# Load tool manual
client = UTCPClient()
client.load_manual("https://api.example.com/utcp-manual.json")

# List available tools
tools = client.list_tools()
print(tools)  # ['weather_api', 'geocode', ...]

# Call a tool directly
result = client.call_tool(
    "weather_api",
    {"location": "San Francisco"}
)
print(result)  # {"temp": 18, "condition": "foggy"}
```

### MCP Example

```python
from mcp import MCPClient

# Connect to MCP server
client = MCPClient("http://localhost:8080")

# Discover tools
tools = await client.list_tools()
print(tools)  # [Tool(name='database_query', ...), ...]

# Call a tool through the server
result = await client.call_tool(
    "database_query",
    {"query": "SELECT * FROM users LIMIT 10"}
)
print(result)
```

## 🔗 External Resources

### Official Documentation
- [UTCP Official Site](https://www.utcp.io/)
- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [UTCP GitHub Organization](https://github.com/utcp-org)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol)

### Community
- UTCP Community Discord
- MCP Community Slack
- Discussion forums and working groups

## 🤝 Contributing

Both UTCP and MCP are evolving standards. If you:
- Find errors in our documentation
- Have implementation feedback
- Want to add examples
- Discover best practices

Please see our [Contributing Guide](../CONTRIBUTING.md).

## 📌 Key Takeaways

1. **UTCP and MCP solve the same problem differently** - enabling AI agents to use tools
2. **UTCP prioritizes simplicity and performance** - direct integration with minimal overhead
3. **MCP prioritizes governance and features** - centralized control with rich capabilities
4. **Both can coexist** - you can use both in the same system
5. **Choose based on your needs** - not on hype or trends

---

**Explore Further:**
- [UTCP Deep Dive →](utcp/README.md)
- [MCP Deep Dive →](mcp/README.md)
- [Detailed Comparison →](comparison.md)
- [Working Examples →](../examples/)


