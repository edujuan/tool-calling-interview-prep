#!/usr/bin/env python3
"""
MCP File Operations Client
===========================

Client that connects to the file operations MCP server and exposes tools to an agent.

This demonstrates:
- MCP client initialization
- Tool discovery
- Tool invocation
- Integration with OpenAI
"""

import os
import json
import subprocess
import openai
from typing import Dict, List, Any, Optional

class MCPClient:
    """
    Client for communicating with MCP servers via STDIO transport.
    """
    
    def __init__(self, server_command: List[str]):
        """
        Initialize MCP client.
        
        Args:
            server_command: Command to start MCP server (e.g., ['python', 'server.py'])
        """
        self.process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        self.request_id = 0
        self.tools: List[Dict] = []
        
        # Initialize connection
        self._initialize()
        
        # Discover tools
        self._discover_tools()
    
    def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send JSON-RPC request to server"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        # Send request
        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        
        if not response_line:
            raise RuntimeError("Server closed connection")
        
        return json.loads(response_line)
    
    def _initialize(self):
        """Initialize MCP connection"""
        response = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "file-operations-client",
                "version": "1.0.0"
            }
        })
        
        if "error" in response:
            raise RuntimeError(f"Initialization failed: {response['error']}")
    
    def _discover_tools(self):
        """Discover available tools from server"""
        response = self._send_request("tools/list")
        
        if "error" in response:
            raise RuntimeError(f"Tool discovery failed: {response['error']}")
        
        self.tools = response.get("result", {}).get("tools", [])
    
    def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of tool
            arguments: Tool arguments
        
        Returns:
            Tool result as JSON string
        """
        response = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        if "error" in response:
            return json.dumps({"error": response["error"]["message"]})
        
        # Extract text content from response
        content = response.get("result", {}).get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "{}")
        
        return "{}"
    
    def get_openai_tools(self) -> List[Dict]:
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []
        
        for tool in self.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            })
        
        return openai_tools
    
    def close(self):
        """Close connection to server"""
        self.process.terminate()
        self.process.wait(timeout=5)

class FileOperationsAgent:
    """Agent that uses MCP file operations server"""
    
    def __init__(self, openai_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Start MCP server
        server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        self.mcp_client = MCPClient(["python3", server_path])
        
        self.conversation_history: List[Dict] = []
        
        print("✓ File Operations Agent initialized")
        print(f"  Available tools: {len(self.mcp_client.tools)}")
        for tool in self.mcp_client.tools:
            print(f"    - {tool['name']}")
    
    def chat(self, user_message: str, verbose: bool = True) -> str:
        """
        Chat with agent about file operations.
        
        Args:
            user_message: User's request
            verbose: Print execution details
        
        Returns:
            Agent's response
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"USER: {user_message}")
            print(f"{'='*60}\n")
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                print(f"[Iteration {iteration}]")
            
            # Call LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=self.conversation_history,
                tools=self.mcp_client.get_openai_tools(),
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check if agent wants to use tools
            if message.tool_calls:
                # Add assistant message
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
                
                # Execute tool calls via MCP
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"  📁 Calling MCP tool: {tool_name}")
                        print(f"     Arguments: {json.dumps(tool_args, indent=6)}")
                    
                    # Call via MCP client
                    result = self.mcp_client.call_tool(tool_name, tool_args)
                    
                    if verbose:
                        result_data = json.loads(result)
                        if "error" not in result_data:
                            print(f"     ✓ Success")
                        else:
                            print(f"     ✗ Error: {result_data['error']}")
                        print()
                    
                    # Add tool result
                    self.conversation_history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id
                    })
                
                continue
            
            else:
                # Final answer
                final_answer = message.content
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
                
                if verbose:
                    print(f"{'='*60}")
                    print(f"AGENT: {final_answer}")
                    print(f"{'='*60}\n")
                
                return final_answer
        
        return "I couldn't complete the request within the iteration limit."
    
    def reset(self):
        """Reset conversation history"""
        self.conversation_history.clear()
    
    def close(self):
        """Close MCP connection"""
        self.mcp_client.close()

def main():
    """Run file operations agent"""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return
    
    # Initialize agent
    agent = FileOperationsAgent(api_key)
    
    print("\n" + "="*60)
    print("File Operations Agent - Interactive Mode")
    print("="*60)
    print("\nThis agent can:")
    print("  • Read and write files")
    print("  • List directories")
    print("  • Search for files")
    print("  • Get file metadata")
    print("  • Create directories")
    print("\nType 'quit' to exit, 'reset' to start new conversation")
    print("="*60)
    
    # Example queries
    examples = [
        # "List all files in the current directory",
        # "Create a file called 'test.txt' with the content 'Hello, MCP!'",
        # "Search for all Python files",
    ]
    
    for example in examples:
        print(f"\n🎯 Example: {example}")
        agent.chat(example, verbose=True)
        agent.reset()
    
    # Interactive mode
    try:
        while True:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset()
                print("✓ Conversation reset")
                continue
            
            # Process request
            agent.chat(user_input, verbose=True)
    
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    
    finally:
        agent.close()

if __name__ == "__main__":
    main()

