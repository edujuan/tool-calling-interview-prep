# Advanced Questions (91-96)

## Advanced Topics

### 91. Design an agent architecture that uses both UTCP and MCP. When would you route to each?

**Answer:**

> **See also:** [Protocol Comparison Guide](../docs/06-protocol-comparison.md#the-hybrid-approach), [Hybrid Architecture Patterns](../docs/03-agent-architectures.md#hybrid-approach-using-both-protocols), [Protocol Comparison](../protocols/comparison.md#hybrid-approach), [Interview Question 45](03-protocols.md#45-can-you-use-both-utcp-and-mcp-together)

**Architecture:**

```python
class HybridToolAgent:
    """Agent that intelligently routes between UTCP and MCP"""
    
    def __init__(self):
        self.utcp_client = UTCPClient()
        self.mcp_client = MCPClient()
        
        # Tool routing rules
        self.routing_rules = {
            "external": "utcp",      # Public APIs
            "internal": "mcp",       # Internal tools
            "sensitive": "mcp",      # High-security
            "high_volume": "utcp",   # Performance-critical
            "stateful": "mcp",       # Need session
            "read_only": "utcp"      # Safe, fast
        }
    
    async def call_tool(self, tool_name: str, args: dict, metadata: dict):
        """Route tool call based on characteristics"""
        
        # Decision factors
        category = metadata.get('category')
        requires_audit = metadata.get('audit_required', False)
        requires_state = metadata.get('stateful', False)
        call_frequency = metadata.get('expected_frequency', 'low')
        
        # Routing logic
        if requires_audit or requires_state:
            # MCP for governance and statefulness
            return await self.mcp_client.call_tool(tool_name, args)
        
        elif call_frequency == 'high' and not metadata.get('sensitive'):
            # UTCP for high-performance public APIs
            return await self.utcp_client.call_tool(tool_name, args)
        
        elif category == 'external' and not requires_audit:
            # UTCP for external APIs (faster)
            return await self.utcp_client.call_tool(tool_name, args)
        
        else:
            # Default to MCP for safety
            return await self.mcp_client.call_tool(tool_name, args)
```

**Routing Decision Matrix:**

| Tool Type | Protocol | Reason |
|-----------|----------|--------|
| Public weather API | UTCP | Fast, no governance needed |
| Customer database | MCP | Audit trail required |
| Real-time stock prices | UTCP | High frequency, performance critical |
| Employee management | MCP | Sensitive, needs access control |
| OpenAPI-documented API | UTCP | Easy integration with existing spec |
| Multi-step workflow tool | MCP | Stateful, benefits from sessions |

**Implementation Benefits:**
- ✅ Optimal performance per tool type
- ✅ Security where needed
- ✅ Cost-effective (no overhead for simple tools)
- ✅ Flexible and maintainable

---

### 92. How would you implement comprehensive error recovery in a multi-tool agent?

**Answer:**

> **See also:** [Error Handling Example](../examples/python-error-handling/), [Error Handling README](../examples/python-error-handling/README.md), [Fundamentals: Error Handling](../docs/02-fundamentals.md#error-handling-and-recovery), [Architecture: Resilient Agents](02-architecture.md#30-how-do-you-make-agents-resilient-to-failures), [Basics: Error Handling](01-basics.md#9-what-happens-when-a-tool-fails)

**Multi-Layer Error Recovery:**

```python
class ResilientAgent:
    """Agent with comprehensive error recovery"""
    
    def __init__(self):
        self.tool_executor = ToolExecutor()
        self.fallback_strategies = {
            "weather_api": ["backup_weather_api", "cached_weather"],
            "database": ["read_replica", "cache"],
            "email": ["backup_smtp", "queue_for_retry"]
        }
        self.circuit_breakers = {}
        self.retry_policies = {}
    
    async def execute_with_recovery(self, tool_name, args):
        """Execute tool with full error recovery"""
        
        # Check circuit breaker
        if self.circuit_breakers.get(tool_name, {}).get("open"):
            return await self.use_fallback(tool_name, args)
        
        # Try primary tool
        try:
            result = await self.try_with_retry(tool_name, args)
            self.record_success(tool_name)
            return result
        
        except ToolTimeoutError:
            logger.warning(f"{tool_name} timed out, trying fallback")
            return await self.use_fallback(tool_name, args)
        
        except ToolRateLimitError as e:
            logger.warning(f"{tool_name} rate limited")
            await asyncio.sleep(e.retry_after or 60)
            return await self.execute_with_recovery(tool_name, args)
        
        except ToolAuthenticationError:
            logger.error(f"{tool_name} auth failed, refreshing credentials")
            await self.refresh_credentials(tool_name)
            return await self.execute_with_recovery(tool_name, args)
        
        except ToolUnavailableError:
            logger.error(f"{tool_name} unavailable, opening circuit breaker")
            self.open_circuit_breaker(tool_name)
            return await self.use_fallback(tool_name, args)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.record_failure(tool_name)
            return await self.graceful_degradation(tool_name, args, e)
    
    async def try_with_retry(self, tool_name, args, max_attempts=3):
        """Retry with exponential backoff"""
        for attempt in range(max_attempts):
            try:
                return await self.tool_executor.execute(tool_name, args)
            except (NetworkError, TransientError) as e:
                if attempt == max_attempts - 1:
                    raise
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retry {attempt + 1} after {wait_time}s")
                await asyncio.sleep(wait_time)
    
    async def use_fallback(self, tool_name, args):
        """Try fallback tools"""
        fallbacks = self.fallback_strategies.get(tool_name, [])
        
        for fallback_tool in fallbacks:
            try:
                logger.info(f"Trying fallback: {fallback_tool}")
                result = await self.tool_executor.execute(fallback_tool, args)
                return {"success": True, "result": result, "source": fallback_tool}
            except Exception as e:
                logger.warning(f"Fallback {fallback_tool} failed: {e}")
                continue
        
        # All fallbacks failed
        return {"success": False, "error": "All alternatives exhausted"}
    
    async def graceful_degradation(self, tool_name, args, error):
        """Provide degraded but functional response"""
        return {
            "success": False,
            "error": str(error),
            "message": f"{tool_name} is temporarily unavailable",
            "suggested_action": "Please try again later or use alternative method"
        }
```

---

### 93. How do you test complex multi-agent systems?

**Answer:**

> **See also:** [Multi-Agent Testing Guide](../examples/python-multi-agent/TESTING.md), [Multi-Agent Test Suite](../examples/python-multi-agent/test_multiagent.py), [Multi-Agent README](../examples/python-multi-agent/README.md), [Multi-Agent Documentation](../docs/05-multi-agent.md)

**Comprehensive Testing Strategy:**

**1. Unit Tests (Individual Agents):**
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_agent_tool_selection():
    """Test single agent's tool selection"""
    agent = Agent(tools=["calculator", "weather"])
    
    with patch.object(agent, 'llm') as mock_llm:
        mock_llm.decide_tool.return_value = "calculator"
        
        result = await agent.query("What's 2+2?")
        
        mock_llm.decide_tool.assert_called_once()
        assert result is not None
```

**2. Integration Tests (Agent Interactions):**
```python
@pytest.mark.integration
async def test_multi_agent_collaboration():
    """Test agents working together"""
    manager = ManagerAgent()
    worker1 = WorkerAgent("data_fetcher")
    worker2 = WorkerAgent("data_analyzer")
    
    # Manager delegates to workers
    result = await manager.delegate_task(
        "Analyze sales data for Q4",
        workers=[worker1, worker2]
    )
    
    assert result["status"] == "complete"
    assert worker1.task_count == 1
    assert worker2.task_count == 1
```

**3. Contract Tests (Agent Communication):**
```python
@pytest.mark.contract
async def test_agent_communication_contract():
    """Verify agents follow communication protocol"""
    sender = Agent("sender")
    receiver = Agent("receiver")
    
    # Define expected message format
    expected_schema = {
        "type": "task_request",
        "from": "sender",
        "to": "receiver",
        "task": str,
        "priority": int
    }
    
    message = sender.create_task_request("Process data", priority=5)
    
    # Verify message matches schema
    assert validate_schema(message, expected_schema)
    
    # Receiver should accept it
    assert receiver.can_handle(message)
```

**4. Load Tests:**
```python
import asyncio
from locust import HttpUser, task, between

class AgentLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def query_agent(self):
        """Simulate user queries"""
        self.client.post("/agent/query", json={
            "query": "What's the weather in NYC?",
            "user_id": "test_user"
        })
    
    @task(3)  # 3x more frequent
    def simple_query(self):
        """Simulate simple queries"""
        self.client.post("/agent/query", json={
            "query": "Hello",
            "user_id": "test_user"
        })
```

**5. Chaos Testing:**
```python
class ChaosTest:
    """Test system resilience"""
    
    async def test_agent_failure(self):
        """Kill random agent and verify system recovers"""
        system = MultiAgentSystem()
        
        # System running normally
        await system.start()
        assert system.health_check()
        
        # Kill random agent
        agent_to_kill = random.choice(system.agents)
        agent_to_kill.stop()
        
        # System should detect and recover
        await asyncio.sleep(5)
        assert system.health_check()
        assert len(system.active_agents()) == len(system.agents)
    
    async def test_network_partition(self):
        """Simulate network issues"""
        with NetworkChaos(latency=1000, packet_loss=0.3):
            result = await agent.query("test query")
            # Should handle network issues gracefully
            assert result is not None
```

**6. End-to-End Tests:**
```python
@pytest.mark.e2e
async def test_complete_workflow():
    """Test entire user workflow"""
    system = ProductionAgentSystem()
    
    # Realistic user interaction
    session = await system.create_session("user123")
    
    # Multi-turn conversation
    response1 = await session.send("What's the weather?")
    assert "temperature" in response1.lower()
    
    response2 = await session.send("Send that to my email")
    assert "sent" in response2.lower() or "email" in response2.lower()
    
    response3 = await session.send("Thanks!")
    assert session.is_complete()
    
    # Verify side effects
    assert len(email_service.sent_emails) == 1
```

**7. Property-Based Testing:**
```python
from hypothesis import given, strategies as st

@given(
    query=st.text(min_size=1, max_size=1000),
    tools=st.lists(st.text(), min_size=1, max_size=10)
)
def test_agent_always_returns_response(query, tools):
    """Agent should always return something, never crash"""
    agent = Agent(tools=tools)
    
    # Should not raise exception
    result = agent.query(query)
    
    # Should return dict with expected structure
    assert isinstance(result, dict)
    assert "response" in result or "error" in result
```

---

### 94. What are the considerations for real-time vs batch agent processing?

**Answer:**

> **See also:** [Streaming Example](../examples/python-streaming/), [Streaming README](../examples/python-streaming/README.md), [Fundamentals: Tool Execution Modes](../docs/02-fundamentals.md#tool-execution-modes), [Basics: Streaming](01-basics.md#17-what-is-streaming-in-the-context-of-tool-calling)

**Real-Time Processing:**
- ✅ Low latency requirements (< 1s)
- ✅ Individual request processing
- ✅ Immediate user feedback
- ✅ Interactive conversations
- ❌ Higher cost per request
- ❌ Limited throughput

**Batch Processing:**
- ✅ High throughput
- ✅ Process many requests together
- ✅ More cost-effective
- ✅ Better resource utilization
- ❌ Delayed results
- ❌ No user interaction

**Hybrid Approach:**

```python
class HybridProcessor:
    def __init__(self):
        self.real_time_agent = RealTimeAgent()
        self.batch_queue = BatchQueue()
        self.batch_size = 100
        self.batch_timeout = 60  # seconds
    
    def route_request(self, request):
        """Route based on priority and requirements"""
        if request.priority == "urgent" or request.interactive:
            # Real-time processing
            return self.real_time_agent.process(request)
        else:
            # Queue for batch processing
            self.batch_queue.add(request)
            
            # Trigger batch if queue is full or timeout reached
            if self.batch_queue.size() >= self.batch_size:
                self.process_batch()
            
            return {"status": "queued", "request_id": request.id}
    
    def process_batch(self):
        """Process accumulated requests together"""
        requests = self.batch_queue.drain(self.batch_size)
        
        # Process all at once for efficiency
        results = self.batch_agent.process_many(requests)
        
        # Store results for later retrieval
        for request, result in zip(requests, results):
            self.store_result(request.id, result)
```

**Use Cases:**
- **Real-Time:** Chatbots, customer service, interactive tools
- **Batch:** Report generation, data analysis, bulk processing

---

**95. How do you implement agent observability and debugging in production?**

**Answer:**

> **See also:** [Production Agent Example](../examples/python-production/), [Production README](../examples/python-production/README.md), [Production Questions](05-production.md#76-how-do-you-monitor-an-agent-system-in-production)

Comprehensive logging, tracing, and visualization:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

class ObservableAgent:
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.logger = StructuredLogger()
        self.metrics = MetricsCollector()
    
    async def query(self, user_input, user_id):
        """Process query with full observability"""
        
        with self.tracer.start_as_current_span("agent_query") as span:
            # Add trace attributes
            span.set_attribute("user_id", user_id)
            span.set_attribute("query_length", len(user_input))
            span.set_attribute("timestamp", datetime.now().isoformat())
            
            # Structured logging
            self.logger.info("query_received", {
                "user_id": user_id,
                "query": user_input,
                "trace_id": span.get_span_context().trace_id
            })
            
            # Metrics
            self.metrics.increment("queries.total")
            self.metrics.histogram("queries.length", len(user_input))
            
            start_time = time.time()
            
            try:
                # Process with sub-spans
                with self.tracer.start_as_current_span("llm_call"):
                    result = await self.process(user_input)
                
                # Record success metrics
                duration = time.time() - start_time
                self.metrics.histogram("queries.duration", duration)
                self.metrics.increment("queries.success")
                
                span.set_attribute("result_length", len(str(result)))
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return result
                
            except Exception as e:
                # Record failure
                self.metrics.increment("queries.failed")
                self.logger.error("query_failed", {
                    "user_id": user_id,
                    "error": str(e),
                    "trace_id": span.get_span_context().trace_id
                })
                
                span.set_status(
                    trace.Status(trace.StatusCode.ERROR, str(e))
                )
                span.record_exception(e)
                
                raise
```

**Observability Stack:**
- **Logging:** Structured logs (JSON) → Elasticsearch/Loki
- **Tracing:** Distributed traces → Jaeger/Tempo
- **Metrics:** Prometheus/Datadog
- **Dashboards:** Grafana
- **Alerting:** PagerDuty/Opsgenie

---

**96. What strategies exist for agent collaboration and coordination?**

**Answer:**

> **See also:** [Multi-Agent Example](../examples/python-multi-agent/), [Multi-Agent README](../examples/python-multi-agent/README.md), [Multi-Agent Documentation](../docs/05-multi-agent.md), [Architecture: Multi-Agent Systems](../docs/03-agent-architectures.md#multi-agent-systems), [Architecture Questions](02-architecture.md#35-what-are-multi-agent-systems)

**Collaboration Patterns:**

**1. Manager-Worker (Hierarchical)**
```python
class ManagerAgent:
    def __init__(self, workers):
        self.workers = workers
    
    async def delegate_task(self, task):
        """Manager breaks down and distributes work"""
        subtasks = self.decompose_task(task)
        
        # Assign to appropriate workers
        results = await asyncio.gather(*[
            self.assign_to_worker(subtask)
            for subtask in subtasks
        ])
        
        # Aggregate results
        return self.synthesize_results(results)
```

**2. Peer-to-Peer (Collaborative)**
```python
class PeerAgent:
    def __init__(self, peers):
        self.peers = peers
    
    async def collaborate(self, task):
        """Agents communicate directly"""
        # Broadcast task to peers
        responses = await self.broadcast_to_peers(task)
        
        # Negotiate best approach
        best_approach = self.negotiate(responses)
        
        return await self.execute(best_approach)
```

**3. Blackboard (Shared State)**
```python
class BlackboardSystem:
    def __init__(self):
        self.blackboard = SharedState()
        self.agents = []
    
    async def solve_problem(self, problem):
        """Agents read/write to shared blackboard"""
        self.blackboard.write("problem", problem)
        
        while not self.is_solved():
            for agent in self.agents:
                # Each agent contributes
                contribution = await agent.contribute(self.blackboard)
                self.blackboard.write(agent.id, contribution)
        
        return self.blackboard.read("solution")
```

**4. Auction-Based (Competitive)**
```python
class AuctionCoordinator:
    async def assign_task(self, task, agents):
        """Agents bid on tasks"""
        bids = await asyncio.gather(*[
            agent.bid(task) for agent in agents
        ])
        
        # Select best bid
        winner = max(bids, key=lambda b: b.score)
        
        return await winner.agent.execute(task)
```

**5. Consensus (Democratic)**
```python
class ConsensusSystem:
    async def make_decision(self, options, agents):
        """Agents vote on decisions"""
        votes = await asyncio.gather(*[
            agent.vote(options) for agent in agents
        ])
        
        # Majority wins
        decision = self.count_votes(votes)
        
        return decision
```

**When to Use Each:**
- **Manager-Worker:** Clear hierarchy, complex tasks
- **Peer-to-Peer:** Equal agents, collaborative work
- **Blackboard:** Complex problem-solving, multiple perspectives
- **Auction:** Resource optimization, competitive allocation
- **Consensus:** Democratic decisions, group agreement needed

---

**🎉 Congratulations!** 

You've completed all 96 questions covering:
- ✅ Basics (1-20)
- ✅ Architecture (21-40)
- ✅ Protocols (41-60)
- ✅ Security (61-75)
- ✅ Production (76-90)
- ✅ Advanced (91-96)

You're now well-prepared for AI agent and tool-calling interviews!

---

**Related Resources:**
- [Back to Main Questions](README.md)
- [Study Guide with Tips](README.md#tips-for-success)
- [Full Documentation](../docs/README.md)
- [Practical Examples](../examples/README.md)
- [Protocol Comparison](../protocols/comparison.md)
- [Multi-Agent Systems](../docs/05-multi-agent.md)
- [Production Patterns](../examples/python-production/)
- [Error Handling](../examples/python-error-handling/)
- [Streaming Responses](../examples/python-streaming/)

