"""
Multi-Agent System Pattern

This example demonstrates a multi-agent architecture where:
1. A Manager agent coordinates multiple specialized agents
2. Each agent has a specific role and expertise
3. Agents communicate via messages
4. Shared context allows collaboration

This is the most sophisticated pattern, best for complex tasks.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()


@dataclass
class Message:
    """Message passed between agents"""
    sender: str
    receiver: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __str__(self):
        return f"[{self.sender} → {self.receiver}]: {self.content[:100]}..."


class Agent(ABC):
    """Base agent class - all agents inherit from this"""
    
    def __init__(
        self,
        name: str,
        role: str,
        tools: Dict[str, callable] = None,
        verbose: bool = True
    ):
        self.name = name
        self.role = role
        self.tools = tools or {}
        self.verbose = verbose
        self._client = None  # Lazy initialization
        self.message_history: List[Message] = []
    
    @property
    def client(self):
        """Lazy load OpenAI client"""
        if self._client is None:
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    @abstractmethod
    def process(self, message: Message) -> Message:
        """Process incoming message and return response"""
        pass
    
    def send_message(self, receiver: str, content: str, metadata: Dict = None) -> Message:
        """Create and return outgoing message"""
        msg = Message(
            sender=self.name,
            receiver=receiver,
            content=content,
            metadata=metadata or {}
        )
        self.message_history.append(msg)
        return msg
    
    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """Helper to call LLM"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _format_tools(self) -> str:
        """Format tool descriptions for prompts"""
        if not self.tools:
            return "No tools available"
        
        descriptions = []
        for name, func in self.tools.items():
            doc = func.__doc__ or "No description"
            first_line = doc.strip().split('\n')[0]
            descriptions.append(f"- {name}: {first_line}")
        return "\n".join(descriptions)


class ResearchAgent(Agent):
    """Specializes in gathering information and research"""
    
    def __init__(self, tools: Dict[str, callable] = None, verbose: bool = True):
        super().__init__(
            name="researcher",
            role="Research Specialist - Gathers information and analyzes data",
            tools=tools,
            verbose=verbose
        )
    
    def process(self, message: Message) -> Message:
        """Research information based on query"""
        
        if self.verbose:
            print(f"\n🔍 {self.name.upper()}: Processing research request...")
            print(f"   Query: {message.content}")
        
        query = message.content
        
        system_prompt = f"""You are a research specialist agent in a multi-agent system.
Your role is to gather information and provide comprehensive research findings.

You have access to these tools:
{self._format_tools()}

Be thorough, accurate, and cite sources when possible."""
        
        prompt = f"""Research Task: {query}

Please:
1. Use available tools to gather relevant information
2. Synthesize findings into a clear summary
3. Highlight key facts and insights

Provide your research findings:"""
        
        # Use tools to gather information
        tool_results = []
        
        # Try to use search tool if available
        if "web_search" in self.tools:
            if self.verbose:
                print(f"   🔎 Using web_search tool...")
            try:
                search_result = self.tools["web_search"](query=query)
                tool_results.append(f"Search results: {search_result}")
            except Exception as e:
                tool_results.append(f"Search failed: {e}")
        
        # Try database if available
        if "search_database" in self.tools:
            if self.verbose:
                print(f"   💾 Using search_database tool...")
            try:
                db_result = self.tools["search_database"](query=query)
                tool_results.append(f"Database results: {db_result}")
            except Exception as e:
                tool_results.append(f"Database search failed: {e}")
        
        # Add tool results to prompt
        if tool_results:
            prompt += f"\n\nTool Results:\n" + "\n".join(tool_results)
        
        # Generate research summary
        findings = self._call_llm(prompt, system_prompt)
        
        if self.verbose:
            print(f"   ✅ Research complete")
            print(f"   📋 Findings: {findings[:150]}...")
        
        return self.send_message(
            receiver=message.sender,
            content=findings,
            metadata={"tool_results": tool_results}
        )


class CodingAgent(Agent):
    """Specializes in writing and analyzing code"""
    
    def __init__(self, tools: Dict[str, callable] = None, verbose: bool = True):
        super().__init__(
            name="coder",
            role="Coding Specialist - Writes and analyzes code",
            tools=tools,
            verbose=verbose
        )
    
    def process(self, message: Message) -> Message:
        """Generate or analyze code based on requirements"""
        
        if self.verbose:
            print(f"\n💻 {self.name.upper()}: Processing coding request...")
            print(f"   Task: {message.content}")
        
        requirements = message.content
        
        system_prompt = """You are a coding specialist agent in a multi-agent system.
Your role is to write clean, efficient, well-documented code.

Follow best practices:
- Write clear, readable code
- Add helpful comments
- Handle errors appropriately
- Follow PEP 8 style (for Python)
- Include docstrings"""
        
        prompt = f"""Coding Task: {requirements}

Please provide:
1. Complete, working code
2. Inline comments explaining key parts
3. Brief usage example if applicable

Your code:"""
        
        # Generate code
        code = self._call_llm(prompt, system_prompt)
        
        # Optionally test code
        test_result = None
        if "code_executor" in self.tools:
            if self.verbose:
                print(f"   🧪 Testing code...")
            try:
                test_result = self.tools["code_executor"](code=code)
                if self.verbose:
                    print(f"   ✅ Code tested successfully")
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Test failed: {e}")
                test_result = f"Test failed: {e}"
        
        # Add test results to response if available
        response_content = code
        if test_result:
            response_content += f"\n\n# Test Results:\n# {test_result}"
        
        if self.verbose:
            print(f"   ✅ Code generation complete")
        
        return self.send_message(
            receiver=message.sender,
            content=response_content,
            metadata={"test_result": test_result}
        )


class ReviewAgent(Agent):
    """Specializes in reviewing and validating work"""
    
    def __init__(self, tools: Dict[str, callable] = None, verbose: bool = True):
        super().__init__(
            name="reviewer",
            role="Review Specialist - Validates and improves quality",
            tools=tools,
            verbose=verbose
        )
    
    def process(self, message: Message) -> Message:
        """Review and provide feedback"""
        
        if self.verbose:
            print(f"\n📝 {self.name.upper()}: Processing review request...")
            print(f"   Content length: {len(message.content)} chars")
        
        content_to_review = message.content
        
        system_prompt = """You are a review specialist agent in a multi-agent system.
Your role is to critically evaluate work and provide constructive feedback.

Focus on:
- Accuracy and correctness
- Completeness
- Clarity and presentation
- Potential improvements
- Issues or concerns

Be thorough but fair."""
        
        prompt = f"""Please review this work:

{content_to_review}

Provide:
1. Overall assessment (Good/Needs Work)
2. Strengths (what's done well)
3. Issues (problems or concerns)
4. Suggestions (improvements)

Your review:"""
        
        # Generate review
        review = self._call_llm(prompt, system_prompt)
        
        # Use validator tool if available
        validation_result = None
        if "validate" in self.tools:
            if self.verbose:
                print(f"   ✓ Running validation...")
            try:
                validation_result = self.tools["validate"](content=content_to_review)
            except Exception as e:
                validation_result = f"Validation error: {e}"
        
        # Add validation results
        if validation_result:
            review += f"\n\nValidation: {validation_result}"
        
        if self.verbose:
            print(f"   ✅ Review complete")
        
        return self.send_message(
            receiver=message.sender,
            content=review,
            metadata={"validation_result": validation_result}
        )


class WriterAgent(Agent):
    """Specializes in writing documentation and reports"""
    
    def __init__(self, tools: Dict[str, callable] = None, verbose: bool = True):
        super().__init__(
            name="writer",
            role="Writing Specialist - Creates documentation and reports",
            tools=tools,
            verbose=verbose
        )
    
    def process(self, message: Message) -> Message:
        """Write documentation or report"""
        
        if self.verbose:
            print(f"\n✍️  {self.name.upper()}: Processing writing request...")
            print(f"   Task: {message.content[:100]}...")
        
        writing_task = message.content
        
        system_prompt = """You are a writing specialist agent in a multi-agent system.
Your role is to create clear, well-structured documentation and reports.

Focus on:
- Clear structure with headings
- Concise but comprehensive
- Proper formatting (markdown)
- Appropriate tone for audience
- Actionable information"""
        
        prompt = f"""Writing Task: {writing_task}

Create well-formatted content that is:
- Easy to read and understand
- Properly structured
- Complete and thorough

Your content:"""
        
        # Generate content
        content = self._call_llm(prompt, system_prompt)
        
        # Format using tool if available
        if "format_document" in self.tools:
            if self.verbose:
                print(f"   📄 Formatting document...")
            try:
                content = self.tools["format_document"](content=content)
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Formatting failed: {e}")
        
        if self.verbose:
            print(f"   ✅ Writing complete")
        
        return self.send_message(
            receiver=message.sender,
            content=content
        )


class ManagerAgent(Agent):
    """Coordinates other agents to accomplish complex tasks"""
    
    def __init__(
        self,
        workers: Dict[str, Agent],
        verbose: bool = True
    ):
        super().__init__(
            name="manager",
            role="Manager - Coordinates team of specialist agents",
            verbose=verbose
        )
        self.workers = workers
        self.shared_context: Dict[str, Any] = {}
    
    def process(self, message: Message) -> str:
        """
        Coordinate workers to complete task
        
        Process:
        1. Analyze the task
        2. Create delegation plan
        3. Assign work to specialists
        4. Collect and synthesize results
        """
        
        task = message.content
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"👔 MANAGER: Coordinating team for task")
            print(f"{'='*70}")
            print(f"Task: {task}")
            print(f"\nAvailable agents: {', '.join(self.workers.keys())}")
            print(f"{'='*70}")
        
        # Phase 1: Create delegation plan
        if self.verbose:
            print(f"\n📋 PHASE 1: Planning delegation...")
        
        plan = self._create_delegation_plan(task)
        
        if not plan:
            return "Failed to create a delegation plan."
        
        # Phase 2: Execute plan
        if self.verbose:
            print(f"\n⚙️  PHASE 2: Executing plan...")
        
        results = self._execute_plan(plan, task)
        
        # Phase 3: Synthesize results
        if self.verbose:
            print(f"\n✨ PHASE 3: Synthesizing final answer...")
        
        final_answer = self._synthesize_results(task, plan, results)
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"✅ TASK COMPLETE")
            print(f"{'='*70}\n")
            print(f"Final Answer:\n{final_answer}")
            print(f"\n{'='*70}\n")
        
        return final_answer
    
    def _create_delegation_plan(self, task: str) -> List[Dict[str, Any]]:
        """Decide which agents should work on this task and in what order"""
        
        agent_descriptions = []
        for name, agent in self.workers.items():
            agent_descriptions.append(f"- {name}: {agent.role}")
        
        agents_list = "\n".join(agent_descriptions)
        
        planning_prompt = f"""You are a manager coordinating a team of specialist agents.

Available agents:
{agents_list}

Task: {task}

Create a delegation plan: which agents should work on this and in what order?
Consider:
- Which agents have relevant expertise
- What dependencies exist (does one agent need another's output?)
- Optimal sequence for collaboration

Respond in JSON format:
[
  {{
    "agent": "agent_name",
    "subtask": "specific task for this agent",
    "depends_on": []
  }},
  ...
]

If an agent needs results from another, list that agent in depends_on.

Plan:"""
        
        response = self._call_llm(planning_prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
                
                if self.verbose:
                    print(f"\n📝 Delegation Plan:")
                    for i, step in enumerate(plan, 1):
                        deps = f" (after: {', '.join(step.get('depends_on', []))})" if step.get('depends_on') else ""
                        print(f"   {i}. {step['agent']}: {step['subtask']}{deps}")
                
                return plan
            else:
                if self.verbose:
                    print(f"   ❌ Could not extract JSON plan")
                return []
        
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Failed to parse plan: {e}")
            return []
    
    def _execute_plan(
        self,
        plan: List[Dict[str, Any]],
        original_task: str
    ) -> Dict[str, str]:
        """Execute the delegation plan"""
        
        results: Dict[str, str] = {}
        
        for step in plan:
            agent_name = step['agent']
            subtask = step['subtask']
            depends_on = step.get('depends_on', [])
            
            # Check if agent exists
            if agent_name not in self.workers:
                if self.verbose:
                    print(f"\n   ⚠️  Agent '{agent_name}' not found, skipping")
                continue
            
            # Build context from dependencies
            context = ""
            if depends_on:
                context = "\n\nContext from previous agents:\n"
                for dep_agent in depends_on:
                    if dep_agent in results:
                        context += f"\n{dep_agent}'s output:\n{results[dep_agent]}\n"
            
            # Add context to subtask
            full_task = subtask + context
            
            # Send task to agent
            task_message = Message(
                sender=self.name,
                receiver=agent_name,
                content=full_task
            )
            
            # Get agent's response
            agent = self.workers[agent_name]
            try:
                response = agent.process(task_message)
                results[agent_name] = response.content
                
                # Store in shared context
                self.shared_context[agent_name] = {
                    "output": response.content,
                    "metadata": response.metadata,
                    "timestamp": response.timestamp
                }
            
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                results[agent_name] = error_msg
                if self.verbose:
                    print(f"\n   ❌ Agent {agent_name} failed: {e}")
        
        return results
    
    def _synthesize_results(
        self,
        original_task: str,
        plan: List[Dict[str, Any]],
        results: Dict[str, str]
    ) -> str:
        """Combine all agent outputs into final answer"""
        
        # Build summary of contributions
        contributions = []
        for agent_name, output in results.items():
            # Find the agent's role
            role = self.workers[agent_name].role if agent_name in self.workers else "Agent"
            contributions.append(f"\n{agent_name} ({role}):\n{output}\n")
        
        contributions_text = "\n".join(contributions)
        
        synthesis_prompt = f"""You are a manager synthesizing your team's work.

Original Task: {original_task}

Team Contributions:
{contributions_text}

Please create a cohesive final answer that:
1. Directly addresses the original task
2. Integrates all relevant contributions
3. Is well-structured and clear
4. Highlights key findings/results

Final Answer:"""
        
        final_answer = self._call_llm(synthesis_prompt)
        
        return final_answer


# ============================================================================
# EXAMPLE TOOLS
# ============================================================================

def web_search(query: str) -> str:
    """Searches the web for information"""
    # Mock implementation
    search_results = {
        "python": "Python is a high-level programming language known for readability and versatility. Created by Guido van Rossum in 1991.",
        "machine learning": "Machine learning is a subset of AI that enables systems to learn from data. Popular frameworks include TensorFlow, PyTorch, and scikit-learn.",
        "web scraping": "Web scraping extracts data from websites. Common tools: BeautifulSoup, Scrapy, Selenium. Always check robots.txt and terms of service.",
        "api": "API (Application Programming Interface) allows different software to communicate. REST and GraphQL are popular API architectures.",
        "database": "Databases store and organize data. SQL databases (PostgreSQL, MySQL) for structured data; NoSQL (MongoDB, Redis) for flexible schemas.",
    }
    
    query_lower = query.lower()
    
    # Find best match
    for key, value in search_results.items():
        if key in query_lower:
            return value
    
    return f"Search results for '{query}': Found general information. Key concepts include best practices, implementation strategies, and common use cases."


def search_database(query: str, table: str = "all") -> str:
    """Searches internal database for information"""
    # Mock implementation
    database = {
        "best practices python": "Python best practices: Use virtual environments, follow PEP 8, write tests, use type hints, document code.",
        "code review checklist": "Code review checklist: 1) Correctness, 2) Tests, 3) Documentation, 4) Performance, 5) Security, 6) Style consistency.",
        "project structure": "Standard Python project: project/src/main.py, tests/, docs/, README.md, requirements.txt, .gitignore.",
        "error handling": "Error handling: Use try-except, catch specific exceptions, log errors, provide helpful messages, fail gracefully.",
    }
    
    query_lower = query.lower()
    
    for key, value in database.items():
        if any(word in query_lower for word in key.split()):
            return value
    
    return f"Database search for '{query}': Found {len(database)} related entries."


def code_executor(code: str) -> str:
    """Executes code and returns result (mock)"""
    # In production, use proper sandboxing!
    # This is a mock implementation
    
    if "def " in code or "class " in code:
        return "Code structure looks valid. Functions and classes defined correctly."
    elif "import " in code:
        return "Code includes imports. Dependencies should be documented."
    else:
        return "Code syntax appears valid."


def validate(content: str) -> str:
    """Validates content quality"""
    # Simple validation checks
    checks = []
    
    if len(content) < 50:
        checks.append("⚠️  Content is quite short")
    else:
        checks.append("✓ Adequate length")
    
    if "\n" in content:
        checks.append("✓ Has structure/breaks")
    
    if any(word in content.lower() for word in ["error", "fail", "issue", "problem"]):
        checks.append("⚠️  Contains error/issue mentions")
    
    return " | ".join(checks) if checks else "✓ Validation passed"


def format_document(content: str, style: str = "markdown") -> str:
    """Formats document in specified style"""
    if style == "markdown":
        # Ensure proper markdown formatting
        if not content.startswith("#"):
            content = "# Document\n\n" + content
    
    return content


# ============================================================================
# MULTI-AGENT SYSTEM SETUP
# ============================================================================

def create_software_team(verbose: bool = True) -> ManagerAgent:
    """
    Create a software development team of agents
    
    Team composition:
    - Manager: Coordinates the team
    - Researcher: Gathers requirements and information
    - Coder: Writes code
    - Reviewer: Reviews and validates work
    - Writer: Creates documentation
    """
    
    # Define tools for each agent
    research_tools = {
        "web_search": web_search,
        "search_database": search_database,
    }
    
    coding_tools = {
        "code_executor": code_executor,
    }
    
    review_tools = {
        "validate": validate,
    }
    
    writing_tools = {
        "format_document": format_document,
    }
    
    # Create specialized agents
    researcher = ResearchAgent(tools=research_tools, verbose=verbose)
    coder = CodingAgent(tools=coding_tools, verbose=verbose)
    reviewer = ReviewAgent(tools=review_tools, verbose=verbose)
    writer = WriterAgent(tools=writing_tools, verbose=verbose)
    
    # Create manager with team
    manager = ManagerAgent(
        workers={
            "researcher": researcher,
            "coder": coder,
            "reviewer": reviewer,
            "writer": writer,
        },
        verbose=verbose
    )
    
    return manager


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    """Run example scenarios"""
    
    print("\n" + "="*70)
    print("🤖 Multi-Agent System - Interactive Demo")
    print("="*70)
    print("\nThis demo shows multiple specialized agents collaborating")
    print("to complete complex tasks.\n")
    
    # Create the team
    print("📋 Creating software development team...")
    manager = create_software_team(verbose=True)
    print("✅ Team ready!\n")
    
    # Example scenarios
    examples = [
        "Research Python web scraping best practices, write a simple scraper, and document it",
        "Create a Python function to calculate fibonacci numbers, review it, and write documentation",
        "Research REST API design, write example code, and create a usage guide",
    ]
    
    print("📋 Running example scenarios...\n")
    
    for i, task in enumerate(examples, 1):
        print(f"\n{'#'*70}")
        print(f"Scenario {i}/{len(examples)}")
        print(f"{'#'*70}")
        
        try:
            # Create task message
            task_message = Message(
                sender="user",
                receiver="manager",
                content=task
            )
            
            # Execute
            result = manager.process(task_message)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        if i < len(examples):
            input("\n⏸️  Press Enter to continue to next scenario...")
    
    # Interactive mode
    print(f"\n{'#'*70}")
    print("💬 Interactive Mode - Ask complex questions!")
    print(f"{'#'*70}")
    print("\nThe team can:")
    print("- Research information")
    print("- Write code")
    print("- Review work")
    print("- Create documentation")
    print("\nType 'exit' or 'quit' to end\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if not user_input:
                continue
            
            task_message = Message(
                sender="user",
                receiver="manager",
                content=user_input
            )
            
            result = manager.process(task_message)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()

