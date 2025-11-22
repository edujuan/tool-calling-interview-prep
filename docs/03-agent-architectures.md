# Agent Architecture Patterns

> **Learn the fundamental patterns for building AI agents** - from simple reactive loops to complex multi-agent systems.

---

## Table of Contents

- [Overview](#overview)
- [Pattern 1: Reactive Agents (ReAct)](#pattern-1-reactive-agents-react)
- [Pattern 2: Planner-Executor](#pattern-2-planner-executor)
- [Pattern 3: Multi-Agent Systems](#pattern-3-multi-agent-systems)
- [Choosing the Right Pattern](#choosing-the-right-pattern)
- [Tool Selection and Chaining](#tool-selection-and-chaining)
- [Prompt Engineering for Agents](#prompt-engineering-for-agents)

---

## Overview

AI agents can be organized into different architectural patterns, each with trade-offs:

```
Agent Architecture Spectrum
                                   
Simple ←─────────────────────────────→ Complex
Fast   ←─────────────────────────────→ Powerful

┌──────────┐   ┌──────────┐   ┌──────────┐
│ Reactive │ → │ Planner  │ → │  Multi   │
│  (ReAct) │   │ Executor │   │  Agent   │
└──────────┘   └──────────┘   └──────────┘

Use Case:        Use Case:      Use Case:
Single task      Multi-step     Complex
Quick response   workflows      collaboration
```

### Quick Comparison

| Pattern | Complexity | Best For | Example Use Case |
|---------|-----------|----------|------------------|
| **Reactive** | Low | Simple, single-purpose agents | Calculator bot, weather lookup |
| **Planner-Executor** | Medium | Multi-step tasks with dependencies | Research report generation |
| **Multi-Agent** | High | Complex, parallel workflows | Enterprise automation system |

---

## Pattern 1: Reactive Agents (ReAct)

**ReAct = Reasoning + Acting**

The agent alternates between thinking and acting in a loop until the task is complete.

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

### Advantages

✅ **Simple to implement** - Straightforward loop
✅ **Flexible** - Can adapt on the fly
✅ **Interpretable** - Can see reasoning steps
✅ **Works with any LLM** - Doesn't require special training

### Disadvantages

❌ **Can be inefficient** - Doesn't plan ahead
❌ **May loop** - Can get stuck repeating actions
❌ **Token intensive** - Full history in every call
❌ **No backtracking** - Can't revise strategy

### When to Use

- Simple, single-purpose agents
- Tasks that don't require complex planning
- When interpretability is important
- Quick prototypes and demos

---

## Pattern 2: Planner-Executor

Separate planning from execution: first create a plan, then execute it step-by-step.

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

### Advantages

✅ **More efficient** - Plans ahead, no wasted actions
✅ **Better for multi-step tasks** - Clear structure
✅ **Can parallelize** - Independent steps can run concurrently
✅ **Easier to debug** - Clear plan vs execution separation

### Disadvantages

❌ **Less flexible** - Harder to adapt mid-execution
❌ **Planning overhead** - Extra LLM call for planning
❌ **May over-plan** - Plans steps that aren't needed
❌ **Requires good planning** - LLM must create valid plans

### When to Use

- Multi-step workflows with dependencies
- Tasks that benefit from upfront planning
- When you can parallelize independent operations
- Research or data gathering tasks

---

## Pattern 3: Multi-Agent Systems

Multiple specialized agents collaborate to solve complex tasks.

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

### Communication Patterns

**1. Hierarchical (Manager-Worker)**
```
Manager
├── Worker 1
├── Worker 2
└── Worker 3
```

**2. Peer-to-Peer**
```
Agent A ↔ Agent B ↔ Agent C
```

**3. Blackboard (Shared Memory)**
```
┌──────────────────┐
│ Shared Blackboard│
│  (All agents     │
│   read/write)    │
└──────────────────┘
    ↕    ↕    ↕
  Agent Agent Agent
```

### Advantages

✅ **Specialization** - Each agent excels at its role
✅ **Parallelization** - Agents can work concurrently
✅ **Scalability** - Add more agents as needed
✅ **Modularity** - Easy to add/remove/replace agents

### Disadvantages

❌ **High complexity** - Many moving parts
❌ **Coordination overhead** - Agents must communicate
❌ **Potential conflicts** - Agents might contradict
❌ **Debugging difficulty** - Hard to trace issues

### When to Use

- Complex tasks requiring diverse expertise
- Tasks that can be parallelized
- Enterprise systems with multiple responsibilities
- When specialization improves quality

---

## Choosing the Right Pattern

### Decision Tree

```
Start: What kind of task?
  │
  ├─ Simple, single tool usage
  │  └─→ Use Reactive (ReAct)
  │
  ├─ Multi-step with clear sequence
  │  └─→ Use Planner-Executor
  │
  └─ Complex, requires multiple specialists
     └─→ Use Multi-Agent
```

### Comparison Matrix

| Factor | Reactive | Planner | Multi-Agent |
|--------|----------|---------|-------------|
| **Implementation Time** | 1 day | 3 days | 1-2 weeks |
| **Token Usage** | High | Medium | Variable |
| **Flexibility** | High | Medium | High |
| **Efficiency** | Low | High | Very High |
| **Debugging** | Easy | Medium | Hard |
| **Cost** | Low | Medium | High |

---

## Tool Selection and Chaining

How agents decide which tools to use and how to combine them:

### Tool Selection Strategies

**1. LLM-based Selection** (Most common)
```python
prompt = f"""
Available tools: {tool_descriptions}
Query: {user_query}

Which tool should be used? Choose one: {tool_names}
"""
```

**2. Semantic Similarity**
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

### Tool Chaining

**Sequential Chaining**
```python
# Output of tool1 → input of tool2
result1 = tool1(query)
result2 = tool2(result1)
result3 = tool3(result2)
```

**Parallel Execution**
```python
import asyncio

# Run multiple tools simultaneously
results = await asyncio.gather(
    tool1(query),
    tool2(query),
    tool3(query)
)
```

---

## Prompt Engineering for Agents

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

### Best Practices

1. **Be explicit** - Clearly state the format
2. **Use examples** - Show correct tool usage
3. **Constrain output** - Limit to valid actions
4. **Provide context** - Give agent necessary information
5. **Set boundaries** - What agent should NOT do

---

## Summary

**Pattern Selection Guide:**

- **Start with Reactive** - For simple use cases, quick prototypes
- **Upgrade to Planner** - When you have multi-step workflows
- **Go Multi-Agent** - For complex, specialized tasks

**Remember:**
- More complex ≠ better
- Choose based on your actual needs
- Can combine patterns (e.g., multi-agent where each agent uses ReAct)

---

**Previous:** [← Fundamentals](02-fundamentals.md) | **Next:** [Security →](04-security.md)

**See also:**
- [ReAct Implementation Example](../examples/python-react-pattern/)
- [Planner-Executor Example](../examples/python-planner-executor/)
- [Multi-Agent Example](../examples/python-multi-agent/)

