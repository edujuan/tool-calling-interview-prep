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

A **multi-agent system** is a collection of autonomous AI agents that work together to accomplish complex tasks that would be difficult or impossible for a single agent. Think of it like a company: instead of one person doing everything, you have specialists working together - a researcher, a developer, a tester - each focused on what they do best.

The key insight is that **specialization beats generalization** for complex tasks. A single "jack-of-all-trades" agent with 50 tools often performs worse than 5 specialized agents with 10 tools each.

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

**Single Agent:** One LLM with all tools - simpler but less focused
**Multi-Agent:** Multiple LLMs, each with specialized role/tools - more complex but more capable

---

## Why Multi-Agent Systems?

Multi-agent systems aren't always the right choice, but when tasks get complex enough, the benefits outweigh the coordination overhead. Before diving into implementation details, let's step back and understand the core value proposition: why would you add the complexity of multiple agents instead of just building one really good agent?

### Advantages

#### 1. **Specialization**
Each agent can focus on what it does best. Just like human teams, specialized agents outperform generalists for complex domains. A research agent with search tools and summarization expertise will find better information than a general-purpose agent trying to do everything.

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
Multiple agents can work simultaneously. This is one of the biggest practical advantages - while a single agent processes tasks sequentially, multiple agents can divide and conquer, dramatically reducing total execution time for independent subtasks.

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
Easy to add, remove, or replace agents. Because each agent is independent, you can swap out implementations, upgrade specific capabilities, or add new specialists without rewriting your entire system. This is similar to microservices architecture in software engineering.

```python
team = AgentTeam()
team.add_agent(researcher)
team.add_agent(coder)
team.add_agent(reviewer)  # ← Add new specialist

# Later...
team.remove_agent(reviewer)  # ← Remove if not needed
```

#### 4. **Fault Tolerance**
If one agent fails, others can continue. Unlike a monolithic agent where one failure stops everything, multi-agent systems can gracefully degrade. You can implement fallbacks, retry with different agents, or continue with partial results.

```python
try:
    result = agent1.process(task)
except AgentError:
    # Fallback to another agent
    result = agent2.process(task)
```

### Disadvantages

These are real costs - don't use multi-agent systems unless the benefits justify them:

❌ **Complexity** - More moving parts to manage: message passing, state synchronization, orchestration logic
❌ **Coordination overhead** - Agents must communicate, which adds latency and potential failure points
❌ **Potential conflicts** - Agents might disagree on approaches or produce inconsistent results
❌ **Debugging difficulty** - Harder to trace issues across multiple agents and message flows
❌ **Higher cost** - Multiple LLM calls mean higher API costs and longer total runtime (even if parallelized)

So you've decided a multi-agent system makes sense for your problem. Great! But now comes the real question: how do you structure your agents? Should they report to a manager? Work as peers? Share a common workspace? The architecture you choose will fundamentally shape how your system behaves.

---

## Architecture Patterns

Choosing the right architecture is critical. Each pattern suits different types of problems and team dynamics. Let's explore the three main patterns with their trade-offs.

### Pattern 1: Hierarchical (Manager-Workers)

This is the most common pattern - one "manager" agent breaks down tasks and delegates to "worker" agents. It mirrors traditional organizational structures and works well when there's a clear way to decompose problems.

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
- Clear task decomposition - you can break the problem into independent subtasks
- One agent can coordinate others - there's a natural "manager" role
- Hierarchical decision-making needed - top-down control makes sense for your problem
- **Example:** Building a research report (manager breaks into: search, summarize, write, format)

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

The hierarchical pattern works great when you have clear top-down task decomposition. But what if your problem doesn't have an obvious "manager"? What if the best solution emerges from agents working together as equals? That's where peer-to-peer comes in.

---

### Pattern 2: Peer-to-Peer (Collaborative)

In this pattern, agents are equals - there's no manager. They communicate directly, negotiate, and collaborate. This works well for problems where no single agent has the full picture and collective intelligence is needed.

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
- No clear hierarchy - no agent should be "in charge"
- Agents need to negotiate - the solution emerges from discussion, not top-down planning
- Collaborative problem-solving - multiple perspectives improve the outcome
- **Example:** Design review (agents debate and refine a solution together)

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

Both hierarchical and peer-to-peer involve direct messaging between agents. But there's a third approach: what if agents didn't talk directly at all? What if they all worked on a shared "canvas" instead, contributing when they see something they can help with? This is the blackboard pattern.

---

### Pattern 3: Blackboard (Shared Memory)

The blackboard pattern uses a shared workspace where all agents read and write. Think of it as a collaborative whiteboard - agents contribute their expertise when they see something they can help with. This is inspired by how human experts collaboratively solve problems on a shared surface.

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
- Agents work on different aspects - each contributes their piece to a shared solution
- Need shared workspace - the problem state is too complex to pass in messages
- Incremental problem solving - the solution builds up over time as agents contribute
- **Example:** Document creation (one agent drafts, another edits, another formats, all working on the same document)

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

We've seen three ways to structure agent teams (hierarchical, peer-to-peer, blackboard). But within any of these patterns, agents need to actually send messages. The *how* of communication is just as important as the *what*. 

Different communication styles make sense for different scenarios. Direct messaging is simplest but creates tight coupling. Publish-subscribe is flexible but needs more infrastructure. Let's examine the options:

How agents talk to each other matters. The communication pattern affects flexibility, performance, and debugging. Choose based on your system's needs.

### 1. Direct Messages

```python
agent_a.send_to(agent_b, "Please analyze this data")
```

**Pros:** Simple, explicit - you know exactly who talks to whom
**Cons:** Tight coupling - agents must know about each other directly

### 2. Broadcast

```python
manager.broadcast_to_all("New task available")
```

**Pros:** Efficient for announcements - one message reaches everyone
**Cons:** All agents receive all messages - wasteful if most aren't relevant

### 3. Publish-Subscribe

```python
# Agents subscribe to topics
agent_a.subscribe("code_reviews")
agent_b.subscribe("code_reviews")

# Publisher sends to topic
manager.publish("code_reviews", "Review PR #123")
```

**Pros:** Decoupled, scalable - agents don't need to know about each other, just topics
**Cons:** More infrastructure - need a pub/sub system

**Best for:** Large systems where agents come and go dynamically

### 4. Message Queue

```python
queue = MessageQueue()
queue.add_task({"type": "research", "topic": "AI"})

# Agents poll queue
task = queue.get_next_task(agent_type="researcher")
```

**Pros:** Load balancing (multiple agents can process tasks), persistence (tasks survive restarts)
**Cons:** Requires queue infrastructure like Redis or RabbitMQ

**Best for:** Production systems with variable load

---

## Implementation Guide

Now that we've covered the architectural patterns and how agents communicate, let's get practical. You have two main paths: use a framework like AutoGen that handles the heavy lifting, or build your own system for maximum control. We'll explore both approaches so you can choose what fits your needs.

### Using AutoGen

Microsoft's AutoGen framework is purpose-built for multi-agent systems and handles most of the coordination complexity for you:

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

AutoGen is great for getting started quickly, but it hides a lot of details. If you want full control over message routing, state management, and agent lifecycle - or if you just want to understand what's happening under the hood - building your own system is surprisingly approachable.

### Custom Implementation

If you need more control or want to understand the internals, building from scratch isn't too complex. Here's a minimal but functional multi-agent system:

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

That implementation guide gives you the mechanics of building a multi-agent system. But there's a higher-level question we need to address: timing and orchestration.

---

## Coordination Strategies

Architecture defines your team structure. Communication defines how agents talk. But there's still a missing piece: **timing**. When do agents work? In what order? Who waits for whom?

This is coordination - the choreography of your multi-agent system. Get it right and you'll see impressive parallelization and efficiency. Get it wrong and you'll have deadlocks, race conditions, and confused agents stepping on each other's work.

Once you have agents and communication, you need coordination - deciding who works on what and when. The strategy you choose affects both performance and complexity.

### 1. Sequential Execution

Agents work one after another in a pipeline. Simple and predictable, but can't exploit parallelism:

```python
result1 = agent1.work()
result2 = agent2.work(result1)
result3 = agent3.work(result2)
```

**Best for:** Pipeline workflows

### 2. Parallel Execution

Agents work simultaneously on independent tasks. Faster but requires careful task independence checking:

```python
results = await asyncio.gather(
    agent1.work(),
    agent2.work(),
    agent3.work()
)
```

**Best for:** Independent tasks

### 3. Dynamic Assignment

Manager assigns tasks based on agent availability. Good for handling variable workloads efficiently:

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

Agents bid for tasks based on their confidence/capability. Optimal but adds overhead for the bidding process:

```python
bids = [agent.bid(task) for agent in agents]
winner = max(bids, key=lambda b: b.confidence)
winner.agent.execute(task)
```

**Best for:** Optimal assignment

We've covered a lot of theory - patterns, communication, coordination. But when should you actually use these in practice? Let's look at concrete scenarios where multi-agent systems deliver real value.

---

## Use Cases

Multi-agent systems shine in domains that naturally decompose into specialized roles. Here are real-world scenarios where they excel:

### 1. Software Development Team

Mimics a real development team with distinct roles:

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

Each agent handles a different stage of the research process:

```python
agents = {
    "searcher": "Finds sources",
    "reader": "Reads papers",
    "analyzer": "Analyzes findings",
    "writer": "Writes summary"
}
```

### 3. Customer Support

Routing system where specialized agents handle their domain:

```python
agents = {
    "classifier": "Categorizes tickets",
    "specialist_billing": "Handles billing",
    "specialist_technical": "Handles technical",
    "escalation": "Handles complex issues"
}
```

### 4. Data Analysis Pipeline

Classic ETL workflow with specialized processing at each stage:

```python
agents = {
    "collector": "Gathers data",
    "cleaner": "Cleans data",
    "analyst": "Analyzes data",
    "visualizer": "Creates charts",
    "reporter": "Generates report"
}
```

You now know the patterns, the communication styles, the coordination strategies, and where to apply them. But knowing what to build is different from building it well. Let's talk about how to avoid the pitfalls that catch most developers building their first multi-agent system.

---

## Best Practices

These lessons come from production multi-agent systems. Follow them to avoid common pitfalls.

### ✅ DO:

1. **Define Clear Roles**
   Give each agent a specific, well-defined responsibility. Avoid overlapping capabilities.
   ```python
   agent = Agent(
       name="DataAnalyst",
       role="Analyze data and find insights",
       tools=["pandas", "visualize"],
       expertise="Statistical analysis"
   )
   ```

2. **Implement Timeouts**
   Agents can get stuck. Always set timeouts to prevent hanging.
   ```python
   result = await asyncio.wait_for(
       agent.work(task),
       timeout=30.0
   )
   ```

3. **Log All Communication**
   You can't debug what you can't see. Log every message between agents.
   ```python
   def send_message(self, message):
       logger.info(f"{self.name} → {message.receiver}: {message.content}")
       self.message_queue.append(message)
   ```

4. **Handle Agent Failures**
   Individual agents will fail. Build in fallbacks and recovery mechanisms.
   ```python
   try:
       result = agent.execute(task)
   except AgentError:
       result = fallback_agent.execute(task)
   ```

5. **Use Message Types**
   Categorize messages (task, result, question, etc.) for easier routing and debugging.
   ```python
   class MessageType(Enum):
       TASK = "task"
       RESULT = "result"
       QUESTION = "question"
       ANSWER = "answer"
   ```

### ❌ DON'T:

1. **Don't create circular dependencies** - Agent A waiting for B waiting for A = deadlock
2. **Don't ignore failed agents** - Silent failures cascade into wrong results
3. **Don't forget synchronization** - Race conditions cause non-deterministic bugs
4. **Don't make agents too complex** - If one agent does too much, split it up
5. **Don't skip error handling** - Multi-agent systems have more failure modes, not fewer

---

## Summary

Multi-agent systems are a powerful tool for complex problems, but they're not always the right choice. Use them when the benefits of specialization and parallelization outweigh the coordination overhead.

**Multi-agent systems enable:**
- ✅ Specialization of agents - each does what it's best at
- ✅ Parallel execution - faster for independent tasks
- ✅ Modular design - easy to extend and maintain
- ✅ Complex problem solving - divide and conquer

**Key patterns to remember:**
- **Hierarchical** (Manager-Workers) - Best for decomposable tasks with clear leadership
- **Peer-to-Peer** (Collaborative) - Best when agents need to negotiate and collaborate
- **Blackboard** (Shared Memory) - Best for incremental, collaborative problem-solving

**When to use multi-agent systems:**
- Complex tasks requiring multiple skills that one agent can't handle well
- Need for parallel processing to reduce latency
- Modularity and maintainability important for long-term projects
- Single agent has grown too complex and needs decomposition

**When NOT to use multi-agent systems:**
- Simple tasks that one agent can handle easily
- Tight latency requirements (coordination adds overhead)
- Limited resources (multiple LLM calls = higher cost)
- Debugging is critical (multi-agent systems are harder to debug)

---

**Next Steps:**
- [AutoGen Tutorial](https://microsoft.github.io/autogen/)
- [Design Patterns](../design/patterns.md)

**Previous:** [← Security](04-security.md) | **See Also:** [Architecture Patterns](03-agent-architectures.md)

