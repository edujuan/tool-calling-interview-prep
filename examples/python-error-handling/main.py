"""
Error Handling Showcase for AI Agents

This example demonstrates comprehensive error handling strategies for
production AI agents including:
- Retry logic with exponential backoff
- Circuit breaker pattern
- Graceful degradation
- Timeout handling
- Validation and sanitization
- Error logging and monitoring
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


# =============================================================================
# ERROR TYPES AND EXCEPTIONS
# =============================================================================

class ToolError(Exception):
    """Base exception for tool errors"""
    pass


class ToolTimeoutError(ToolError):
    """Tool execution timeout"""
    pass


class ToolValidationError(ToolError):
    """Tool input validation failed"""
    pass


class CircuitBreakerOpen(ToolError):
    """Circuit breaker is open, preventing execution"""
    pass


# =============================================================================
# CIRCUIT BREAKER PATTERN
# =============================================================================

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, block requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    
    Tracks failures and opens the circuit after threshold is reached,
    preventing further calls until recovery period passes.
    """
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    success_count: int = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        # Check if we should attempt recovery
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN. "
                    f"Will retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            # Successful call in HALF_OPEN state, reset to CLOSED
            logger.info("Circuit breaker closing after successful recovery")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
        else:
            self.success_count += 1
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker opening after {self.failure_count} failures"
            )
            self.state = CircuitState.OPEN
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed in HALF_OPEN, go back to OPEN
            logger.warning("Circuit breaker reopening after failed recovery attempt")
            self.state = CircuitState.OPEN


# =============================================================================
# RETRY DECORATOR WITH EXPONENTIAL BACKOFF
# =============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    
                    time.sleep(delay)
                    delay *= backoff_factor
            
            raise last_exception
        
        return wrapper
    return decorator


# =============================================================================
# TIMEOUT WRAPPER
# =============================================================================

import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: float):
    """
    Context manager for timeout handling.
    
    Note: This uses SIGALRM which only works on Unix systems.
    For production, consider using threading.Timer or asyncio.wait_for
    """
    def timeout_handler(signum, frame):
        raise ToolTimeoutError(f"Operation timed out after {seconds}s")
    
    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))
    
    try:
        yield
    finally:
        # Restore the old handler and cancel alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# =============================================================================
# VALIDATION AND SANITIZATION
# =============================================================================

class InputValidator:
    """Validate and sanitize tool inputs"""
    
    @staticmethod
    def validate_string(
        value: str,
        min_length: int = 0,
        max_length: int = 1000,
        allowed_chars: Optional[str] = None
    ) -> str:
        """Validate string input"""
        if not isinstance(value, str):
            raise ToolValidationError(f"Expected string, got {type(value)}")
        
        if len(value) < min_length:
            raise ToolValidationError(
                f"String too short (min: {min_length}, got: {len(value)})"
            )
        
        if len(value) > max_length:
            raise ToolValidationError(
                f"String too long (max: {max_length}, got: {len(value)})"
            )
        
        if allowed_chars:
            invalid_chars = set(value) - set(allowed_chars)
            if invalid_chars:
                raise ToolValidationError(
                    f"Invalid characters: {invalid_chars}"
                )
        
        return value
    
    @staticmethod
    def validate_number(
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> float:
        """Validate numeric input"""
        if not isinstance(value, (int, float)):
            raise ToolValidationError(f"Expected number, got {type(value)}")
        
        if min_value is not None and value < min_value:
            raise ToolValidationError(
                f"Value too small (min: {min_value}, got: {value})"
            )
        
        if max_value is not None and value > max_value:
            raise ToolValidationError(
                f"Value too large (max: {max_value}, got: {value})"
            )
        
        return value
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        # Remove any parent directory references
        if ".." in path or path.startswith("/"):
            raise ToolValidationError(
                "Path cannot contain '..' or start with '/'"
            )
        
        # Remove leading/trailing whitespace
        path = path.strip()
        
        # Basic validation
        if not path:
            raise ToolValidationError("Path cannot be empty")
        
        return path


# =============================================================================
# TOOLS WITH ERROR HANDLING
# =============================================================================

class ResilientTools:
    """Tools with comprehensive error handling"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0
        )
        self.validator = InputValidator()
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def calculate_with_retry(self, expression: str) -> Dict[str, Any]:
        """
        Calculator with retry logic.
        
        Demonstrates:
        - Input validation
        - Retry on failure
        - Error logging
        """
        try:
            # Validate input
            expression = self.validator.validate_string(
                expression,
                min_length=1,
                max_length=100
            )
            
            logger.info(f"Calculating: {expression}")
            
            # Safe evaluation (limited scope)
            result = eval(expression, {"__builtins__": {}}, {
                "abs": abs, "pow": pow, "round": round,
                "sum": sum, "min": min, "max": max
            })
            
            return {
                "success": True,
                "result": result,
                "expression": expression
            }
            
        except ToolValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "error_type": "validation"
            }
        
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            return {
                "success": False,
                "error": f"Calculation error: {str(e)}",
                "error_type": "execution"
            }
    
    def api_call_with_circuit_breaker(self, endpoint: str) -> Dict[str, Any]:
        """
        API call with circuit breaker protection.
        
        Demonstrates:
        - Circuit breaker pattern
        - Graceful degradation
        """
        try:
            result = self.circuit_breaker.call(
                self._simulate_api_call,
                endpoint
            )
            return result
            
        except CircuitBreakerOpen as e:
            logger.warning(f"Circuit breaker open: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "circuit_breaker",
                "fallback_data": "Using cached data"
            }
        
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_error"
            }
    
    def _simulate_api_call(self, endpoint: str) -> Dict[str, Any]:
        """Simulate an API call (can fail randomly for demo)"""
        import random
        
        # Simulate random failures for demo
        if random.random() < 0.3:  # 30% failure rate
            raise Exception("Simulated API failure")
        
        return {
            "success": True,
            "endpoint": endpoint,
            "data": {"temperature": 72, "condition": "sunny"}
        }
    
    def safe_file_operation(self, filepath: str, content: str) -> Dict[str, Any]:
        """
        File operation with validation and error handling.
        
        Demonstrates:
        - Path sanitization
        - Input validation
        - Timeout handling
        """
        try:
            # Sanitize and validate path
            filepath = self.validator.sanitize_path(filepath)
            
            # Validate content
            content = self.validator.validate_string(
                content,
                max_length=10000
            )
            
            logger.info(f"Writing to file: {filepath}")
            
            # Simulate file operation with timeout
            # Note: timeout() only works on Unix systems
            try:
                # with timeout(5.0):
                with open(filepath, 'w') as f:
                    f.write(content)
            except NameError:
                # timeout not available on Windows
                with open(filepath, 'w') as f:
                    f.write(content)
            
            return {
                "success": True,
                "filepath": filepath,
                "bytes_written": len(content)
            }
            
        except ToolValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "validation"
            }
        
        except ToolTimeoutError as e:
            logger.error(f"Timeout: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "timeout"
            }
        
        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "io_error"
            }


# =============================================================================
# AGENT WITH ERROR HANDLING
# =============================================================================

class ResilientAgent:
    """AI agent with comprehensive error handling"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.tools = ResilientTools()
        self.error_log = []
    
    def chat(self, user_message: str, verbose: bool = True) -> str:
        """
        Chat with error-resilient agent.
        
        Demonstrates:
        - LLM call error handling
        - Tool execution error handling
        - Error recovery strategies
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"USER: {user_message}")
            print(f"{'='*70}\n")
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # Call LLM with retry
            response = self._call_llm_with_retry(messages)
            
            response_message = response.choices[0].message
            
            # Check for tool calls
            if response_message.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in response_message.tool_calls
                    ]
                })
                
                # Execute tools with error handling
                for tool_call in response_message.tool_calls:
                    if verbose:
                        print(f"🔧 Calling tool: {tool_call.function.name}")
                    
                    result = self._execute_tool_safely(
                        tool_call.function.name,
                        tool_call.function.arguments
                    )
                    
                    if verbose:
                        print(f"   Result: {json.dumps(result, indent=2)}\n")
                    
                    # Add result to messages
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id
                    })
                
                # Get final response
                final_response = self._call_llm_with_retry(messages)
                final_message = final_response.choices[0].message.content
            else:
                final_message = response_message.content
            
            if verbose:
                print(f"{'='*70}")
                print(f"AGENT: {final_message}")
                print(f"{'='*70}\n")
            
            return final_message
            
        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            logger.error(error_msg)
            self.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "message": user_message
            })
            
            return f"I encountered an error: {str(e)}. Please try again or rephrase your request."
    
    @retry_with_backoff(max_retries=3, initial_delay=2.0)
    def _call_llm_with_retry(self, messages):
        """Call LLM with retry logic"""
        return self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=self._get_tool_definitions(),
            tool_choice="auto"
        )
    
    def _execute_tool_safely(
        self,
        tool_name: str,
        arguments_json: str
    ) -> Dict[str, Any]:
        """Execute tool with comprehensive error handling"""
        try:
            arguments = json.loads(arguments_json)
            
            if tool_name == "calculate_with_retry":
                return self.tools.calculate_with_retry(arguments["expression"])
            
            elif tool_name == "api_call_with_circuit_breaker":
                return self.tools.api_call_with_circuit_breaker(arguments["endpoint"])
            
            elif tool_name == "safe_file_operation":
                return self.tools.safe_file_operation(
                    arguments["filepath"],
                    arguments["content"]
                )
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "error_type": "unknown_tool"
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON arguments: {e}")
            return {
                "success": False,
                "error": f"Invalid arguments: {str(e)}",
                "error_type": "json_error"
            }
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_error"
            }
    
    def _get_tool_definitions(self):
        """Get tool definitions for LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculate_with_retry",
                    "description": "Calculate mathematical expressions with automatic retry on failure",
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
            },
            {
                "type": "function",
                "function": {
                    "name": "api_call_with_circuit_breaker",
                    "description": "Make API call with circuit breaker protection against cascading failures",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "API endpoint to call"
                            }
                        },
                        "required": ["endpoint"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "safe_file_operation",
                    "description": "Safely write to a file with validation and error handling",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to file (relative, no parent directories)"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write"
                            }
                        },
                        "required": ["filepath", "content"]
                    }
                }
            }
        ]
    
    def show_error_log(self):
        """Display error log"""
        if not self.error_log:
            print("No errors logged")
            return
        
        print("\n📊 Error Log:")
        print("="*70)
        for i, error in enumerate(self.error_log, 1):
            print(f"\n{i}. {error['timestamp']}")
            print(f"   Message: {error['message']}")
            print(f"   Error: {error['error']}")
        print()


# =============================================================================
# DEMO
# =============================================================================

def main():
    """Run error handling demonstrations"""
    
    print("\n" + "="*70)
    print("🛡️  Error Handling Showcase for AI Agents")
    print("="*70)
    print("\nThis example demonstrates:")
    print("- Retry logic with exponential backoff")
    print("- Circuit breaker pattern")
    print("- Input validation and sanitization")
    print("- Timeout handling")
    print("- Graceful error recovery")
    print("="*70)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  OPENAI_API_KEY not set. Running tool demos only.\n")
        
        # Demo tools without agent
        tools = ResilientTools()
        
        print("\n1. Calculator with Retry:")
        print("-" * 70)
        result = tools.calculate_with_retry("10 * 5 + 3")
        print(json.dumps(result, indent=2))
        
        print("\n2. API Call with Circuit Breaker:")
        print("-" * 70)
        for i in range(5):
            result = tools.api_call_with_circuit_breaker("weather/current")
            print(f"Call {i+1}: {json.dumps(result, indent=2)}")
            time.sleep(0.5)
        
        print("\n3. Safe File Operation:")
        print("-" * 70)
        result = tools.safe_file_operation("test.txt", "Hello, World!")
        print(json.dumps(result, indent=2))
        
        # Demo validation errors
        print("\n4. Validation Error Demo:")
        print("-" * 70)
        result = tools.safe_file_operation("../etc/passwd", "hack")
        print(json.dumps(result, indent=2))
        
        return
    
    # Full agent demo
    agent = ResilientAgent(api_key)
    
    examples = [
        "Calculate 15 * 20 + 100",
        "Call the weather API",
        "Write 'test content' to output.txt",
    ]
    
    print("\n📋 Running example queries...\n")
    
    for query in examples:
        try:
            agent.chat(query, verbose=True)
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error: {e}\n")
    
    # Show error log
    agent.show_error_log()
    
    # Interactive mode
    print("\n" + "="*70)
    print("💬 Interactive Mode")
    print("="*70)
    print("Try commands that might fail, and watch error recovery in action!")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if not user_input:
                continue
            
            agent.chat(user_input, verbose=True)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break


if __name__ == "__main__":
    main()

