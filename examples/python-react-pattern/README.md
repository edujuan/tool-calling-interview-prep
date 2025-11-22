# ReAct Pattern Agent Example

A complete implementation of the **ReAct (Reasoning + Acting)** agent pattern.

## What is ReAct?

ReAct is an agent architecture that alternates between:
- **Reasoning (Thought)**: The agent thinks about what to do next
- **Acting (Action)**: The agent uses a tool
- **Observing**: The agent sees the result and continues thinking

```
User Query → Thought → Action → Observation → Thought → ... → Final Answer
```

## Features

- ✅ **Complete ReAct implementation** - Full reasoning loop
- ✅ **Multiple tools** - Calculator, weather, web search, time
- ✅ **Verbose mode** - See agent's thinking process
- ✅ **Error handling** - Graceful failures
- ✅ **Interactive mode** - Ask your own questions
- ✅ **Well-documented** - Learn from the code

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Run Examples

```bash
python main.py
```

This will run through several pre-configured examples, then enter interactive mode.

### Use as Library

```python
from main import ReactAgent, calculator, get_weather

# Define tools
tools = {
    "calculator": calculator,
    "get_weather": get_weather
}

# Create agent
agent = ReactAgent(tools=tools)

# Ask question
result = agent.run("What's the weather in Paris?")
print(result)
```

## Example Execution

```
🎯 TASK: What's the weather in Paris and London? Which one is warmer?

🔄 Iteration 1/10
────────────────────────────────────────────────────────────────────────

💭 Agent is thinking...

💡 Thought: I need to get weather for both Paris and London to compare
🔧 Action: get_weather
📋 Input: {
  "location": "Paris",
  "units": "celsius"
}
👁️  Observation: {'temp': 18, 'condition': 'cloudy', 'humidity': 65, 'location': 'Paris', 'units': 'celsius'}

🔄 Iteration 2/10
────────────────────────────────────────────────────────────────────────

💭 Agent is thinking...

💡 Thought: Now I need to get weather for London
🔧 Action: get_weather
📋 Input: {
  "location": "London",
  "units": "celsius"
}
👁️  Observation: {'temp': 15, 'condition': 'rainy', 'humidity': 80, 'location': 'London', 'units': 'celsius'}

🔄 Iteration 3/10
────────────────────────────────────────────────────────────────────────

💭 Agent is thinking...

💡 Thought: I now have weather for both cities and can compare
🔧 Action: Final Answer
📋 Input: {
  "answer": "Paris is warmer at 18°C (cloudy) compared to London at 15°C (rainy). Paris is 3°C warmer."
}

======================================================================
✅ FINAL ANSWER: Paris is warmer at 18°C (cloudy) compared to London at 15°C (rainy). Paris is 3°C warmer.
======================================================================
```

## How It Works

### 1. Agent Loop

The agent runs a loop up to `max_iterations`:

```python
for iteration in range(max_iterations):
    # 1. Build prompt with history
    prompt = build_prompt(query, history)
    
    # 2. Get LLM response
    response = call_llm(prompt)
    
    # 3. Parse into structured step
    step = parse_response(response)
    
    # 4. Check if final answer
    if step.is_final:
        return step.answer
    
    # 5. Execute action
    observation = execute_action(step.action, step.input)
    
    # 6. Add to history
    history.append(step)
```

### 2. Prompt Structure

The prompt includes:
- System instructions (how to use ReAct format)
- Tool descriptions
- Conversation history (previous thoughts/actions/observations)

### 3. Response Parsing

Parses LLM output to extract:
```
Thought: [reasoning text]
Action: [tool name]
Action Input: {JSON object}
```

### 4. Tool Execution

Executes the chosen tool with provided inputs and captures the result as an observation.

## Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `calculator` | Math expressions | `calculator(expression='2 + 2')` |
| `get_weather` | Current weather | `get_weather(location='Paris')` |
| `search_web` | Web search | `search_web(query='Python')` |
| `get_current_time` | Current time | `get_current_time(timezone='UTC')` |

## Adding Your Own Tools

```python
def my_custom_tool(param1: str, param2: int) -> str:
    """Tool description here - the LLM will read this!"""
    # Your implementation
    return result

# Add to tools dict
tools = {
    "my_custom_tool": my_custom_tool,
    # ... other tools
}

agent = ReactAgent(tools=tools)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_iterations` | 10 | Max reasoning loops before stopping |
| `verbose` | True | Print execution trace |
| `model` | gpt-4 | OpenAI model to use |
| `temperature` | 0 | LLM temperature (0 = deterministic) |

## Common Issues

### "Agent reached maximum iterations"

**Cause**: Task too complex or agent is stuck in a loop

**Solutions**:
- Increase `max_iterations`
- Simplify the query
- Add more relevant tools
- Improve tool descriptions

### "Tool 'X' not found"

**Cause**: LLM hallucinated a tool name

**Solutions**:
- Make tool descriptions clearer
- Use few-shot examples in prompt
- Validate tool names before execution

### Slow execution

**Cause**: Each iteration calls the LLM API

**Solutions**:
- Use faster model (gpt-3.5-turbo)
- Implement caching
- Consider Planner-Executor pattern instead

## Learning Resources

**In this repo:**
- [Agent Architectures Guide](../../docs/03-agent-architectures.md)
- [Fundamentals](../../docs/02-fundamentals.md)
- [Planner-Executor Example](../python-planner-executor/)

**External:**
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [LangChain ReAct](https://python.langchain.com/docs/modules/agents/agent_types/react)

## Next Steps

1. ✅ Run this example
2. 📝 Read the code - it's heavily commented
3. 🔧 Add your own tools
4. 🧪 Try different queries
5. 📚 Learn about [Planner-Executor](../python-planner-executor/) pattern
6. 🚀 Build your own agent!

## License

MIT - Feel free to use in your own projects!


