# Design Patterns and Architecture

> **Architectural guidance, patterns, and anti-patterns for building robust AI agents with tool-calling capabilities**

---

## 📐 Overview

This directory contains design patterns, anti-patterns, architecture diagrams, and best practices for building production-ready AI agent systems. Whether you're implementing ReAct agents, multi-agent systems, or tool-calling workflows, you'll find actionable patterns and visual guides here.

---

## 📚 Core Documentation

### [Design Patterns](patterns.md)
**10 proven patterns for building reliable, maintainable AI agents**

Covers tool design, agent architecture, error handling, state management, security, and testing patterns. Learn how to:
- Wrap tools with validation and timeouts (Tool Wrapper Pattern)
- Create tools from configurations (Factory Pattern)
- Build complex workflows from simple tools (Composition Pattern)
- Implement flexible agent behaviors (Strategy Pattern)
- Handle cascading failures gracefully (Circuit Breaker Pattern)
- Secure your agents with allowlists (Security Patterns)
- Test agents without external dependencies (Test Double Pattern)

### [Anti-Patterns](anti-patterns.md)
**14 common mistakes to avoid when building AI agents**

Learn what NOT to do through real-world examples. Key anti-patterns include:
- **God Tools** - Tools that do too much
- **Silent Failures** - Errors that look like success
- **eval() for Everything** - Critical security vulnerability
- **Credentials in Prompts** - Exposing secrets to LLMs
- **Infinite Loop Trap** - Agents that never stop
- **Testing in Production** - Using real APIs in tests
- **No Input Validation** - Trusting LLM output blindly

Each anti-pattern includes bad examples, why it's problematic, and better approaches.

### [Architecture Diagrams](diagrams/)
**Visual guides to understanding agent architectures and tool-calling systems**

ASCII diagrams and visual representations covering:
- **Tool Calling Flow** - Step-by-step execution sequences
- **Agent Architectures** - ReAct, Planner-Executor, Multi-Agent systems
- **Protocol Comparisons** - [MCP vs UTCP visual comparison](diagrams/protocol-comparison.gif)
- **Production Systems** - Full production architecture with monitoring
- **Sandboxed Execution** - Security layers for tool execution
- **Data Flow Diagrams** - Real-world agent workflows

#### Diagrams
- [Agent Architecture Patterns](diagrams/README.md#agent-architectures) - ReAct, Planner-Executor, Multi-Agent
- [UTCP vs MCP Comparison](diagrams/protocol-comparison.gif) - Animated comparison
- [Protocol Architecture Comparison](diagrams/README.md#protocol-comparisons) - Detailed MCP vs UTCP
- [Production System Architecture](diagrams/README.md#production-agent-system) - Full production setup
- [Sandboxed Tool Execution](diagrams/README.md#sandboxed-tool-execution) - Security patterns
- [Tool Call Flow Diagrams](diagrams/README.md#tool-calling-flow) - Execution sequences

#### External Resources with Diagrams
- [ReAct Paper (arXiv)](https://arxiv.org/abs/2210.03629) - Authoritative source on reasoning + acting agents
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling) - Official function calling documentation
- [Anthropic Claude Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) - Claude's tool use patterns
- [LangChain Agent Documentation](https://docs.langchain.com/docs/modules/agents/) - Framework-specific architectures
- [AWS AI/ML Security Best Practices](https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/security.html) - Production security patterns

---

## 🎯 Quick Links

### By Use Case
- **Building your first agent?** Start with [patterns.md](patterns.md#tool-design-patterns)
- **Production deployment?** See [diagrams/README.md](diagrams/README.md#production-agent-system)
- **Security concerns?** Check [patterns.md](patterns.md#security-patterns) and [anti-patterns.md](anti-patterns.md#security-anti-patterns)
- **Performance issues?** Review [anti-patterns.md](anti-patterns.md#performance-anti-patterns)
- **Testing strategy?** See [patterns.md](patterns.md#testing-patterns)

### By Architecture Pattern
- [**ReAct Pattern**](diagrams/README.md#1-react-pattern) - Reasoning + Acting loop
- [**Planner-Executor Pattern**](diagrams/README.md#2-planner-executor-pattern) - Plan then execute
- [**Multi-Agent System**](diagrams/README.md#3-multi-agent-system-hierarchical) - Hierarchical agents

### Protocol Resources
- [**MCP vs UTCP Comparison**](diagrams/protocol-comparison.gif) - Animated visual comparison
- [**Protocol Architecture Details**](diagrams/README.md#protocol-comparisons) - When to use which protocol
- [**UTCP Examples**](../examples/python-utcp-weather/) - Working UTCP implementation
- [**MCP Examples**](../examples/python-mcp-files/) - Working MCP implementation

---

## 🏗️ Architecture Decision Records

This section documents key architectural decisions made in the project:

### ADR-001: Hybrid Protocol Approach
- **Decision:** Use UTCP for external public APIs, MCP for internal tools
- **Rationale:** Optimizes for speed (UTCP) and control (MCP)
- **Trade-off:** Increased complexity, mitigated by adapter layer

### ADR-002: Plan-and-Execute for Structured Tasks
- **Decision:** Use Planner-Executor pattern over pure ReAct for predictable workflows
- **Rationale:** More efficient for multi-step tasks, better user experience
- **Trade-off:** Less flexible, mitigated by allowing re-planning on failures

*See [patterns.md](patterns.md) for full ADR details*

---

## 🎨 Pattern Overview

<table>
<tr>
<th>Category</th>
<th>Patterns</th>
</tr>
<tr>
<td><strong>Tool Design</strong></td>
<td>
• Tool Wrapper<br>
• Tool Factory<br>
• Tool Composition
</td>
</tr>
<tr>
<td><strong>Agent Architecture</strong></td>
<td>
• Strategy Pattern<br>
• Chain of Responsibility<br>
• ReAct Loop
</td>
</tr>
<tr>
<td><strong>Error Handling</strong></td>
<td>
• Circuit Breaker<br>
• Retry with Backoff<br>
• Graceful Degradation
</td>
</tr>
<tr>
<td><strong>State Management</strong></td>
<td>
• Memento Pattern<br>
• Stateless Agents<br>
• Context Management
</td>
</tr>
<tr>
<td><strong>Security</strong></td>
<td>
• Allowlist Enforcement<br>
• Input Validation<br>
• Sandboxed Execution
</td>
</tr>
<tr>
<td><strong>Testing</strong></td>
<td>
• Test Doubles<br>
• Mock Tools<br>
• Error Case Testing
</td>
</tr>
</table>

---

## 🚀 Getting Started

### 1. **Learn the Basics**
Start with the [Tool Calling Flow diagram](diagrams/README.md#tool-calling-flow) to understand how agents interact with tools.

### 2. **Study Patterns**
Read through [patterns.md](patterns.md) to learn proven approaches for common challenges.

### 3. **Avoid Pitfalls**
Review [anti-patterns.md](anti-patterns.md) to learn from common mistakes.

### 4. **See It in Action**
Check out [working examples](../examples/) that implement these patterns.

### 5. **Choose Your Architecture**
Use the [architecture diagrams](diagrams/) to select the right pattern for your use case.

---

## 🔗 External Resources

### Official Documentation
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Claude Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [LangChain Agent Documentation](https://docs.langchain.com/docs/modules/agents/)

### Research Papers
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)

### System Design
- [System Design Primer](https://github.com/donnemartin/system-design-primer)
- [Cloud Design Patterns (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/)
- [AWS AI/ML Security Best Practices](https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/security.html)

---

## 📖 Related Documentation

- [**Documentation**](../docs/) - Comprehensive guides on fundamentals, architectures, and security
- [**Examples**](../examples/) - Working code examples implementing these patterns
- [**Protocols**](../protocols/) - UTCP and MCP specifications and tutorials
- [**Projects**](../projects/) - Full project implementations

---

## 🤝 Contributing

Have a pattern or anti-pattern to share? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Submitting new patterns
- Adding diagrams
- Documenting architecture decisions
- Sharing real-world examples

---

## 📝 Quick Reference Checklist

**Before deploying an agent, verify:**

- [ ] Tools are focused and well-documented
- [ ] Error handling returns clear success/failure
- [ ] Credentials are never in prompts
- [ ] Input validation on all tools
- [ ] Max iteration limits to prevent loops
- [ ] Error cases are tested
- [ ] Expensive operations are cached
- [ ] No `eval()` on untrusted input
- [ ] State is managed cleanly
- [ ] Security allowlists are in place

*Full checklist in [anti-patterns.md](anti-patterns.md#quick-checklist)*
