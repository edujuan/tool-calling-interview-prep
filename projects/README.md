# Projects

End-to-end project tutorials that combine multiple concepts into complete, working applications.

## 🎯 Available Projects

### Beginner Projects (⭐)

| Project | Description | Skills | Time |
|---------|-------------|--------|------|
| [Calculator Agent](calculator-agent/) | Simple multi-operation calculator | Basic tool-calling, ReAct pattern | 1-2 hours |
| [Weather Dashboard](weather-dashboard/) | Get weather for multiple cities | API integration, UTCP | 2-3 hours |
| [File Assistant](file-assistant/) | Read and search local files | MCP, file operations | 2-3 hours |

### Intermediate Projects (⭐⭐)

| Project | Description | Skills | Time |
|---------|-------------|--------|------|
| [Data Analyst Bot](data-analyst-bot/) | Analyze CSV data, generate reports | Multi-tool, data processing | 4-6 hours |
| [Customer Support Assistant](customer-support-assistant/) | Search KB, query CRM, create tickets | UTCP + MCP, complex workflows | 5-7 hours |
| [Code Review Agent](code-review-agent/) | Review PRs, suggest improvements | GitHub API, analysis | 4-6 hours |

### Advanced Projects (⭐⭐⭐)

| Project | Description | Skills | Time |
|---------|-------------|--------|------|
| [DevOps Copilot](devops-copilot/) | Deploy, monitor, manage services | CLI tools, sandboxing, security | 8-10 hours |
| [Research Assistant](research-assistant/) | Search web, summarize, cite sources | Multi-step planning, web scraping | 8-10 hours |
| [Multi-Agent System](multi-agent-system/) | Collaborative agents | Architecture, coordination | 10-12 hours |

## 📋 Project Structure

Each project includes:

```
project-name/
├── README.md              # Complete tutorial
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── src/                  # Source code
│   ├── agent.py         # Main agent logic
│   ├── tools/           # Tool implementations
│   └── utils/           # Helper functions
├── config/              # Configuration
│   ├── utcp-manuals/    # UTCP tool manuals
│   └── settings.json    # App settings
├── tests/               # Tests
│   └── test_agent.py
├── docs/                # Additional documentation
│   └── architecture.md
└── data/                # Sample data (if needed)
    └── sample.csv
```

## 🚀 Quick Start

### General Setup

```bash
# 1. Choose a project
cd projects/data-analyst-bot

# 2. Read the README
cat README.md

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run the project
python src/main.py
```

## 📖 Learning Paths

### Path 1: Learn by Difficulty

**Week 1 - Basics:**
1. Calculator Agent (understand tool-calling)
2. Weather Dashboard (learn UTCP)
3. File Assistant (learn MCP)

**Week 2 - Intermediate:**
4. Data Analyst Bot (multi-tool coordination)
5. Customer Support Assistant (real-world workflow)

**Week 3 - Advanced:**
6. DevOps Copilot (security and sandboxing)
7. Multi-Agent System (architecture at scale)

### Path 2: Learn by Interest

**For Data/Analytics:**
1. Calculator Agent → Data Analyst Bot → Research Assistant

**For DevOps:**
1. File Assistant → Code Review Agent → DevOps Copilot

**For Customer Service:**
1. Weather Dashboard → Customer Support Assistant → Multi-Agent System

## 🎓 What You'll Learn

### Technical Skills

**Tool-Calling:**
- Defining tools
- Tool selection logic
- Error handling
- Result parsing

**Protocols:**
- UTCP manual creation
- MCP server integration
- Protocol comparison

**Agent Architectures:**
- ReAct pattern
- Plan-and-Execute
- Multi-Agent systems

**Production Skills:**
- Error handling
- Logging and monitoring
- Testing strategies
- Security practices

### Soft Skills

**System Design:**
- Breaking down problems
- Choosing appropriate tools
- Trade-off analysis

**Debugging:**
- Troubleshooting agent behavior
- Interpreting LLM decisions
- Fixing tool integrations

**Best Practices:**
- Code organization
- Documentation
- Testing

## 🏆 Project Showcase

### Data Analyst Bot

**What it does:**
- Loads CSV files
- Performs statistical analysis
- Generates visualizations
- Creates summary reports

**Tools used:**
- `load_csv` - Read data files
- `analyze_data` - Statistical operations
- `create_plot` - Generate charts
- `save_report` - Export results

**Key learnings:**
- Chaining multiple tools
- Handling structured data
- Error recovery
- User interaction

**[Start Project →](data-analyst-bot/)**

---

### Customer Support Assistant

**What it does:**
- Searches knowledge base
- Queries customer records
- Creates support tickets
- Sends email updates

**Tools used:**
- `search_kb` (UTCP) - Public docs
- `query_crm` (MCP) - Internal DB
- `create_ticket` (MCP) - Ticketing system
- `send_email` (UTCP) - Email API

**Key learnings:**
- Hybrid UTCP/MCP
- Complex workflows
- State management
- Security practices

**[Start Project →](customer-support-assistant/)**

---

### DevOps Copilot

**What it does:**
- Checks service health
- Deploys applications
- Rolls back on issues
- Sends alerts

**Tools used:**
- `check_status` - Health checks
- `deploy_service` - Deployment
- `rollback` - Revert changes
- `alert` - Notifications

**Key learnings:**
- Command-line tools
- Sandboxing
- Permission management
- Production safety

**[Start Project →](devops-copilot/)**

## 💡 Tips for Success

### Before Starting

1. **Read the full README** - Understand the goal
2. **Check prerequisites** - Ensure you have required knowledge
3. **Set up environment** - Get API keys, install tools
4. **Review examples** - Look at similar projects

### While Building

1. **Start small** - Get basic version working first
2. **Test frequently** - Verify each component
3. **Read error messages** - They're usually helpful
4. **Use logging** - Understand what's happening
5. **Iterate** - Improve gradually

### Getting Unstuck

1. **Review documentation** - Check [docs](../docs/)
2. **Look at examples** - See [examples](../examples/)
3. **Ask questions** - Use GitHub Discussions
4. **Simplify** - Remove complexity to isolate issues
5. **Take breaks** - Fresh perspective helps

## 🔧 Common Issues

### Issue: API Rate Limits

**Problem:** Hitting API rate limits during testing

**Solution:**
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
def call_api_cached(endpoint, params):
    return call_api(endpoint, params)

# Add delays
import time
time.sleep(1)  # Between calls
```

### Issue: LLM Not Using Tools

**Problem:** Agent responds directly instead of calling tools

**Solution:**
- Check tool descriptions are clear
- Verify tool list is passed to LLM
- Try more explicit prompting
- Use function-calling mode if available

### Issue: Complex Error Handling

**Problem:** Agent breaks on tool failures

**Solution:**
```python
try:
    result = call_tool(name, args)
except ToolError as e:
    # Inform LLM of error so it can adapt
    result = {"error": str(e), "suggestion": "try alternative"}
```

## 🤝 Contributing Projects

Want to add a project? Great!

**Requirements:**
- ✅ Complete, working code
- ✅ Detailed README with setup
- ✅ Clear learning objectives
- ✅ Tests (at least basic ones)
- ✅ Example outputs/screenshots
- ✅ Appropriate difficulty level

**Process:**
1. Create project in your fork
2. Test thoroughly
3. Write comprehensive README
4. Submit PR
5. Address review feedback

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

## 📚 Additional Resources

**Documentation:**
- [Agent Architectures](../docs/03-agent-architectures.md)
- [Security Best Practices](../docs/11-security.md)
- [Testing Agents](../docs/18-testing.md)

**Examples:**
- [Simple Examples](../examples/)
- [Design Patterns](../design/)

**Community:**
- GitHub Discussions
- Discord Server
- Office Hours

## 🎯 Your First Project

**Recommended:** Start with [Calculator Agent](calculator-agent/)

**Why:**
- Simple concept
- Clear objectives
- Quick to complete
- Teaches fundamentals
- Foundation for complex projects

**After completing:**
- ✅ You'll understand tool-calling basics
- ✅ You'll have working code to reference
- ✅ You'll be ready for intermediate projects
- ✅ You'll have confidence to build your own

---

**Ready to build?** Pick a project and dive in! 🚀

**Questions?** Open a [Discussion](https://github.com/yourusername/ai-agent-tool-calling/discussions)


