# Architecture Diagrams & Visual Aids

> **Visual guides to understanding AI agent architectures and tool-calling systems**

---

## Table of Contents

1. [Tool Calling Flow](#tool-calling-flow)
2. [Agent Architectures](#agent-architectures)
3. [Protocol Comparisons](#protocol-comparisons)
4. [System Architectures](#system-architectures)
5. [Data Flow Diagrams](#data-flow-diagrams)

---

## Tool Calling Flow

### Basic Tool Calling Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    TOOL CALLING LOOP                         │
└─────────────────────────────────────────────────────────────┘

    ┌──────────┐
    │  START   │
    └────┬─────┘
         │
         ▼
    ┌─────────────────┐
    │  User Query     │ ──► "What's the weather in Paris?"
    └────┬────────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │  LLM Analyzes Query          │
    │  - Understands intent        │
    │  - Identifies needed tool    │
    └────┬─────────────────────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │  Decision: Need Tool?        │
    └────┬─────────────────────────┘
         │
         ├─ Yes ────────────────────┐
         │                          ▼
         │                    ┌─────────────────┐
         │                    │  Generate       │
         │                    │  Tool Call      │
         │                    └────┬────────────┘
         │                         │
         │                         ▼
         │                    ┌─────────────────┐
         │                    │  Execute Tool   │
         │                    └────┬────────────┘
         │                         │
         │                         ▼
         │                    ┌─────────────────┐
         │                    │  Tool Result    │
         │                    └────┬────────────┘
         │                         │
         │                         ▼
         │                    ┌─────────────────┐
         │                    │  Add to Context │
         │                    └────┬────────────┘
         │                         │
         │                         └──► Loop back to LLM
         │
         └─ No ─────────────────────┐
                                    ▼
                              ┌──────────────┐
                              │  Final       │
                              │  Answer      │
                              └──────┬───────┘
                                     │
                                     ▼
                                ┌─────────┐
                                │  END    │
                                └─────────┘
```

### Detailed Tool Call Sequence

```
User                LLM                 Tool Registry         Tool
  │                  │                       │                │
  │─────Query───────►│                       │                │
  │                  │                       │                │
  │                  │───List Tools─────────►│                │
  │                  │◄──Available Tools─────│                │
  │                  │                       │                │
  │                  │ (Decides to use tool) │                │
  │                  │                       │                │
  │                  │───Tool Call Request──►│                │
  │                  │  {name: "weather",    │                │
  │                  │   args: {city: "Paris"}│               │
  │                  │                       │                │
  │                  │                       │──Execute──────►│
  │                  │                       │                │
  │                  │                       │◄──Result───────│
  │                  │◄──Tool Result─────────│  {temp: 20°C}  │
  │                  │                       │                │
  │                  │ (Processes result)    │                │
  │                  │                       │                │
  │◄────Answer───────│                       │                │
  │  "It's 20°C"     │                       │                │
  │                  │                       │                │
```

---

## Agent Architectures

### 1. ReAct Pattern

```
┌───────────────────────────────────────────────────────────┐
│                      REACT AGENT                          │
│                                                            │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐         │
│  │ THOUGHT  │ ──► │ ACTION   │ ──► │ OBSERVE  │ ──┐     │
│  └──────────┘     └──────────┘     └──────────┘   │     │
│       ▲                                             │     │
│       │                                             │     │
│       └─────────────────────────────────────────────┘     │
│                                                            │
│  Loop continues until problem solved                      │
└───────────────────────────────────────────────────────────┘

Example Flow:

Iteration 1:
  Thought:  "I need to find the weather"
  Action:   call_weather_api(city="Paris")
  Observe:  {"temp": 20, "condition": "sunny"}

Iteration 2:
  Thought:  "I have the weather data, I can answer now"
  Action:   respond_to_user
  Observe:  [Done]
```

### 2. Planner-Executor Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                  PLANNER-EXECUTOR AGENT                      │
└─────────────────────────────────────────────────────────────┘

Phase 1: PLANNING
─────────────────
  ┌───────────┐
  │   Task    │  "Book a flight and hotel in Paris"
  └─────┬─────┘
        │
        ▼
  ┌─────────────────────────────┐
  │   PLANNER (LLM)             │
  │                             │
  │  Creates step-by-step plan: │
  │   1. Search flights         │
  │   2. Select best option     │
  │   3. Search hotels          │
  │   4. Book hotel             │
  │   5. Confirm booking        │
  └─────────┬───────────────────┘
            │
            ▼
    [Plan Generated]

Phase 2: EXECUTION
──────────────────
    ┌──────────────┐
    │  EXECUTOR    │
    └──────┬───────┘
           │
           ├──► Step 1: Execute search_flights()
           │         └─► Result: [Flight options]
           │
           ├──► Step 2: Execute select_flight(id=123)
           │         └─► Result: {flight_selected}
           │
           ├──► Step 3: Execute search_hotels()
           │         └─► Result: [Hotel options]
           │
           ├──► Step 4: Execute book_hotel(id=456)
           │         └─► Result: {booking_confirmed}
           │
           └──► Step 5: Execute send_confirmation()
                     └─► Result: {email_sent}

If step fails → Replan from that point
```

### 3. Multi-Agent System (Hierarchical)

```
┌──────────────────────────────────────────────────────────────┐
│                   MULTI-AGENT SYSTEM                          │
└──────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  MANAGER AGENT  │
                    │                 │
                    │  Responsibilities:
                    │  • Decompose task
                    │  • Assign workers
                    │  • Synthesize results
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  WORKER 1   │  │  WORKER 2   │  │  WORKER 3   │
    │             │  │             │  │             │
    │ Researcher  │  │   Coder     │  │  Reviewer   │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           │                │                │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │   TOOLS     │  │   TOOLS     │  │   TOOLS     │
    │ • Search    │  │ • CodeGen   │  │ • Lint      │
    │ • Read      │  │ • Execute   │  │ • Test      │
    └─────────────┘  └─────────────┘  └─────────────┘

Example Flow:
  User: "Research asyncio and create example code"
  
  Manager: Breaks into subtasks
    ├─► Worker 1: "Research Python asyncio"
    │      └─► Uses search + read tools
    │      └─► Returns: [Documentation summary]
    │
    ├─► Worker 2: "Create example code"
    │      └─► Uses codegen + execute tools
    │      └─► Returns: [Working code]
    │
    └─► Worker 3: "Review code quality"
           └─► Uses lint + test tools
           └─► Returns: [Review report]
  
  Manager: Synthesizes all results into final answer
```

---

## Protocol Comparisons

### MCP vs UTCP Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         MCP                                   │
└──────────────────────────────────────────────────────────────┘

    ┌────────┐         ┌────────┐         ┌────────┐
    │   AI   │         │  MCP   │         │  MCP   │
    │ Agent  │◄───────►│ Client │◄───────►│ Server │
    └────────┘         └────────┘         └────────┘
                                                │
                                                ▼
                                          ┌──────────┐
                                          │ Resource │
                                          │  (API,   │
                                          │  DB, etc)│
                                          └──────────┘

Flow:
  1. Agent → Client: "I need tool X"
  2. Client → Server: JSON-RPC request
  3. Server → Resource: Execute operation
  4. Resource → Server: Result
  5. Server → Client: JSON-RPC response
  6. Client → Agent: Tool result

Pros: Stateful, flexible, custom logic
Cons: Extra hop, requires server

┌──────────────────────────────────────────────────────────────┐
│                         UTCP                                  │
└──────────────────────────────────────────────────────────────┘

    ┌────────┐         ┌────────────┐
    │   AI   │         │   UTCP     │         ┌─────────┐
    │ Agent  │◄───────►│  Executor  │◄───────►│   API   │
    └────────┘         └────────────┘         └─────────┘
                             ▲
                             │
                       ┌─────┴──────┐
                       │ JSON Manual│
                       │ (API Spec) │
                       └────────────┘

Flow:
  1. Agent → Executor: "Call tool X with args Y"
  2. Executor reads manual for tool X
  3. Executor → API: Direct HTTP request
  4. API → Executor: Response
  5. Executor → Agent: Tool result

Pros: Faster, simpler, no server
Cons: Limited to API calls, stateless

┌──────────────────────────────────────────────────────────────┐
│                      KEY DIFFERENCES                          │
└──────────────────────────────────────────────────────────────┘

╔════════════════╦═══════════════╦═══════════════════╗
║   Aspect       ║     MCP       ║       UTCP        ║
╠════════════════╬═══════════════╬═══════════════════╣
║ Architecture   ║ Client-Server ║ Direct            ║
║ State          ║ Stateful      ║ Stateless         ║
║ Latency        ║ Higher        ║ Lower             ║
║ Flexibility    ║ High          ║ Medium            ║
║ Complexity     ║ High          ║ Low               ║
║ Use Case       ║ Internal tools║ External APIs     ║
╚════════════════╩═══════════════╩═══════════════════╝
```

---

## System Architectures

### Production Agent System

```
┌──────────────────────────────────────────────────────────────────┐
│                   PRODUCTION AGENT SYSTEM                         │
└──────────────────────────────────────────────────────────────────┘

                          ┌───────────────┐
                          │    User       │
                          └───────┬───────┘
                                  │
                                  ▼
                   ┌──────────────────────────┐
                   │    API Gateway           │
                   │  • Rate limiting         │
                   │  • Authentication        │
                   └─────────┬────────────────┘
                             │
             ┌───────────────┼───────────────┐
             │               │               │
             ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Agent 1   │  │  Agent 2   │  │  Agent 3   │
    │ (Instance) │  │ (Instance) │  │ (Instance) │
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │                │                │
           └────────────────┼────────────────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
                ▼          ▼          ▼
         ┌──────────┐ ┌────────┐ ┌─────────┐
         │Tool Cache│ │Logs DB │ │ Queue   │
         └──────────┘ └────────┘ └─────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Monitoring   │
                    │ Dashboard    │
                    └──────────────┘

Key Components:

1. Load Balancer
   • Distributes requests
   • Health checks
   • Failover

2. Agent Instances
   • Stateless workers
   • Horizontal scaling
   • Isolated execution

3. Tool Cache
   • Cache tool results
   • Reduce API calls
   • TTL management

4. Logging & Monitoring
   • Track all requests
   • Performance metrics
   • Error tracking

5. Message Queue
   • Async tasks
   • Job scheduling
   • Rate limiting
```

### Sandboxed Tool Execution

```
┌──────────────────────────────────────────────────────────┐
│                 SANDBOXED EXECUTION                       │
└──────────────────────────────────────────────────────────┘

                        ┌─────────┐
                        │  Agent  │
                        └────┬────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │ Execution Layer │
                   └────┬────────────┘
                        │
            ┌───────────┼───────────┐
            │           │           │
            ▼           ▼           ▼
    ┌───────────┐ ┌──────────┐ ┌──────────┐
    │  Docker   │ │ gVisor   │ │Firecracker│
    │ Container │ │Sandbox   │ │   VM     │
    └─────┬─────┘ └─────┬────┘ └─────┬────┘
          │             │             │
          └─────────────┼─────────────┘
                        │
                  ┌─────▼─────┐
                  │   Tool    │
                  │ Execution │
                  └───────────┘

Security Layers:

Layer 1: Input Validation
  ├─ Sanitize arguments
  ├─ Type checking
  └─ Size limits

Layer 2: Resource Limits
  ├─ CPU quota
  ├─ Memory limit
  ├─ Timeout
  └─ Network restrictions

Layer 3: Sandboxing
  ├─ Isolated filesystem
  ├─ No network access (if not needed)
  ├─ Limited syscalls
  └─ No privileged operations

Layer 4: Monitoring
  ├─ Log all actions
  ├─ Detect anomalies
  └─ Kill on violation
```

---

## Data Flow Diagrams

### Data Analysis Agent Flow

```
┌──────────────────────────────────────────────────────────────┐
│              DATA ANALYSIS AGENT FLOW                         │
└──────────────────────────────────────────────────────────────┘

User Query: "Analyze sales_data.csv and create charts"

Step 1: Load Data
─────────────────
  ┌──────────────┐
  │load_dataset()│
  └──────┬───────┘
         │
         ▼
   [sales_data.csv]
         │
         ▼
   ┌──────────────┐
   │ pandas.DataFrame
   │  • 1000 rows
   │  • 8 columns
   └──────┬───────┘
         │
         └─► Stored in memory

Step 2: Understand Data
────────────────────────
  ┌───────────────┐
  │get_data_info()│
  └──────┬────────┘
         │
         ▼
   ┌─────────────────────┐
   │ Data Summary        │
   │ • Column types      │
   │ • Missing values    │
   │ • Statistics        │
   └──────┬──────────────┘
         │
         └─► Returned to Agent

Step 3: Query Data
───────────────────
  ┌─────────────┐
  │query_data() │
  │ operation:  │
  │ groupby     │
  └──────┬──────┘
         │
         ▼
   ┌─────────────────────────┐
   │ df.groupby('category')  │
   │   ['sales'].sum()       │
   └──────┬──────────────────┘
         │
         ▼
   [Aggregated Results]
         │
         └─► Returned to Agent

Step 4: Visualize
──────────────────
  ┌───────────────────┐
  │create_visualization│
  │  type: bar        │
  └──────┬────────────┘
         │
         ▼
   ┌──────────────────┐
   │ matplotlib       │
   │ plt.bar()        │
   └──────┬───────────┘
         │
         ▼
   ┌──────────────────┐
   │ output/chart.png │
   └──────────────────┘
         │
         └─► Path returned to Agent

Step 5: Report
───────────────
  ┌──────────────────┐
  │generate_report() │
  └──────┬───────────┘
         │
         ▼
   ┌────────────────────┐
   │ Compile:           │
   │ • Data summary     │
   │ • Key findings     │
   │ • Chart references │
   └──────┬─────────────┘
         │
         ▼
   ┌──────────────────┐
   │ output/report.md │
   └──────────────────┘
         │
         └─► Path returned to Agent

Step 6: Final Response
───────────────────────
  Agent synthesizes all results:
  
  "I've analyzed your sales data. Key findings:
   - Total sales: $245K
   - Top category: Electronics
   - Growth trend: +15% MoM
   
   See visualizations in output/chart.png
   Full report: output/report.md"
```

### Tool Call Decision Tree

```
┌────────────────────────────────────────────────────────────┐
│              TOOL CALL DECISION TREE                        │
└────────────────────────────────────────────────────────────┘

                    [User Query]
                         │
                         ▼
              ┌──────────────────────┐
              │ Can I answer directly│
              │ with my knowledge?   │
              └──────┬───────────────┘
                     │
        ┌────────────┼────────────┐
        │ YES        │            │ NO
        ▼            │            ▼
   ┌─────────┐      │      ┌──────────────┐
   │ Respond │      │      │ Need tools?  │
   └─────────┘      │      └──────┬───────┘
                    │             │
                    │   ┌─────────┼─────────┐
                    │   │ YES     │         │ NO
                    │   ▼         │         ▼
                    │ ┌────────────────┐  [Clarify]
                    │ │ Which tool(s)? │
                    │ └───┬────────────┘
                    │     │
                    │     ├─► Single tool needed
                    │     │     │
                    │     │     └─► Execute tool
                    │     │           │
                    │     │           └─► Got result
                    │     │                 │
                    │     │        ┌────────┼────────┐
                    │     │        │        │        │
                    │     │   Sufficient  Need      Error
                    │     │        │     more       │
                    │     │        ▼     tools      ▼
                    │     │     Respond    │     Retry/
                    │     │                │     Fallback
                    │     │                ▼
                    │     │          [Loop back]
                    │     │
                    │     └─► Multiple tools needed
                    │           │
                    │           ├─► Sequential?
                    │           │     └─► Execute one by one
                    │           │
                    │           └─► Parallel?
                    │                 └─► Execute simultaneously
                    │
                    └──► [Final Answer]

Decision Factors:
  • Query complexity
  • Tool availability
  • Previous context
  • Tool dependencies
  • Cost/latency trade-offs
```

---

## Legend

### Symbols Used

```
┌─┐  Box/Container
│ │  Vertical line
─── Horizontal line
►   Arrow (points to)
▼   Arrow down
◄   Arrow left
▲   Arrow up
└── Connection
├── Branch
┼   Intersection
```

### Common Patterns

```
┌────────┐
│ Entity │  = Component/System
└────────┘

[State]    = Current state/data

─────►     = Data flow

┌──┴──┐
│Loop │    = Iterative process
└─────┘

  X
 / \      = Decision point
Y   N
```

---

## Creating Your Own Diagrams

### Tools

**ASCII Art:**
- [asciiflow.com](https://asciiflow.com) - Online ASCII diagram editor
- [draw.io](https://draw.io) - Professional diagrams
- [mermaid.js](https://mermaid.js.org) - Markdown-based diagrams

**Example Mermaid:**

\`\`\`mermaid
graph TD
    A[User] -->|Query| B[Agent]
    B -->|Tool Call| C[Tool]
    C -->|Result| B
    B -->|Response| A
\`\`\`

### Best Practices

1. **Keep it simple** - Don't overcomplicate
2. **Label clearly** - Every box should be obvious
3. **Show data flow** - Use arrows consistently
4. **Add legends** - Explain symbols
5. **Use hierarchy** - Group related components

---

## Next Steps

- [Design Patterns](../patterns.md) - Implementation patterns
- [Anti-Patterns](../anti-patterns.md) - What to avoid
- [Examples](../../examples/) - Working code examples

---

**Note:** These are text-based diagrams optimized for markdown rendering. For presentation-quality diagrams, export to tools like draw.io, Lucidchart, or create with code using mermaid.js or PlantUML.

