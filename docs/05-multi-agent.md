# Multi-Agent Systems

> **Learn how multiple AI agents can collaborate to solve complex problems**

---

## Table of Contents

- [Introduction](#introduction)
- [Why Multi-Agent Systems?](#why-multi-agent-systems)
- [Architecture Patterns](#architecture-patterns)
- [Communication Patterns](#communication-patterns)
- [Implementation Guide](#implementation-guide)
- [Coordination Strategies](#coordination-strategies)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)

---

## Introduction

A **multi-agent system** is a collection of autonomous AI agents that work together to accomplish complex tasks that would be difficult or impossible for a single agent.

### Key Concepts

```
Single Agent              Multi-Agent System
┌──────────┐             ┌──────────┐  ┌──────────┐
│          │             │ Manager  │  │ Worker 1 │
│  Agent   │             │  Agent   │◄─┤ Specialist│
│          │       vs    └────┬─────┘  └──────────┘
└──────────┘                  │         
                              │        ┌──────────┐
                              └───────►│ Worker 2 │
                                       │ Specialist│
                                       └──────────┘
```

**Single Agent:** One LLM with all tools
**Multi-Agent:** Multiple LLMs, each with specialized role/tools

---

## Why Multi-Agent Systems?

### Advantages

#### 1. **Specialization**
Each agent can focus on what it does best.

```python
research_agent = Agent(
    role="researcher",
    tools=["web_search", "pdf_reader", "summarize"],
    expertise="Finding and analyzing information"
)

coding_agent = Agent(
    role="coder",
    tools=["code_executor", "linter", "debugger"],
    expertise="Writing and testing code"
)
```

#### 2. **Parallelization**
Multiple agents can work simultaneously.

```python
# Sequential (single agent)
result1 = agent.research("topic A")  # 30 seconds
result2 = agent.research("topic B")  # 30 seconds
# Total: 60 seconds

# Parallel (multi-agent)
results = await asyncio.gather(
    agent1.research("topic A"),  # 30 seconds
    agent2.research("topic B")   # 30 seconds
)
# Total: 30 seconds!
```

#### 3. **Modularity**
Easy to add, remove, or replace agents.

```python
team = AgentTeam()
team.add_agent(researcher)
team.add_agent(coder)
team.add_agent(reviewer)  # ← Add new specialist

# Later...
team.remove_agent(reviewer)  # ← Remove if not needed
```

#### 4. **Fault Tolerance**
If one agent fails, others can continue.

```python
try:
    result = agent1.process(task)
except AgentError:
    # Fallback to another agent
    result = agent2.process(task)
```

### Disadvantages

❌ **Complexity** - More moving parts to manage
❌ **Coordination overhead** - Agents must communicate
❌ **Potential conflicts** - Agents might disagree
❌ **Debugging difficulty** - Harder to trace issues
❌ **Higher cost** - Multiple LLM calls

---

## Architecture Patterns

### Pattern 1: Hierarchical (Manager-Workers)

**Structure:**
```
         ┌─────────────┐
         │   Manager   │  ← Coordinates workers
         │    Agent    │
         └──────┬──────┘
                │
      ┌─────────┼─────────┐
      │         │         │
┌─────▼────┐ ┌──▼──────┐ ┌▼────────┐
│ Worker 1 │ │Worker 2 │ │Worker 3 │
│ Research │ │  Code   │ │  Test   │
└──────────┘ └─────────┘ └─────────┘
```

**When to use:**
- Clear task decomposition
- One agent can coordinate others
- Hierarchical decision-making needed

**Implementation:**

```python
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Task:
    description: str
    assigned_to: str
    status: str = "pending"
    result: Any = None

class ManagerAgent:
    """Coordinates worker agents"""
    
    def __init__(self, llm, workers: Dict[str, 'WorkerAgent']):
        self.llm = llm
        self.workers = workers
    
    def execute(self, goal: str) -> str:
        """Break down goal and coordinate workers"""
        
        # Step 1: Create plan
        plan = self._create_plan(goal)
        
        # Step 2: Assign tasks
        tasks = []
        for step in plan:
            task = Task(
                description=step['description'],
                assigned_to=step['agent']
            )
            tasks.append(task)
        
        # Step 3: Execute tasks
        results = {}
        for task in tasks:
            worker = self.workers[task.assigned_to]
            task.result = worker.execute(task.description)
            task.status = "completed"
            results[task.assigned_to] = task.result
        
        # Step 4: Synthesize results
        return self._synthesize(goal, results)
    
    def _create_plan(self, goal: str) -> List[Dict]:
        """Use LLM to create execution plan"""
        prompt = f"""Break down this goal into tasks for specialists:
        
Goal: {goal}

Available specialists:
{self._list_workers()}

Return JSON array:
[
  {{"agent": "researcher", "description": "Research X"}},
  {{"agent": "coder", "description": "Implement Y"}},
  ...
]
"""
        response = self.llm.generate(prompt)
        return self._parse_plan(response)
    
    def _list_workers(self) -> str:
        return "\n".join([
            f"- {name}: {agent.role}"
            for name, agent in self.workers.items()
        ])
    
    def _synthesize(self, goal: str, results: Dict) -> str:
        """Combine worker results into final answer"""
        prompt = f"""Synthesize these results into a final answer:

Goal: {goal}

Results:
{self._format_results(results)}

Final answer:"""
        return self.llm.generate(prompt)

class WorkerAgent:
    """Specialized worker agent"""
    
    def __init__(self, name: str, role: str, llm, tools: Dict):
        self.name = name
        self.role = role
        self.llm = llm
        self.tools = tools
    
    def execute(self, task: str) -> str:
        """Execute assigned task using available tools"""
        
        prompt = f"""You are a {self.role}. Complete this task:

Task: {task}

Available tools: {list(self.tools.keys())}

Use tools to complete the task and return the result.
"""
        
        # Simple tool-use loop (like ReAct)
        for _ in range(5):  # Max 5 steps
            response = self.llm.generate(prompt)
            
            # Check if using a tool
            if "USE_TOOL:" in response:
                tool_name, args = self._parse_tool_call(response)
                result = self.tools[tool_name](**args)
                prompt += f"\nTool result: {result}\n"
            else:
                # Final answer
                return response
        
        return "Task could not be completed"

# Usage
manager = ManagerAgent(
    llm=your_llm,
    workers={
        "researcher": WorkerAgent(
            "researcher",
            "Information researcher",
            llm=your_llm,
            tools={"web_search": search_tool, "read_pdf": pdf_tool}
        ),
        "coder": WorkerAgent(
            "coder",
            "Software developer",
            llm=your_llm,
            tools={"write_code": code_tool, "run_tests": test_tool}
        )
    }
)

result = manager.execute("Research Python asyncio and create example code")
```

---

### Pattern 2: Peer-to-Peer (Collaborative)

**Structure:**
```
┌──────────┐     ┌──────────┐
│ Agent A  │◄───►│ Agent B  │
│Research  │     │  Coding  │
└────┬─────┘     └─────┬────┘
     │                 │
     │    ┌──────────┐ │
     └───►│ Agent C  │◄┘
          │  Review  │
          └──────────┘
```

**When to use:**
- No clear hierarchy
- Agents need to negotiate
- Collaborative problem-solving

**Implementation:**

```python
class CollaborativeAgent:
    """Agent that can communicate with peers"""
    
    def __init__(self, name: str, role: str, llm):
        self.name = name
        self.role = role
        self.llm = llm
        self.peers: List['CollaborativeAgent'] = []
        self.messages: List[Dict] = []
    
    def add_peer(self, agent: 'CollaborativeAgent'):
        """Add another agent as peer"""
        self.peers.append(agent)
        agent.peers.append(self)  # Bidirectional
    
    def send_message(self, to: str, content: str):
        """Send message to peer"""
        for peer in self.peers:
            if peer.name == to:
                peer.receive_message(self.name, content)
    
    def receive_message(self, from_agent: str, content: str):
        """Receive message from peer"""
        self.messages.append({
            "from": from_agent,
            "content": content,
            "timestamp": time.time()
        })
    
    def collaborate(self, task: str) -> str:
        """Work with peers to solve task"""
        
        # Announce task to peers
        for peer in self.peers:
            self.send_message(
                peer.name,
                f"Working on: {task}. Can you help?"
            )
        
        # Wait for responses
        time.sleep(1)  # Simple synchronization
        
        # Gather peer input
        peer_input = [msg['content'] for msg in self.messages]
        
        # Solve with peer context
        prompt = f"""You are {self.role}.

Task: {task}

Input from peers:
{chr(10).join(peer_input)}

Your contribution:"""
        
        return self.llm.generate(prompt)

# Usage
researcher = CollaborativeAgent("Alice", "Researcher", llm)
coder = CollaborativeAgent("Bob", "Coder", llm)
reviewer = CollaborativeAgent("Carol", "Reviewer", llm)

# Connect them
researcher.add_peer(coder)
coder.add_peer(reviewer)
reviewer.add_peer(researcher)

# Collaborate
result = researcher.collaborate("Build a web scraper")
```

---

### Pattern 3: Blackboard (Shared Memory)

**Structure:**
```
    ┌─────────────────────────┐
    │   SHARED BLACKBOARD     │
    │  (Common workspace)     │
    │                         │
    │  • Problem state        │
    │  • Partial solutions    │
    │  • Shared data          │
    └────────▲────▲────▲──────┘
             │    │    │
    ┌────────┴┐ ┌─┴────┴┐ ┌─────────┐
    │Agent A  │ │Agent B│ │Agent C  │
    │(reads   │ │(reads │ │(reads   │
    │ writes) │ │ writes│ │ writes) │
    └─────────┘ └───────┘ └─────────┘
```

**When to use:**
- Agents work on different aspects
- Need shared workspace
- Incremental problem solving

**Implementation:**

```python
class Blackboard:
    """Shared workspace for agents"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.history: List[Dict] = []
    
    def write(self, key: str, value: Any, agent: str):
        """Write to blackboard"""
        self.data[key] = value
        self.history.append({
            "action": "write",
            "key": key,
            "value": value,
            "agent": agent,
            "timestamp": time.time()
        })
    
    def read(self, key: str) -> Any:
        """Read from blackboard"""
        return self.data.get(key)
    
    def read_all(self) -> Dict[str, Any]:
        """Read entire blackboard"""
        return self.data.copy()

class BlackboardAgent:
    """Agent that uses shared blackboard"""
    
    def __init__(self, name: str, specialty: str, llm, blackboard: Blackboard):
        self.name = name
        self.specialty = specialty
        self.llm = llm
        self.blackboard = blackboard
    
    def contribute(self, problem: str) -> bool:
        """Make contribution to shared solution"""
        
        # Read current state
        current_state = self.blackboard.read_all()
        
        # Decide if can contribute
        prompt = f"""You are a {self.specialty}.

Problem: {problem}

Current state of solution:
{json.dumps(current_state, indent=2)}

Can you contribute? If yes, provide your contribution.
Format: {{"can_contribute": true/false, "contribution": {{...}}}}
"""
        
        response = self.llm.generate(prompt)
        decision = json.loads(response)
        
        if decision['can_contribute']:
            # Write contribution
            contribution = decision['contribution']
            for key, value in contribution.items():
                self.blackboard.write(key, value, self.name)
            return True
        
        return False

# Usage
blackboard = Blackboard()

agents = [
    BlackboardAgent("Alice", "Data analyst", llm, blackboard),
    BlackboardAgent("Bob", "Visualizer", llm, blackboard),
    BlackboardAgent("Carol", "Writer", llm, blackboard)
]

problem = "Create a sales report with charts"

# Agents contribute iteratively
max_rounds = 5
for round in range(max_rounds):
    contributions = 0
    for agent in agents:
        if agent.contribute(problem):
            contributions += 1
    
    if contributions == 0:
        break  # No one has more to add

# Final solution is on blackboard
solution = blackboard.read_all()
```

---

## Communication Patterns

### 1. Direct Messages

```python
agent_a.send_to(agent_b, "Please analyze this data")
```

**Pros:** Simple, explicit
**Cons:** Tight coupling

### 2. Broadcast

```python
manager.broadcast_to_all("New task available")
```

**Pros:** Efficient for announcements
**Cons:** All agents receive all messages

### 3. Publish-Subscribe

```python
# Agents subscribe to topics
agent_a.subscribe("code_reviews")
agent_b.subscribe("code_reviews")

# Publisher sends to topic
manager.publish("code_reviews", "Review PR #123")
```

**Pros:** Decoupled, scalable
**Cons:** More infrastructure

### 4. Message Queue

```python
queue = MessageQueue()
queue.add_task({"type": "research", "topic": "AI"})

# Agents poll queue
task = queue.get_next_task(agent_type="researcher")
```

**Pros:** Load balancing, persistence
**Cons:** Requires queue infrastructure

---

## Implementation Guide

### Using AutoGen

Microsoft's AutoGen framework is designed for multi-agent systems:

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# Define agents
researcher = AssistantAgent(
    name="Researcher",
    system_message="You are a researcher. Find information.",
    llm_config={"model": "gpt-4"}
)

coder = AssistantAgent(
    name="Coder",
    system_message="You are a coder. Write code.",
    llm_config={"model": "gpt-4"}
)

reviewer = AssistantAgent(
    name="Reviewer",
    system_message="You are a code reviewer. Review code for issues.",
    llm_config={"model": "gpt-4"}
)

# Create group chat
group_chat = GroupChat(
    agents=[researcher, coder, reviewer],
    messages=[],
    max_round=10
)

# Create manager
manager = GroupChatManager(
    groupchat=group_chat,
    llm_config={"model": "gpt-4"}
)

# Start conversation
user_proxy = UserProxyAgent(name="User")
user_proxy.initiate_chat(
    manager,
    message="Build a web scraper for news articles"
)
```

### Custom Implementation

```python
from typing import List, Optional
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    DONE = "done"

class Message:
    def __init__(self, sender: str, receiver: str, content: str, msg_type: str = "task"):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.type = msg_type
        self.timestamp = time.time()

class MultiAgentSystem:
    """Orchestrates multiple agents"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.message_queue: List[Message] = []
    
    def register_agent(self, agent: 'Agent'):
        """Add agent to system"""
        self.agents[agent.name] = agent
        agent.system = self
    
    def send_message(self, message: Message):
        """Route message to recipient"""
        self.message_queue.append(message)
    
    def tick(self):
        """Process one round of agent actions"""
        
        # Deliver messages
        for message in self.message_queue:
            if message.receiver in self.agents:
                self.agents[message.receiver].receive(message)
        self.message_queue.clear()
        
        # Let each agent act
        for agent in self.agents.values():
            if agent.state == AgentState.IDLE:
                agent.act()
    
    def run_until_complete(self, max_ticks: int = 100):
        """Run until all agents done or timeout"""
        for _ in range(max_ticks):
            self.tick()
            
            # Check if all done
            if all(a.state == AgentState.DONE for a in self.agents.values()):
                break

class Agent:
    def __init__(self, name: str, role: str, llm):
        self.name = name
        self.role = role
        self.llm = llm
        self.state = AgentState.IDLE
        self.inbox: List[Message] = []
        self.system: Optional[MultiAgentSystem] = None
    
    def receive(self, message: Message):
        """Receive a message"""
        self.inbox.append(message)
    
    def send(self, to: str, content: str, msg_type: str = "info"):
        """Send message to another agent"""
        message = Message(self.name, to, content, msg_type)
        if self.system:
            self.system.send_message(message)
    
    def act(self):
        """Take action based on messages"""
        if not self.inbox:
            return
        
        # Process inbox
        for message in self.inbox:
            if message.type == "task":
                self.state = AgentState.WORKING
                result = self._process_task(message.content)
                self.send(message.sender, result, "result")
                self.state = AgentState.DONE
        
        self.inbox.clear()
    
    def _process_task(self, task: str) -> str:
        """Process task using LLM and tools"""
        prompt = f"You are {self.role}. Complete: {task}"
        return self.llm.generate(prompt)

# Usage
system = MultiAgentSystem()

researcher = Agent("Alice", "Researcher", llm)
coder = Agent("Bob", "Coder", llm)

system.register_agent(researcher)
system.register_agent(coder)

# Start workflow
researcher.send("Bob", "Research async programming", "task")

# Run system
system.run_until_complete()
```

---

## Coordination Strategies

### 1. Sequential Execution

Agents work one after another:

```python
result1 = agent1.work()
result2 = agent2.work(result1)
result3 = agent3.work(result2)
```

**Best for:** Pipeline workflows

### 2. Parallel Execution

Agents work simultaneously:

```python
results = await asyncio.gather(
    agent1.work(),
    agent2.work(),
    agent3.work()
)
```

**Best for:** Independent tasks

### 3. Dynamic Assignment

Manager assigns tasks based on agent availability:

```python
def assign_task(task):
    for agent in agents:
        if agent.is_idle():
            agent.assign(task)
            return
    queue.add(task)  # Wait for free agent
```

**Best for:** Load balancing

### 4. Auction-Based

Agents bid for tasks:

```python
bids = [agent.bid(task) for agent in agents]
winner = max(bids, key=lambda b: b.confidence)
winner.agent.execute(task)
```

**Best for:** Optimal assignment

---

## Use Cases

### 1. Software Development Team

```python
agents = {
    "product_manager": "Defines requirements",
    "architect": "Designs system",
    "developer": "Writes code",
    "tester": "Tests code",
    "reviewer": "Reviews code quality"
}
```

### 2. Research Assistant

```python
agents = {
    "searcher": "Finds sources",
    "reader": "Reads papers",
    "analyzer": "Analyzes findings",
    "writer": "Writes summary"
}
```

### 3. Customer Support

```python
agents = {
    "classifier": "Categorizes tickets",
    "specialist_billing": "Handles billing",
    "specialist_technical": "Handles technical",
    "escalation": "Handles complex issues"
}
```

### 4. Data Analysis Pipeline

```python
agents = {
    "collector": "Gathers data",
    "cleaner": "Cleans data",
    "analyst": "Analyzes data",
    "visualizer": "Creates charts",
    "reporter": "Generates report"
}
```

---

## Best Practices

### ✅ DO:

1. **Define Clear Roles**
   ```python
   agent = Agent(
       name="DataAnalyst",
       role="Analyze data and find insights",
       tools=["pandas", "visualize"],
       expertise="Statistical analysis"
   )
   ```

2. **Implement Timeouts**
   ```python
   result = await asyncio.wait_for(
       agent.work(task),
       timeout=30.0
   )
   ```

3. **Log All Communication**
   ```python
   def send_message(self, message):
       logger.info(f"{self.name} → {message.receiver}: {message.content}")
       self.message_queue.append(message)
   ```

4. **Handle Agent Failures**
   ```python
   try:
       result = agent.execute(task)
   except AgentError:
       result = fallback_agent.execute(task)
   ```

5. **Use Message Types**
   ```python
   class MessageType(Enum):
       TASK = "task"
       RESULT = "result"
       QUESTION = "question"
       ANSWER = "answer"
   ```

### ❌ DON'T:

1. **Don't create circular dependencies**
2. **Don't ignore failed agents**
3. **Don't forget synchronization**
4. **Don't make agents too complex**
5. **Don't skip error handling**

---

## Summary

**Multi-agent systems enable:**
- ✅ Specialization of agents
- ✅ Parallel execution
- ✅ Modular design
- ✅ Complex problem solving

**Key patterns:**
- Hierarchical (Manager-Workers)
- Peer-to-Peer (Collaborative)
- Blackboard (Shared Memory)

**When to use:**
- Complex tasks requiring multiple skills
- Need for parallel processing
- Modularity and maintainability important
- Single agent too complex

**When NOT to use:**
- Simple tasks
- Tight latency requirements
- Limited resources
- Debugging is critical

---

**Next Steps:**
- [Build Multi-Agent Example](../examples/python-multi-agent/)
- [AutoGen Tutorial](https://microsoft.github.io/autogen/)
- [Design Patterns](../design/patterns.md)

**Previous:** [← Security](04-security.md) | **See Also:** [Architecture Patterns](03-agent-architectures.md)

