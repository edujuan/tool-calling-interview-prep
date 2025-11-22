"""
Streaming Agent Example

Demonstrates real-time streaming responses from AI agents.
Shows tokens as they're generated, providing better UX for long responses.

Features:
- Real-time token streaming
- Progress indicators
- Tool call streaming
- Partial response handling
- Graceful error recovery during streaming
"""

import os
import sys
import json
import time
from typing import Generator, Dict, Any, List
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# STREAMING UTILITIES
# =============================================================================

class StreamingDisplay:
    """Utilities for displaying streaming content"""
    
    @staticmethod
    def print_streaming(text: str, delay: float = 0.03):
        """Print text with streaming effect"""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()  # New line at end
    
    @staticmethod
    def print_chunk(chunk: str):
        """Print a chunk without newline"""
        print(chunk, end='', flush=True)
    
    @staticmethod
    def show_spinner(message: str, duration: float = 0.5):
        """Show a temporary spinner"""
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        end_time = time.time() + duration
        i = 0
        
        while time.time() < end_time:
            print(f'\r{frames[i % len(frames)]} {message}', end='', flush=True)
            time.sleep(0.1)
            i += 1
        
        print('\r' + ' ' * (len(message) + 3) + '\r', end='', flush=True)
    
    @staticmethod
    def show_progress_bar(current: int, total: int, width: int = 40):
        """Show progress bar"""
        if total == 0:
            percent = 100
        else:
            percent = int((current / total) * 100)
        
        filled = int((width * current) / total) if total > 0 else width
        bar = '█' * filled + '░' * (width - filled)
        
        print(f'\r|{bar}| {percent}% ({current}/{total})', end='', flush=True)


# =============================================================================
# TOOLS FOR STREAMING AGENT
# =============================================================================

def search_documents(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Simulated document search (would be real in production).
    Returns results that agent can stream back to user.
    """
    # Simulate search delay
    time.sleep(0.5)
    
    documents = [
        {
            "title": f"Document about {query}",
            "content": f"This document contains detailed information about {query}. "
                      "It covers various aspects including definitions, use cases, "
                      "and best practices.",
            "relevance": 0.95
        },
        {
            "title": f"Guide to {query}",
            "content": f"A comprehensive guide explaining {query} with examples "
                      "and practical applications.",
            "relevance": 0.87
        },
        {
            "title": f"{query}: Deep Dive",
            "content": f"An in-depth analysis of {query}, exploring advanced concepts "
                      "and implementation details.",
            "relevance": 0.82
        }
    ]
    
    results = documents[:max_results]
    
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


def analyze_data(dataset: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """
    Simulated data analysis (would be real computation in production).
    """
    time.sleep(0.8)
    
    analyses = {
        "summary": {
            "mean": 42.5,
            "median": 40.0,
            "std_dev": 12.3,
            "count": 100
        },
        "trend": {
            "direction": "increasing",
            "rate": "15% per year",
            "confidence": 0.89
        },
        "forecast": {
            "next_period": 48.7,
            "confidence_interval": [45.2, 52.1],
            "model": "ARIMA"
        }
    }
    
    return {
        "dataset": dataset,
        "analysis_type": analysis_type,
        "results": analyses.get(analysis_type, analyses["summary"])
    }


def calculate_complex(expression: str) -> Dict[str, Any]:
    """
    Calculator for complex expressions.
    Simulates longer computation time.
    """
    time.sleep(0.3)
    
    try:
        result = eval(expression, {"__builtins__": {}}, {
            "abs": abs, "pow": pow, "round": round,
            "sum": sum, "min": min, "max": max
        })
        
        return {
            "expression": expression,
            "result": result,
            "success": True
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "success": False
        }


# =============================================================================
# STREAMING AGENT
# =============================================================================

class StreamingAgent:
    """
    AI agent with streaming response capabilities.
    
    Streams tokens as they're generated for better UX,
    especially for long responses.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.display = StreamingDisplay()
        self.tools_available = {
            "search_documents": search_documents,
            "analyze_data": analyze_data,
            "calculate_complex": calculate_complex
        }
    
    def chat_streaming(self, user_message: str, verbose: bool = True):
        """
        Chat with streaming responses.
        
        Displays tokens as they arrive, providing real-time feedback.
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"👤 YOU: {user_message}")
            print(f"{'='*70}\n")
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # First call - may include tool calls
            response_stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._get_tool_definitions(),
                tool_choice="auto",
                stream=True  # Enable streaming
            )
            
            # Collect streaming response
            collected_messages = []
            tool_calls = []
            
            if verbose:
                print("🤖 AGENT: ", end='', flush=True)
            
            # Process stream
            for chunk in response_stream:
                delta = chunk.choices[0].delta
                
                # Handle content (text response)
                if delta.content:
                    collected_messages.append(delta.content)
                    if verbose:
                        self.display.print_chunk(delta.content)
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        # Initialize tool call if needed
                        while len(tool_calls) <= tool_call.index:
                            tool_calls.append({
                                "id": "",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        # Update tool call data
                        if tool_call.id:
                            tool_calls[tool_call.index]["id"] = tool_call.id
                        if tool_call.function.name:
                            tool_calls[tool_call.index]["function"]["name"] = tool_call.function.name
                        if tool_call.function.arguments:
                            tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
            
            if verbose and collected_messages:
                print()  # New line after streaming content
            
            # Handle tool calls if any
            if tool_calls:
                if verbose:
                    print(f"\n{'─'*70}")
                    print("🔧 TOOL CALLS:")
                
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": "".join(collected_messages),
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": tc["function"]
                        }
                        for tc in tool_calls
                    ]
                })
                
                # Execute each tool
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args_json = tool_call["function"]["arguments"]
                    
                    if verbose:
                        print(f"\n  📞 Calling: {tool_name}")
                        self.display.show_spinner(f"    Executing {tool_name}...", 0.5)
                    
                    # Execute tool
                    result = self._execute_tool(tool_name, tool_args_json)
                    
                    if verbose:
                        print(f"    ✅ Result: {json.dumps(result, indent=6)}")
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call["id"]
                    })
                
                # Get final streaming response
                if verbose:
                    print(f"\n{'─'*70}")
                    print("🤖 AGENT: ", end='', flush=True)
                
                final_stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True
                )
                
                final_response = []
                for chunk in final_stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        final_response.append(content)
                        if verbose:
                            self.display.print_chunk(content)
                
                if verbose:
                    print()  # New line
            
            if verbose:
                print(f"{'='*70}\n")
            
            return "".join(collected_messages) if not tool_calls else "".join(final_response)
            
        except Exception as e:
            if verbose:
                print(f"\n❌ Error during streaming: {e}\n")
            raise
    
    def _execute_tool(self, tool_name: str, arguments_json: str) -> Dict[str, Any]:
        """Execute a tool and return result"""
        try:
            arguments = json.loads(arguments_json)
            
            if tool_name in self.tools_available:
                return self.tools_available[tool_name](**arguments)
            else:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "success": False
                }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def _get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for OpenAI"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Search through documents to find relevant information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 3)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_data",
                    "description": "Analyze a dataset and return statistics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dataset": {
                                "type": "string",
                                "description": "Name of the dataset to analyze"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["summary", "trend", "forecast"],
                                "description": "Type of analysis to perform"
                            }
                        },
                        "required": ["dataset"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_complex",
                    "description": "Calculate complex mathematical expressions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression to evaluate"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ]


# =============================================================================
# COMPARISON: STREAMING VS NON-STREAMING
# =============================================================================

def compare_streaming_vs_blocking(agent: StreamingAgent, message: str):
    """Demonstrate the difference between streaming and blocking"""
    
    print("\n" + "="*70)
    print("COMPARISON: Streaming vs. Non-Streaming")
    print("="*70)
    
    # Non-streaming (blocking)
    print("\n1️⃣  NON-STREAMING (Blocking):")
    print("─"*70)
    print("👤 YOU:", message)
    print("\n⏳ Waiting for complete response...")
    
    start = time.time()
    
    # Simulate blocking call
    response = agent.client.chat.completions.create(
        model=agent.model,
        messages=[{"role": "user", "content": message}],
        stream=False
    )
    
    blocking_time = time.time() - start
    
    print(f"🤖 AGENT: {response.choices[0].message.content}")
    print(f"\n⏱️  Total time: {blocking_time:.2f}s (user sees nothing until complete)")
    
    # Streaming
    print("\n" + "─"*70)
    print("\n2️⃣  STREAMING (Real-time):")
    print("─"*70)
    
    start = time.time()
    agent.chat_streaming(message, verbose=True)
    streaming_time = time.time() - start
    
    print(f"⏱️  Total time: {streaming_time:.2f}s (user sees tokens as generated)")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY:")
    print(f"  • Blocking mode: User waits {blocking_time:.2f}s with no feedback")
    print(f"  • Streaming mode: User gets immediate feedback")
    print(f"  • Better UX even if total time is similar!")
    print("="*70 + "\n")


# =============================================================================
# MAIN DEMO
# =============================================================================

def main():
    """Run streaming demonstrations"""
    
    print("\n" + "="*70)
    print("🌊 Streaming Agent Demo")
    print("="*70)
    print("\nThis example demonstrates real-time streaming responses.")
    print("Watch as tokens appear as they're generated!")
    print("="*70)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️  OPENAI_API_KEY not set.")
        print("Set your API key to see streaming in action:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nNote: Streaming requires actual API calls to demonstrate.\n")
        return
    
    agent = StreamingAgent(api_key)
    
    # Demo scenarios
    print("\n📋 Running streaming demonstrations...\n")
    
    demos = [
        {
            "name": "Simple Question",
            "message": "Explain what AI agents are in 2-3 sentences."
        },
        {
            "name": "Tool Usage",
            "message": "Search for documents about machine learning and summarize what you find."
        },
        {
            "name": "Complex Task",
            "message": "Analyze the 'sales' dataset with a trend analysis, then explain the results."
        }
    ]
    
    for i, demo in enumerate(demos, 1):
        print(f"\n{'#'*70}")
        print(f"Demo {i}/{len(demos)}: {demo['name']}")
        print(f"{'#'*70}")
        
        try:
            agent.chat_streaming(demo["message"], verbose=True)
            
            if i < len(demos):
                input("\n⏸️  Press Enter for next demo...")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Comparison demo
    print(f"\n{'#'*70}")
    print(f"Demo {len(demos)+1}: Streaming vs. Non-Streaming Comparison")
    print(f"{'#'*70}")
    
    try:
        compare_streaming_vs_blocking(
            agent,
            "Explain the benefits of streaming responses in AI applications."
        )
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Interactive mode
    print("\n" + "="*70)
    print("💬 Interactive Streaming Mode")
    print("="*70)
    print("Ask questions and watch responses stream in real-time!")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if not user_input:
                continue
            
            agent.chat_streaming(user_input, verbose=True)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()

