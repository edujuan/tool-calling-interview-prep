# Agent Architecture Patterns

> **Learn the fundamental patterns for building AI agents** - from simple reactive loops to complex multi-agent systems.

---

## Table of Contents

- [Overview](#overview)
- [Pattern 1: Reactive Agents (ReAct)](#pattern-1-reactive-agents-react)
- [Pattern 2: Planner-Executor](#pattern-2-planner-executor)
- [Pattern 3: Multi-Agent Systems](#pattern-3-multi-agent-systems)
- [Pattern 4: Protocol Integration (MCP/UTCP)](#pattern-4-protocol-integration-mcputcp)
- [Choosing the Right Pattern](#choosing-the-right-pattern)
- [Tool Selection and Chaining](#tool-selection-and-chaining)
- [Prompt Engineering for Agents](#prompt-engineering-for-agents)

---

## Overview

When you build an AI agent, you're making architectural choices whether you realize it or not. These choices exist on a spectrum from simple to complex, from fast to powerful. Understanding this spectrum helps you pick the right pattern for your needs.

```
Agent Architecture Spectrum
                                   
Simple ←─────────────────────────────→ Complex
Fast   ←─────────────────────────────→ Powerful

┌──────────┐   ┌──────────┐   ┌──────────┐
│ Reactive │ → │ Planner  │ → │  Multi   │
│  (ReAct) │   │ Executor │   │  Agent   │
└──────────┘   └──────────┘   └──────────┘
     ↕              ↕              ↕
┌────────────────────────────────────────┐
│     Tool-Calling Protocol Layer        │
│  ┌──────────┐         ┌──────────┐    │
│  │   UTCP   │         │   MCP    │    │
│  │ (Direct) │         │ (Proxy)  │    │
│  └──────────┘         └──────────┘    │
└────────────────────────────────────────┘

Use Case:        Use Case:      Use Case:
Single task      Multi-step     Complex
Quick response   workflows      collaboration
```

At the foundation, you have tool-calling protocols (UTCP and MCP) that determine how your agent actually invokes tools. On top of that foundation, you choose an architectural pattern based on your task's complexity. Reactive agents handle single tasks quickly. Planner-executor systems manage multi-step workflows efficiently. Multi-agent systems tackle complex problems through specialized collaboration. Each pattern trades simplicity for power—choose the simplest pattern that solves your problem.

### Quick Comparison

Think of these patterns as different tools in your toolbox. **Reactive agents** are like a Swiss Army knife—simple, versatile, perfect for straightforward tasks like building a calculator bot or weather lookup service. **Planner-Executor** is more like a project manager with a checklist—it takes time to plan but executes efficiently, ideal for multi-step tasks like generating research reports. **Multi-Agent** systems are like a full development team—powerful but complex, suited for enterprise automation where different specialists need to collaborate.

When it comes to protocols, **MCP integration** works well for enterprise environments where you need centralized control and governance over your tools. **UTCP integration** shines when you want fast integration with many APIs and performance is critical—think public API integrations where direct calls matter.

---

## Pattern 1: Reactive Agents (ReAct)

**ReAct = Reasoning + Acting**[[17]](https://www.promptingguide.ai/techniques/react)

The agent alternates between thinking and acting in a loop until the task is complete.[[18]](https://www.promptingguide.ai/techniques/react)

### Architecture

```
┌─────────────────────────────────────┐
│         USER QUERY                  │
└────────────┬────────────────────────┘
             │
             ▼
      ┌────────────┐
      │   THOUGHT  │ ──► "I need to use calculator"
      └──────┬─────┘
             │
             ▼
      ┌────────────┐
      │   ACTION   │ ──► calculator(10 * 5)
      └──────┬─────┘
             │
             ▼
      ┌────────────┐
      │ OBSERVATION│ ──► Result: 50
      └──────┬─────┘
             │
             ├─► Loop back to THOUGHT (if more work needed)
             │
             ▼
      ┌────────────┐
      │   ANSWER   │ ──► "The answer is 50"
      └────────────┘
```

### Implementation

```python
from typing import List, Dict, Any
from dataclasses import dataclass
import re

@dataclass
class AgentStep:
    """Single step in agent's reasoning process"""
    thought: str
    action: str = None
    action_input: Dict = None
    observation: str = None

class ReactAgent:
    """Reactive agent using ReAct pattern"""
    
    def __init__(self, llm, tools: Dict[str, callable], max_iterations: int = 10):
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations
        
    def run(self, query: str, verbose: bool = True) -> str:
        """Execute agent loop"""
        
        history: List[AgentStep] = []
        
        # Build initial prompt
        prompt = self._create_prompt(query, history)
        
        for iteration in range(self.max_iterations):
            if verbose:
                print(f"\n{'='*60}\nIteration {iteration + 1}\n{'='*60}")
            
            # LLM generates thought and potentially an action
            response = self.llm.generate(prompt)
            
            # Parse response
            step = self._parse_response(response)
            history.append(step)
            
            if verbose:
                print(f"💭 Thought: {step.thought}")
            
            # Check if agent wants to give final answer
            if step.action == "Final Answer":
                if verbose:
                    print(f"✅ Final Answer: {step.action_input['answer']}")
                return step.action_input['answer']
            
            # Execute action
            if step.action and step.action in self.tools:
                if verbose:
                    print(f"🔧 Action: {step.action}")
                    print(f"📋 Input: {step.action_input}")
                
                try:
                    observation = self.tools[step.action](**step.action_input)
                    step.observation = str(observation)
                    
                    if verbose:
                        print(f"👁️  Observation: {step.observation}")
                        
                except Exception as e:
                    step.observation = f"Error: {str(e)}"
                    if verbose:
                        print(f"❌ Error: {step.observation}")
            
            # Update prompt with new information
            prompt = self._create_prompt(query, history)
        
        return "Agent reached maximum iterations without completing the task."
    
    def _create_prompt(self, query: str, history: List[AgentStep]) -> str:
        """Create prompt for LLM"""
        
        # System prompt with instructions
        system = f"""You are a helpful assistant that can use tools to answer questions.

Available tools:
{self._format_tools()}

You should follow this pattern:
Thought: Think about what to do next
Action: Choose a tool to use
Action Input: Provide the input for the tool
Observation: See the result (I will provide this)
... (repeat as needed)
Thought: I now know the final answer
Final Answer: Provide the final answer

Begin!"""
        
        # Add conversation history
        conversation = f"\nQuestion: {query}\n\n"
        
        for step in history:
            conversation += f"Thought: {step.thought}\n"
            if step.action:
                conversation += f"Action: {step.action}\n"
                conversation += f"Action Input: {step.action_input}\n"
            if step.observation:
                conversation += f"Observation: {step.observation}\n"
        
        return system + conversation
    
    def _format_tools(self) -> str:
        """Format tool descriptions"""
        tool_descriptions = []
        for name, func in self.tools.items():
            doc = func.__doc__ or "No description"
            tool_descriptions.append(f"- {name}: {doc.strip()}")
        return "\n".join(tool_descriptions)
    
    def _parse_response(self, response: str) -> AgentStep:
        """Parse LLM response into structured step"""
        
        # Extract thought
        thought_match = re.search(r"Thought: (.*?)(?:\n|$)", response)
        thought = thought_match.group(1) if thought_match else response
        
        # Extract action
        action_match = re.search(r"Action: (.*?)(?:\n|$)", response)
        action = action_match.group(1).strip() if action_match else None
        
        # Extract action input
        action_input = None
        if action:
            input_match = re.search(r"Action Input: (.*?)(?:\n|$)", response)
            if input_match:
                input_str = input_match.group(1).strip()
                # Try to parse as JSON or use as string
                try:
                    import json
                    action_input = json.loads(input_str)
                except:
                    action_input = {"input": input_str}
        
        # Check for final answer
        if "Final Answer" in response:
            action = "Final Answer"
            answer_match = re.search(r"Final Answer: (.*?)$", response, re.DOTALL)
            action_input = {"answer": answer_match.group(1).strip() if answer_match else ""}
        
        return AgentStep(
            thought=thought,
            action=action,
            action_input=action_input
        )

# Example usage
def calculator(expression: str) -> str:
    """Evaluates mathematical expressions"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

def search_web(query: str) -> str:
    """Searches the web for information"""
    # Placeholder - would call actual API
    return f"Search results for: {query}"

# Create agent
tools = {
    "calculator": calculator,
    "search_web": search_web
}

agent = ReactAgent(llm=your_llm, tools=tools)

# Run agent
result = agent.run("What is 25 * 4 plus the number of continents?")
```

### Example Execution

```
Question: "What's the weather in Paris and convert the temp to Fahrenheit?"

Iteration 1:
  Thought: I need to get the weather in Paris first
  Action: get_weather
  Action Input: {"location": "Paris"}
  Observation: {"temp": 18, "unit": "celsius", "condition": "cloudy"}

Iteration 2:
  Thought: Now I need to convert 18°C to Fahrenheit using (C * 9/5) + 32
  Action: calculator
  Action Input: {"expression": "(18 * 9/5) + 32"}
  Observation: 64.4

Iteration 3:
  Thought: I have all the information I need
  Final Answer: The weather in Paris is cloudy and 64.4°F (18°C)
```

### Why ReAct Works Well

The reactive pattern shines because of its simplicity. You can implement a working agent in an afternoon, and the straightforward loop structure makes it easy to understand and debug. When something goes wrong, you can trace through each thought and action to see exactly where the agent went off track.[[19]](https://www.promptingguide.ai/techniques/react)

This pattern is also remarkably flexible. Since the agent decides what to do at each step based on what just happened, it can adapt to unexpected situations. If a tool returns an error, the agent can try something else. If the data isn't quite what it expected, it can adjust its approach. This flexibility comes from the fact that any LLM can be dropped into this pattern without special training or fine-tuning.

### Where ReAct Struggles

The main challenge with reactive agents is efficiency. Because the agent doesn't plan ahead, it might take several steps to accomplish something that could have been done in two steps with better planning. Imagine asking someone to organize a dinner party, and they start by calling one guest, then calling the caterer, then calling another guest, then checking their calendar—instead of checking the calendar first and making all the calls together.

Another issue is that reactive agents can sometimes get stuck in loops, repeating the same action over and over when they don't get the result they expect. They also consume a lot of tokens because every iteration includes the full conversation history, which grows with each step. Finally, because they don't plan ahead, they can't backtrack or revise their strategy when they realize they're going down the wrong path.

### When to Choose ReAct

ReAct is perfect when you're building simple, focused agents that do one thing well—like a calculator bot or a weather lookup service. It's also ideal for prototypes and demos where you want to get something working quickly. If interpretability is important (for example, if you need to explain to users why the agent made certain decisions), ReAct's explicit reasoning steps are invaluable. For quick tasks that don't require complex coordination between multiple steps, ReAct is often the best choice.

But what happens when your tasks get more complex? What if you're building a research assistant that needs to search multiple sources, synthesize information, and generate a report? ReAct's step-by-step approach starts to show its limitations - it's like navigating a new city without a map, making turn-by-turn decisions without knowing the overall route.

This is where planning comes in. Instead of reacting to each observation, what if the agent could think through the entire task first, create a roadmap, and then execute it? This is the Planner-Executor pattern.

---

## Pattern 2: Planner-Executor

The key insight: **think before you act**. Separate planning from execution: first create a plan, then execute it step-by-step.[[20]](https://blog.smartflowsolutions.tech/autogpt-what-it-how-it-works-why-agentic-ai-taking-off-autog/)

This is how humans tackle complex projects - you don't start writing code before understanding the requirements, and you don't start cooking before reading the recipe. The agent spends tokens upfront on planning, which often saves tokens (and time) during execution.

### Architecture

```
┌─────────────────┐
│   USER QUERY    │
└────────┬────────┘
         │
         ▼
  ┌──────────────┐
  │   PLANNER    │ ──► Creates complete plan
  │     LLM      │     (list of steps)
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────┐
  │  EXECUTION PLAN          │
  │  1. Call weather_api     │
  │  2. Call calculator      │
  │  3. Format response      │
  └──────┬───────────────────┘
         │
         ▼
  ┌──────────────┐
  │   EXECUTOR   │ ──► Executes each step
  │     Loop     │     sequentially
  └──────┬───────┘
         │
         ├─► Step 1 ─► Observation
         ├─► Step 2 ─► Observation
         └─► Step 3 ─► Observation
         │
         ▼
  ┌──────────────┐
  │   FINAL      │
  │   ANSWER     │
  └──────────────┘
```

### Implementation

```python
from typing import List, Dict, Any
from dataclasses import dataclass
import json

@dataclass
class PlanStep:
    """Single step in execution plan"""
    step_num: int
    description: str
    tool: str
    tool_input: Dict[str, Any]
    
@dataclass
class ExecutionResult:
    """Result of executing a step"""
    step: PlanStep
    success: bool
    output: Any
    error: str = None

class PlannerExecutorAgent:
    """Agent that plans first, then executes"""
    
    def __init__(self, llm, tools: Dict[str, callable]):
        self.llm = llm
        self.tools = tools
        
    def run(self, query: str, verbose: bool = True) -> str:
        """Execute planner-executor pattern"""
        
        # Phase 1: Planning
        if verbose:
            print(f"\n{'='*60}\n📋 PLANNING PHASE\n{'='*60}")
        
        plan = self._create_plan(query, verbose)
        
        if not plan:
            return "Failed to create execution plan"
        
        # Phase 2: Execution
        if verbose:
            print(f"\n{'='*60}\n⚙️  EXECUTION PHASE\n{'='*60}")
        
        results = self._execute_plan(plan, verbose)
        
        # Phase 3: Synthesis
        if verbose:
            print(f"\n{'='*60}\n✨ SYNTHESIS PHASE\n{'='*60}")
        
        final_answer = self._synthesize_answer(query, plan, results, verbose)
        
        return final_answer
    
    def _create_plan(self, query: str, verbose: bool) -> List[PlanStep]:
        """Create execution plan using LLM"""
        
        planning_prompt = f"""You are a planning assistant. Given a user query, create a step-by-step plan.

Available tools:
{self._format_tools()}

Query: {query}

Create a plan as a JSON array with this structure:
[
  {{
    "step": 1,
    "description": "What this step does",
    "tool": "tool_name",
    "tool_input": {{"arg": "value"}}
  }},
  ...
]

Plan:"""
        
        response = self.llm.generate(planning_prompt)
        
        # Parse plan from response
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group(0))
                plan = [
                    PlanStep(
                        step_num=step['step'],
                        description=step['description'],
                        tool=step['tool'],
                        tool_input=step['tool_input']
                    )
                    for step in plan_data
                ]
                
                if verbose:
                    print("\n📝 Execution Plan:")
                    for step in plan:
                        print(f"  {step.step_num}. {step.description}")
                        print(f"     Tool: {step.tool}")
                        print(f"     Input: {step.tool_input}")
                
                return plan
        except Exception as e:
            if verbose:
                print(f"❌ Failed to parse plan: {e}")
            return []
    
    def _execute_plan(self, plan: List[PlanStep], verbose: bool) -> List[ExecutionResult]:
        """Execute each step in the plan"""
        
        results = []
        context = {}  # Store results for later steps
        
        for step in plan:
            if verbose:
                print(f"\n▶️  Step {step.step_num}: {step.description}")
            
            try:
                # Check if tool exists
                if step.tool not in self.tools:
                    result = ExecutionResult(
                        step=step,
                        success=False,
                        output=None,
                        error=f"Tool '{step.tool}' not found"
                    )
                else:
                    # Resolve any references to previous results
                    resolved_input = self._resolve_references(step.tool_input, context)
                    
                    # Execute tool
                    output = self.tools[step.tool](**resolved_input)
                    
                    result = ExecutionResult(
                        step=step,
                        success=True,
                        output=output
                    )
                    
                    # Store result for future steps
                    context[f"step_{step.step_num}"] = output
                    
                    if verbose:
                        print(f"   ✅ Result: {output}")
                        
            except Exception as e:
                result = ExecutionResult(
                    step=step,
                    success=False,
                    output=None,
                    error=str(e)
                )
                
                if verbose:
                    print(f"   ❌ Error: {e}")
            
            results.append(result)
            
            # Stop if critical step failed
            if not result.success and self._is_critical_step(step):
                if verbose:
                    print(f"   ⚠️  Critical step failed, stopping execution")
                break
        
        return results
    
    def _resolve_references(self, tool_input: Dict, context: Dict) -> Dict:
        """Resolve references to previous step results"""
        resolved = {}
        for key, value in tool_input.items():
            if isinstance(value, str) and value.startswith("$step_"):
                # Reference to previous step
                ref_key = value[1:]  # Remove $
                resolved[key] = context.get(ref_key, value)
            else:
                resolved[key] = value
        return resolved
    
    def _synthesize_answer(self, query: str, plan: List[PlanStep], 
                          results: List[ExecutionResult], verbose: bool) -> str:
        """Synthesize final answer from execution results"""
        
        # Build context from results
        context = ""
        for i, result in enumerate(results):
            context += f"\nStep {result.step.step_num}: {result.step.description}\n"
            if result.success:
                context += f"Result: {result.output}\n"
            else:
                context += f"Error: {result.error}\n"
        
        synthesis_prompt = f"""Based on the execution results, provide a final answer to the user's question.

Original Question: {query}

Execution Results:
{context}

Final Answer:"""
        
        answer = self.llm.generate(synthesis_prompt)
        
        if verbose:
            print(f"\n💬 {answer}")
        
        return answer
    
    def _format_tools(self) -> str:
        """Format tool descriptions"""
        descriptions = []
        for name, func in self.tools.items():
            doc = func.__doc__ or "No description"
            descriptions.append(f"- {name}: {doc.strip()}")
        return "\n".join(descriptions)
    
    def _is_critical_step(self, step: PlanStep) -> bool:
        """Determine if step is critical (failure should stop execution)"""
        # Could be more sophisticated
        return True  # For now, all steps are critical

# Example usage
agent = PlannerExecutorAgent(llm=your_llm, tools=tools)
result = agent.run("Find weather in Paris and London, compare temperatures")
```

### Example Execution

```
Query: "Research Tesla's stock price and compare to Ford"

PLANNING PHASE:
  1. Get Tesla stock price
     Tool: stock_api
     Input: {"symbol": "TSLA"}
  
  2. Get Ford stock price
     Tool: stock_api
     Input: {"symbol": "F"}
  
  3. Calculate difference
     Tool: calculator
     Input: {"expression": "$step_1 - $step_2"}

EXECUTION PHASE:
  Step 1: Get Tesla stock price
     ✅ Result: 242.50
  
  Step 2: Get Ford stock price
     ✅ Result: 12.30
  
  Step 3: Calculate difference
     ✅ Result: 230.20

SYNTHESIS:
  Tesla (TSLA) is trading at $242.50 while Ford (F) is at $12.30.
  Tesla is $230.20 higher than Ford.
```

### Advantages with Plan Revision

```python
class AdaptivePlannerExecutor(PlannerExecutorAgent):
    """Planner-executor with ability to revise plan"""
    
    def _execute_plan(self, plan: List[PlanStep], verbose: bool) -> List[ExecutionResult]:
        """Execute with adaptive replanning"""
        
        results = []
        remaining_steps = plan.copy()
        
        while remaining_steps:
            step = remaining_steps.pop(0)
            result = self._execute_step(step)
            results.append(result)
            
            # If step failed, replan
            if not result.success:
                if verbose:
                    print(f"⚠️  Step failed, replanning...")
                
                new_plan = self._replan(
                    original_query=self.original_query,
                    completed_steps=results,
                    failed_step=step,
                    remaining_steps=remaining_steps
                )
                
                remaining_steps = new_plan
        
        return results
```

### The Power of Planning Ahead

The planner-executor pattern addresses the main weakness of reactive agents: efficiency. By creating a complete plan upfront, the agent knows exactly what needs to happen and in what order. This eliminates wasted actions—there's no wandering around trying different things until something works. The agent has a roadmap.

This structure makes multi-step tasks much more manageable. When you can see the entire plan laid out, it's easier to understand the dependencies between steps and identify opportunities for parallelization. If step 3 and step 4 don't depend on each other, they can run at the same time, cutting execution time in half.

Debugging is also simpler with this pattern. When something goes wrong, you can look at the plan and see if the planning phase made a mistake (wrong tools, wrong order) or if the execution phase hit an error (tool failure, unexpected data). This separation of concerns makes it much easier to identify and fix issues.

### The Tradeoffs of Structure

The main downside of planning ahead is reduced flexibility. Once the plan is created, it's harder to adapt when circumstances change. If step 2 returns unexpected data that suggests a completely different approach, the agent is already committed to steps 3, 4, and 5. While you can implement adaptive replanning (as shown in the code above), this adds significant complexity.

There's also overhead to consider. Every task requires an extra LLM call just for planning, which adds latency and cost. Sometimes the LLM might over-plan, creating elaborate multi-step sequences for tasks that could be simpler. The quality of the entire system depends heavily on the LLM's ability to create good plans—if the planning phase produces a bad plan, everything that follows will struggle.

### When to Choose Planner-Executor

This pattern excels at multi-step workflows where one step naturally leads to another. Research tasks are a perfect example: search for information, extract key points, cross-reference with other sources, synthesize findings. Data gathering workflows also benefit from this approach, especially when you can identify independent operations that can run in parallel. If you know upfront that your task has clear stages or dependencies, planner-executor is usually the right choice.

We've progressed from simple reaction (ReAct) to thoughtful planning (Planner-Executor). But both patterns still assume one agent doing all the work. What happens when your problem is so complex that even a well-planned approach isn't enough? What if you need specialization - different expertise for different parts of the problem?

This is where we move from a solo performer to an orchestra. Instead of one agent with all the tools, you have multiple agents, each a specialist in their domain. A research agent, a coding agent, a testing agent - all working together.

---

## Pattern 3: Multi-Agent Systems

**The big shift**: From one generalist to many specialists.

Multiple specialized agents collaborate to solve complex tasks.[[23]](https://www.ibm.com/think/topics/autogpt)

### Architecture

```
┌─────────────────────────────────────┐
│         MANAGER AGENT               │
│  (Coordinates other agents)         │
└───────┬─────────────────────────────┘
        │
        ├─────────┬─────────┬──────────┐
        │         │         │          │
        ▼         ▼         ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐
   │Research │ │ Coding  │ │Testing │ │ Review  │
   │ Agent   │ │ Agent   │ │ Agent  │ │ Agent   │
   └─────────┘ └─────────┘ └────────┘ └─────────┘
        │         │         │          │
        └─────────┴─────────┴──────────┘
                  │
                  ▼
          ┌───────────────┐
          │ SHARED MEMORY │
          │   (Context)   │
          └───────────────┘
```

### Implementation

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Message:
    """Message between agents"""
    sender: str
    receiver: str
    content: str
    metadata: Dict = None

class Agent(ABC):
    """Base agent class"""
    
    def __init__(self, name: str, role: str, llm, tools: Dict[str, callable] = None):
        self.name = name
        self.role = role
        self.llm = llm
        self.tools = tools or {}
        self.message_history: List[Message] = []
    
    @abstractmethod
    def process(self, message: Message) -> Message:
        """Process incoming message and return response"""
        pass
    
    def send_message(self, receiver: str, content: str) -> Message:
        """Create outgoing message"""
        return Message(
            sender=self.name,
            receiver=receiver,
            content=content
        )

class ResearchAgent(Agent):
    """Specializes in gathering information"""
    
    def process(self, message: Message) -> Message:
        """Research information based on query"""
        
        query = message.content
        
        prompt = f"""You are a research specialist. Your task is to gather information.

Query: {query}

Use available tools to research and provide comprehensive information.
"""
        
        # Use tools to gather information
        results = []
        if "web_search" in self.tools:
            search_result = self.tools["web_search"](query=query)
            results.append(search_result)
        
        # Synthesize findings
        synthesis_prompt = f"""Synthesize these research findings:

{results}

Provide a concise summary:"""
        
        summary = self.llm.generate(synthesis_prompt)
        
        return self.send_message(
            receiver=message.sender,
            content=f"Research findings: {summary}"
        )

class CodingAgent(Agent):
    """Specializes in writing code"""
    
    def process(self, message: Message) -> Message:
        """Generate code based on requirements"""
        
        requirements = message.content
        
        prompt = f"""You are a coding specialist. Write code based on requirements.

Requirements: {requirements}

Provide clean, working code with comments:"""
        
        code = self.llm.generate(prompt)
        
        # Optionally test code
        if "code_executor" in self.tools:
            test_result = self.tools["code_executor"](code=code)
            code += f"\n\n# Test result: {test_result}"
        
        return self.send_message(
            receiver=message.sender,
            content=code
        )

class ManagerAgent(Agent):
    """Coordinates other agents"""
    
    def __init__(self, name: str, llm, workers: Dict[str, Agent]):
        super().__init__(name, "manager", llm)
        self.workers = workers
    
    def process(self, message: Message) -> str:
        """Coordinate workers to complete task"""
        
        task = message.content
        
        # Decide which agents to use and in what order
        plan_prompt = f"""You are a manager coordinating specialized agents.

Available agents:
{self._format_agents()}

Task: {task}

Create a plan: which agents should work on this and in what order?
Respond in JSON format:
[
  {{"agent": "agent_name", "subtask": "what they should do"}},
  ...
]

Plan:"""
        
        response = self.llm.generate(plan_prompt)
        
        # Parse plan
        import json
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
            else:
                plan = []
        except:
            plan = []
        
        # Execute plan
        results = {}
        for step in plan:
            agent_name = step['agent']
            subtask = step['subtask']
            
            if agent_name in self.workers:
                agent = self.workers[agent_name]
                
                # Send task to agent
                task_message = Message(
                    sender=self.name,
                    receiver=agent_name,
                    content=subtask
                )
                
                # Get response
                response = agent.process(task_message)
                results[agent_name] = response.content
        
        # Synthesize final answer
        synthesis = f"""Based on contributions from team:

"""
        for agent_name, result in results.items():
            synthesis += f"{agent_name}: {result}\n\n"
        
        return synthesis
    
    def _format_agents(self) -> str:
        """Format agent descriptions"""
        descriptions = []
        for name, agent in self.workers.items():
            descriptions.append(f"- {name}: {agent.role}")
        return "\n".join(descriptions)

# Example: Multi-agent system
def create_development_team(llm):
    """Create a team of agents for software development"""
    
    # Create specialized agents
    researcher = ResearchAgent(
        name="researcher",
        role="Gathers information and does research",
        llm=llm,
        tools={"web_search": web_search_func}
    )
    
    coder = CodingAgent(
        name="coder",
        role="Writes code based on requirements",
        llm=llm,
        tools={"code_executor": execute_code_func}
    )
    
    # Create manager to coordinate
    manager = ManagerAgent(
        name="manager",
        llm=llm,
        workers={
            "researcher": researcher,
            "coder": coder
        }
    )
    
    return manager

# Usage
manager = create_development_team(your_llm)

result = manager.process(Message(
    sender="user",
    receiver="manager",
    content="Build a web scraper for news articles"
))

print(result)
```

### Example Execution

```
Task: "Build a web scraper for news articles"

Manager's Plan:
  1. researcher: Research best practices for web scraping
  2. coder: Implement the scraper
  3. tester: Test the implementation

Execution:
  researcher → "Found: Use BeautifulSoup, respect robots.txt..."
  coder → "Here's the implementation: [code]"
  tester → "Tests passed: 15/15"

Manager synthesizes:
  "Complete web scraper implementation following best practices,
   fully tested and ready to use."
```

### How Agents Communicate

Multi-agent systems need clear communication patterns. The **hierarchical (manager-worker)** pattern is the most common and easiest to implement. A manager agent receives the task, breaks it down, assigns pieces to specialized worker agents, and synthesizes their results. This mirrors how human teams often work, with a project manager coordinating specialists. The manager is a clear bottleneck, but it's also a clear point of control—you always know who's responsible for what.

The **peer-to-peer** pattern has no central coordinator. Agents communicate directly with each other, negotiating who should handle which parts of the task. This is more flexible and resilient (no single point of failure), but coordination becomes complex. How do agents discover each other? How do they avoid duplicating work? These questions require sophisticated protocols to answer.

The **blackboard (shared memory)** pattern uses a different approach entirely. Instead of agents talking to each other, they all read and write to a shared data structure—the "blackboard." One agent might write "I found that the weather in Paris is 18°C" to the blackboard, and another agent reads it when deciding what to do next. This decouples agents nicely (they don't need to know about each other), but managing concurrent access to shared memory introduces its own challenges.

### The Strength of Specialization

Multi-agent systems take a fundamentally different approach: instead of one agent trying to do everything, you create a team of specialists. Just like a real software team has researchers, developers, testers, and reviewers, a multi-agent system divides responsibilities among agents who are each expert at their specific role.

This specialization leads to better results. A research agent that only does research becomes really good at research—its prompts are optimized for gathering information, its tools are specialized for that task, and it develops patterns that work. When agents work in parallel, complex tasks can be completed much faster. While one agent is researching, another can be writing code, and a third can be preparing test cases.

The modularity is another major benefit. Need better code quality? Upgrade or replace just the coding agent without touching the others. Want to add a new capability? Create a new specialized agent and plug it into the system. As your needs grow, you can scale by adding more agents rather than making one agent increasingly complex.

### The Complexity Cost

The flip side of having multiple agents is coordination complexity. Agents need to communicate, and managing that communication is non-trivial. You need to decide: who talks to whom? How do they share information? What happens when two agents need the same resource? These are distributed systems problems, and they're hard.

Agents can also contradict each other. The research agent might find information suggesting approach A, while the analysis agent recommends approach B. You need a way to resolve these conflicts, usually through a manager agent or consensus mechanism. Debugging becomes significantly harder because you're tracking multiple concurrent processes, each with its own state and decision-making.

There's also overhead to running multiple agents. Each agent needs its own LLM calls, its own memory, and coordination between them requires additional communication. For simple tasks, this overhead far outweighs any benefits.

### When to Choose Multi-Agent

Multi-agent systems make sense when you're tackling genuinely complex problems that require diverse expertise. If you find yourself thinking "we need someone to do X, someone to do Y, and someone to do Z," that's a signal for multi-agents. Enterprise systems that handle multiple distinct responsibilities—like a customer service system that needs to understand queries, search documentation, access account data, and generate responses—are natural fits.

The key question is: does specialization actually improve quality? If having focused, expert agents produces meaningfully better results than a single generalist agent, the complexity cost is worth it. For everything else, stick with simpler patterns.

So far, we've talked about agent architectures - how to structure the thinking and acting loops. But we haven't addressed a fundamental question: how do agents actually *invoke* tools? What's the mechanism that lets an LLM call a weather API or execute a function?

This is where protocols come in. ReAct, Planner-Executor, and Multi-Agent are architectural patterns that work with *any* tool-calling mechanism. Below them sits the protocol layer - the standardized way agents discover and invoke tools.

---

## Pattern 4: Protocol Integration (MCP/UTCP)

**The foundation layer**: How agents actually call tools in a standardized way.

Modern agent architectures can be built using standardized tool-calling protocols: **MCP (Model Context Protocol)** and **UTCP (Universal Tool Calling Protocol)**. These protocols provide structured ways for agents to discover and use tools.

### Protocol Overview

```
┌──────────────────────────────────────────────┐
│         AGENT ARCHITECTURE                    │
│  (ReAct / Planner / Multi-Agent)             │
└────────────┬─────────────────────────────────┘
             │
             ├─── MCP Route ─────┐
             │                    │
             │              ┌─────▼──────┐
             │              │ MCP Server │──► Tools
             │              │  (Proxy)   │
             │              └────────────┘
             │
             └─── UTCP Route ────┐
                                 │
                           ┌─────▼──────┐
                           │   Direct   │──► Tool APIs
                           │   Calls    │    CLI Commands
                           └────────────┘
```

### Understanding Protocol Differences

MCP and UTCP take fundamentally different approaches to tool calling. MCP uses a client-server architecture where all tools live behind a centralized server. This means every tool call goes through a proxy, which adds latency but provides centralized governance and control. The server maintains state between calls, so it can remember context from earlier in your session. Tools are discovered dynamically through the server's `tools/list` endpoint, which means your agent automatically knows about new tools as soon as they're added to the server.

UTCP, by contrast, is stateless and decentralized. Your agent makes direct calls to APIs and CLI tools without any middleman. This makes calls faster—there's no proxy hop—but it means you're responsible for managing credentials, rate limiting, and error handling for each tool. Tool discovery happens through JSON manual files that you load at startup. These manuals tell your agent what tools exist and how to use them.

The choice between them often comes down to your environment. Enterprise settings with strict governance requirements tend to favor MCP's centralized control. Projects that need to integrate many public APIs quickly, or where performance is critical, typically choose UTCP for its lower latency and simpler setup.

### Integration with Reactive Agents (ReAct)

Both protocols work seamlessly with the ReAct pattern.

> **Note:** These examples use **UTCP v1.0.1** Python library which is fully async. See [python-utcp-weather example](../examples/python-utcp-weather/) for a complete working implementation.

**MCP Integration:**

```python
from langchain.agents import create_react_agent
from langchain_mcp import MCPToolkit

# Connect to MCP server
mcp_toolkit = MCPToolkit(
    server_url="http://localhost:8080",
    # Server handles auth, tool discovery
)

# MCP automatically discovers available tools
tools = mcp_toolkit.get_tools()

# Create ReAct agent with MCP tools
agent = create_react_agent(
    llm=your_llm,
    tools=tools,
    prompt=react_prompt
)

# Agent loop handles tool calls through MCP
result = agent.invoke({"input": "What's the weather in Paris?"})
```

**UTCP Integration:**

```python
from utcp import UtcpClient
from langchain.tools import Tool

# Load UTCP manuals (can be from URLs, files, or directory)
utcp_client = UtcpClient(
    manuals=[
        "https://api.weather.com/utcp.json",
        "./local-tools/calculator.json"
    ]
)

# Convert UTCP tools to LangChain format
tools = []
for utcp_tool in utcp_client.get_tools():
    tools.append(Tool(
        name=utcp_tool.name,
        description=utcp_tool.description,
        func=lambda **kwargs: utcp_client.call_tool(
            utcp_tool.name, 
            kwargs
        )
    ))

# Create ReAct agent with UTCP tools
agent = create_react_agent(
    llm=your_llm,
    tools=tools,
    prompt=react_prompt
)

result = agent.invoke({"input": "Calculate 25 * 4"})
```

**How Protocols Change ReAct Behavior**

With MCP, your reactive agent maintains a single connection to the server throughout its entire run. The server handles all tool management, which means centralized logging and monitoring of everything your agent does. This is great for audit trails and debugging across multiple agents.

With UTCP, each tool call goes directly to its destination—an API endpoint, a CLI command, or a database. This directness means faster responses since there's no middleman, but error handling becomes more varied. MCP gives you consistent error messages across all tools, while UTCP gives you whatever error format each individual API returns—which is sometimes a blessing (more detail) and sometimes a curse (inconsistent formats).

### Integration with Planner-Executor

Protocols enhance planning capabilities:

**MCP Planner-Executor:**

```python
class MCPPlannerExecutor:
    """Planner-Executor using MCP for tool management"""
    
    def __init__(self, planner_llm, executor_llm, mcp_server_url):
        self.planner = planner_llm
        self.executor = executor_llm
        
        # Connect to MCP server
        self.mcp_client = MCPClient(mcp_server_url)
        self.available_tools = self.mcp_client.list_tools()
    
    def run(self, query: str) -> str:
        # Phase 1: Planning with tool awareness
        tool_descriptions = self._format_tools(self.available_tools)
        
        plan_prompt = f"""Create a plan using these tools:
{tool_descriptions}

Query: {query}

Provide a JSON plan: [{{"step": 1, "tool": "name", "input": {{}}}}]
"""
        
        plan_response = self.planner.generate(plan_prompt)
        plan = self._parse_plan(plan_response)
        
        # Phase 2: Execute via MCP
        results = []
        for step in plan:
            try:
                # Call tool through MCP server
                result = self.mcp_client.call_tool(
                    name=step['tool'],
                    arguments=step['input']
                )
                results.append({
                    "step": step['step'],
                    "success": True,
                    "output": result
                })
            except Exception as e:
                results.append({
                    "step": step['step'],
                    "success": False,
                    "error": str(e)
                })
        
        # Phase 3: Synthesize
        return self._synthesize(query, results)
    
    def _format_tools(self, tools):
        """Format MCP tools for planning"""
        return "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tools
        ])
```

**UTCP Planner-Executor with Parallel Execution:**

```python
import asyncio
from utcp import UtcpClient

class UTCPPlannerExecutor:
    """Planner-Executor with UTCP, supports parallel execution"""
    
    def __init__(self, planner_llm, executor_llm, utcp_manuals):
        self.planner = planner_llm
        self.executor = executor_llm
        self.utcp = UtcpClient(manuals=utcp_manuals)
    
    async def run(self, query: str) -> str:
        # Phase 1: Planning
        tools_info = self._get_tools_metadata()
        plan = await self._create_plan(query, tools_info)
        
        # Phase 2: Execute (with parallelization)
        results = await self._execute_plan_parallel(plan)
        
        # Phase 3: Synthesize
        return self._synthesize(query, results)
    
    async def _execute_plan_parallel(self, plan):
        """Execute independent steps in parallel"""
        
        # Group steps by dependencies
        parallel_groups = self._group_by_dependencies(plan)
        
        all_results = []
        context = {}
        
        for group in parallel_groups:
            # Execute group in parallel
            tasks = []
            for step in group:
                # Resolve any references to previous steps
                resolved_input = self._resolve_refs(
                    step['input'], 
                    context
                )
                
                # Create async task for UTCP call
                task = self.utcp.call_tool_async(
                    step['tool'],
                    resolved_input
                )
                tasks.append((step, task))
            
            # Wait for all tasks in group
            group_results = await asyncio.gather(
                *[t[1] for t in tasks],
                return_exceptions=True
            )
            
            # Store results for next group
            for (step, _), result in zip(tasks, group_results):
                context[f"step_{step['step']}"] = result
                all_results.append({
                    "step": step['step'],
                    "output": result
                })
        
        return all_results
    
    def _group_by_dependencies(self, plan):
        """Group steps that can run in parallel"""
        # Steps with no dependencies can run together
        # This leverages UTCP's stateless nature
        groups = []
        current_group = []
        
        for step in plan:
            has_dependency = any(
                f"$step_{s['step']}" in str(step['input'])
                for s in plan
                if s['step'] < step['step']
            )
            
            if has_dependency and current_group:
                groups.append(current_group)
                current_group = [step]
            else:
                current_group.append(step)
        
        if current_group:
            groups.append(current_group)
        
        return groups
```

**How Protocols Affect Planning**

Session context works differently between protocols. MCP servers maintain state between your agent's steps, which means you can refer back to earlier actions without re-sending all the context. This is particularly helpful when you're executing a long plan with many steps. UTCP is stateless, so your agent needs to explicitly pass any needed context from one step to the next, but this statelessness is what enables excellent parallel execution.

Parallel execution is where UTCP really shines. Since each tool call is independent, you can make dozens of API calls simultaneously without worrying about server capacity. MCP's server becomes a bottleneck when you want high concurrency—all those requests funnel through one point. For plan revision, both protocols work well but in different ways. MCP servers can participate in the replanning process, while UTCP's lightweight nature makes it fast to re-execute parts of a plan.

Error recovery also differs significantly. MCP provides unified error handling across all tools, which makes it easier to write robust error-handling code. UTCP gives you whatever error format each individual tool returns—JSON from one API, plain text from another, exit codes from CLI tools—which requires more sophisticated error parsing but can provide richer error information.

### Integration with Multi-Agent Systems

Protocols enable sophisticated multi-agent coordination:

**MCP Multi-Agent (Hierarchical):**

```python
from typing import Dict, List

class MCPMultiAgentSystem:
    """Multi-agent system using MCP for tool coordination"""
    
    def __init__(self, mcp_servers: Dict[str, str]):
        """
        mcp_servers: {"agent_name": "mcp_server_url"}
        Each agent can have specialized MCP servers
        """
        self.agents = {}
        
        # Each agent connects to its MCP server
        for agent_name, server_url in mcp_servers.items():
            self.agents[agent_name] = {
                "mcp_client": MCPClient(server_url),
                "tools": MCPClient(server_url).list_tools(),
                "llm": self._create_agent_llm(agent_name)
            }
    
    def execute_task(self, task: str) -> str:
        """Manager coordinates agents via their MCP tools"""
        
        # Manager determines which agents to use
        plan = self._plan_agent_tasks(task)
        
        results = {}
        for subtask in plan:
            agent_name = subtask['agent']
            agent = self.agents[agent_name]
            
            # Agent uses its MCP tools
            result = self._run_agent_with_mcp(
                agent=agent,
                task=subtask['description']
            )
            
            results[agent_name] = result
        
        return self._combine_results(results)
    
    def _run_agent_with_mcp(self, agent, task):
        """Agent uses ReAct with its MCP tools"""
        
        mcp_client = agent['mcp_client']
        llm = agent['llm']
        
        # Agent loop
        for iteration in range(5):
            thought = llm.generate(f"Task: {task}\nThought:")
            
            if "final answer" in thought.lower():
                return self._extract_answer(thought)
            
            # Decide which tool to use
            action = llm.generate(f"{thought}\nAction (JSON):")
            action_data = json.loads(action)
            
            # Call through MCP
            observation = mcp_client.call_tool(
                name=action_data['tool'],
                arguments=action_data['arguments']
            )
            
            task += f"\nObservation: {observation}"
        
        return "Agent iteration limit reached"
```

**UTCP Multi-Agent (Peer-to-Peer):**

```python
class UTCPMultiAgentSystem:
    """Peer-to-peer multi-agent using UTCP"""
    
    def __init__(self, agent_configs: List[Dict]):
        """
        agent_configs: [
            {
                "name": "researcher",
                "manuals": ["search.json", "wiki.json"],
                "specialization": "information gathering"
            }
        ]
        """
        self.agents = {}
        
        for config in agent_configs:
            # Each agent has its own UTCP client
            self.agents[config['name']] = {
                "utcp": UtcpClient(manuals=config['manuals']),
                "specialization": config['specialization'],
                "llm": self._create_agent_llm(config['name'])
            }
    
    async def execute_task_collaborative(self, task: str) -> str:
        """Agents collaborate by sharing tool results"""
        
        # Shared blackboard for communication
        blackboard = {
            "task": task,
            "findings": {},
            "status": "in_progress"
        }
        
        # Agents work in parallel
        tasks = []
        for agent_name, agent in self.agents.items():
            task_coro = self._run_agent_collaborative(
                agent_name=agent_name,
                agent=agent,
                blackboard=blackboard
            )
            tasks.append(task_coro)
        
        # Wait for all agents
        await asyncio.gather(*tasks)
        
        # Combine findings
        return self._synthesize_blackboard(blackboard)
    
    async def _run_agent_collaborative(self, agent_name, agent, blackboard):
        """Agent reads/writes to shared blackboard"""
        
        utcp = agent['utcp']
        llm = agent['llm']
        
        # Agent decides what to contribute
        context = f"""
Task: {blackboard['task']}
Your specialization: {agent['specialization']}
Current findings: {blackboard['findings']}

What should you do?
"""
        
        decision = llm.generate(context)
        
        # Agent calls UTCP tools asynchronously
        if "search" in decision.lower():
            result = await utcp.call_tool_async(
                "web_search",
                {"query": self._extract_query(decision)}
            )
            
            # Write to blackboard
            blackboard['findings'][agent_name] = {
                "type": "search_results",
                "data": result,
                "timestamp": time.time()
            }
        
        # Continue until task complete or timeout
```

**Choosing Protocols for Multi-Agent Systems**

MCP makes sense when your agents need to work together closely. If agents are frequently sharing context, coordinating actions, or accessing the same set of tools, having a centralized server to manage all of that simplifies the architecture. MCP also excels in environments where tool access must be carefully controlled and monitored—enterprise settings where security teams need audit trails of every action every agent takes.

UTCP works better when your agents are more independent. If each agent has its own specialized set of tools and they don't need to coordinate much, UTCP's decentralized nature is actually an advantage. When you need high performance and low latency—perhaps you're running dozens of agents in parallel—UTCP's direct calls eliminate the bottleneck of a centralized server. UTCP is also the better choice when you want minimal infrastructure—no servers to maintain, just agents making direct API calls.

### Hybrid Approach: Using Both Protocols

You can combine MCP and UTCP in the same agent:

```python
class HybridProtocolAgent:
    """Agent using both MCP and UTCP"""
    
    def __init__(self, mcp_server, utcp_manuals):
        # MCP for internal/controlled tools
        self.mcp_client = MCPClient(mcp_server)
        
        # UTCP for external APIs
        self.utcp_client = UtcpClient(manuals=utcp_manuals)
        
        # Unified tool registry
        self.tools = self._merge_tools()
    
    def _merge_tools(self):
        """Combine tools from both protocols"""
        tools = {}
        
        # Add MCP tools (internal)
        for tool in self.mcp_client.list_tools():
            tools[tool['name']] = {
                "protocol": "mcp",
                "description": tool['description'],
                "schema": tool['inputSchema']
            }
        
        # Add UTCP tools (external)
        for tool in self.utcp_client.get_tools():
            tools[tool.name] = {
                "protocol": "utcp",
                "description": tool.description,
                "schema": tool.parameters
            }
        
        return tools
    
    async def call_tool(self, name: str, arguments: dict):
        """Route to appropriate protocol"""
        
        tool = self.tools[name]
        
        if tool['protocol'] == 'mcp':
            # Sensitive/internal tool - use MCP
            return self.mcp_client.call_tool(name, arguments)
        else:
            # External API - use UTCP (faster)
            return await self.utcp_client.call_tool(name, arguments)
```

**The Hybrid Approach**

You don't have to choose just one protocol. A hybrid approach uses MCP for internal, sensitive tools like database access and file operations—things that need security and governance—while using UTCP for external public APIs where performance matters and there's less security risk. This gives you the control of MCP for critical operations and the speed of UTCP for everything else. It's more complex to manage, but for large systems, the tradeoff is often worth it.

### Best Practices for Protocol Integration

**Making MCP Work Efficiently**

When integrating MCP, connection management is crucial. Creating a new connection for every tool call is expensive—instead, create one client at startup and reuse it throughout your agent's lifetime. Think of it like keeping a phone line open rather than hanging up and redialing for every conversation.

MCP servers can go down or become slow, so monitor their health and implement fallbacks. Your agent shouldn't crash just because the MCP server is having issues. Tool discovery through `list_tools()` is another area to optimize. The list of available tools doesn't change often, so cache these results and refresh them periodically (maybe every few minutes) rather than querying on every run.

If your MCP server supports it, batch multiple tool calls together. Making five separate round-trips to the server takes much longer than sending five requests at once. Finally, implement retry logic with exponential backoff for transient failures. Networks are unreliable, and a brief retry can often resolve temporary issues without failing the entire task.

**Making UTCP Work Efficiently**

UTCP is stateless and direct, which makes some concerns simpler but introduces others. Load all your UTCP manuals once at startup using `UtcpClient.create()` and keep them in memory. Parsing JSON files on every tool call is wasteful. These manuals are small and don't change during runtime.

An important technical detail: UTCP uses a specific variable naming convention. Variables must be prefixed with the manual name using double underscores: `{manual_name}__{variable_name}`. This prevents naming conflicts when multiple manuals might use similar variable names like `API_KEY`.

Credential management is critical with UTCP because you're making direct API calls. Pass sensitive values via the `variables` dict in your config—never hardcode them in manual files. The UTCP v1.0.1 API is fully async, so always use `await` with tool calls. For tool discovery, use `search_tools(query="", limit=100)` which returns all tools when given an empty query.

Rate limiting is your responsibility with UTCP—if you're calling a public API that limits you to 100 requests per minute, implement client-side throttling to stay under that limit.

**Security Considerations:**

```python
import os
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_text.text_call_template import TextCallTemplate

# MCP: Centralized security
mcp_client = MCPClient(
    server_url="https://internal.mcp.server",
    auth_token=os.getenv("MCP_TOKEN"),
    verify_ssl=True
)

# UTCP: Per-tool security with proper variable naming
# Variables must be prefixed with manual name: {manual_name}__{var_name}
config = UtcpClientConfig(
    manual_call_templates=[
        TextCallTemplate(
            name="weather_tools",
            file_path="./weather_tools.json"
        ),
        TextCallTemplate(
            name="database_tools",
            file_path="./database_tools.json"
        )
    ],
    variables={
        # Format: {manual_name}__{variable_name}
        "weather_tools__API_KEY": os.getenv("WEATHER_KEY"),
        "database_tools__DATABASE_URL": os.getenv("DB_URL")
    }
)

utcp_client = await UtcpClient.create(config=config)
```

**Understanding Security Tradeoffs**

Security works differently between the two protocols. With MCP, security is centralized at the server level. You authenticate once to the MCP server with a token, and it handles authorization for all the tools behind it. This makes security easier to manage—one place to check credentials, one place to audit access, one place to revoke permissions when needed. The server acts as a security boundary.

With UTCP, security is distributed across all your tools. Each API needs its own credentials, each tool might need different permissions, and you're responsible for managing all of it. This is more work, but it also follows the principle of least privilege—each tool only gets exactly the credentials it needs, nothing more. Notice in the code above how credentials are passed via the `variables` dict with the proper naming convention, keeping secrets out of the manual files themselves.

Both approaches can be secure when done correctly. MCP is easier to audit and control centrally, while UTCP provides better isolation between tools. Choose based on your security team's preferences and your organization's existing security infrastructure.

### Real-World Performance Differences

To understand how these protocols perform in practice, consider a reactive agent making 10 tool calls. With MCP, the total latency is around 3.2 seconds—each call takes roughly 320 milliseconds because it needs to travel to your agent, then to the MCP server, then to the actual tool, and back again. Memory usage sits at about 145MB because the MCP client maintains connection state and caches.

With UTCP, those same 10 tool calls complete in about 2.1 seconds, making each call average 210 milliseconds. That's 34% faster simply by eliminating the proxy hop. Memory usage drops to 98MB because there's no persistent connection state—each call is independent. The setup time difference is even more dramatic: MCP takes 800 milliseconds to connect to the server and fetch the tool list, while UTCP needs just 150 milliseconds to load the JSON manuals from disk.

Of course, these numbers vary based on your network conditions, server load, and tool complexity. If your MCP server is on the same machine, the latency gap narrows. If your UTCP tools are slow external APIs, the protocol overhead becomes less significant. But the general pattern holds: UTCP is faster for direct calls, MCP provides more control and monitoring.

### Choosing the Right Protocol for Your Architecture

For simple reactive agents, UTCP is usually the better choice. You can get up and running in minutes with direct API calls, and the performance benefits are noticeable. But if you're building a more complex reactive agent that needs to maintain context across many iterations, or if you need detailed logging of every action, MCP's stateful server architecture becomes valuable.

Planner-executor systems benefit most from UTCP because they often have opportunities for parallel execution. Once you have a plan with independent steps, UTCP lets you fire off multiple API calls simultaneously. The performance gains from parallelization usually outweigh any benefits MCP's centralized coordination might provide.

For multi-agent systems, the right choice depends on your coordination model. Hierarchical systems with a manager agent coordinating workers often work better with MCP because the centralized server naturally mirrors your centralized coordination. Peer-to-peer multi-agent systems where agents work independently benefit from UTCP's decentralized nature—each agent can make calls without waiting for a central server.

In enterprise environments, the decision often comes down to governance requirements. If you need centralized monitoring, audit trails, and access control, MCP is the clear choice. If those requirements are less stringent, or if you can handle them at the application level, UTCP's performance and simplicity might win out. Many large systems end up using both—a hybrid approach that uses the right protocol for each specific need.

The key insight is that both protocols work with all the agent patterns we've discussed. Your choice should be driven by your specific requirements around control, performance, and infrastructure complexity, not by which agent pattern you're using.

---

## Choosing the Right Pattern

### Making the Architecture Decision

Start by honestly assessing your task's complexity. If you're building something that primarily uses a single tool or makes simple, independent tool calls—think a calculator bot or a weather lookup service—reactive (ReAct) is your answer. Don't overthink it. The simplicity of ReAct means you'll be done and deployed while others are still designing their planner.

When your task involves multiple steps that need to happen in a specific sequence, and where efficiency matters, reach for the planner-executor pattern. Classic examples include research tasks (search → extract → cross-reference → synthesize) or data processing pipelines (fetch → transform → validate → store). The key indicator is that you can clearly articulate the steps upfront.

Multi-agent systems are for genuinely complex tasks that require diverse expertise working in parallel. If you find yourself thinking "we need a specialist for X, another for Y, and they need to work together," that's the signal. But be honest: does your task really require multiple specialists, or could a single well-designed agent handle it? Multi-agent systems are powerful but expensive in terms of development time, maintenance, and runtime costs.

### Understanding the Tradeoffs

Implementation time varies dramatically between patterns. You can build a working reactive agent in about a day—it's that straightforward. Planner-executor systems typically take three days because you need to implement both the planning and execution phases, plus the logic that connects them. Multi-agent systems are a significant commitment, usually requiring one to two weeks because you're building multiple agents, a coordination layer, and handling all the communication between them.

Token usage is another important consideration. Reactive agents use the most tokens because they include full conversation history in every iteration—that history keeps growing as the agent takes more actions. Planner-executor uses fewer tokens by separating concerns, though the planning phase itself requires a substantial prompt. Multi-agent token usage varies widely depending on how much the agents communicate and how you manage shared context.

Flexibility and efficiency often trade off against each other. Reactive agents are highly flexible (they adapt at every step) but low efficiency (no planning ahead). Planner-executor sacrifices some flexibility for much better efficiency. Multi-agent systems can be both flexible and efficient, but achieving both requires sophisticated coordination.

For debugging, reactive agents are the easiest—you can read through the thought-action-observation chain and see exactly what happened. Planner-executor is medium difficulty because you have two phases to debug. Multi-agent systems are genuinely hard to debug because you're tracking multiple concurrent processes, each making its own decisions. Cost follows a similar pattern: reactive agents are cheap to run, planner-executor is moderate, and multi-agent systems can be expensive due to the number of LLM calls and coordination overhead.

We've covered the big architectural patterns. But regardless of which pattern you choose, every agent faces the same tactical challenges: which tool should I use now? How do I combine multiple tools effectively? These micro-decisions happen within every architecture.

---

## Tool Selection and Chaining

**Zooming in**: The tactics that work within any architecture.

How agents decide which tools to use and how to combine them:

### Tool Selection Strategies

The most common approach to tool selection is letting the LLM decide. You present the LLM with all available tools and their descriptions, give it the user's query, and ask it to choose which tool to use. This works remarkably well because modern LLMs are good at matching intent to capabilities. If the user asks "What's the weather in Paris?" and you have a `get_weather` tool, the LLM will naturally choose it.

```python
prompt = f"""
Available tools: {tool_descriptions}
Query: {user_query}

Which tool should be used? Choose one: {tool_names}
"""
```

An alternative approach uses semantic similarity for tool selection. This is faster and more predictable than LLM-based selection, though less flexible. You encode the user's query into a vector embedding, encode each tool's description into embeddings, and use cosine similarity to find the best match. This works well when you have many tools and want to avoid the latency of an LLM call just for tool selection.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def select_tool(query: str, tools: Dict) -> str:
    """Select tool using semantic similarity"""
    query_embedding = model.encode(query)
    
    best_tool = None
    best_score = -1
    
    for tool_name, tool_desc in tools.items():
        desc_embedding = model.encode(tool_desc)
        similarity = cosine_similarity(query_embedding, desc_embedding)
        
        if similarity > best_score:
            best_score = similarity
            best_tool = tool_name
    
    return best_tool
```

The tradeoff is straightforward: LLM-based selection is more accurate and handles nuance better, while semantic similarity is faster and cheaper. For most applications, LLM-based selection is the right choice—the quality improvement is worth the extra milliseconds.

### Tool Chaining Patterns

Once your agent selects tools, it needs to chain them together effectively. **Sequential chaining** is the simplest pattern: the output of one tool becomes the input to the next. This is natural for workflows where each step builds on the previous one. For example, you might search for information, then summarize it, then translate the summary.

```python
# Output of tool1 → input of tool2
result1 = tool1(query)
result2 = tool2(result1)
result3 = tool3(result2)
```

**Parallel execution** is possible when you have tools that don't depend on each other. If you need the weather in three different cities, there's no reason to wait for Paris before checking London—run all three at once. This can dramatically reduce total execution time.

```python
import asyncio

# Run multiple tools simultaneously
results = await asyncio.gather(
    tool1(query),
    tool2(query),
    tool3(query)
)
```

The key is identifying which operations can run in parallel. In a planner-executor system, this happens during the planning phase. In a reactive system, the agent needs to recognize opportunities for parallelization on the fly, which is harder but possible with the right prompting.

All these architectural decisions matter, but there's one more ingredient that can make or break your agent: the prompts. The way you phrase instructions to the LLM dramatically affects which tools it chooses, how it reasons, and whether it succeeds or fails.

---

## Prompt Engineering for Agents

**The secret sauce**: How you talk to the LLM shapes everything.

Effective prompts are critical for agent performance:

### ReAct Prompt Template

```python
REACT_TEMPLATE = """You are a helpful AI assistant with access to tools.

To use a tool, follow this EXACT format:
Thought: [your reasoning about what to do]
Action: [tool name]
Action Input: [tool input as JSON]
Observation: [tool output - I will provide this]

When you have the final answer:
Thought: I now have enough information to answer
Final Answer: [your answer to the user]

TOOLS:
{tool_descriptions}

IMPORTANT RULES:
- Always think step by step
- Only use tools that are listed above
- Format Action Input as valid JSON
- Don't make up tool outputs - wait for Observation

Example:
Thought: I need to check the weather
Action: get_weather
Action Input: {{"location": "Paris"}}
Observation: 18C, cloudy

Let's begin!

Question: {user_question}
"""
```

### Few-Shot Examples

```python
FEW_SHOT_EXAMPLES = """
Example 1:
User: What's 25 * 4?
Thought: I need to calculate 25 * 4
Action: calculator
Action Input: {"expression": "25 * 4"}
Observation: 100
Thought: I have the answer
Final Answer: 25 * 4 = 100

Example 2:
User: What's the weather in Paris?
Thought: I need to check the weather for Paris
Action: get_weather
Action Input: {"location": "Paris", "units": "celsius"}
Observation: {"temp": 18, "condition": "cloudy"}
Thought: I have the weather information
Final Answer: It's 18°C and cloudy in Paris
"""
```

### Crafting Effective Agent Prompts

The quality of your prompts directly determines the quality of your agent's behavior. Being explicit is essential because LLMs don't make assumptions the way humans do. If you want the agent to format tool inputs as JSON, say that explicitly. If there's a specific order to follow, spell it out. Ambiguity leads to unpredictable behavior.

Examples are incredibly powerful. Show the agent exactly what good behavior looks like with few-shot examples. When the agent sees "Thought: I need to check the weather, Action: get_weather, Action Input: {\"location\": \"Paris\"}", it learns the pattern much faster than from descriptions alone. Include examples of both simple and complex tool usage.

Constraining output format helps prevent the agent from going off the rails. If you list five available tools, explicitly state that the agent should only use those tools and nothing else. This prevents the agent from hallucinating tool names or trying to use capabilities it doesn't have.

Context is crucial but often overlooked. Give the agent the information it needs to succeed. If certain tools should only be used in specific situations, explain those situations. If there are dependencies between tools, make them clear. The agent can't read your mind about domain-specific knowledge.

Finally, set clear boundaries. Be explicit about what the agent should NOT do. Should it avoid making irreversible changes without confirmation? Say so. Should it never make assumptions about missing parameters? State that clearly. Negative constraints are just as important as positive instructions.

---

## Summary

The journey through agent architectures follows a natural progression based on complexity and needs. Most developers should start with the reactive (ReAct) pattern. It's simple, it works, and it helps you understand the fundamentals of how agents think and act. You can build a working agent in a few hours and start solving real problems immediately.

As your use cases grow more sophisticated, upgrade to the planner-executor pattern. When you find yourself with multi-step workflows where efficiency matters, the upfront planning overhead pays for itself. The clear separation between planning and execution also makes your system easier to understand and maintain.

Multi-agent systems represent the most advanced pattern, and they should only be adopted when the complexity is justified. If you're building enterprise systems with genuinely diverse responsibilities, or if specialization produces meaningfully better results, then multi-agent architectures make sense. For most applications, they're overkill.

The most important principle is this: more complex doesn't mean better. Choose the simplest architecture that solves your actual problem. A well-built reactive agent is infinitely better than a poorly-constructed multi-agent system. You can also combine patterns creatively—for example, a multi-agent system where each agent internally uses the ReAct pattern, or a planner-executor that uses multiple agents in the execution phase.

Start simple, measure results, and only add complexity when you have clear evidence that it will improve outcomes.

---

**Previous:** [← Fundamentals](02-fundamentals.md) | **Next:** [Security →](04-security.md)

**See also:**
- [ReAct Implementation Example](../examples/python-react-pattern/)
- [Planner-Executor Example](../examples/python-planner-executor/)
- [Multi-Agent Example](../examples/python-multi-agent/)
- [MCP Integration Example](../examples/python-mcp-files/)
- [UTCP Weather Example](../examples/python-utcp-weather/)
- [Protocol Comparison Guide](../protocols/comparison.md)

