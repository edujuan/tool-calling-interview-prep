"""
Planner-Executor Agent Pattern

This example demonstrates the plan-and-execute pattern where:
1. A planner creates a complete plan upfront
2. An executor carries out each step
3. The planner can revise if steps fail

This is more efficient than ReAct for multi-step tasks.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

@dataclass
class PlanStep:
    """Single step in execution plan"""
    step_num: int
    description: str
    tool: str
    tool_input: Dict[str, Any]
    dependencies: List[int] = None  # Step numbers this depends on
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class ExecutionResult:
    """Result of executing a step"""
    step: PlanStep
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0


class PlannerExecutorAgent:
    """Agent using plan-and-execute pattern"""
    
    def __init__(self, tools: Dict[str, Callable], max_replans: int = 2):
        self.tools = tools
        self.max_replans = max_replans
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def run(self, query: str, verbose: bool = True) -> str:
        """
        Execute task using plan-and-execute pattern
        
        Args:
            query: User's request
            verbose: Whether to print detailed execution
        
        Returns:
            Final answer
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"🎯 TASK: {query}")
            print(f"{'='*70}\n")
        
        replans_used = 0
        execution_results = []
        
        while replans_used <= self.max_replans:
            # Phase 1: Planning
            if verbose:
                print(f"{'─'*70}")
                print(f"📋 PLANNING PHASE (Attempt {replans_used + 1})")
                print(f"{'─'*70}\n")
            
            plan = self._create_plan(
                query,
                previous_results=execution_results,
                verbose=verbose
            )
            
            if not plan:
                return "Failed to create a valid execution plan."
            
            # Phase 2: Execution
            if verbose:
                print(f"\n{'─'*70}")
                print(f"⚙️  EXECUTION PHASE")
                print(f"{'─'*70}\n")
            
            execution_results = self._execute_plan(plan, verbose=verbose)
            
            # Check if all steps succeeded
            failures = [r for r in execution_results if not r.success]
            
            if not failures:
                # Success! Synthesize answer
                if verbose:
                    print(f"\n{'─'*70}")
                    print(f"✨ SYNTHESIS PHASE")
                    print(f"{'─'*70}\n")
                
                return self._synthesize_answer(query, execution_results, verbose=verbose)
            
            # Some steps failed - try replanning
            replans_used += 1
            
            if replans_used <= self.max_replans:
                if verbose:
                    print(f"\n⚠️  Some steps failed. Replanning...")
                    print(f"Failed steps: {[r.step.description for r in failures]}\n")
            else:
                if verbose:
                    print(f"\n❌ Max replanning attempts reached.\n")
                
                # Return partial results
                return self._synthesize_partial_answer(query, execution_results)
        
        return "Unable to complete the task after multiple attempts."
    
    def _create_plan(
        self,
        query: str,
        previous_results: List[ExecutionResult] = None,
        verbose: bool = True
    ) -> List[PlanStep]:
        """Create execution plan using LLM"""
        
        # Build planning prompt
        context = ""
        if previous_results:
            context = "\n\nPrevious execution results:\n"
            for result in previous_results:
                status = "✓" if result.success else "✗"
                context += f"{status} Step {result.step.step_num}: {result.step.description}"
                if result.success:
                    context += f" → {result.output}\n"
                else:
                    context += f" → ERROR: {result.error}\n"
        
        planning_prompt = f"""You are a planning assistant. Create a step-by-step execution plan.

Available tools:
{self._format_tools()}

Task: {query}
{context}

Create a plan as a JSON array. Each step should:
1. Have a clear description
2. Specify which tool to use
3. Provide tool inputs (use $stepN to reference previous step outputs)
4. List dependencies (which steps must complete first)

Format:
[
  {{
    "step": 1,
    "description": "What this step does",
    "tool": "tool_name",
    "tool_input": {{"arg": "value"}},
    "dependencies": []
  }},
  ...
]

Guidelines:
- Keep steps simple and focused
- Steps can run in parallel if no dependencies
- Reference previous results with $step1, $step2, etc.
- If replanning, learn from failed steps

Plan:"""
        
        response = self.client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": planning_prompt}]
        )
        
        # Parse plan
        plan_text = response.choices[0].message.content
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', plan_text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group(0))
                
                plan = []
                for step_data in plan_data:
                    step = PlanStep(
                        step_num=step_data['step'],
                        description=step_data['description'],
                        tool=step_data['tool'],
                        tool_input=step_data['tool_input'],
                        dependencies=step_data.get('dependencies', [])
                    )
                    plan.append(step)
                
                if verbose:
                    print("📝 Execution Plan:")
                    for step in plan:
                        deps = f" (depends on: {step.dependencies})" if step.dependencies else ""
                        print(f"  {step.step_num}. {step.description}{deps}")
                        print(f"     Tool: {step.tool}")
                        print(f"     Input: {json.dumps(step.tool_input)}")
                
                return plan
            else:
                if verbose:
                    print("❌ Could not extract JSON plan from response")
                return []
                
        except Exception as e:
            if verbose:
                print(f"❌ Failed to parse plan: {e}")
            return []
    
    def _execute_plan(
        self,
        plan: List[PlanStep],
        verbose: bool = True
    ) -> List[ExecutionResult]:
        """Execute each step in the plan"""
        
        results: Dict[int, ExecutionResult] = {}
        context = {}  # Store step outputs
        
        # Execute steps in order (respecting dependencies)
        remaining_steps = plan.copy()
        
        while remaining_steps:
            # Find steps that can execute (dependencies met)
            ready_steps = [
                step for step in remaining_steps
                if all(dep in results for dep in step.dependencies)
            ]
            
            if not ready_steps:
                # Circular dependency or impossible plan
                if verbose:
                    print("❌ Cannot proceed - unmet dependencies")
                break
            
            # Execute ready steps
            for step in ready_steps:
                if verbose:
                    print(f"\n▶️  Step {step.step_num}: {step.description}")
                
                start_time = time.time()
                
                # Resolve references to previous results
                resolved_input = self._resolve_references(
                    step.tool_input,
                    context
                )
                
                # Execute tool
                try:
                    if step.tool not in self.tools:
                        raise ValueError(f"Tool '{step.tool}' not found")
                    
                    output = self.tools[step.tool](**resolved_input)
                    
                    result = ExecutionResult(
                        step=step,
                        success=True,
                        output=output,
                        duration_ms=(time.time() - start_time) * 1000
                    )
                    
                    # Store for future steps
                    context[f"step{step.step_num}"] = output
                    
                    if verbose:
                        print(f"   ✅ Success: {output}")
                        print(f"   ⏱️  Duration: {result.duration_ms:.0f}ms")
                
                except Exception as e:
                    result = ExecutionResult(
                        step=step,
                        success=False,
                        output=None,
                        error=str(e),
                        duration_ms=(time.time() - start_time) * 1000
                    )
                    
                    if verbose:
                        print(f"   ❌ Error: {e}")
                
                results[step.step_num] = result
                remaining_steps.remove(step)
        
        # Return results in step order
        return [results[i] for i in sorted(results.keys())]
    
    def _resolve_references(
        self,
        tool_input: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve $stepN references in tool inputs"""
        
        resolved = {}
        
        for key, value in tool_input.items():
            if isinstance(value, str) and value.startswith("$step"):
                # Reference to previous step output
                step_key = value[1:]  # Remove $
                if step_key in context:
                    resolved[key] = context[step_key]
                else:
                    # Keep original if can't resolve
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def _synthesize_answer(
        self,
        query: str,
        results: List[ExecutionResult],
        verbose: bool = True
    ) -> str:
        """Synthesize final answer from execution results"""
        
        # Build context from results
        context = ""
        for result in results:
            context += f"\nStep {result.step.step_num}: {result.step.description}\n"
            context += f"Result: {result.output}\n"
        
        synthesis_prompt = f"""Based on the execution results, provide a final answer to the user's question.

Original Question: {query}

Execution Results:
{context}

Provide a clear, concise answer that directly addresses the user's question:"""
        
        response = self.client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        
        answer = response.choices[0].message.content
        
        if verbose:
            print(f"💬 {answer}")
        
        return answer
    
    def _synthesize_partial_answer(
        self,
        query: str,
        results: List[ExecutionResult]
    ) -> str:
        """Create answer from partial results when some steps failed"""
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        answer = f"I was able to complete {len(successful_results)} out of {len(results)} steps:\n\n"
        
        for result in successful_results:
            answer += f"✓ {result.step.description}: {result.output}\n"
        
        answer += f"\nHowever, {len(failed_results)} steps failed:\n"
        
        for result in failed_results:
            answer += f"✗ {result.step.description}: {result.error}\n"
        
        return answer
    
    def _format_tools(self) -> str:
        """Format tool descriptions for prompt"""
        descriptions = []
        for name, func in self.tools.items():
            doc = func.__doc__ or "No description"
            first_line = doc.strip().split('\n')[0]
            descriptions.append(f"- {name}: {first_line}")
        return "\n".join(descriptions)


# ============================================================================
# EXAMPLE TOOLS
# ============================================================================

def calculator(expression: str) -> float:
    """Evaluates mathematical expressions"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def get_weather(location: str, units: str = "celsius") -> Dict[str, Any]:
    """Gets current weather for a location"""
    # Mock implementation
    weather_data = {
        "paris": {"temp": 18, "condition": "cloudy"},
        "london": {"temp": 15, "condition": "rainy"},
        "new york": {"temp": 22, "condition": "sunny"},
        "tokyo": {"temp": 25, "condition": "partly cloudy"},
    }
    
    location_lower = location.lower()
    if location_lower in weather_data:
        data = weather_data[location_lower]
        return f"{data['temp']}°{units[0].upper()}, {data['condition']}"
    else:
        raise ValueError(f"Weather data not available for {location}")


def search_database(query: str, table: str = "all") -> str:
    """Searches database for information"""
    # Mock implementation
    results = {
        "population paris": "2.1 million",
        "population london": "9 million",
        "population new york": "8.3 million",
        "population tokyo": "13.9 million",
    }
    
    query_lower = query.lower()
    for key, value in results.items():
        if key in query_lower:
            return value
    
    return "No results found"


def format_report(data: str, style: str = "simple") -> str:
    """Formats data into a report"""
    if style == "simple":
        return f"Report:\n{data}"
    elif style == "detailed":
        return f"=== DETAILED REPORT ===\n\n{data}\n\n=== END REPORT ==="
    else:
        return data


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    """Run example queries"""
    
    print("\n" + "="*70)
    print("🤖 Planner-Executor Agent - Interactive Demo")
    print("="*70)
    
    # Define available tools
    tools = {
        "calculator": calculator,
        "get_weather": get_weather,
        "search_database": search_database,
        "format_report": format_report,
    }
    
    # Create agent
    agent = PlannerExecutorAgent(tools=tools, max_replans=2)
    
    # Example queries
    examples = [
        "Get weather in Paris and London, then calculate the temperature difference",
        "Find populations of Tokyo and New York, calculate total, and create a report",
        "What's 100 * 5 + 200?",
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
    print("💬 Interactive Mode - Ask multi-step questions!")
    print(f"{'#'*70}")
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

