# Building Your First Tool-Calling Agent

Welcome! In this tutorial, you'll build your first AI agent capable of using tools. We'll start simple and progressively add capabilities.

## What You'll Build

By the end of this tutorial, you'll have an agent that can:
- ✅ Use a calculator tool to perform math
- ✅ Fetch weather data from an API
- ✅ Chain multiple tools to solve complex tasks
- ✅ Handle errors gracefully

**Estimated time:** 30-45 minutes

---

## Prerequisites

### Knowledge Requirements
- Basic Python programming
- Understanding of APIs and HTTP requests
- Familiarity with LLMs (helpful but not required)

### Technical Requirements
```bash
# Python 3.10 or higher
python --version  # Should be 3.10+

# pip for package installation
pip --version
```

### What You'll Learn
- How tool calling works in practice
- How to define tools for an LLM
- How to create a simple agent loop
- Prompt engineering for tool use
- Using UTCP for direct API access

---

## Part 1: Setup Your Environment

### Step 1: Create a Project Directory

```bash
mkdir my-first-agent
cd my-first-agent
```

### Step 2: Set Up a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

Create a `requirements.txt`:

```txt
openai>=1.3.0
python-dotenv>=1.0.0
requests>=2.31.0
utcp>=1.0.0
```

Install:
```bash
pip install -r requirements.txt
```

### Step 4: Set Up API Keys

Create a `.env` file:

```bash
# OpenAI API key (required)
OPENAI_API_KEY=sk-your-key-here

# Weather API key (optional for Part 3)
WEATHER_API_KEY=your-openweathermap-key
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Weather: https://openweathermap.org/api (free tier available)

---

## Part 2: Your First Tool - Calculator

### Understanding Tool Structure

A tool needs three components:

```python
{
    "name": "calculator",              # Unique identifier
    "description": "What it does",     # Tells LLM when to use it
    "parameters": { ... }              # JSON Schema for inputs
}
```

### Step 1: Create the Calculator Tool

Create `agent.py`:

```python
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define our calculator tool
calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluates mathematical expressions. Use for any calculation.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A valid Python mathematical expression (e.g., '2 + 2', '100 / 5')"
                }
            },
            "required": ["expression"]
        }
    }
}

# Tool implementation
def calculator(expression: str) -> dict:
    """Safely evaluate a mathematical expression."""
    try:
        # Use eval cautiously - only for math expressions
        # In production, use a math parser library like 'ast' or 'simpleeval'
        result = eval(expression, {"__builtins__": {}}, {})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

# Tool registry
TOOLS = {
    "calculator": calculator
}
```

### Step 2: Create the Agent Loop

Add to `agent.py`:

```python
def run_agent(user_message: str, max_iterations: int = 5):
    """
    Main agent loop - handles conversation with tool calling.
    
    Args:
        user_message: The user's query
        max_iterations: Maximum tool calls allowed (prevents infinite loops)
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to tools. Use them when needed."},
        {"role": "user", "content": user_message}
    ]
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call LLM with available tools
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=[calculator_tool],
            tool_choice="auto"  # Let the model decide
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        # Check if LLM wants to call a tool
        if message.tool_calls:
            # Process each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"\n🔧 Tool Call: {tool_name}")
                print(f"   Arguments: {tool_args}")
                
                # Execute the tool
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](**tool_args)
                    print(f"   Result: {result}")
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                else:
                    print(f"   ❌ Unknown tool: {tool_name}")
            
            # Continue loop to let LLM process tool results
            continue
        
        # No tool calls - LLM has final answer
        if message.content:
            return message.content
        
    return "⚠️ Max iterations reached"


# Main execution
if __name__ == "__main__":
    print("🤖 Agent ready! Ask me anything...\n")
    
    # Test queries
    queries = [
        "What is 25 * 4?",
        "If I have $150 and spend $47.50, how much do I have left?",
        "What's the square root of 144?",
    ]
    
    for query in queries:
        print(f"👤 User: {query}")
        response = run_agent(query)
        print(f"🤖 Agent: {response}\n")
        print("-" * 60 + "\n")
```

### Step 3: Run Your First Agent!

```bash
python agent.py
```

**Expected Output:**
```
🤖 Agent ready! Ask me anything...

👤 User: What is 25 * 4?

🔧 Tool Call: calculator
   Arguments: {'expression': '25 * 4'}
   Result: {'result': 100}

🤖 Agent: 25 multiplied by 4 equals 100.

------------------------------------------------------------
```

### 🎉 Congratulations!

You just created your first tool-calling agent! Let's understand what happened:

1. **User asks a question** requiring calculation
2. **LLM decides** to use the calculator tool
3. **Agent executes** the tool with extracted arguments
4. **Result goes back** to the LLM
5. **LLM formulates** a natural language response

---

## Part 3: Adding an External API (Weather)

Now let's add a real-world API using UTCP.

### Step 1: Create UTCP Weather Manual

Create `weather_manual.json`:

```json
{
  "manual_version": "1.0.0",
  "utcp_version": "1.0.1",
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a specific city. Returns temperature, conditions, humidity.",
      "inputs": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name (e.g., 'London', 'New York', 'Tokyo')"
          },
          "units": {
            "type": "string",
            "description": "Temperature units",
            "enum": ["metric", "imperial"],
            "default": "metric"
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "http_method": "GET",
        "query_params": {
          "q": "${location}",
          "units": "${units}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    }
  ],
  "auth": {
    "auth_type": "api_key",
    "api_key": "${WEATHER_API_KEY}",
    "var_name": "appid",
    "location": "query"
  }
}
```

### Step 2: Add UTCP Client

Create `weather_tool.py`:

```python
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def get_weather(location: str, units: str = "metric") -> dict:
    """
    Fetch weather data using OpenWeatherMap API.
    
    Args:
        location: City name
        units: 'metric' (Celsius) or 'imperial' (Fahrenheit)
    
    Returns:
        Weather data dictionary
    """
    api_key = os.getenv("WEATHER_API_KEY")
    
    if not api_key:
        return {"error": "WEATHER_API_KEY not configured"}
    
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "units": units,
            "appid": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant information
        return {
            "location": data["name"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "units": "°C" if units == "metric" else "°F"
        }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except KeyError as e:
        return {"error": f"Unexpected API response format: {str(e)}"}
```

### Step 3: Update Agent with Weather Tool

Update `agent.py` to include weather:

```python
from weather_tool import get_weather

# Add weather tool definition
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a specific city. Returns temperature, conditions, humidity.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name (e.g., 'London', 'New York', 'Tokyo')"
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units: 'metric' (Celsius) or 'imperial' (Fahrenheit)",
                    "enum": ["metric", "imperial"],
                    "default": "metric"
                }
            },
            "required": ["location"]
        }
    }
}

# Update tool registry
TOOLS = {
    "calculator": calculator,
    "get_weather": get_weather
}

# Update the run_agent function to include both tools
def run_agent(user_message: str, max_iterations: int = 5):
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to tools. Use them when needed."},
        {"role": "user", "content": user_message}
    ]
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=[calculator_tool, weather_tool],  # Both tools!
            tool_choice="auto"
        )
        
        # ... rest of the loop remains the same
```

### Step 4: Test Multi-Tool Agent

Update the test queries:

```python
if __name__ == "__main__":
    print("🤖 Agent ready with Calculator and Weather tools!\n")
    
    queries = [
        "What is 25 * 4?",
        "What's the weather like in Tokyo?",
        "If it's 20°C in Paris, what is that in Fahrenheit? First check the weather.",
    ]
    
    for query in queries:
        print(f"👤 User: {query}")
        response = run_agent(query)
        print(f"🤖 Agent: {response}\n")
        print("-" * 60 + "\n")
```

**Expected Output:**
```
👤 User: If it's 20°C in Paris, what is that in Fahrenheit? First check the weather.

🔧 Tool Call: get_weather
   Arguments: {'location': 'Paris', 'units': 'metric'}
   Result: {'location': 'Paris', 'temperature': 20, 'humidity': 65, 'description': 'clear sky', 'units': '°C'}

🔧 Tool Call: calculator
   Arguments: {'expression': '20 * 9/5 + 32'}
   Result: {'result': 68.0}

🤖 Agent: The current temperature in Paris is 20°C with clear skies. 
Converting to Fahrenheit: 20°C equals 68°F.
```

### 🎉 Congratulations!

Your agent can now:
- Use multiple tools
- Chain tools together (weather → calculation)
- Handle real-world APIs

---

## Part 4: Understanding the Agent Loop

Let's visualize what's happening:

```
┌─────────────────────────────────────────────────────────┐
│  USER: "What's the weather in Paris?"                   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  AGENT: Send to LLM with available tools                │
│  - calculator                                            │
│  - get_weather                                           │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  LLM DECISION:                                           │
│  "I need to use get_weather tool"                       │
│  Arguments: {"location": "Paris", "units": "metric"}    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  AGENT: Execute get_weather("Paris", "metric")          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  TOOL: Call OpenWeatherMap API                          │
│  Returns: {"temperature": 20, "description": "cloudy"}  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  AGENT: Send result back to LLM                         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  LLM: Process result, formulate response                │
│  "The weather in Paris is 20°C and cloudy."             │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  USER: Receives natural language answer                 │
└─────────────────────────────────────────────────────────┘
```

**Key Points:**

1. **LLM Decides:** The model chooses which tool to use based on descriptions
2. **Agent Executes:** Your code runs the actual tool function
3. **Iterative:** Process repeats until LLM has enough info
4. **Safety:** `max_iterations` prevents infinite loops

---

## Part 5: Error Handling

Let's make our agent more robust:

```python
def run_agent(user_message: str, max_iterations: int = 5):
    """Agent loop with improved error handling."""
    
    messages = [
        {"role": "system", "content": """You are a helpful assistant with access to tools.
        
Guidelines:
- Use tools when you need external data or computations
- If a tool returns an error, explain it to the user
- If you're unsure, ask for clarification rather than guessing
"""},
        {"role": "user", "content": user_message}
    ]
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=[calculator_tool, weather_tool],
                tool_choice="auto",
                timeout=30  # Add timeout
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        print(f"   ❌ Invalid JSON arguments for {tool_name}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"error": "Invalid arguments format"})
                        })
                        continue
                    
                    print(f"\n🔧 Tool Call: {tool_name}")
                    print(f"   Arguments: {tool_args}")
                    
                    if tool_name in TOOLS:
                        try:
                            result = TOOLS[tool_name](**tool_args)
                            print(f"   ✅ Result: {result}")
                        except Exception as e:
                            result = {"error": f"Tool execution failed: {str(e)}"}
                            print(f"   ❌ Error: {result}")
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                    else:
                        print(f"   ❌ Unknown tool: {tool_name}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"error": f"Tool '{tool_name}' not found"})
                        })
                
                continue
            
            if message.content:
                return message.content
        
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    return "⚠️ Max iterations reached. The task may be too complex."
```

**What we added:**

- ✅ Timeout on API calls
- ✅ JSON parsing error handling
- ✅ Tool execution try-catch
- ✅ Better error messages to user
- ✅ Clear logging

---

## Part 6: Making It Interactive

Let's add a CLI for real conversations:

```python
def interactive_mode():
    """Run agent in interactive mode."""
    print("🤖 Interactive Agent (type 'exit' to quit)\n")
    print("Available tools:")
    print("  📊 calculator - Perform math calculations")
    print("  🌤️  get_weather - Get current weather for any city")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print()  # Blank line before tool calls
            response = run_agent(user_input)
            print(f"\n🤖 Agent: {response}\n")
            print("-" * 60)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    # Choose mode
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        # Run test queries
        print("🤖 Running test queries...\n")
        queries = [
            "What is 25 * 4?",
            "What's the weather like in Tokyo?",
            "If it's currently 15°C in London, what's that in Fahrenheit?",
        ]
        
        for query in queries:
            print(f"👤 User: {query}")
            response = run_agent(query)
            print(f"🤖 Agent: {response}\n")
            print("-" * 60 + "\n")
```

**Run it:**

```bash
# Test mode (default)
python agent.py

# Interactive mode
python agent.py --interactive
```

**Interactive Example:**
```
🤖 Interactive Agent (type 'exit' to quit)

Available tools:
  📊 calculator - Perform math calculations
  🌤️  get_weather - Get current weather for any city

👤 You: What's warmer, Paris or London?

🔧 Tool Call: get_weather
   Arguments: {'location': 'Paris', 'units': 'metric'}
   ✅ Result: {'location': 'Paris', 'temperature': 18, ...}

🔧 Tool Call: get_weather
   Arguments: {'location': 'London', 'units': 'metric'}
   ✅ Result: {'location': 'London', 'temperature': 15, ...}

🤖 Agent: Paris is warmer at 18°C, compared to London at 15°C.
```

---

## Part 7: Best Practices

### 1. Tool Description Quality

**❌ Bad:**
```python
"description": "Gets weather"
```

**✅ Good:**
```python
"description": "Get current weather for a specific city. Returns temperature, conditions, humidity, and wind speed. Use when user asks about weather, temperature, or climate."
```

**Why:** Better descriptions help the LLM choose the right tool.

### 2. Parameter Validation

```python
def get_weather(location: str, units: str = "metric") -> dict:
    # Validate inputs
    if not location or len(location.strip()) == 0:
        return {"error": "Location cannot be empty"}
    
    if units not in ["metric", "imperial"]:
        return {"error": f"Invalid units: {units}. Use 'metric' or 'imperial'"}
    
    # ... rest of function
```

### 3. Timeouts and Retries

```python
import time

def get_weather_with_retry(location: str, units: str = "metric", retries: int = 3) -> dict:
    """Weather API with retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return process_response(response)
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            return {"error": "Request timeout after retries"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
```

### 4. Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_agent(user_message: str, max_iterations: int = 5):
    logger.info(f"New query: {user_message}")
    
    # ... in tool execution
    logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
    result = TOOLS[tool_name](**tool_args)
    logger.info(f"Tool result: {result}")
```

### 5. Cost Monitoring

```python
def run_agent(user_message: str, max_iterations: int = 5):
    total_tokens = 0
    
    # ... in API call
    response = client.chat.completions.create(...)
    
    tokens_used = response.usage.total_tokens
    total_tokens += tokens_used
    
    logger.info(f"Tokens used: {tokens_used}, Total: {total_tokens}")
    
    # Alert if expensive
    if total_tokens > 10000:
        logger.warning(f"High token usage: {total_tokens}")
```

---

## Common Issues and Solutions

### Issue 1: Tool Not Being Called

**Symptoms:** LLM tries to answer without using tools

**Solutions:**
- ✅ Improve tool description (be more specific)
- ✅ Add examples in system prompt
- ✅ Use `tool_choice="required"` to force tool use

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=[calculator_tool],
    tool_choice="required"  # Force tool use
)
```

### Issue 2: Wrong Arguments

**Symptoms:** Tool receives incorrect or malformed arguments

**Solutions:**
- ✅ Better parameter descriptions
- ✅ Add examples in parameter description
- ✅ Validate and return clear errors

```python
"properties": {
    "expression": {
        "type": "string",
        "description": "Mathematical expression. Examples: '2+2', '10*5', '100/4'"
    }
}
```

### Issue 3: Infinite Loops

**Symptoms:** Agent keeps calling tools repeatedly

**Solutions:**
- ✅ Set reasonable `max_iterations`
- ✅ Check for repeated tool calls
- ✅ Add loop detection

```python
seen_calls = set()

for tool_call in message.tool_calls:
    call_signature = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
    
    if call_signature in seen_calls:
        logger.warning("Repeated tool call detected")
        break
    
    seen_calls.add(call_signature)
```

### Issue 4: API Rate Limits

**Symptoms:** Weather API returns 429 errors

**Solutions:**
- ✅ Implement caching
- ✅ Add rate limiting
- ✅ Use fallback data

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_weather_cached(location: str, units: str = "metric") -> dict:
    """Cached weather API (cache for 10 minutes)."""
    return get_weather(location, units)

# Clear cache every 10 minutes
def clear_cache_periodically():
    time.sleep(600)  # 10 minutes
    get_weather_cached.cache_clear()
```

---

## Next Steps

### Extend Your Agent

1. **Add More Tools:**
   - Web search (DuckDuckGo, Brave)
   - Database queries (SQLite)
   - File operations (read/write)
   - Email sending

2. **Improve the Agent:**
   - Add conversation memory
   - Implement tool chaining strategies
   - Add multi-turn conversations
   - Create specialized agents

3. **Production Ready:**
   - Add comprehensive error handling
   - Implement proper logging
   - Add monitoring and metrics
   - Deploy as an API (FastAPI)

### Learning Path

- **Next:** [08-tool-integration.md](08-tool-integration.md) - Advanced integration patterns
- **Then:** [09-prompt-engineering.md](09-prompt-engineering.md) - Optimize prompts
- **Also:** [11-security.md](11-security.md) - Security best practices

### Example Projects

Check out these complete examples:
- [python-basic](../examples/python-basic/) - Expanded version of this tutorial
- [python-multi-tool](../examples/python-multi-tool/) - Multiple tools with chaining
- [python-utcp-weather](../examples/python-utcp-weather/) - Full UTCP implementation
- [data-analyst-bot](../projects/data-analyst-bot/) - Real-world project

---

## Complete Code

Your final `agent.py` should look like this:

```python
"""
Simple tool-calling agent with calculator and weather tools.
"""
import json
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from weather_tool import get_weather

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Tool Definitions
calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluates mathematical expressions. Use for any calculation. Examples: '2+2', '100/4', '5*10'",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A valid Python mathematical expression"
                }
            },
            "required": ["expression"]
        }
    }
}

weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a specific city. Returns temperature, conditions, humidity. Use when user asks about weather.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name (e.g., 'London', 'New York')"
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units",
                    "enum": ["metric", "imperial"],
                    "default": "metric"
                }
            },
            "required": ["location"]
        }
    }
}

# Tool Implementations
def calculator(expression: str) -> dict:
    """Safely evaluate mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

# Tool Registry
TOOLS = {
    "calculator": calculator,
    "get_weather": get_weather
}

# Agent Loop
def run_agent(user_message: str, max_iterations: int = 5):
    """Main agent loop with tool calling."""
    
    messages = [
        {"role": "system", "content": """You are a helpful assistant with access to tools.

Guidelines:
- Use tools when you need external data or computations
- If a tool returns an error, explain it to the user
- Be concise but helpful
"""},
        {"role": "user", "content": user_message}
    ]
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=[calculator_tool, weather_tool],
                tool_choice="auto",
                timeout=30
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON for {tool_name}")
                        continue
                    
                    logger.info(f"Tool: {tool_name}, Args: {tool_args}")
                    print(f"\n🔧 Tool Call: {tool_name}")
                    print(f"   Arguments: {tool_args}")
                    
                    if tool_name in TOOLS:
                        try:
                            result = TOOLS[tool_name](**tool_args)
                            print(f"   ✅ Result: {result}")
                        except Exception as e:
                            result = {"error": f"Execution failed: {str(e)}"}
                            print(f"   ❌ Error: {result}")
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                    else:
                        logger.error(f"Unknown tool: {tool_name}")
                
                continue
            
            if message.content:
                return message.content
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"❌ Error: {str(e)}"
    
    return "⚠️ Max iterations reached"


def interactive_mode():
    """Interactive CLI mode."""
    print("🤖 Interactive Agent (type 'exit' to quit)\n")
    print("Available tools:")
    print("  📊 calculator - Perform math calculations")
    print("  🌤️  get_weather - Get weather for any city")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print()
            response = run_agent(user_input)
            print(f"\n🤖 Agent: {response}\n")
            print("-" * 60)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    import sys
    
    if "--interactive" in sys.argv:
        interactive_mode()
    else:
        print("🤖 Running test queries...\n")
        
        queries = [
            "What is 25 * 4?",
            "What's the weather like in Tokyo?",
            "If it's 15°C in London, what's that in Fahrenheit?",
        ]
        
        for query in queries:
            print(f"👤 User: {query}")
            response = run_agent(query)
            print(f"🤖 Agent: {response}\n")
            print("-" * 60 + "\n")
```

---

## Summary

**What you learned:**

✅ How to define tools for an LLM
✅ How to create an agent loop
✅ How to execute tools and return results
✅ How to handle errors gracefully
✅ How to integrate external APIs
✅ How to make agents interactive

**Key Takeaways:**

1. **Tools = Functions + Metadata** - LLMs need good descriptions
2. **Loop Until Done** - Agent iterates until task complete
3. **Error Handling Matters** - Real-world APIs fail
4. **Start Simple** - Add complexity incrementally

**You're now ready to:**
- Build agents for real-world tasks
- Integrate any API as a tool
- Debug and improve agent behavior
- Move to advanced patterns

---

## Resources

- **OpenAI Function Calling:** https://platform.openai.com/docs/guides/function-calling
- **UTCP Documentation:** https://www.utcp.io/
- **Example Projects:** [../examples/](../examples/)
- **Community Discord:** [Join here](#)

---

**Happy building! 🚀**

*Questions or issues? Open a GitHub issue or check the FAQ.*

