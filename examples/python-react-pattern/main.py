"""
ReAct Pattern Agent - Explicit Implementation

This example shows the ReAct (Reasoning + Acting) pattern in action.
The agent alternates between thinking and acting until it completes the task.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AgentStep:
    """Single step in the ReAct loop"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    is_final: bool = False


class ReactAgent:
    """Reactive agent using Reasoning + Acting pattern"""
    
    def __init__(self, tools: Dict[str, Callable], max_iterations: int = 10):
        self.tools = tools
        self.max_iterations = max_iterations
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history: List[AgentStep] = []
    
    def run(self, query: str, verbose: bool = True) -> str:
        """
        Execute the ReAct loop to answer the query
        
        Args:
            query: User's question or request
            verbose: Whether to print detailed execution trace
            
        Returns:
            Final answer string
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"🎯 TASK: {query}")
            print(f"{'='*70}\n")
        
        self.conversation_history = []
        
        for iteration in range(self.max_iterations):
            if verbose:
                print(f"\n{'─'*70}")
                print(f"🔄 Iteration {iteration + 1}/{self.max_iterations}")
                print(f"{'─'*70}")
            
            # Build prompt with history
            prompt = self._build_prompt(query)
            
            # Get LLM response
            if verbose:
                print("\n💭 Agent is thinking...")
            
            response = self._call_llm(prompt)
            
            # Parse response into structured step
            step = self._parse_response(response)
            self.conversation_history.append(step)
            
            if verbose:
                print(f"\n💡 Thought: {step.thought}")
            
            # Check if agent has final answer
            if step.is_final:
                final_answer = step.action_input.get('answer', '')
                if verbose:
                    print(f"\n{'='*70}")
                    print(f"✅ FINAL ANSWER: {final_answer}")
                    print(f"{'='*70}\n")
                return final_answer
            
            # Execute action if specified
            if step.action:
                if verbose:
                    print(f"🔧 Action: {step.action}")
                    print(f"📋 Input: {json.dumps(step.action_input, indent=2)}")
                
                observation = self._execute_action(step.action, step.action_input)
                step.observation = observation
                
                if verbose:
                    print(f"👁️  Observation: {observation}")
        
        # Max iterations reached
        return "Sorry, I reached the maximum number of iterations without completing the task."
    
    def _build_prompt(self, query: str) -> str:
        """Build the prompt for the LLM including instructions and history"""
        
        # System instructions
        system = f"""You are a helpful AI assistant that uses tools to accomplish tasks.

You MUST follow this EXACT format for each step:

Thought: [Think about what to do next]
Action: [Name of the tool to use]
Action Input: [JSON object with tool parameters]

After you use a tool, I will provide:
Observation: [Result from the tool]

Then you continue with another Thought/Action/Observation cycle.

When you have enough information to answer:
Thought: I now know the final answer
Action: Final Answer
Action Input: {{"answer": "your final answer here"}}

AVAILABLE TOOLS:
{self._format_tool_descriptions()}

RULES:
- Always start with "Thought:"
- Use ONLY the tools listed above
- Action Input MUST be valid JSON
- Be concise and focused
- Don't make assumptions about tool outputs

Let's begin!

"""
        
        # Add query and history
        conversation = f"Question: {query}\n\n"
        
        for step in self.conversation_history:
            conversation += f"Thought: {step.thought}\n"
            if step.action:
                conversation += f"Action: {step.action}\n"
                conversation += f"Action Input: {json.dumps(step.action_input)}\n"
            if step.observation:
                conversation += f"Observation: {step.observation}\n"
        
        return system + conversation
    
    def _call_llm(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content
    
    def _parse_response(self, response: str) -> AgentStep:
        """Parse LLM response into structured AgentStep"""
        
        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else response
        
        # Extract Action
        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        action = action_match.group(1).strip() if action_match else None
        
        # Extract Action Input
        action_input = None
        if action:
            input_match = re.search(r"Action Input:\s*(\{.+?\})", response, re.DOTALL | re.IGNORECASE)
            if input_match:
                try:
                    action_input = json.loads(input_match.group(1))
                except json.JSONDecodeError:
                    # Try to extract as simple string
                    action_input = {"input": input_match.group(1).strip()}
        
        # Check if this is the final answer
        is_final = False
        if action and "final answer" in action.lower():
            is_final = True
        
        return AgentStep(
            thought=thought,
            action=action,
            action_input=action_input or {},
            is_final=is_final
        )
    
    def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        """Execute a tool and return the observation"""
        
        # Normalize action name
        action = action.strip()
        
        # Check if tool exists
        if action not in self.tools:
            return f"Error: Tool '{action}' not found. Available tools: {list(self.tools.keys())}"
        
        # Execute tool
        try:
            tool_func = self.tools[action]
            result = tool_func(**action_input)
            return str(result)
        except Exception as e:
            return f"Error executing {action}: {str(e)}"
    
    def _format_tool_descriptions(self) -> str:
        """Format tool descriptions for the prompt"""
        descriptions = []
        for name, func in self.tools.items():
            # Get function docstring
            doc = func.__doc__ or "No description available"
            # Clean up docstring
            doc = doc.strip().split('\n')[0]  # First line only
            descriptions.append(f"- {name}: {doc}")
        return "\n".join(descriptions)


# ============================================================================
# EXAMPLE TOOLS
# ============================================================================

def calculator(expression: str) -> float:
    """Evaluates mathematical expressions. Example: calculator(expression='2 + 2')"""
    try:
        # WARNING: eval is dangerous in production! Use a safe math parser instead
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def get_weather(location: str, units: str = "celsius") -> Dict[str, Any]:
    """Gets current weather for a location. Example: get_weather(location='Paris', units='celsius')"""
    # Mock implementation - in real world, call actual API
    weather_data = {
        "paris": {"temp": 18, "condition": "cloudy", "humidity": 65},
        "london": {"temp": 15, "condition": "rainy", "humidity": 80},
        "new york": {"temp": 22, "condition": "sunny", "humidity": 50},
        "tokyo": {"temp": 25, "condition": "partly cloudy", "humidity": 60},
    }
    
    location_lower = location.lower()
    if location_lower in weather_data:
        data = weather_data[location_lower].copy()
        data["location"] = location
        data["units"] = units
        return data
    else:
        return {"error": f"Weather data not available for {location}"}


def search_web(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """Searches the web and returns top results. Example: search_web(query='Python tutorials', num_results=3)"""
    # Mock implementation - in real world, call actual search API
    results = [
        {
            "title": f"Result 1 for: {query}",
            "snippet": "This is a relevant search result about the query.",
            "url": "https://example.com/1"
        },
        {
            "title": f"Result 2 for: {query}",
            "snippet": "Another helpful page with information on this topic.",
            "url": "https://example.com/2"
        },
        {
            "title": f"Result 3 for: {query}",
            "snippet": "A comprehensive guide covering various aspects.",
            "url": "https://example.com/3"
        }
    ]
    return results[:num_results]


def get_current_time(timezone: str = "UTC") -> str:
    """Gets current time in specified timezone. Example: get_current_time(timezone='America/New_York')"""
    from datetime import datetime
    import pytz
    
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error: {e}. Use standard timezone names like 'America/New_York'"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    """Run example queries"""
    
    print("\n" + "="*70)
    print("🤖 ReAct Pattern Agent - Interactive Demo")
    print("="*70)
    
    # Define available tools
    tools = {
        "calculator": calculator,
        "get_weather": get_weather,
        "search_web": search_web,
        "get_current_time": get_current_time
    }
    
    # Create agent
    agent = ReactAgent(tools=tools, max_iterations=10)
    
    # Example queries
    examples = [
        "What's the weather in Paris and London? Which one is warmer?",
        "Calculate 15% tip on a $42.50 bill",
        "What's 25 * 4 + 10?",
    ]
    
    print("\n📋 Running example queries...\n")
    
    for i, query in enumerate(examples, 1):
        print(f"\n{'#'*70}")
        print(f"Example {i}/{len(examples)}")
        print(f"{'#'*70}")
        
        try:
            result = agent.run(query, verbose=True)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        if i < len(examples):
            input("\n⏸️  Press Enter to continue to next example...")
    
    # Interactive mode
    print(f"\n{'#'*70}")
    print("💬 Interactive Mode - Ask your own questions!")
    print("{'#'*70}")
    print("\nType 'exit' or 'quit' to end\n")
    
    while True:
        try:
            user_query = input("You: ").strip()
            
            if user_query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if not user_query:
                continue
            
            result = agent.run(user_query, verbose=True)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()

