"""
Tool Call Tracer for Debugging AI Agents

Wraps agent tools to trace all calls, arguments, results, and timing.
Useful for debugging, optimization, and understanding agent behavior.

Usage:
    from tool_tracer import ToolTracer
    
    tracer = ToolTracer()
    
    # Wrap your tools
    calculator = tracer.wrap(calculator_func, "calculator")
    weather = tracer.wrap(weather_func, "weather_api")
    
    # Use tools normally
    result = calculator(expression="2+2")
    
    # View trace
    tracer.print_summary()
    tracer.export_to_json("trace.json")
"""

import time
import json
import functools
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import traceback

@dataclass
class ToolCall:
    """Record of a single tool call"""
    tool_name: str
    call_id: str
    timestamp: str
    args: Dict[str, Any]
    kwargs: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str]
    duration_ms: float
    stack_trace: Optional[str] = None


class ToolTracer:
    """Traces tool calls for debugging and analysis"""
    
    def __init__(self, enable_stack_trace: bool = False):
        self.calls: List[ToolCall] = []
        self.enable_stack_trace = enable_stack_trace
        self.call_counter = 0
        self.start_time = time.time()
    
    def wrap(self, func: Callable, name: Optional[str] = None) -> Callable:
        """
        Wrap a function to trace its calls
        
        Args:
            func: Function to wrap
            name: Name for the tool (defaults to function name)
        
        Returns:
            Wrapped function that traces calls
        """
        tool_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate unique call ID
            self.call_counter += 1
            call_id = f"{tool_name}_{self.call_counter}"
            
            # Record start time
            start_time = time.time()
            timestamp = datetime.now().isoformat()
            
            # Capture stack trace if enabled
            stack_trace = None
            if self.enable_stack_trace:
                stack_trace = ''.join(traceback.format_stack()[:-1])
            
            # Attempt to execute function
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
                # Include exception in stack trace
                if self.enable_stack_trace:
                    stack_trace += '\n' + traceback.format_exc()
            
            # Record end time
            duration_ms = (time.time() - start_time) * 1000
            
            # Create call record
            call = ToolCall(
                tool_name=tool_name,
                call_id=call_id,
                timestamp=timestamp,
                args=list(args) if args else [],
                kwargs=kwargs,
                result=self._serialize_result(result),
                success=success,
                error=error,
                duration_ms=round(duration_ms, 2),
                stack_trace=stack_trace
            )
            
            # Store call
            self.calls.append(call)
            
            # Re-raise exception if one occurred
            if not success:
                raise
            
            return result
        
        return wrapper
    
    def _serialize_result(self, result: Any) -> Any:
        """Serialize result for JSON export"""
        try:
            # Try JSON serialization
            json.dumps(result)
            return result
        except (TypeError, ValueError):
            # Fall back to string representation
            return str(result)
    
    def get_calls(self, tool_name: Optional[str] = None, 
                  success: Optional[bool] = None) -> List[ToolCall]:
        """
        Get filtered list of tool calls
        
        Args:
            tool_name: Filter by tool name (None = all)
            success: Filter by success status (None = all)
        
        Returns:
            List of matching ToolCall objects
        """
        calls = self.calls
        
        if tool_name is not None:
            calls = [c for c in calls if c.tool_name == tool_name]
        
        if success is not None:
            calls = [c for c in calls if c.success == success]
        
        return calls
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics"""
        total_calls = len(self.calls)
        successful_calls = len([c for c in self.calls if c.success])
        failed_calls = total_calls - successful_calls
        
        if not self.calls:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "tools_used": [],
            }
        
        # Per-tool statistics
        tool_stats = {}
        for call in self.calls:
            if call.tool_name not in tool_stats:
                tool_stats[call.tool_name] = {
                    "calls": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_duration_ms": 0,
                    "avg_duration_ms": 0,
                    "min_duration_ms": float('inf'),
                    "max_duration_ms": 0,
                }
            
            stats = tool_stats[call.tool_name]
            stats["calls"] += 1
            stats["successes"] += 1 if call.success else 0
            stats["failures"] += 0 if call.success else 1
            stats["total_duration_ms"] += call.duration_ms
            stats["min_duration_ms"] = min(stats["min_duration_ms"], call.duration_ms)
            stats["max_duration_ms"] = max(stats["max_duration_ms"], call.duration_ms)
        
        # Calculate averages
        for stats in tool_stats.values():
            stats["avg_duration_ms"] = round(
                stats["total_duration_ms"] / stats["calls"], 2
            )
        
        total_duration = sum(c.duration_ms for c in self.calls)
        elapsed_time = time.time() - self.start_time
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": round(successful_calls / total_calls * 100, 1) if total_calls > 0 else 0,
            "total_tool_time_ms": round(total_duration, 2),
            "elapsed_real_time_s": round(elapsed_time, 2),
            "tools_used": list(tool_stats.keys()),
            "per_tool_stats": tool_stats,
        }
    
    def print_summary(self, detailed: bool = False):
        """Print human-readable summary"""
        print("\n" + "=" * 70)
        print("🔍 TOOL CALL TRACE SUMMARY")
        print("=" * 70)
        
        stats = self.get_statistics()
        
        # Overall stats
        print(f"\n📊 Overall Statistics:")
        print(f"  Total Calls:      {stats['total_calls']}")
        print(f"  Successful:       {stats['successful_calls']} ({stats['success_rate']}%)")
        print(f"  Failed:           {stats['failed_calls']}")
        print(f"  Total Tool Time:  {stats['total_tool_time_ms']:.2f}ms")
        print(f"  Elapsed Time:     {stats['elapsed_real_time_s']:.2f}s")
        
        # Per-tool stats
        if stats['per_tool_stats']:
            print(f"\n🔧 Per-Tool Statistics:")
            for tool_name, tool_stats in stats['per_tool_stats'].items():
                print(f"\n  {tool_name}:")
                print(f"    Calls:        {tool_stats['calls']}")
                print(f"    Success Rate: {tool_stats['successes']}/{tool_stats['calls']} " +
                      f"({tool_stats['successes']/tool_stats['calls']*100:.1f}%)")
                print(f"    Avg Duration: {tool_stats['avg_duration_ms']:.2f}ms")
                print(f"    Min Duration: {tool_stats['min_duration_ms']:.2f}ms")
                print(f"    Max Duration: {tool_stats['max_duration_ms']:.2f}ms")
        
        # Detailed call log
        if detailed and self.calls:
            print(f"\n📝 Detailed Call Log:")
            for i, call in enumerate(self.calls, 1):
                status = "✅" if call.success else "❌"
                print(f"\n  {i}. {status} {call.call_id}")
                print(f"     Time: {call.timestamp}")
                print(f"     Args: {call.args}")
                if call.kwargs:
                    print(f"     Kwargs: {call.kwargs}")
                print(f"     Duration: {call.duration_ms:.2f}ms")
                if call.success:
                    result_str = str(call.result)
                    if len(result_str) > 100:
                        result_str = result_str[:100] + "..."
                    print(f"     Result: {result_str}")
                else:
                    print(f"     Error: {call.error}")
        
        print("\n" + "=" * 70 + "\n")
    
    def export_to_json(self, filename: str):
        """Export trace to JSON file"""
        data = {
            "statistics": self.get_statistics(),
            "calls": [asdict(call) for call in self.calls]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Exported trace to {filename}")
    
    def export_to_csv(self, filename: str):
        """Export trace to CSV file"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'call_id', 'tool_name', 'timestamp', 'success',
                'duration_ms', 'args', 'kwargs', 'result', 'error'
            ])
            
            # Data
            for call in self.calls:
                writer.writerow([
                    call.call_id,
                    call.tool_name,
                    call.timestamp,
                    call.success,
                    call.duration_ms,
                    json.dumps(call.args),
                    json.dumps(call.kwargs),
                    json.dumps(call.result) if call.success else '',
                    call.error or ''
                ])
        
        print(f"✅ Exported trace to {filename}")
    
    def clear(self):
        """Clear all traced calls"""
        self.calls = []
        self.call_counter = 0
        self.start_time = time.time()
    
    def find_slow_calls(self, threshold_ms: float = 1000) -> List[ToolCall]:
        """Find calls slower than threshold"""
        return [c for c in self.calls if c.duration_ms > threshold_ms]
    
    def find_errors(self) -> List[ToolCall]:
        """Find all failed calls"""
        return [c for c in self.calls if not c.success]


# ==============================================================================
# Example Usage
# ==============================================================================

def example_usage():
    """Demonstrate tracer usage"""
    
    # Create tracer
    tracer = ToolTracer(enable_stack_trace=False)
    
    # Define some example tools
    def calculator(expression: str) -> float:
        """Calculate mathematical expression"""
        time.sleep(0.05)  # Simulate work
        return eval(expression)
    
    def get_weather(location: str) -> dict:
        """Get weather for location"""
        time.sleep(0.1)  # Simulate API call
        return {"location": location, "temp": 20, "condition": "sunny"}
    
    def failing_tool(x: int) -> int:
        """This tool always fails"""
        raise ValueError("Intentional error for testing")
    
    # Wrap tools
    calc = tracer.wrap(calculator, "calculator")
    weather = tracer.wrap(get_weather, "weather_api")
    fail = tracer.wrap(failing_tool, "failing_tool")
    
    # Use tools
    print("Running example agent with traced tools...\n")
    
    calc(expression="2 + 2")
    calc(expression="10 * 5")
    weather(location="Paris")
    weather(location="London")
    calc(expression="100 / 5")
    
    try:
        fail(x=10)
    except ValueError:
        pass  # Expected
    
    # Print summary
    tracer.print_summary(detailed=True)
    
    # Export traces
    tracer.export_to_json("trace_example.json")
    
    # Find slow calls
    slow_calls = tracer.find_slow_calls(threshold_ms=80)
    if slow_calls:
        print(f"⚠️  Found {len(slow_calls)} slow calls (>80ms)")
        for call in slow_calls:
            print(f"   - {call.tool_name}: {call.duration_ms:.2f}ms")
    
    # Find errors
    errors = tracer.find_errors()
    if errors:
        print(f"\n❌ Found {len(errors)} failed calls:")
        for call in errors:
            print(f"   - {call.tool_name}: {call.error}")


if __name__ == "__main__":
    example_usage()



