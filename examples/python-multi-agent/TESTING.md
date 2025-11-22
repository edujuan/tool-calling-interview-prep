# Testing Guide

Complete guide to testing the multi-agent system.

## 🧪 Test Suite

The `test_multiagent.py` file contains 11 comprehensive tests:

### Tests Included

1. ✅ **Message Creation** - Verifies Message dataclass
2. ✅ **Agent Message Sending** - Tests agent communication
3. ✅ **Tool Functions** - Tests all 5 tools
4. ✅ **Research Agent** - Tests research functionality
5. ✅ **Coding Agent** - Tests code generation
6. ✅ **Review Agent** - Tests review process
7. ✅ **Writer Agent** - Tests documentation creation
8. ✅ **Manager Agent** - Tests team coordination
9. ✅ **Manager Delegation Plan** - Tests planning logic
10. ✅ **Software Team Creation** - Tests team setup
11. ✅ **Full Workflow** - Tests complete end-to-end

## 🚀 Running Tests

### Basic Test Run

```bash
python test_multiagent.py
```

Expected output:
```
======================================================================
🧪 Running Multi-Agent System Tests
======================================================================

✓ Message creation test passed
✓ Agent message sending test passed
✓ All tool functions test passed
✓ Research agent test passed
✓ Coding agent test passed
✓ Review agent test passed
✓ Writer agent test passed
✓ Manager agent test passed
✓ Manager delegation plan test passed
✓ Software team creation test passed
✓ Full workflow test passed

======================================================================
Results: 11 passed, 0 failed
======================================================================
```

### With pytest (if installed)

```bash
pip install pytest
pytest test_multiagent.py -v
```

## 🔍 What Gets Tested

### Unit Tests

Each agent is tested individually:

```python
def test_research_agent():
    """Test ResearchAgent with mocked LLM"""
    agent = ResearchAgent(tools={"web_search": web_search})
    
    # Mock LLM call
    with patch.object(agent, '_call_llm', return_value="Mocked findings"):
        msg = Message(sender="manager", receiver="researcher", content="Research Python")
        response = agent.process(msg)
        
        assert response.sender == "researcher"
        assert len(response.content) > 0
```

### Integration Tests

The full system is tested:

```python
def test_full_workflow_mock():
    """Test complete workflow with all mocked calls"""
    manager = create_software_team(verbose=False)
    
    # Mock all LLM calls
    with patch.object(manager, '_call_llm', side_effect=mock_llm_call):
        msg = Message(sender="user", receiver="manager", content="Test task")
        result = manager.process(msg)
        
        assert isinstance(result, str)
        assert len(result) > 0
```

## 🎯 Manual Testing

### Test Without API Key

The test suite uses mocking, so no API key is needed:

```bash
# No OPENAI_API_KEY required
python test_multiagent.py
```

### Test With Real API

For end-to-end testing with real API calls:

```bash
# Set up API key
export OPENAI_API_KEY=your_key_here

# Run demo
python demo.py

# Or interactive mode
python main.py
```

## 📊 Test Coverage

The tests cover:

- ✅ Message passing between agents
- ✅ Agent initialization and setup
- ✅ Tool execution
- ✅ Manager coordination logic
- ✅ Delegation planning
- ✅ Error handling
- ✅ Full workflow execution

## 🔧 Adding Your Own Tests

### Test a Custom Agent

```python
def test_my_custom_agent():
    """Test your custom agent"""
    agent = MyCustomAgent(tools=my_tools, verbose=False)
    
    # Mock LLM if needed
    with patch.object(agent, '_call_llm', return_value="Expected output"):
        msg = Message(sender="test", receiver="my_agent", content="Test input")
        response = agent.process(msg)
        
        assert response.sender == "my_agent"
        assert "expected" in response.content.lower()
    
    print("✓ Custom agent test passed")
```

### Test a Custom Tool

```python
def test_my_custom_tool():
    """Test your custom tool"""
    result = my_custom_tool(param="test")
    
    assert result is not None
    assert len(result) > 0
    # Add specific assertions
    
    print("✓ Custom tool test passed")
```

## 🐛 Debugging Failed Tests

### Common Issues

#### Import Error

```
ImportError: No module named 'main'
```

**Solution**: Make sure you're in the correct directory:
```bash
cd examples/python-multi-agent
python test_multiagent.py
```

#### OpenAI API Error (in tests)

```
The api_key client option must be set
```

**Solution**: Tests shouldn't need API key. This means mocking failed. Check:
- Agent's `_call_llm` is properly mocked
- OpenAI client is lazily loaded (not in `__init__`)

#### Assertion Failed

```
AssertionError: ...
```

**Solution**: 
- Check what the test expects vs what it got
- Add print statements to debug
- Verify mock return values match expected format

### Debug Mode

Add verbose output to tests:

```python
def test_with_debug():
    agent = ResearchAgent(verbose=True)  # Enable verbose mode
    # ... rest of test
```

## 📈 Performance Testing

### Measure Execution Time

```python
import time

start = time.time()
result = manager.process(task_message)
duration = time.time() - start

print(f"Execution time: {duration:.2f}s")
```

### Profile Memory Usage

```python
import tracemalloc

tracemalloc.start()

# Run your test
result = manager.process(task_message)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

## ✅ Continuous Integration

### GitHub Actions Example

```yaml
name: Test Multi-Agent System

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd examples/python-multi-agent
          python test_multiagent.py
```

## 🎭 Mock Strategies

### Mock LLM Responses

```python
# Simple mock
with patch.object(agent, '_call_llm', return_value="Fixed response"):
    result = agent.process(message)

# Dynamic mock based on input
def dynamic_mock(prompt, system_prompt=None):
    if "research" in prompt.lower():
        return "Research findings..."
    return "Default response"

with patch.object(agent, '_call_llm', side_effect=dynamic_mock):
    result = agent.process(message)
```

### Mock Tools

```python
# Mock a tool
def mock_web_search(query):
    return f"Mock results for: {query}"

agent = ResearchAgent(tools={"web_search": mock_web_search})
```

## 📝 Test Checklist

Before committing changes:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] No linter errors
- [ ] Code is documented
- [ ] New features have tests
- [ ] Manual testing done (if applicable)

Run full check:

```bash
# Run tests
python test_multiagent.py

# Check linting (if pylint installed)
pylint main.py

# Check formatting (if black installed)
black --check main.py
```

## 🚀 Quick Verification

Run this one-liner to verify everything:

```bash
cd examples/python-multi-agent && python test_multiagent.py && echo "✅ All tests passed!"
```

## 📚 See Also

- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [main.py](main.py) - Implementation with inline comments
- [demo.py](demo.py) - Simple demonstration script

## 💡 Tips

1. **Run tests frequently** - After each change
2. **Use verbose mode** - For debugging
3. **Mock external calls** - Keep tests fast and reliable
4. **Test edge cases** - Not just happy path
5. **Keep tests simple** - One concept per test

Happy testing! 🧪✨



