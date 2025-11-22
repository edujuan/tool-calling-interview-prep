# Utility Scripts

Helpful scripts for developing and testing AI agents.

## Available Scripts

### 1. Mock API Server (`mock_api_server.py`)

A lightweight Flask server that simulates various APIs for testing agents without external dependencies.

**Features:**
- Weather API
- Stock market API
- News search API
- Mock database queries
- Calculator endpoint
- Intentional delays and failures for testing

**Usage:**
```bash
pip install flask
python mock_api_server.py
```

Server runs on `http://localhost:8000`

**Example requests:**
```bash
# Weather
curl "http://localhost:8000/api/weather?location=paris"

# Stock price
curl "http://localhost:8000/api/stocks/AAPL"

# News search
curl "http://localhost:8000/api/news?q=AI&limit=3"

# Database query
curl "http://localhost:8000/api/db/users"
```

### 2. Tool Tracer (`tool_tracer.py`)

Debug and profile agent tool calls with detailed tracing.

**Features:**
- Trace all tool calls with timing
- Success/failure tracking
- Export to JSON/CSV
- Find slow or failing calls
- Statistics per tool

**Usage:**
```python
from tool_tracer import ToolTracer

tracer = ToolTracer()

# Wrap your tools
calculator = tracer.wrap(calculator_func, "calculator")
weather = tracer.wrap(weather_api, "weather")

# Use normally
result = calculator(expression="2 + 2")

# View trace
tracer.print_summary(detailed=True)
tracer.export_to_json("trace.json")

# Find issues
slow_calls = tracer.find_slow_calls(threshold_ms=1000)
errors = tracer.find_errors()
```

**Example output:**
```
🔍 TOOL CALL TRACE SUMMARY
======================================================================

📊 Overall Statistics:
  Total Calls:      5
  Successful:       4 (80.0%)
  Failed:           1
  Total Tool Time:  250.00ms
  Elapsed Time:     1.50s

🔧 Per-Tool Statistics:

  calculator:
    Calls:        3
    Success Rate: 3/3 (100.0%)
    Avg Duration: 50.00ms
    Min Duration: 45.00ms
    Max Duration: 55.00ms

  weather_api:
    Calls:        2
    Success Rate: 1/2 (50.0%)
    Avg Duration: 100.00ms
```

## Requirements

**Mock API Server:**
- Flask >= 2.0.0

**Tool Tracer:**
- No additional dependencies (uses stdlib)

Install all:
```bash
pip install flask
```

## Development

### Adding New Mock Endpoints

Edit `mock_api_server.py`:

```python
@app.route('/api/your-endpoint', methods=['GET'])
def your_endpoint():
    """Your endpoint description"""
    log_request()
    simulate_latency()
    
    # Your logic here
    return jsonify({"data": "value"})
```

### Extending Tool Tracer

Subclass `ToolTracer`:

```python
class CustomTracer(ToolTracer):
    def on_call_complete(self, call: ToolCall):
        """Called after each tool call"""
        if call.duration_ms > 1000:
            self.send_alert(f"Slow call: {call.tool_name}")
```

## Tips

**Mock Server:**
- Use for integration tests
- Avoid rate limits during development
- Test error handling without real failures
- Consistent, predictable responses

**Tool Tracer:**
- Find performance bottlenecks
- Debug unexpected tool behavior
- Track down failures
- Optimize agent execution

## See Also

- [Examples](../examples/) - Using these scripts in practice
- [Testing Guide](../docs/testing.md) - Testing strategies
- [Performance Guide](../docs/performance.md) - Optimization techniques
