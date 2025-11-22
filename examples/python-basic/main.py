"""
Simple Calculator Agent Example

This is a minimal example showing how an AI agent can use a calculator tool.
Perfect for understanding the basics of tool-calling.
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression.
    
    Args:
        expression: A valid Python mathematical expression (e.g., "2 + 2" or "10 * 5")
        
    Returns:
        The result as a string, or an error message if evaluation fails
    """
    try:
        # Evaluate the expression safely (note: eval can be dangerous in production!)
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


# Define tool schema for the LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "Evaluates mathematical expressions. "
                "Use this for any calculation. "
                "Supports +, -, *, /, **, sqrt, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "A valid Python mathematical expression. "
                            "Examples: '2 + 2', '10 * 5', '100 ** 0.5'"
                        )
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


def run_agent(user_message: str, verbose: bool = True):
    """
    Run the agent with a user message.
    
    Args:
        user_message: The user's question or request
        verbose: Whether to print detailed information
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"User: {user_message}")
        print(f"{'='*60}\n")
    
    # Initialize conversation
    messages = [{"role": "user", "content": user_message}]
    
    # First LLM call - agent decides what to do
    if verbose:
        print("🤔 Agent is thinking...")
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto"  # Let model decide whether to use tool
    )
    
    response_message = response.choices[0].message
    
    # Check if the model wants to call a tool
    if response_message.tool_calls:
        if verbose:
            print("🔧 Agent decided to use a tool!\n")
        
        # Add the assistant's response to messages
        messages.append(response_message)
        
        # Process each tool call
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if verbose:
                print(f"📞 Calling: {function_name}")
                print(f"📋 Arguments: {function_args}")
            
            # Execute the function
            if function_name == "calculator":
                function_response = calculator(function_args["expression"])
            else:
                function_response = f"Unknown function: {function_name}"
            
            if verbose:
                print(f"✅ Result: {function_response}\n")
            
            # Add function response to messages
            messages.append({
                "role": "tool",
                "content": function_response,
                "tool_call_id": tool_call.id
            })
        
        # Second LLM call - get final answer
        if verbose:
            print("🤔 Agent is formulating final response...")
        
        final_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        final_message = final_response.choices[0].message.content
    else:
        # No tool was needed
        final_message = response_message.content
        if verbose:
            print("💭 Agent answered directly (no tool needed)\n")
    
    if verbose:
        print(f"{'='*60}")
        print(f"Agent: {final_message}")
        print(f"{'='*60}\n")
    
    return final_message


def main():
    """Run several example queries"""
    
    print("\n🤖 Simple Calculator Agent")
    print("=" * 60)
    print("This agent can perform mathematical calculations.")
    print("Watch how it decides when to use the calculator tool!")
    print("=" * 60)
    
    # Example queries
    examples = [
        "What is 25 * 4 + 10?",
        "Calculate the square root of 144",
        "What is 2 to the power of 10?",
        "Hello! How are you today?",  # No calculation needed
        "If I have 5 apples and buy 3 more, then give away 2, how many do I have?"
    ]
    
    for query in examples:
        try:
            run_agent(query, verbose=True)
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
    
    # Interactive mode
    print("\n" + "="*60)
    print("💡 Try your own questions! (type 'exit' to quit)")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye! 👋\n")
                break
            
            if user_input:
                run_agent(user_input, verbose=True)
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋\n")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()

