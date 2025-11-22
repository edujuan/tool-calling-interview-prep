"""
Production-Ready AI Agent

Demonstrates production-grade patterns for deploying AI agents:
- Structured logging
- Metrics collection and monitoring
- Health checks and status endpoints
- Request tracing and debugging
- Performance monitoring
- Cost tracking
- Rate limiting
- Audit logs
- Configuration management
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
from collections import defaultdict, deque
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# STRUCTURED LOGGING
# =============================================================================

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """Production-grade structured logger"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler with formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler for audit trail
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def log(self, level: LogLevel, message: str, **kwargs):
        """Log with structured context"""
        context = json.dumps(kwargs) if kwargs else ""
        log_message = f"{message} {context}".strip()
        
        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_message)
    
    def debug(self, message: str, **kwargs):
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self.log(LogLevel.CRITICAL, message, **kwargs)


# =============================================================================
# METRICS COLLECTION
# =============================================================================

@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    request_id: str
    timestamp: datetime
    duration_ms: float
    token_count: int
    tool_calls: int
    cost_usd: float
    model: str
    success: bool
    error: Optional[str] = None


class MetricsCollector:
    """Collect and aggregate metrics for monitoring"""
    
    def __init__(self, window_size: int = 1000):
        self.metrics: deque = deque(maxlen=window_size)
        self.total_requests = 0
        self.total_errors = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.tool_usage_counts = defaultdict(int)
    
    def record_request(self, metrics: RequestMetrics):
        """Record metrics for a request"""
        self.metrics.append(metrics)
        self.total_requests += 1
        
        if not metrics.success:
            self.total_errors += 1
        
        self.total_tokens += metrics.token_count
        self.total_cost += metrics.cost_usd
    
    def record_tool_usage(self, tool_name: str):
        """Record tool usage"""
        self.tool_usage_counts[tool_name] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        if not self.metrics:
            return {
                "total_requests": 0,
                "error_rate": 0.0,
                "avg_duration_ms": 0.0,
                "avg_tokens": 0.0,
                "total_cost_usd": 0.0
            }
        
        recent_metrics = list(self.metrics)
        
        return {
            "total_requests": self.total_requests,
            "recent_requests": len(recent_metrics),
            "error_rate": (self.total_errors / self.total_requests * 100) if self.total_requests > 0 else 0,
            "avg_duration_ms": sum(m.duration_ms for m in recent_metrics) / len(recent_metrics),
            "avg_tokens": sum(m.token_count for m in recent_metrics) / len(recent_metrics),
            "total_cost_usd": self.total_cost,
            "tool_usage": dict(self.tool_usage_counts),
            "requests_per_model": self._count_by_model(recent_metrics)
        }
    
    def _count_by_model(self, metrics: List[RequestMetrics]) -> Dict[str, int]:
        """Count requests by model"""
        counts = defaultdict(int)
        for m in metrics:
            counts[m.model] += 1
        return dict(counts)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring"""
        stats = self.get_stats()
        
        # Determine health status
        error_rate = stats["error_rate"]
        
        if error_rate > 50:
            status = "critical"
        elif error_rate > 20:
            status = "degraded"
        elif error_rate > 5:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "error_rate": error_rate,
            "total_requests": stats["total_requests"],
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# REQUEST TRACING
# =============================================================================

@dataclass
class TraceSpan:
    """A span in a trace (represents an operation)"""
    span_id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def finish(self):
        """Mark span as complete"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


class RequestTracer:
    """Trace requests for debugging and monitoring"""
    
    def __init__(self):
        self.traces: Dict[str, List[TraceSpan]] = {}
    
    def start_trace(self, request_id: str) -> str:
        """Start a new trace"""
        self.traces[request_id] = []
        return request_id
    
    def start_span(self, request_id: str, name: str, **metadata) -> TraceSpan:
        """Start a new span in the trace"""
        span = TraceSpan(
            span_id=str(uuid.uuid4())[:8],
            name=name,
            start_time=datetime.now(),
            metadata=metadata
        )
        
        if request_id in self.traces:
            self.traces[request_id].append(span)
        
        return span
    
    def get_trace(self, request_id: str) -> List[TraceSpan]:
        """Get all spans for a request"""
        return self.traces.get(request_id, [])
    
    def format_trace(self, request_id: str) -> str:
        """Format trace for display"""
        spans = self.get_trace(request_id)
        
        if not spans:
            return f"No trace found for request {request_id}"
        
        output = [f"\n📊 Trace for Request {request_id}"]
        output.append("="*70)
        
        for span in spans:
            status = "✅" if not span.error else "❌"
            duration = f"{span.duration_ms:.2f}ms" if span.duration_ms else "in progress"
            
            output.append(f"\n{status} {span.name} ({duration})")
            
            if span.metadata:
                for key, value in span.metadata.items():
                    output.append(f"   {key}: {value}")
            
            if span.error:
                output.append(f"   ERROR: {span.error}")
        
        return "\n".join(output)


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.capacity = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.refill_rate = requests_per_minute / 60.0  # per second
    
    def _refill(self):
        """Refill tokens based on time passed"""
        now = time.time()
        time_passed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + time_passed * self.refill_rate
        )
        self.last_update = now
    
    def can_proceed(self) -> bool:
        """Check if request can proceed"""
        self._refill()
        return self.tokens >= 1
    
    def consume(self) -> bool:
        """Consume a token, return success"""
        self._refill()
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        
        return False
    
    def wait_time(self) -> float:
        """Get wait time until next token available"""
        self._refill()
        
        if self.tokens >= 1:
            return 0.0
        
        tokens_needed = 1 - self.tokens
        return tokens_needed / self.refill_rate


# =============================================================================
# COST TRACKING
# =============================================================================

class CostTracker:
    """Track API costs"""
    
    # Approximate costs per 1K tokens (as of 2024)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }
    
    def __init__(self):
        self.total_cost = 0.0
        self.costs_by_model = defaultdict(float)
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for a request"""
        pricing = self.PRICING.get(model, self.PRICING["gpt-3.5-turbo"])
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        total = input_cost + output_cost
        
        self.total_cost += total
        self.costs_by_model[model] += total
        
        return total
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "by_model": {
                model: round(cost, 4)
                for model, cost in self.costs_by_model.items()
            }
        }


# =============================================================================
# PRODUCTION AGENT
# =============================================================================

class ProductionAgent:
    """Production-ready AI agent with monitoring and observability"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        log_file: Optional[str] = "agent.log",
        rate_limit: int = 60
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # Observability components
        self.logger = StructuredLogger("ProductionAgent", log_file=log_file)
        self.metrics = MetricsCollector()
        self.tracer = RequestTracer()
        self.rate_limiter = RateLimiter(requests_per_minute=rate_limit)
        self.cost_tracker = CostTracker()
        
        self.logger.info("Agent initialized", model=model, rate_limit=rate_limit)
    
    def chat(self, user_message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a chat message with full production monitoring.
        
        Returns detailed response with metrics and trace info.
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self.logger.info(
            "Request received",
            request_id=request_id,
            user_id=user_id,
            message_length=len(user_message)
        )
        
        # Start trace
        self.tracer.start_trace(request_id)
        
        # Rate limiting
        rate_span = self.tracer.start_span(request_id, "rate_limiting")
        if not self.rate_limiter.consume():
            wait_time = self.rate_limiter.wait_time()
            rate_span.error = f"Rate limit exceeded, retry in {wait_time:.2f}s"
            rate_span.finish()
            
            self.logger.warning(
                "Rate limit exceeded",
                request_id=request_id,
                wait_time=wait_time
            )
            
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": wait_time,
                "request_id": request_id
            }
        rate_span.finish()
        
        try:
            # LLM call
            llm_span = self.tracer.start_span(
                request_id,
                "llm_call",
                model=self.model,
                message_length=len(user_message)
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": user_message}]
            )
            
            llm_span.metadata["tokens"] = response.usage.total_tokens
            llm_span.finish()
            
            # Calculate cost
            cost_span = self.tracer.start_span(request_id, "cost_calculation")
            cost = self.cost_tracker.calculate_cost(
                self.model,
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            cost_span.metadata["cost_usd"] = cost
            cost_span.finish()
            
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            
            self.metrics.record_request(RequestMetrics(
                request_id=request_id,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                token_count=response.usage.total_tokens,
                tool_calls=0,
                cost_usd=cost,
                model=self.model,
                success=True
            ))
            
            self.logger.info(
                "Request completed",
                request_id=request_id,
                duration_ms=duration_ms,
                tokens=response.usage.total_tokens,
                cost_usd=cost
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "request_id": request_id,
                "metadata": {
                    "duration_ms": duration_ms,
                    "tokens": response.usage.total_tokens,
                    "cost_usd": cost,
                    "model": self.model
                }
            }
            
        except Exception as e:
            # Record error
            duration_ms = (time.time() - start_time) * 1000
            
            self.metrics.record_request(RequestMetrics(
                request_id=request_id,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                token_count=0,
                tool_calls=0,
                cost_usd=0.0,
                model=self.model,
                success=False,
                error=str(e)
            ))
            
            self.logger.error(
                "Request failed",
                request_id=request_id,
                error=str(e),
                duration_ms=duration_ms
            )
            
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.get_stats()
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status"""
        return self.metrics.get_health_status()
    
    def get_trace(self, request_id: str) -> str:
        """Get trace for a request"""
        return self.tracer.format_trace(request_id)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return self.cost_tracker.get_summary()


# =============================================================================
# MONITORING DASHBOARD
# =============================================================================

def print_dashboard(agent: ProductionAgent):
    """Print monitoring dashboard"""
    metrics = agent.get_metrics()
    health = agent.get_health()
    costs = agent.get_cost_summary()
    
    print("\n" + "="*70)
    print("📊 PRODUCTION AGENT DASHBOARD")
    print("="*70)
    
    # Health Status
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "degraded": "🟡",
        "critical": "❌"
    }
    
    print(f"\n{status_emoji.get(health['status'], '❓')} Status: {health['status'].upper()}")
    
    # Request Metrics
    print(f"\n📈 Request Metrics:")
    print(f"  Total Requests: {metrics['total_requests']}")
    print(f"  Error Rate: {metrics['error_rate']:.2f}%")
    print(f"  Avg Duration: {metrics['avg_duration_ms']:.2f}ms")
    print(f"  Avg Tokens: {metrics['avg_tokens']:.0f}")
    
    # Cost Metrics
    print(f"\n💰 Cost Metrics:")
    print(f"  Total Cost: ${costs['total_cost_usd']}")
    if costs['by_model']:
        for model, cost in costs['by_model'].items():
            print(f"    {model}: ${cost}")
    
    # Tool Usage
    if metrics.get('tool_usage'):
        print(f"\n🔧 Tool Usage:")
        for tool, count in metrics['tool_usage'].items():
            print(f"    {tool}: {count}")
    
    print("\n" + "="*70 + "\n")


# =============================================================================
# DEMO
# =============================================================================

def main():
    """Run production agent demo"""
    
    print("\n" + "="*70)
    print("🏭 Production-Ready AI Agent Demo")
    print("="*70)
    print("\nThis example demonstrates:")
    print("- Structured logging")
    print("- Metrics collection")
    print("- Request tracing")
    print("- Rate limiting")
    print("- Cost tracking")
    print("- Health monitoring")
    print("="*70)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️  OPENAI_API_KEY not set.")
        print("Set your API key to run the production demo.\n")
        return
    
    # Initialize production agent
    agent = ProductionAgent(
        api_key=api_key,
        model="gpt-5-mini",
        log_file="production_agent.log",
        rate_limit=60  # 60 requests per minute
    )
    
    print("\n✅ Production agent initialized")
    print("\nRunning example requests...\n")
    
    # Example requests
    test_messages = [
        "What is machine learning?",
        "Explain neural networks in simple terms.",
        "What are the benefits of AI?",
    ]
    
    request_ids = []
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'─'*70}")
        print(f"Request {i}/{len(test_messages)}")
        print(f"{'─'*70}")
        print(f"Message: {message}")
        
        result = agent.chat(message, user_id=f"user_{i}")
        request_ids.append(result.get("request_id"))
        
        if result["success"]:
            print(f"\n✅ Response: {result['response'][:100]}...")
            print(f"\n📊 Metadata:")
            for key, value in result['metadata'].items():
                print(f"   {key}: {value}")
        else:
            print(f"\n❌ Error: {result['error']}")
        
        time.sleep(0.5)  # Small delay between requests
    
    # Show dashboard
    print_dashboard(agent)
    
    # Show trace for last request
    if request_ids and request_ids[-1]:
        print(agent.get_trace(request_ids[-1]))
    
    # Health check
    print("\n🏥 Health Check:")
    print(json.dumps(agent.get_health(), indent=2))
    
    # Interactive mode
    print("\n" + "="*70)
    print("💬 Interactive Mode")
    print("="*70)
    print("Chat with the production agent (type 'stats' for dashboard, 'exit' to quit)\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                print_dashboard(agent)
                break
            
            if user_input.lower() == 'stats':
                print_dashboard(agent)
                continue
            
            if not user_input:
                continue
            
            result = agent.chat(user_input)
            
            if result["success"]:
                print(f"\nAgent: {result['response']}\n")
                print(f"[Request ID: {result['request_id']}, "
                      f"Duration: {result['metadata']['duration_ms']:.0f}ms, "
                      f"Cost: ${result['metadata']['cost_usd']:.6f}]")
            else:
                print(f"\n❌ Error: {result['error']}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            print_dashboard(agent)
            break


if __name__ == "__main__":
    main()

