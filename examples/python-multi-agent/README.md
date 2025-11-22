# Multi-Agent System Example

A complete implementation of the **Multi-Agent System** pattern with specialized agents collaborating under a manager.

## What is Multi-Agent System?

Unlike single-agent patterns (ReAct, Planner-Executor), multi-agent systems use **multiple specialized agents** that work together:

1. **Manager** coordinates the team
2. **Specialized Agents** handle specific tasks (research, coding, review, writing)
3. **Message Passing** enables communication
4. **Shared Context** maintains collaboration state

```
User Request → Manager → [Research, Code, Review, Write] → Synthesized Result
```

## Architecture

```
┌─────────────────────────────────────┐
│         MANAGER AGENT               │
│  (Coordinates other agents)         │
└───────┬─────────────────────────────┘
        │
        ├─────────┬─────────┬──────────┬──────────┐
        │         │         │          │          │
        ▼         ▼         ▼          ▼          ▼
   ┌──────────┐ ┌──────┐ ┌────────┐ ┌────────┐
   │Research  │ │Coder │ │Reviewer│ │Writer  │
   │ Agent    │ │Agent │ │ Agent  │ │ Agent  │
   └──────────┘ └──────┘ └────────┘ └────────┘
        │         │         │          │
        └─────────┴─────────┴──────────┘
                  │
                  ▼
          ┌───────────────┐
          │ SHARED CONTEXT│
          └───────────────┘
```

## Advantages over Other Patterns

✅ **Specialization** - Each agent excels at its specific role
✅ **Parallel Processing** - Multiple agents can work simultaneously
✅ **Scalability** - Easy to add new specialized agents
✅ **Modularity** - Agents are independent and replaceable
✅ **Complex Tasks** - Can handle sophisticated multi-faceted problems

## Features

- ✅ Complete multi-agent implementation
- ✅ Manager-worker pattern
- ✅ 4 specialized agents (researcher, coder, reviewer, writer)
- ✅ Message-based communication
- ✅ Shared context for collaboration
- ✅ Dependency-aware task delegation
- ✅ 6 example tools
- ✅ Verbose execution tracing
- ✅ Interactive mode

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
# Create .env file and add:
# OPENAI_API_KEY=your_key_here
```

## Usage

### Run Examples

```bash
python main.py
```

### Use as Library

```python
from main import create_software_team, Message

# Create team
manager = create_software_team(verbose=True)

# Assign task
task = Message(
    sender="user",
    receiver="manager",
    content="Research Python best practices and write example code"
)

result = manager.process(task)
print(result)
```

## Example Execution

```
🎯 Task: Research Python web scraping, write a scraper, and document it

======================================================================
👔 MANAGER: Coordinating team for task
======================================================================
Available agents: researcher, coder, reviewer, writer

📋 PHASE 1: Planning delegation...

📝 Delegation Plan:
   1. researcher: Research Python web scraping best practices
   2. coder: Write a simple web scraper (after: researcher)
   3. reviewer: Review the scraper code (after: coder)
   4. writer: Create documentation (after: coder, reviewer)

⚙️  PHASE 2: Executing plan...

🔍 RESEARCHER: Processing research request...
   Query: Research Python web scraping best practices
   🔎 Using web_search tool...
   💾 Using search_database tool...
   ✅ Research complete
   📋 Findings: Web scraping extracts data from websites...

💻 CODER: Processing coding request...
   Task: Write a simple web scraper
   Context from previous agents:
   researcher's output: [research findings]
   ✅ Code generation complete

📝 REVIEWER: Processing review request...
   Content length: 450 chars
   ✓ Running validation...
   ✅ Review complete

✍️  WRITER: Processing writing request...
   Task: Create documentation
   📄 Formatting document...
   ✅ Writing complete

✨ PHASE 3: Synthesizing final answer...

======================================================================
✅ TASK COMPLETE
======================================================================

Final Answer:
# Python Web Scraper Documentation

## Overview
This scraper follows best practices including:
- Respecting robots.txt
- Rate limiting requests
- Error handling

## Code
[Generated code with comments]

## Review Results
- Code structure: Good
- Error handling: Adequate
- Documentation: Complete

## Usage
[Usage instructions]
```

## The Agents

### 1. Manager Agent

**Role**: Coordinates the team

**Responsibilities**:
- Analyzes incoming tasks
- Creates delegation plans
- Assigns work to specialists
- Synthesizes final results

**Process**:
1. Understand task requirements
2. Identify which agents are needed
3. Determine execution order
4. Collect and combine results

### 2. Research Agent

**Role**: Information gathering specialist

**Capabilities**:
- Web search
- Database queries
- Data analysis
- Information synthesis

**Tools**:
- `web_search(query)` - Search for information
- `search_database(query)` - Query internal knowledge

### 3. Coding Agent

**Role**: Software development specialist

**Capabilities**:
- Write code in multiple languages
- Follow best practices
- Add documentation
- Test code

**Tools**:
- `code_executor(code)` - Test code execution

### 4. Review Agent

**Role**: Quality assurance specialist

**Capabilities**:
- Code review
- Quality validation
- Issue identification
- Improvement suggestions

**Tools**:
- `validate(content)` - Run validation checks

### 5. Writer Agent

**Role**: Documentation specialist

**Capabilities**:
- Technical writing
- Documentation creation
- Report generation
- Content formatting

**Tools**:
- `format_document(content)` - Format documents

## How It Works

### Phase 1: Planning

Manager analyzes the task and creates a delegation plan:

```python
# Manager decides which agents to use
plan = [
    {"agent": "researcher", "subtask": "Research topic X", "depends_on": []},
    {"agent": "coder", "subtask": "Write code", "depends_on": ["researcher"]},
    {"agent": "reviewer", "subtask": "Review code", "depends_on": ["coder"]},
    {"agent": "writer", "subtask": "Document", "depends_on": ["coder", "reviewer"]}
]
```

### Phase 2: Execution

Manager sends tasks to agents in order, respecting dependencies:

```python
for step in plan:
    # Wait for dependencies
    if all_dependencies_complete(step):
        # Send task to agent
        message = Message(sender="manager", receiver=agent_name, content=subtask)
        
        # Agent processes and responds
        response = agent.process(message)
        
        # Store result for dependent agents
        results[agent_name] = response.content
```

### Phase 3: Synthesis

Manager combines all contributions into a cohesive answer:

```python
# Collect all agent outputs
contributions = {
    "researcher": research_findings,
    "coder": generated_code,
    "reviewer": review_comments,
    "writer": documentation
}

# Synthesize final answer
final_answer = manager.synthesize(contributions)
```

## Message Passing

Agents communicate via structured messages:

```python
@dataclass
class Message:
    sender: str        # Who sent it
    receiver: str      # Who should receive it
    content: str       # The actual message
    metadata: Dict     # Additional data
    timestamp: float   # When it was sent
```

Example:

```python
message = Message(
    sender="manager",
    receiver="researcher",
    content="Research Python web scraping best practices",
    metadata={"priority": "high"}
)

response = researcher.process(message)
# response.content contains research findings
```

## Adding Your Own Agents

```python
from main import Agent, Message

class MySpecializedAgent(Agent):
    """Your custom agent"""
    
    def __init__(self, tools=None, verbose=True):
        super().__init__(
            name="my_agent",
            role="Description of what this agent does",
            tools=tools,
            verbose=verbose
        )
    
    def process(self, message: Message) -> Message:
        """Process incoming request"""
        
        # 1. Parse the request
        task = message.content
        
        # 2. Do your specialized work
        result = self.do_specialized_work(task)
        
        # 3. Return response message
        return self.send_message(
            receiver=message.sender,
            content=result
        )
    
    def do_specialized_work(self, task: str) -> str:
        """Your agent's core logic"""
        # Use self._call_llm() to interact with LLM
        # Use self.tools to call available tools
        # Return your result
        pass

# Add to team
manager = ManagerAgent(
    workers={
        "my_agent": MySpecializedAgent(),
        # ... other agents
    }
)
```

## Adding Custom Tools

```python
def my_custom_tool(param1: str, param2: int) -> str:
    """Tool description that LLM will read
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
    
    Returns:
        Description of return value
    """
    # Your implementation
    result = f"Processed {param1} with {param2}"
    return result

# Give tool to agent
agent = ResearchAgent(
    tools={
        "my_custom_tool": my_custom_tool,
        # ... other tools
    }
)
```

## Communication Patterns

This implementation uses **Hierarchical (Manager-Worker)**:

```
Manager
├── Worker 1
├── Worker 2
├── Worker 3
└── Worker 4
```

You could also implement:

**Peer-to-Peer**:
```
Agent A ↔ Agent B ↔ Agent C
```

**Blackboard (Shared Memory)**:
```
┌──────────────────┐
│ Shared Blackboard│ ← All agents read/write
└──────────────────┘
    ↕    ↕    ↕
  Agent Agent Agent
```

## Configuration

```python
# Create custom team
manager = ManagerAgent(
    workers={
        "agent1": Agent1(tools=tools1, verbose=True),
        "agent2": Agent2(tools=tools2, verbose=True),
    },
    verbose=True  # Show detailed execution
)

# Process task
result = manager.process(Message(
    sender="user",
    receiver="manager",
    content="Your complex task here"
))
```

## When to Use Multi-Agent

✅ **Use when:**
- Task requires diverse expertise
- Can benefit from specialization
- Multiple aspects need attention
- Building enterprise systems
- Quality is critical

❌ **Don't use when:**
- Task is simple and straightforward
- Single agent pattern suffices
- Overhead isn't justified
- Need quick prototyping

## Comparison to Other Patterns

| Aspect | ReAct | Planner-Executor | Multi-Agent |
|--------|-------|------------------|-------------|
| **Complexity** | Low | Medium | High |
| **Setup Time** | 1 day | 3 days | 1-2 weeks |
| **Specialization** | None | None | High |
| **Flexibility** | High | Medium | Very High |
| **Best For** | Simple tasks | Multi-step workflows | Complex systems |
| **Debugging** | Easy | Medium | Hard |
| **Scalability** | Limited | Medium | Excellent |

## Common Patterns

### Sequential Processing

```python
# Each agent builds on previous work
plan = [
    {"agent": "researcher", "depends_on": []},
    {"agent": "coder", "depends_on": ["researcher"]},
    {"agent": "reviewer", "depends_on": ["coder"]},
]
```

### Parallel Processing

```python
# Multiple agents work simultaneously
plan = [
    {"agent": "researcher", "depends_on": []},
    {"agent": "analyst", "depends_on": []},  # Parallel
    {"agent": "synthesizer", "depends_on": ["researcher", "analyst"]},
]
```

### Iterative Refinement

```python
# Agents iterate until quality threshold met
while not quality_sufficient:
    draft = writer.process(task)
    review = reviewer.process(draft)
    if review.quality > threshold:
        break
    # Incorporate feedback and iterate
```

## Troubleshooting

### "Agent not found"

**Cause**: Manager trying to delegate to non-existent agent

**Solution**: Ensure agent is in the `workers` dict when creating manager

### "Circular dependency"

**Cause**: Agent A depends on B, B depends on A

**Solution**: Check `depends_on` in delegation plan for cycles

### "Context too large"

**Cause**: Too many messages or large outputs

**Solution**:
- Summarize agent outputs before passing to next agent
- Clear message history periodically
- Use smaller, focused agents

## Advanced Features

### Custom Synthesis

Override `_synthesize_results` in ManagerAgent:

```python
class CustomManager(ManagerAgent):
    def _synthesize_results(self, task, plan, results):
        # Custom synthesis logic
        return custom_synthesis(results)
```

### Agent Memory

Add memory to agents:

```python
class MemoryAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = []
    
    def process(self, message):
        # Use memory from previous interactions
        context = self.memory[-5:]  # Last 5 interactions
        # ... process with context
        self.memory.append(message)
```

### Dynamic Team Formation

Create teams based on task:

```python
def create_dynamic_team(task: str):
    # Analyze task
    if "code" in task.lower():
        return create_software_team()
    elif "analysis" in task.lower():
        return create_analyst_team()
    else:
        return create_general_team()
```

## Performance Tips

1. **Use async/await** for parallel agent execution
2. **Cache results** to avoid redundant work
3. **Limit context size** passed between agents
4. **Profile** to find bottlenecks
5. **Use streaming** for real-time feedback

## Testing Your Multi-Agent System

```bash
# Run included tests
python -m pytest test_multiagent.py

# Test specific scenario
python main.py --scenario "your test case"
```

## Example Use Cases

1. **Software Development**: Research → Code → Review → Document
2. **Content Creation**: Research → Write → Edit → Format
3. **Data Analysis**: Collect → Process → Analyze → Report
4. **Customer Support**: Classify → Research → Respond → Follow-up
5. **Research**: Literature Review → Experiment → Analysis → Write Paper

## Next Steps

1. ✅ Run this example
2. 📝 Compare to ReAct and Planner-Executor
3. 🔧 Add your own specialized agents
4. 🔧 Create custom tools
5. 🧪 Try complex multi-faceted tasks
6. 🚀 Build your production system!

## See Also

- [ReAct Pattern](../python-react-pattern/) - Simpler single-agent approach
- [Planner-Executor](../python-planner-executor/) - Mid-complexity pattern
- [Agent Architectures](../../docs/03-agent-architectures.md) - Deep dive
- [Design Patterns](../../design/patterns.md) - Best practices

## Resources

- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) - Multi-agent framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent collaboration

## License

MIT - Feel free to use in your own projects!


