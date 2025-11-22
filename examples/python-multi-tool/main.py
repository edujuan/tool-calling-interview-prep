#!/usr/bin/env python3
"""
Multi-Tool Agent Example
========================

Demonstrates an agent that intelligently uses multiple tools from different sources:
- Native Python functions (calculator, file operations)
- External APIs (weather, news)
- Mock MCP server (database operations)
- UTCP-style direct API calls

This example showcases:
1. Tool discovery and registration
2. Intelligent tool selection
3. Tool chaining (using output of one tool as input to another)
4. Error handling and fallbacks
5. Hybrid MCP/UTCP usage
"""

import os
import json
import time
import openai
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

@dataclass
class Tool:
    """Represents a callable tool with metadata"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    source: str  # "native", "api", "mcp"
    
    def to_openai_format(self) -> Dict:
        """Convert to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

# =============================================================================
# NATIVE TOOLS (Python Functions)
# =============================================================================

def calculator(expression: str) -> str:
    """Evaluate a mathematical expression"""
    try:
        # Safe eval with limited scope
        result = eval(expression, {"__builtins__": {}}, {
            "abs": abs, "pow": pow, "round": round,
            "sum": sum, "min": min, "max": max
        })
        return json.dumps({"result": result, "expression": expression})
    except Exception as e:
        return json.dumps({"error": str(e)})

def read_file(filepath: str) -> str:
    """Read contents of a file"""
    try:
        # Security: Only read from current directory
        if ".." in filepath or filepath.startswith("/"):
            return json.dumps({"error": "Invalid file path"})
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        return json.dumps({
            "filepath": filepath,
            "content": content[:500],  # Limit to 500 chars
            "size": len(content)
        })
    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {filepath}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def write_file(filepath: str, content: str) -> str:
    """Write content to a file"""
    try:
        # Security: Only write to current directory
        if ".." in filepath or filepath.startswith("/"):
            return json.dumps({"error": "Invalid file path"})
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return json.dumps({
            "filepath": filepath,
            "bytes_written": len(content),
            "success": True
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def current_time(timezone: str = "UTC") -> str:
    """Get current time in specified timezone"""
    # Simplified - in production, use pytz
    now = datetime.now()
    return json.dumps({
        "time": now.isoformat(),
        "timezone": timezone,
        "unix": int(now.timestamp())
    })

# =============================================================================
# API TOOLS (External APIs)
# =============================================================================

def get_weather(city: str) -> str:
    """Get weather for a city (mock API)"""
    # In production, call real API like OpenWeatherMap
    # This is a mock response
    mock_weather = {
        "city": city,
        "temperature": 72,
        "condition": "Sunny",
        "humidity": 45,
        "source": "mock_api"
    }
    return json.dumps(mock_weather)

def search_news(query: str, limit: int = 5) -> str:
    """Search for news articles (mock API)"""
    # In production, call NewsAPI
    mock_articles = [
        {
            "title": f"Breaking: {query} makes headlines",
            "source": "Tech News",
            "published": "2024-01-15"
        },
        {
            "title": f"Analysis: The impact of {query}",
            "source": "Science Daily",
            "published": "2024-01-14"
        }
    ]
    return json.dumps({"articles": mock_articles[:limit], "query": query})

def translate_text(text: str, target_language: str) -> str:
    """Translate text to target language (mock)"""
    # In production, call Google Translate API
    return json.dumps({
        "original": text,
        "translated": f"[{target_language.upper()}] {text}",
        "target_language": target_language,
        "source": "mock_translator"
    })

# =============================================================================
# MCP-STYLE TOOLS (Simulated MCP server)
# =============================================================================

class MockMCPServer:
    """Simulates an MCP server with database operations"""
    
    def __init__(self):
        self.data = {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"}
            ],
            "products": [
                {"id": 1, "name": "Laptop", "price": 999},
                {"id": 2, "name": "Mouse", "price": 25}
            ]
        }
    
    def query_database(self, table: str, filter_key: Optional[str] = None, 
                      filter_value: Optional[Any] = None) -> str:
        """Query mock database"""
        if table not in self.data:
            return json.dumps({"error": f"Table '{table}' not found"})
        
        results = self.data[table]
        
        if filter_key and filter_value:
            results = [
                row for row in results 
                if row.get(filter_key) == filter_value
            ]
        
        return json.dumps({
            "table": table,
            "results": results,
            "count": len(results)
        })
    
    def insert_record(self, table: str, record: Dict) -> str:
        """Insert record into mock database"""
        if table not in self.data:
            return json.dumps({"error": f"Table '{table}' not found"})
        
        # Generate ID
        max_id = max([r['id'] for r in self.data[table]], default=0)
        record['id'] = max_id + 1
        
        self.data[table].append(record)
        
        return json.dumps({
            "success": True,
            "table": table,
            "inserted_id": record['id']
        })

# =============================================================================
# TOOL REGISTRY
# =============================================================================

class ToolRegistry:
    """Central registry for all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.mcp_server = MockMCPServer()
    
    def register(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def register_native_tools(self):
        """Register native Python function tools"""
        
        native_tools = [
            Tool(
                name="calculator",
                description="Evaluate mathematical expressions. Supports +, -, *, /, **, abs, pow, round, sum, min, max.",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate, e.g., '2 + 2' or 'pow(10, 2)'"
                        }
                    },
                    "required": ["expression"]
                },
                function=calculator,
                source="native"
            ),
            Tool(
                name="read_file",
                description="Read contents of a text file from the current directory.",
                parameters={
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to file (relative to current directory)"
                        }
                    },
                    "required": ["filepath"]
                },
                function=read_file,
                source="native"
            ),
            Tool(
                name="write_file",
                description="Write content to a text file in the current directory.",
                parameters={
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to file (relative to current directory)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to file"
                        }
                    },
                    "required": ["filepath", "content"]
                },
                function=write_file,
                source="native"
            ),
            Tool(
                name="current_time",
                description="Get current date and time.",
                parameters={
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (default: UTC)",
                            "default": "UTC"
                        }
                    },
                    "required": []
                },
                function=current_time,
                source="native"
            )
        ]
        
        for tool in native_tools:
            self.register(tool)
    
    def register_api_tools(self):
        """Register external API tools"""
        
        api_tools = [
            Tool(
                name="get_weather",
                description="Get current weather for a city.",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name, e.g., 'London' or 'New York'"
                        }
                    },
                    "required": ["city"]
                },
                function=get_weather,
                source="api"
            ),
            Tool(
                name="search_news",
                description="Search for recent news articles on a topic.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of articles to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                },
                function=search_news,
                source="api"
            ),
            Tool(
                name="translate_text",
                description="Translate text to a target language.",
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to translate"
                        },
                        "target_language": {
                            "type": "string",
                            "description": "Target language code (e.g., 'es', 'fr', 'de')"
                        }
                    },
                    "required": ["text", "target_language"]
                },
                function=translate_text,
                source="api"
            )
        ]
        
        for tool in api_tools:
            self.register(tool)
    
    def register_mcp_tools(self):
        """Register MCP server tools"""
        
        mcp_tools = [
            Tool(
                name="query_database",
                description="Query data from database tables (users, products). Can filter by key-value pairs.",
                parameters={
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Table name: 'users' or 'products'"
                        },
                        "filter_key": {
                            "type": "string",
                            "description": "Optional: field to filter by (e.g., 'name', 'id')"
                        },
                        "filter_value": {
                            "type": "string",
                            "description": "Optional: value to filter for"
                        }
                    },
                    "required": ["table"]
                },
                function=self.mcp_server.query_database,
                source="mcp"
            ),
            Tool(
                name="insert_record",
                description="Insert a new record into database table.",
                parameters={
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Table name: 'users' or 'products'"
                        },
                        "record": {
                            "type": "object",
                            "description": "Record to insert (JSON object)"
                        }
                    },
                    "required": ["table", "record"]
                },
                function=self.mcp_server.insert_record,
                source="mcp"
            )
        ]
        
        for tool in mcp_tools:
            self.register(tool)
    
    def get_openai_tools(self) -> List[Dict]:
        """Get all tools in OpenAI function calling format"""
        return [tool.to_openai_format() for tool in self.tools.values()]
    
    def execute(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool by name"""
        if tool_name not in self.tools:
            return json.dumps({"error": f"Tool '{tool_name}' not found"})
        
        tool = self.tools[tool_name]
        
        try:
            result = tool.function(**arguments)
            return result
        except Exception as e:
            return json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_name
            })
    
    def list_tools(self) -> str:
        """List all registered tools"""
        summary = []
        for name, tool in self.tools.items():
            summary.append(f"- {name} ({tool.source}): {tool.description}")
        return "\n".join(summary)

# =============================================================================
# MULTI-TOOL AGENT
# =============================================================================

class MultiToolAgent:
    """Agent that uses multiple tools intelligently"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.registry = ToolRegistry()
        self.conversation_history: List[Dict] = []
        self.tool_call_log: List[Dict] = []
        
        # Register all tools
        self.registry.register_native_tools()
        self.registry.register_api_tools()
        self.registry.register_mcp_tools()
        
        print(f"✓ Initialized MultiToolAgent with {len(self.registry.tools)} tools")
        print(f"  - Native tools: {sum(1 for t in self.registry.tools.values() if t.source == 'native')}")
        print(f"  - API tools: {sum(1 for t in self.registry.tools.values() if t.source == 'api')}")
        print(f"  - MCP tools: {sum(1 for t in self.registry.tools.values() if t.source == 'mcp')}")
    
    def chat(self, user_message: str, max_iterations: int = 10, verbose: bool = True) -> str:
        """
        Chat with the agent. Agent can use tools as needed.
        
        Args:
            user_message: User's input
            max_iterations: Maximum tool-use iterations
            verbose: Print detailed execution trace
        
        Returns:
            Agent's final response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"USER: {user_message}")
            print(f"{'='*60}\n")
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                print(f"[Iteration {iteration}]")
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=self.registry.get_openai_tools(),
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check if agent wants to use tools
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
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"  🔧 Calling tool: {tool_name}")
                        print(f"     Arguments: {json.dumps(tool_args, indent=6)}")
                    
                    # Execute tool
                    start_time = time.time()
                    result = self.registry.execute(tool_name, tool_args)
                    duration = time.time() - start_time
                    
                    if verbose:
                        print(f"     Result: {result[:200]}...")
                        print(f"     Duration: {duration:.3f}s\n")
                    
                    # Log tool call
                    self.tool_call_log.append({
                        "iteration": iteration,
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": result,
                        "duration": duration,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id
                    })
                
                # Continue loop to let agent process tool results
                continue
            
            else:
                # No more tool calls - agent has final answer
                final_answer = message.content
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
                
                if verbose:
                    print(f"{'='*60}")
                    print(f"AGENT: {final_answer}")
                    print(f"{'='*60}")
                    print(f"\nCompleted in {iteration} iteration(s)")
                    print(f"Total tool calls: {len(self.tool_call_log)}\n")
                
                return final_answer
        
        # Max iterations reached
        return "I apologize, but I've reached the maximum number of steps. Please try rephrasing your request."
    
    def show_tool_usage_stats(self):
        """Display statistics about tool usage"""
        if not self.tool_call_log:
            print("No tools have been used yet.")
            return
        
        print("\n📊 Tool Usage Statistics")
        print("=" * 60)
        
        # Count by tool
        tool_counts = {}
        tool_times = {}
        
        for log in self.tool_call_log:
            tool = log['tool']
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
            tool_times[tool] = tool_times.get(tool, 0) + log['duration']
        
        print(f"\nTotal tool calls: {len(self.tool_call_log)}")
        print(f"Unique tools used: {len(tool_counts)}")
        
        print("\nBreakdown by tool:")
        for tool in sorted(tool_counts.keys()):
            count = tool_counts[tool]
            avg_time = tool_times[tool] / count
            tool_obj = self.registry.tools[tool]
            print(f"  • {tool} ({tool_obj.source}): {count} calls, avg {avg_time:.3f}s")
        
        print()
    
    def reset(self):
        """Reset conversation history and logs"""
        self.conversation_history.clear()
        self.tool_call_log.clear()
        print("✓ Conversation reset")

# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def main():
    """Run example scenarios"""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Initialize agent
    agent = MultiToolAgent(api_key)
    
    print("\n" + "="*60)
    print("Multi-Tool Agent - Interactive Mode")
    print("="*60)
    print("\nAvailable tools:")
    print(agent.registry.list_tools())
    print("\nType 'quit' to exit, 'reset' to start new conversation")
    print("Type 'stats' to see tool usage statistics")
    print("="*60)
    
    # Example scenarios (uncomment to run automatically)
    example_scenarios = [
        # "What's the weather in London? Translate the result to Spanish.",
        # "Query the database for all users, then calculate the average of their IDs.",
        # "Get the current time, then write it to a file called 'timestamp.txt'",
        # "Search for news about 'artificial intelligence' and summarize the top result."
    ]
    
    for scenario in example_scenarios:
        print(f"\n🎯 Scenario: {scenario}")
        agent.chat(scenario, verbose=True)
        agent.show_tool_usage_stats()
        agent.reset()
    
    # Interactive mode
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset()
                continue
            
            if user_input.lower() == 'stats':
                agent.show_tool_usage_stats()
                continue
            
            # Process user input
            response = agent.chat(user_input, verbose=True)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

