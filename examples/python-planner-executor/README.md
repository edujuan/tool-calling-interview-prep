# Planner-Executor Agent Example

A complete implementation of the **Planner-Executor** agent pattern.

## What is Planner-Executor?

Unlike ReAct which decides one step at a time, Planner-Executor:
1. **Plans** all steps upfront (creates a complete execution plan)
2. **Executes** each step in order
3. **Replans** if steps fail

```
User Query → Planner → [Step 1, Step 2, Step 3...] → Executor → Final Answer
```

## Advantages over ReAct

✅ **More efficient** - Plans ahead, no wasted iterations
✅ **Better for complex tasks** - Can see dependencies
✅ **Can parallelize** - Independent steps could run concurrently
✅ **Easier to debug** - Clear separation between planning and execution

## Features

- ✅ Complete plan-and-execute implementation
- ✅ Automatic replanning on failures
- ✅ Step dependencies support
- ✅ Reference previous step outputs
- ✅ 4 example tools (calculator, weather, database, format)
- ✅ Verbose execution trace
- ✅ Interactive mode

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

### Use as Library

```python
from main import PlannerExecutorAgent, calculator, get_weather

tools = {
    "calculator": calculator,
    "get_weather": get_weather
}

agent = PlannerExecutorAgent(tools=tools)
result = agent.run("Get weather in Paris and calculate 2+2")
print(result)
```

## Example Execution

```
🎯 TASK: Get weather in Paris and London, then calculate temperature difference

──────────────────────────────────────────────────────────────────────
📋 PLANNING PHASE (Attempt 1)
──────────────────────────────────────────────────────────────────────

📝 Execution Plan:
  1. Get weather for Paris
     Tool: get_weather
     Input: {"location": "Paris", "units": "celsius"}
  2. Get weather for London
     Tool: get_weather
     Input: {"location": "London", "units": "celsius"}
  3. Calculate temperature difference (depends on: [1, 2])
     Tool: calculator
     Input: {"expression": "$step1 - $step2"}

──────────────────────────────────────────────────────────────────────
⚙️  EXECUTION PHASE
──────────────────────────────────────────────────────────────────────

▶️  Step 1: Get weather for Paris
   ✅ Success: 18°C, cloudy
   ⏱️  Duration: 2ms

▶️  Step 2: Get weather for London
   ✅ Success: 15°C, rainy
   ⏱️  Duration: 1ms

▶️  Step 3: Calculate temperature difference
   ✅ Success: 3.0
   ⏱️  Duration: 1ms

──────────────────────────────────────────────────────────────────────
✨ SYNTHESIS PHASE
──────────────────────────────────────────────────────────────────────

💬 Paris is currently 18°C and cloudy, while London is 15°C and rainy.
    The temperature difference is 3°C, with Paris being warmer.
```

## How It Works

### Phase 1: Planning

```python
# Agent sends planning prompt to LLM
prompt = f"""
Create a step-by-step plan for: {query}
Available tools: {tools}

Return JSON:
[
  {"step": 1, "tool": "tool_name", "input": {...}, "dependencies": []},
  ...
]
"""

# LLM returns structured plan
plan = parse_llm_response(response)
```

### Phase 2: Execution

```python
for step in plan:
    # Wait for dependencies to complete
    if all_dependencies_met(step):
        # Resolve references to previous steps
        inputs = resolve_references(step.input, previous_results)
        
        # Execute tool
        result = execute_tool(step.tool, inputs)
        
        # Store for future steps
        previous_results[step.number] = result
```

### Phase 3: Replanning (if needed)

```python
if any_step_failed:
    # Create new plan considering failures
    new_plan = replan(query, failed_steps, successful_results)
    # Try again...
```

### Phase 4: Synthesis

```python
# Combine all results into final answer
answer = llm.synthesize(query, all_results)
```

## Step Dependencies

Steps can depend on previous steps:

```json
[
  {
    "step": 1,
    "description": "Get weather for Paris",
    "tool": "get_weather",
    "input": {"location": "Paris"},
    "dependencies": []
  },
  {
    "step": 2,
    "description": "Get weather for London",
    "tool": "get_weather",
    "input": {"location": "London"},
    "dependencies": []  // Can run in parallel with step 1
  },
  {
    "step": 3,
    "description": "Calculate difference",
    "tool": "calculator",
    "input": {"expression": "$step1 - $step2"},
    "dependencies": [1, 2]  // Must wait for steps 1 and 2
  }
]
```

## Referencing Previous Results

Use `$stepN` in tool inputs to reference previous step outputs:

```json
{
  "tool": "calculator",
  "input": {
    "expression": "$step1 + $step2"  // Uses outputs of steps 1 and 2
  }
}
```

## Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `calculator` | Math expressions | `calculator(expression='2 + 2')` |
| `get_weather` | Current weather | `get_weather(location='Paris')` |
| `search_database` | Query database | `search_database(query='population paris')` |
| `format_report` | Format data | `format_report(data='...', style='detailed')` |

## Adding Your Own Tools

```python
def my_tool(param1: str, param2: int) -> str:
    """Tool description - LLM reads this!
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Result description
    """
    # Your implementation
    return result

# Add to tools dict
tools = {
    "my_tool": my_tool,
    # ... other tools
}

agent = PlannerExecutorAgent(tools=tools)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_replans` | 2 | Max times to replan on failure |
| `verbose` | True | Print execution trace |
| `model` | gpt-4 | OpenAI model to use |

## Common Issues

### "Plan creation failed"

**Cause**: LLM couldn't create valid JSON plan

**Solutions**:
- Improve tool descriptions
- Simplify the query
- Use GPT-4 instead of GPT-3.5

### "Step dependencies not met"

**Cause**: Circular dependency in plan

**Solutions**:
- Check plan for circular references
- Agent should replan automatically
- May need to simplify task

### "Reference $stepN not found"

**Cause**: Step referenced before it executed

**Solutions**:
- Check step dependencies
- Ensure dependent steps list prerequisites
- Agent execution order respects dependencies

## Comparison to ReAct

| Aspect | ReAct | Planner-Executor |
|--------|-------|------------------|
| **Planning** | One step at a time | All steps upfront |
| **Efficiency** | May waste iterations | More efficient |
| **Flexibility** | Can adapt quickly | Must replan to change |
| **Complexity** | Simpler | More complex |
| **Best For** | Simple tasks | Multi-step workflows |
| **Token Usage** | Higher (many iterations) | Lower (planned) |

## When to Use Planner-Executor

✅ **Use when:**
- Multi-step tasks with clear dependencies
- Tasks that benefit from upfront planning
- Efficiency is important
- Steps can run in parallel

❌ **Don't use when:**
- Simple, single-tool tasks
- Highly dynamic situations
- Need maximum flexibility
- ReAct is sufficient

## Next Steps

1. ✅ Run this example
2. 📝 Compare execution trace to ReAct
3. 🔧 Add your own tools
4. 🧪 Try complex multi-step queries
5. 📚 Learn about [Multi-Agent Systems](../../docs/05-multi-agent.md)
6. 🚀 Build your own agent!

## See Also

- [ReAct Pattern Example](../python-react-pattern/) - Compare approaches
- [Agent Architectures](../../docs/03-agent-architectures.md) - Deep dive
- [Design Patterns](../../design/patterns.md) - Best practices

## License

MIT - Feel free to use in your own projects!

