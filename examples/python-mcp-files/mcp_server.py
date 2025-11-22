#!/usr/bin/env python3
"""
MCP File Operations Server
===========================

A Model Context Protocol (MCP) server that provides file system operations.

This server implements:
- File reading (with safety checks)
- File writing (sandboxed to workspace)
- Directory listing
- File search
- File metadata

Demonstrates MCP features:
- Tool registration and discovery
- Request/response handling
- Error handling
- JSON-RPC protocol
- STDIO transport
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# =============================================================================
# MCP SERVER BASE
# =============================================================================

class MCPServer:
    """
    Base MCP server implementation using STDIO transport.
    
    Communicates via JSON-RPC 2.0 over stdin/stdout.
    """
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.tools: Dict[str, Dict] = {}
        self.workspace = Path.cwd()  # Sandbox to current directory
    
    def register_tool(self, name: str, description: str, 
                     parameters: Dict, handler):
        """Register a tool with the server"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": parameters,
            "handler": handler
        }
    
    def handle_request(self, request: Dict) -> Dict:
        """Handle incoming JSON-RPC request"""
        
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return self._handle_initialize(request_id, params)
            
            elif method == "tools/list":
                return self._handle_tools_list(request_id)
            
            elif method == "tools/call":
                return self._handle_tools_call(request_id, params)
            
            else:
                return self._error_response(
                    request_id,
                    -32601,
                    f"Method not found: {method}"
                )
        
        except Exception as e:
            return self._error_response(
                request_id,
                -32603,
                f"Internal error: {str(e)}"
            )
    
    def _handle_initialize(self, request_id: int, params: Dict) -> Dict:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }
    
    def _handle_tools_list(self, request_id: int) -> Dict:
        """Handle tools listing request"""
        tools_list = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"]
            }
            for tool in self.tools.values()
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools_list
            }
        }
    
    def _handle_tools_call(self, request_id: int, params: Dict) -> Dict:
        """Handle tool execution request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._error_response(
                request_id,
                -32602,
                f"Tool not found: {tool_name}"
            )
        
        tool = self.tools[tool_name]
        handler = tool["handler"]
        
        try:
            result = handler(**arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        
        except Exception as e:
            return self._error_response(
                request_id,
                -32603,
                f"Tool execution failed: {str(e)}"
            )
    
    def _error_response(self, request_id: int, code: int, message: str) -> Dict:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    def run(self):
        """Run server loop (STDIO transport)"""
        self._log("Server started", "info")
        self._log(f"Workspace: {self.workspace}", "info")
        
        for line in sys.stdin:
            try:
                request = json.loads(line)
                self._log(f"Request: {request.get('method')}", "debug")
                
                response = self.handle_request(request)
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                self._log(f"Invalid JSON: {e}", "error")
            except Exception as e:
                self._log(f"Error: {e}", "error")
    
    def _log(self, message: str, level: str = "info"):
        """Log to stderr (stdout is for JSON-RPC)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level.upper()}] {message}", file=sys.stderr)

# =============================================================================
# FILE OPERATIONS TOOLS
# =============================================================================

class FileOperationsServer(MCPServer):
    """MCP server with file operations tools"""
    
    def __init__(self):
        super().__init__("file-operations-server", "1.0.0")
        
        # Register all tools
        self._register_tools()
    
    def _register_tools(self):
        """Register file operation tools"""
        
        # Read file
        self.register_tool(
            name="read_file",
            description="Read the contents of a file from the workspace",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file (relative to workspace)"
                    }
                },
                "required": ["path"]
            },
            handler=self.read_file
        )
        
        # Write file
        self.register_tool(
            name="write_file",
            description="Write content to a file in the workspace",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file (relative to workspace)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            },
            handler=self.write_file
        )
        
        # List directory
        self.register_tool(
            name="list_directory",
            description="List files and directories in a directory",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to directory (relative to workspace, '.' for root)",
                        "default": "."
                    }
                },
                "required": []
            },
            handler=self.list_directory
        )
        
        # Search files
        self.register_tool(
            name="search_files",
            description="Search for files matching a pattern",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '*.txt', '**/*.py')"
                    }
                },
                "required": ["pattern"]
            },
            handler=self.search_files
        )
        
        # Get file info
        self.register_tool(
            name="get_file_info",
            description="Get metadata about a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file"
                    }
                },
                "required": ["path"]
            },
            handler=self.get_file_info
        )
        
        # Create directory
        self.register_tool(
            name="create_directory",
            description="Create a new directory",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to directory"
                    }
                },
                "required": ["path"]
            },
            handler=self.create_directory
        )
    
    def _validate_path(self, path: str) -> Path:
        """
        Validate that path is within workspace (security check).
        
        Prevents directory traversal attacks.
        """
        full_path = (self.workspace / path).resolve()
        
        # Check if path is within workspace
        try:
            full_path.relative_to(self.workspace)
        except ValueError:
            raise PermissionError(f"Access denied: path outside workspace")
        
        return full_path
    
    def read_file(self, path: str) -> Dict:
        """Read file contents"""
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                return {"error": "File not found"}
            
            if not file_path.is_file():
                return {"error": "Not a file"}
            
            # Read content
            content = file_path.read_text()
            
            return {
                "path": str(path),
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1
            }
        
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    def write_file(self, path: str, content: str) -> Dict:
        """Write content to file"""
        try:
            file_path = self._validate_path(path)
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            file_path.write_text(content)
            
            return {
                "path": str(path),
                "bytes_written": len(content),
                "success": True
            }
        
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}
    
    def list_directory(self, path: str = ".") -> Dict:
        """List directory contents"""
        try:
            dir_path = self._validate_path(path)
            
            if not dir_path.exists():
                return {"error": "Directory not found"}
            
            if not dir_path.is_dir():
                return {"error": "Not a directory"}
            
            # List contents
            items = []
            for item in sorted(dir_path.iterdir()):
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "path": str(path),
                "items": items,
                "count": len(items)
            }
        
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}
    
    def search_files(self, pattern: str) -> Dict:
        """Search for files matching pattern"""
        try:
            # Search within workspace
            matches = []
            for file_path in self.workspace.glob(pattern):
                try:
                    # Validate each match
                    self._validate_path(file_path.relative_to(self.workspace))
                    
                    matches.append({
                        "path": str(file_path.relative_to(self.workspace)),
                        "type": "directory" if file_path.is_dir() else "file",
                        "size": file_path.stat().st_size if file_path.is_file() else None
                    })
                except (ValueError, PermissionError):
                    continue
            
            return {
                "pattern": pattern,
                "matches": matches,
                "count": len(matches)
            }
        
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def get_file_info(self, path: str) -> Dict:
        """Get file metadata"""
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                return {"error": "File not found"}
            
            stat = file_path.stat()
            
            return {
                "path": str(path),
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
        
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to get info: {str(e)}"}
    
    def create_directory(self, path: str) -> Dict:
        """Create a directory"""
        try:
            dir_path = self._validate_path(path)
            
            if dir_path.exists():
                return {"error": "Path already exists"}
            
            dir_path.mkdir(parents=True, exist_ok=False)
            
            return {
                "path": str(path),
                "success": True
            }
        
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to create directory: {str(e)}"}

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the MCP file operations server"""
    server = FileOperationsServer()
    server.run()

if __name__ == "__main__":
    main()


