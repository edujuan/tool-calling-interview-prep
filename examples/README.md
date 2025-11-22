# Examples

This directory contains working examples of AI agents with tool-calling capabilities. Each example is self-contained and includes setup instructions.

## 📚 Available Examples

### Beginner Examples

| Example | Language | Protocol | Complexity | Time |
|---------|----------|----------|------------|------|
| [Simple Calculator Agent](python-basic/) | Python | None | ⭐ | 10 min |
| [Weather Agent (UTCP)](python-utcp-weather/) | Python | UTCP | ⭐ | 15 min |
| [File Reader (MCP)](python-mcp-files/) | Python | MCP | ⭐⭐ | 20 min |

### Intermediate Examples

| Example | Language | Protocol | Complexity | Time |
|---------|----------|----------|------------|------|
| [Multi-Tool Agent](python-multi-tool/) | Python | Both | ⭐⭐ | 30 min |
| [ReAct Pattern Agent](python-react-pattern/) | Python | None | ⭐⭐ | 30 min |
| [Planner-Executor Agent](python-planner-executor/) | Python | None | ⭐⭐⭐ | 45 min |

### Advanced Examples

| Example | Language | Protocol | Complexity | Time |
|---------|----------|----------|------------|------|
| [Error Handling Showcase](python-error-handling/) | Python | None | ⭐⭐⭐ | 45 min |
| [Streaming Agent](python-streaming/) | Python | None | ⭐⭐⭐ | 45 min |
| [Production-Ready Agent](python-production/) | Python | None | ⭐⭐⭐⭐⭐ | 1 hour |

## 🚀 Quick Start

### Prerequisites

```bash
# Python examples
python --version  # 3.10+
pip install -r requirements.txt

# TypeScript examples
node --version   # 16+
npm install
```

### Running an Example

```bash
# 1. Navigate to example directory
cd examples/python-basic

# 2. Read the README
cat README.md

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment (if needed)
cp .env.example .env
# Edit .env with your API keys

# 5. Run the example
python main.py
```

## 📂 Example Structure

Each example follows this structure:

```
example-name/
├── README.md           # Setup and explanation
├── main.py            # Main entry point
├── requirements.txt   # Dependencies
├── .env.example       # Environment template
├── tools/             # Tool definitions (if applicable)
│   ├── weather.py
│   └── calculator.py
├── utcp-manuals/      # UTCP manifests (if applicable)
│   └── tools.json
└── tests/             # Tests (if applicable)
    └── test_agent.py
```

## 🎯 Examples by Learning Goal

### Learn Basic Tool-Calling
1. [Simple Calculator Agent](python-basic/) - Minimal example
2. [Weather Agent](python-utcp-weather/) - Real API integration
3. [Multi-Tool Agent](python-multi-tool/) - Multiple tool sources

### Learn UTCP Protocol
1. [Weather Agent (UTCP)](python-utcp-weather/) - Real OpenWeatherMap API
2. [Multi-Tool UTCP](python-multi-tool/) - Hybrid MCP/UTCP usage

### Learn MCP Protocol
1. [File Reader (MCP)](python-mcp-files/) - Complete MCP server/client
2. [Multi-Tool Agent](python-multi-tool/) - Hybrid MCP/UTCP usage

### Learn Agent Architectures
1. [ReAct Agent](python-react-pattern/) - Reasoning + Acting pattern
2. [Plan-and-Execute](python-planner-executor/) - Upfront planning pattern
3. [Multi-Tool Agent](python-multi-tool/) - Tool registry pattern

### Learn Production Practices
1. [Error Handling](python-error-handling/) - Retry, circuit breaker, validation
2. [Streaming Responses](python-streaming/) - Real-time token streaming
3. [Production-Ready Agent](python-production/) - Monitoring, logging, metrics

## 💻 Example Code Snippets

### Minimal Agent (No Framework)

```python
from openai import OpenAI

client = OpenAI()

def calculator(expression: str) -> str:
    """Simple calculator tool"""
    return str(eval(expression))

# Define tool for LLM
tools = [{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluates mathematical expressions",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    }
}]

# Agent loop
messages = [{"role": "user", "content": "What is 15 * 8?"}]

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools
)

# Execute tool if called
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    result = calculator(tool_call.function.arguments["expression"])
    print(f"Result: {result}")
```

### With LangChain

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain import hub
import math

# Safe calculator function
def safe_calc(expression: str) -> str:
    """Safely evaluate math expressions"""
    try:
        safe_dict = {"__builtins__": {}, "sqrt": math.sqrt}
        return str(eval(expression, safe_dict, {}))
    except Exception as e:
        return f"Error: {str(e)}"

tools = [
    Tool(
        name="Calculator",
        func=safe_calc,
        description="For math calculations"
    )
]

# Create agent with modern LangChain API
llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = agent_executor.invoke({"input": "What is 15 * 8?"})
print(result["output"])
```

### UTCP Direct

```python
from utcp.utcp_client import UtcpClient
import asyncio

async def main():
    # Create UTCP client with configuration
    client = await UtcpClient.create(
        config={
            "manual_path": "./tools/weather.json"
        }
    )
    
    # Call tool (format: "manual_name.tool_name")
    result = await client.call_tool(
        "weather.get_weather",
        {"location": "San Francisco"}
    )
    print(result)

# Run the async function
asyncio.run(main())
```

### MCP Client

```python
from mcp import MCPClient

async def main():
    # Connect to MCP server
    client = MCPClient("http://localhost:8080")
    
    # List tools
    tools = await client.list_tools()
    
    # Call tool
    result = await client.call_tool(
        "read_file",
        {"path": "/tmp/data.txt"}
    )
    print(result)
```

## 🧪 Testing Examples

All examples include tests:

```bash
# Run tests for an example
cd examples/python-basic
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## 🔧 Common Setup Issues

### Issue: Missing API Key
```
Error: OpenAI API key not found
Solution: Create .env file with OPENAI_API_KEY=your_key
```

### Issue: Import Error
```
Error: No module named 'langchain'
Solution: pip install -r requirements.txt
```

### Issue: MCP Server Not Running
```
Error: Connection refused to localhost:8080
Solution: Start MCP server first: python server.py
```

## 📖 Learning Path

### Day 1: Basics
- Morning: Read [Introduction](../docs/01-introduction.md)
- Afternoon: Run [Simple Calculator Agent](python-basic/)
- Evening: Modify the calculator agent to add new tools

### Day 2: Protocols
- Morning: Read [UTCP Overview](../protocols/utcp/README.md)
- Afternoon: Run [Weather Agent (UTCP)](python-utcp-weather/)
- Evening: Read [MCP Overview](../protocols/mcp/README.md)

### Day 3: Building
- Morning: Run [Multi-Tool Agent](python-multi-tool/)
- Afternoon: Start [Your First Project](../projects/calculator-agent/)
- Evening: Experiment with different tools

### Day 4-5: Advanced
- Explore [Multi-Agent System](python-multi-agent/)
- Study [Production Example](python-production/)
- Build your own custom agent

## 🎓 Example Categories

### By Framework

**No Framework**: Direct API usage
- [Simple Calculator](python-basic/)

**LangChain**: Most popular agent framework
- [LangChain UTCP](langchain-utcp/)
- [LangChain MCP](langchain-mcp/)

**AutoGen**: Multi-agent systems
- [AutoGen Collaboration](python-autogen/)

### By Tool Type

**Web APIs**: External service integration
- [Weather API](python-utcp-weather/)
- [Web Search](typescript-search/)

**Local Functions**: In-process tools
- [Calculator](python-basic/)
- [File Operations](python-mcp-files/)

**Command-Line**: System command execution
- [Shell Tools](python-cli-tools/)
- [Git Operations](python-git-agent/)

**Databases**: Data queries
- [SQL Agent](python-database/)
- [Vector DB Agent](python-vector-db/)

## 💡 Tips for Learning

1. **Start Simple**: Begin with `python-basic`, don't jump to complex examples
2. **Type It Out**: Don't just copy-paste, type the code to understand it
3. **Experiment**: Modify examples, break things, see what happens
4. **Read Docs**: Each example README explains concepts
5. **Ask Questions**: Use GitHub Discussions if you're stuck

## 🤝 Contributing Examples

Want to add an example? Great!

Requirements:
- ✅ Self-contained (works in isolation)
- ✅ Well-documented README
- ✅ Includes requirements.txt
- ✅ Has .env.example for secrets
- ✅ Includes tests (preferred)
- ✅ Clear comments in code

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

## 🔗 External Resources

- [OpenAI Cookbook](https://cookbook.openai.com/)
- [LangChain Examples](https://docs.langchain.com/docs/use_cases/agents)
- [UTCP Examples Repo](https://github.com/utcp-org/examples)
- [MCP Servers Repo](https://github.com/modelcontextprotocol/servers)

---

**Ready to start?** Pick an example and dive in! 🚀

**Questions?** Open a [Discussion](https://github.com/yourusername/ai-agent-tool-calling/discussions)

