"""
Test suite for multi-agent system

This tests the core functionality without requiring OpenAI API calls.
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import (
    Message,
    Agent,
    ResearchAgent,
    CodingAgent,
    ReviewAgent,
    WriterAgent,
    ManagerAgent,
    web_search,
    search_database,
    code_executor,
    validate,
    format_document,
    create_software_team
)


def test_message_creation():
    """Test Message dataclass"""
    msg = Message(
        sender="agent1",
        receiver="agent2",
        content="Test message"
    )
    
    assert msg.sender == "agent1"
    assert msg.receiver == "agent2"
    assert msg.content == "Test message"
    assert isinstance(msg.metadata, dict)
    print("✓ Message creation test passed")


def test_agent_message_sending():
    """Test agent can send messages"""
    
    class TestAgent(Agent):
        def process(self, message):
            return self.send_message(
                receiver=message.sender,
                content="Response"
            )
    
    agent = TestAgent(name="test", role="tester", verbose=False)
    
    msg = Message(sender="user", receiver="test", content="Hello")
    response = agent.process(msg)
    
    assert response.sender == "test"
    assert response.receiver == "user"
    assert response.content == "Response"
    print("✓ Agent message sending test passed")


def test_tool_functions():
    """Test all tool functions work"""
    
    # Test web_search
    result = web_search("python")
    assert "Python" in result
    assert len(result) > 0
    
    # Test search_database
    result = search_database("best practices")
    assert len(result) > 0
    
    # Test code_executor
    result = code_executor("def foo(): pass")
    assert "valid" in result.lower() or "correct" in result.lower()
    
    # Test validate
    result = validate("This is some content to validate")
    assert len(result) > 0
    
    # Test format_document
    result = format_document("Some content")
    assert "Some content" in result
    
    print("✓ All tool functions test passed")


def test_research_agent():
    """Test ResearchAgent with mocked LLM"""
    
    tools = {
        "web_search": web_search,
        "search_database": search_database
    }
    
    agent = ResearchAgent(tools=tools, verbose=False)
    
    # Mock the LLM call
    with patch.object(agent, '_call_llm', return_value="Mocked research findings"):
        msg = Message(sender="manager", receiver="researcher", content="Research Python")
        response = agent.process(msg)
        
        assert response.sender == "researcher"
        assert response.receiver == "manager"
        assert len(response.content) > 0
    
    print("✓ Research agent test passed")


def test_coding_agent():
    """Test CodingAgent with mocked LLM"""
    
    tools = {
        "code_executor": code_executor
    }
    
    agent = CodingAgent(tools=tools, verbose=False)
    
    # Mock the LLM call
    with patch.object(agent, '_call_llm', return_value="def hello(): return 'world'"):
        msg = Message(sender="manager", receiver="coder", content="Write a function")
        response = agent.process(msg)
        
        assert response.sender == "coder"
        assert "def" in response.content or "return" in response.content
    
    print("✓ Coding agent test passed")


def test_review_agent():
    """Test ReviewAgent with mocked LLM"""
    
    tools = {
        "validate": validate
    }
    
    agent = ReviewAgent(tools=tools, verbose=False)
    
    # Mock the LLM call
    with patch.object(agent, '_call_llm', return_value="Review: Code looks good"):
        msg = Message(sender="manager", receiver="reviewer", content="def foo(): pass")
        response = agent.process(msg)
        
        assert response.sender == "reviewer"
        assert len(response.content) > 0
    
    print("✓ Review agent test passed")


def test_writer_agent():
    """Test WriterAgent with mocked LLM"""
    
    tools = {
        "format_document": format_document
    }
    
    agent = WriterAgent(tools=tools, verbose=False)
    
    # Mock the LLM call
    with patch.object(agent, '_call_llm', return_value="# Documentation\n\nThis is a document"):
        msg = Message(sender="manager", receiver="writer", content="Write docs")
        response = agent.process(msg)
        
        assert response.sender == "writer"
        assert len(response.content) > 0
    
    print("✓ Writer agent test passed")


def test_manager_agent():
    """Test ManagerAgent coordination"""
    
    # Create simple mock agents
    researcher = ResearchAgent(verbose=False)
    coder = CodingAgent(verbose=False)
    
    manager = ManagerAgent(
        workers={
            "researcher": researcher,
            "coder": coder
        },
        verbose=False
    )
    
    # Check manager has workers
    assert "researcher" in manager.workers
    assert "coder" in manager.workers
    assert len(manager.workers) == 2
    
    print("✓ Manager agent test passed")


def test_manager_delegation_plan():
    """Test manager can create delegation plan"""
    
    researcher = ResearchAgent(verbose=False)
    coder = CodingAgent(verbose=False)
    
    manager = ManagerAgent(
        workers={
            "researcher": researcher,
            "coder": coder
        },
        verbose=False
    )
    
    # Mock the LLM call to return a valid plan
    mock_plan = '[{"agent": "researcher", "subtask": "Research topic", "depends_on": []}]'
    
    with patch.object(manager, '_call_llm', return_value=mock_plan):
        plan = manager._create_delegation_plan("Test task")
        
        assert isinstance(plan, list)
        assert len(plan) > 0
        assert "agent" in plan[0]
    
    print("✓ Manager delegation plan test passed")


def test_create_software_team():
    """Test software team creation"""
    
    manager = create_software_team(verbose=False)
    
    assert isinstance(manager, ManagerAgent)
    assert len(manager.workers) == 4
    assert "researcher" in manager.workers
    assert "coder" in manager.workers
    assert "reviewer" in manager.workers
    assert "writer" in manager.workers
    
    # Check each agent has appropriate tools
    researcher = manager.workers["researcher"]
    assert "web_search" in researcher.tools
    
    coder = manager.workers["coder"]
    assert "code_executor" in coder.tools
    
    print("✓ Software team creation test passed")


def test_full_workflow_mock():
    """Test complete workflow with all mocked calls"""
    
    manager = create_software_team(verbose=False)
    
    # Mock all LLM calls
    mock_responses = {
        "plan": '[{"agent": "researcher", "subtask": "Research", "depends_on": []}]',
        "research": "Research findings about the topic",
        "synthesis": "Final synthesized answer combining all agent work"
    }
    
    def mock_llm_call(prompt, system_prompt=None):
        if "delegation plan" in prompt.lower():
            return mock_responses["plan"]
        elif "research" in prompt.lower():
            return mock_responses["research"]
        else:
            return mock_responses["synthesis"]
    
    # Patch all agents' LLM calls
    with patch.object(manager, '_call_llm', side_effect=mock_llm_call):
        for agent in manager.workers.values():
            agent._call_llm = Mock(side_effect=mock_llm_call)
        
        msg = Message(
            sender="user",
            receiver="manager",
            content="Simple test task"
        )
        
        result = manager.process(msg)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    print("✓ Full workflow test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 Running Multi-Agent System Tests")
    print("="*70 + "\n")
    
    tests = [
        test_message_creation,
        test_agent_message_sending,
        test_tool_functions,
        test_research_agent,
        test_coding_agent,
        test_review_agent,
        test_writer_agent,
        test_manager_agent,
        test_manager_delegation_plan,
        test_create_software_team,
        test_full_workflow_mock,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

