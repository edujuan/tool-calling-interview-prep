# Simple Calculator Agent

A minimal example of an AI agent that can use a calculator tool. Perfect for beginners!

## What This Example Teaches

- ✅ Basic tool-calling concepts
- ✅ How LLMs decide when to use tools
- ✅ Tool definition and schemas
- ✅ The agent execution loop

## Prerequisites

- Python 3.10+
- OpenAI API key

## Setup

```bash
# 1. Navigate to this directory
cd examples/python-basic

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Running the Example

```bash
python main.py
```

Expected output:
```
User: What is 25 * 4 + 10?

Agent thinking: I need to calculate this expression
Tool called: calculator(expression="25 * 4 + 10")
Tool result: 110

Agent: The answer is 110.
```

## Code Walkthrough

### 1. Define a Tool

```python
def calculator(expression: str) -> str:
    """Evaluates a mathematical expression."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
```

**Key Points:**
- Simple Python function
- Takes a string (math expression)
- Returns a string (result)
- Handles errors gracefully

### 2. Create Tool Schema

```python
tools = [{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluates mathematical expressions. Use for any calculation.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A valid Python math expression (e.g., '2 + 2')"
                }
            },
            "required": ["expression"]
        }
    }
}]
```

**Why This Matters:**
- LLM reads the description to understand what the tool does
- Parameters schema tells LLM what arguments to provide
- Clear descriptions = better tool selection

### 3. The Agent Loop

```python
messages = [{"role": "user", "content": "What is 25 * 4 + 10?"}]

# First LLM call
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools
)

# Check if tool was called
if response.choices[0].message.tool_calls:
    # Execute tool
    tool_call = response.choices[0].message.tool_calls[0]
    result = calculator(args["expression"])
    
    # Add result to conversation
    messages.append(tool_result_message)
    
    # Second LLM call with result
    final_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
```

**The Flow:**
1. User asks a question
2. LLM decides to use calculator
3. We execute the calculator
4. LLM receives result
5. LLM formats final answer

## Experiments to Try

### 1. Add More Tools

Try adding a weather tool:

```python
def get_weather(location: str) -> str:
    """Mock weather API"""
    return f"The weather in {location} is sunny, 22°C"
```

### 2. Complex Calculations

Ask: "What is the square root of 144 plus 50?"

The agent should calculate: `144**0.5 + 50 = 62`

### 3. Error Handling

Ask: "What is abc + 123?"

See how the agent handles invalid expressions.

### 4. Multi-Step

Ask: "Calculate 10 * 5, then add 20 to that result"

Does the agent chain the calculations?

## Common Issues

### Issue: "API key not found"
**Solution:** Make sure `.env` file exists with your key:
```
OPENAI_API_KEY=sk-...
```

### Issue: "Rate limit exceeded"
**Solution:** You've hit OpenAI's rate limit. Wait a moment and try again.

### Issue: Tool not being called
**Solution:** Make sure:
- Tool description is clear
- Question requires calculation
- Model is gpt-4 or gpt-3.5-turbo-0613+

## Understanding the Output

```
User: What is 25 * 4 + 10?
```
Your question

```
Agent thinking: I need to calculate this expression
```
LLM's internal reasoning (in messages)

```
Tool called: calculator(expression="25 * 4 + 10")
```
LLM decided to use the calculator tool

```
Tool result: 110
```
Our calculator function returned this

```
Agent: The answer is 110.
```
LLM formats the final response

## Next Steps

After mastering this example:

1. **Add more tools** - Try file reading, API calls, etc.
2. **Try UTCP** - See how [UTCP Weather Example](../python-utcp-weather/) differs
3. **Add complexity** - Move to [Multi-Tool Agent](../python-multi-tool/)
4. **Build a project** - Try [Calculator Agent Project](../../projects/calculator-agent/)

## Key Takeaways

✅ Tools are just Python functions with schemas
✅ LLMs use descriptions to decide when to call tools
✅ The agent loop: Ask → Decide → Execute → Respond
✅ Clear descriptions lead to better tool selection

## Files in This Example

- `main.py` - The complete agent code
- `requirements.txt` - Python dependencies
- `.env.example` - Template for API keys
- `README.md` - This file

## Learn More

- [Tool-Calling Introduction](../../docs/01-introduction.md)
- [Fundamentals](../../docs/02-fundamentals.md)
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

