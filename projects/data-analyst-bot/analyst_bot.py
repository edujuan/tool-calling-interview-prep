#!/usr/bin/env python3
"""
Data Analyst Bot
================

An AI-powered data analyst that can load, analyze, and visualize data using natural language.

Usage:
    python analyst_bot.py
"""

import os
import json
import openai
from typing import List, Dict, Any, Optional
from tools import DataAnalystTools

class DataAnalystBot:
    """
    AI bot that analyzes data using natural language commands.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.tools = DataAnalystTools()
        self.conversation_history: List[Dict] = []
        
        print("✓ Data Analyst Bot initialized")
        print(f"  Model: {model}")
        print(f"  Available tools: {len(self.tools.get_tool_definitions())}")
    
    def chat(self, user_message: str, verbose: bool = False) -> str:
        """
        Process user message and return response.
        
        Args:
            user_message: User's question or command
            verbose: Print detailed execution log
        
        Returns:
            Bot's response
        """
        # Handle special commands
        if user_message.lower().startswith("load "):
            # Quick load command
            filepath = user_message[5:].strip()
            return self._execute_tool("load_dataset", {"filepath": filepath})
        
        # Add to conversation
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                print(f"\n[Iteration {iteration}]")
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._get_messages(),
                tools=self.tools.get_tool_definitions(),
                tool_choice="auto",
                temperature=0.1  # Low temperature for consistent data analysis
            )
            
            message = response.choices[0].message
            
            # Check for tool calls
            if message.tool_calls:
                # Add assistant message with tool calls
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # Execute tool calls
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"  🔧 {tool_name}({', '.join(f'{k}={v}' for k, v in tool_args.items())})")
                    
                    # Execute
                    result = self._execute_tool(tool_name, tool_args)
                    
                    if verbose:
                        # Show result preview
                        result_preview = result[:150] + "..." if len(result) > 150 else result
                        print(f"     → {result_preview}")
                    
                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id
                    })
                
                continue  # Next iteration
            
            else:
                # Final answer
                final_answer = message.content
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
                
                return final_answer
        
        return "I couldn't complete the analysis within the iteration limit. Please try a simpler query."
    
    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool and return result"""
        try:
            result = self.tools.execute(tool_name, arguments)
            return result
        except Exception as e:
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})
    
    def _get_messages(self) -> List[Dict]:
        """Get messages for LLM with system prompt"""
        system_prompt = """You are a data analyst AI assistant. Your role is to help users analyze data.

Guidelines:
1. Always load dataset first before analyzing
2. Use get_data_info to understand the dataset structure
3. Use appropriate tools for each task
4. Provide clear, actionable insights
5. Suggest visualizations when helpful
6. Explain your findings in plain language

When analyzing data:
- Check column names and types first
- Handle missing data appropriately
- Use correct column names in queries
- Create visualizations to support findings
- Generate reports for comprehensive analysis

Available tools: load_dataset, get_data_info, query_data, create_visualization, generate_report
"""
        
        return [
            {"role": "system", "content": system_prompt},
            *self.conversation_history
        ]
    
    def reset(self):
        """Reset conversation history"""
        self.conversation_history.clear()
        self.tools.clear_data()

def main():
    """Run the data analyst bot"""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Get your API key at: https://platform.openai.com/api-keys")
        return
    
    # Create bot
    bot = DataAnalystBot(api_key)
    
    # Welcome message
    print("\n" + "="*60)
    print("📊 Data Analyst Bot - Ready!")
    print("="*60)
    print("\nAvailable commands:")
    print("  • Ask questions about your data")
    print("  • Type 'load <file>' to load a dataset")
    print("  • Type 'reset' to start fresh")
    print("  • Type 'quit' to exit")
    print("\nExample datasets in data/:")
    print("  - sales_data.csv")
    print("  - customers.json")
    print("="*60 + "\n")
    
    # Interactive loop
    while True:
        try:
            user_input = input("💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\nGoodbye! 👋")
                break
            
            if user_input.lower() == 'reset':
                bot.reset()
                print("✓ Conversation reset\n")
                continue
            
            # Process input
            print()  # Blank line
            response = bot.chat(user_input, verbose=False)
            print(f"\n🤖 Bot: {response}\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()

