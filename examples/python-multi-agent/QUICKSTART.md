# Quick Start Guide

Get up and running with the multi-agent system in 5 minutes!

## 📦 What's Included

```
python-multi-agent/
├── main.py              # Core multi-agent implementation
├── demo.py              # Simple demo script  
├── test_multiagent.py   # Comprehensive test suite
├── README.md            # Full documentation
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
└── QUICKSTART.md        # This file
```

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
cd examples/python-multi-agent

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Test Without API Key

```bash
# Run automated tests (no API key needed)
python test_multiagent.py
```

Expected output:
```
✓ Message creation test passed
✓ Agent message sending test passed
✓ All tool functions test passed
... (11 tests)
Results: 11 passed, 0 failed
```

### 3. Run With API Key (Optional)

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...

# Run simple demo
python demo.py

# Or run full interactive demo
python main.py
```

## 🎯 Quick Test

Without API key:
```bash
python test_multiagent.py
```

With API key:
```bash
python demo.py
```

## 🤖 The Agents

The system includes 5 agents:

1. **Manager** - Coordinates the team
2. **Researcher** - Gathers information
3. **Coder** - Writes code
4. **Reviewer** - Quality checks
5. **Writer** - Creates documentation

## 💡 Example Task

```python
from main import create_software_team, Message

# Create team
manager = create_software_team()

# Assign complex task
task = Message(
    sender="user",
    receiver="manager", 
    content="Research Python decorators, write examples, review them, and document"
)

# Execute
result = manager.process(task)
print(result)
```

## 📚 What Happens

1. **Manager** analyzes task and creates delegation plan
2. **Researcher** gathers information about decorators
3. **Coder** writes example code using research
4. **Reviewer** checks code quality
5. **Writer** creates documentation
6. **Manager** synthesizes everything into final answer

## ✅ Verification

Run this to verify everything works:

```bash
# Should pass all 11 tests
python test_multiagent.py

# Should show demo message
python demo.py
```

## 🔧 Customization

### Add New Agent

```python
from main import Agent, Message

class DataAnalyst(Agent):
    def __init__(self, tools=None, verbose=True):
        super().__init__(
            name="analyst",
            role="Data Analysis Specialist",
            tools=tools,
            verbose=verbose
        )
    
    def process(self, message: Message) -> Message:
        # Your logic here
        result = self.analyze_data(message.content)
        return self.send_message(
            receiver=message.sender,
            content=result
        )
```

### Add New Tool

```python
def my_tool(param: str) -> str:
    """Tool description for LLM"""
    # Your implementation
    return result

# Give to agent
agent = ResearchAgent(tools={"my_tool": my_tool})
```

## 🐛 Troubleshooting

### Tests fail with API key error
- **Solution**: Tests don't need API key - check import errors

### "Agent not found"  
- **Solution**: Ensure agent is added to manager's workers dict

### Demo shows warning
- **Solution**: Normal if no API key - tests still work

## 📖 Next Steps

1. ✅ Run tests: `python test_multiagent.py`
2. 📝 Read full docs: `README.md`
3. 🔧 Try demo: `python demo.py` (with API key)
4. 💻 Run interactive: `python main.py` (with API key)
5. 🎨 Customize agents for your use case

## 🆘 Need Help?

- **Full Documentation**: See `README.md`
- **Code Examples**: Check `main.py` comments
- **Test Examples**: See `test_multiagent.py`
- **Architecture Guide**: `../../docs/03-agent-architectures.md`

## ⚡ TL;DR

```bash
# Install and test (no API key needed)
pip install -r requirements.txt
python test_multiagent.py

# If you have API key
cp .env.example .env
# Add your key to .env
python demo.py
```

That's it! You now have a working multi-agent system. 🎉


