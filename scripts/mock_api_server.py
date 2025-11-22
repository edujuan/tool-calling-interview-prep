"""
Mock API Server for Testing Agents

A lightweight mock server that simulates various APIs for testing
agents without making real external calls.

Usage:
    python mock_api_server.py

Then point your agent tools to http://localhost:8000
"""

from flask import Flask, request, jsonify
import random
import time
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# Mock Data
# ==============================================================================

WEATHER_DATA = {
    "paris": {"temp": 18, "condition": "cloudy", "humidity": 65},
    "london": {"temp": 15, "condition": "rainy", "humidity": 80},
    "new york": {"temp": 22, "condition": "sunny", "humidity": 50},
    "tokyo": {"temp": 25, "condition": "partly cloudy", "humidity": 60},
    "sydney": {"temp": 28, "condition": "sunny", "humidity": 55},
}

STOCK_PRICES = {
    "AAPL": 182.50,
    "GOOGL": 142.30,
    "MSFT": 378.90,
    "TSLA": 242.50,
    "AMZN": 155.80,
}

NEWS_ARTICLES = [
    {
        "title": "AI Advances in 2024",
        "source": "Tech News",
        "url": "https://example.com/ai-advances",
        "published": "2024-01-15",
        "summary": "Major breakthroughs in AI technology this year."
    },
    {
        "title": "Climate Change Update",
        "source": "Science Daily",
        "url": "https://example.com/climate",
        "published": "2024-01-14",
        "summary": "Latest research on climate change impacts."
    },
    {
        "title": "Stock Market Rally",
        "source": "Financial Times",
        "url": "https://example.com/stocks",
        "published": "2024-01-13",
        "summary": "Markets reach new highs amid economic optimism."
    }
]

# ==============================================================================
# Helper Functions
# ==============================================================================

def log_request():
    """Log incoming request"""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")

def simulate_latency(min_ms=100, max_ms=500):
    """Simulate API latency"""
    delay = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay)

def random_failure(probability=0.1):
    """Randomly fail with given probability"""
    if random.random() < probability:
        return True
    return False

# ==============================================================================
# Weather API Endpoints
# ==============================================================================

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Get weather for a location"""
    log_request()
    simulate_latency()
    
    # Random failures for testing
    if random_failure(0.05):
        return jsonify({"error": "Weather service temporarily unavailable"}), 503
    
    location = request.args.get('location', '').lower()
    units = request.args.get('units', 'celsius')
    
    if not location:
        return jsonify({"error": "Missing 'location' parameter"}), 400
    
    if location in WEATHER_DATA:
        data = WEATHER_DATA[location].copy()
        data['location'] = location.title()
        data['units'] = units
        data['timestamp'] = datetime.now().isoformat()
        return jsonify(data)
    else:
        return jsonify({
            "error": f"Weather data not available for {location}",
            "available_locations": list(WEATHER_DATA.keys())
        }), 404

@app.route('/api/weather/forecast', methods=['GET'])
def get_forecast():
    """Get 3-day forecast"""
    log_request()
    simulate_latency()
    
    location = request.args.get('location', '').lower()
    
    if location not in WEATHER_DATA:
        return jsonify({"error": "Location not found"}), 404
    
    base_weather = WEATHER_DATA[location]
    forecast = []
    
    for i in range(3):
        day_weather = base_weather.copy()
        day_weather['temp'] += random.randint(-3, 3)
        day_weather['day'] = i + 1
        forecast.append(day_weather)
    
    return jsonify({
        "location": location.title(),
        "forecast": forecast
    })

# ==============================================================================
# Stock Market API Endpoints
# ==============================================================================

@app.route('/api/stocks/<symbol>', methods=['GET'])
def get_stock(symbol):
    """Get stock price"""
    log_request()
    simulate_latency()
    
    symbol = symbol.upper()
    
    if symbol in STOCK_PRICES:
        base_price = STOCK_PRICES[symbol]
        # Add some random variation
        current_price = base_price + random.uniform(-5, 5)
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        return jsonify({
            "symbol": symbol,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "error": f"Symbol {symbol} not found",
            "available_symbols": list(STOCK_PRICES.keys())
        }), 404

# ==============================================================================
# News API Endpoints
# ==============================================================================

@app.route('/api/news', methods=['GET'])
def get_news():
    """Search news articles"""
    log_request()
    simulate_latency()
    
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 3))
    
    # Simple filtering by query
    if query:
        filtered = [
            article for article in NEWS_ARTICLES
            if query.lower() in article['title'].lower() or 
               query.lower() in article['summary'].lower()
        ]
    else:
        filtered = NEWS_ARTICLES
    
    return jsonify({
        "query": query,
        "total_results": len(filtered),
        "articles": filtered[:limit]
    })

# ==============================================================================
# Database API Endpoints
# ==============================================================================

MOCK_DATABASE = {
    "users": [
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "role": "admin"},
        {"id": 2, "name": "Bob Jones", "email": "bob@example.com", "role": "user"},
        {"id": 3, "name": "Carol White", "email": "carol@example.com", "role": "user"},
    ],
    "products": [
        {"id": 101, "name": "Widget", "price": 29.99, "stock": 100},
        {"id": 102, "name": "Gadget", "price": 49.99, "stock": 50},
        {"id": 103, "name": "Doohickey", "price": 19.99, "stock": 200},
    ]
}

@app.route('/api/db/<table>', methods=['GET'])
def query_database(table):
    """Query mock database"""
    log_request()
    simulate_latency()
    
    if table not in MOCK_DATABASE:
        return jsonify({"error": f"Table '{table}' not found"}), 404
    
    # Support simple filtering
    filter_key = request.args.get('filter_key')
    filter_value = request.args.get('filter_value')
    
    data = MOCK_DATABASE[table]
    
    if filter_key and filter_value:
        data = [
            row for row in data
            if str(row.get(filter_key, '')).lower() == filter_value.lower()
        ]
    
    return jsonify({
        "table": table,
        "count": len(data),
        "rows": data
    })

# ==============================================================================
# Calculator API
# ==============================================================================

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Perform calculation"""
    log_request()
    simulate_latency(50, 200)
    
    data = request.get_json()
    expression = data.get('expression', '')
    
    if not expression:
        return jsonify({"error": "Missing 'expression' field"}), 400
    
    try:
        # Safe evaluation (limited operators)
        import ast
        import operator
        
        OPERATORS = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
        }
        
        def safe_eval(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                return OPERATORS[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = safe_eval(node.operand)
                if isinstance(node.op, ast.USub):
                    return -operand
                elif isinstance(node.op, ast.UAdd):
                    return operand
            else:
                raise ValueError("Unsupported operation")
        
        node = ast.parse(expression, mode='eval')
        result = safe_eval(node.body)
        
        return jsonify({
            "expression": expression,
            "result": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Invalid expression: {str(e)}"
        }), 400

# ==============================================================================
# Utility Endpoints
# ==============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/echo', methods=['POST'])
def echo():
    """Echo back the request body (for testing)"""
    log_request()
    data = request.get_json()
    return jsonify({
        "received": data,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/slow', methods=['GET'])
def slow_endpoint():
    """Intentionally slow endpoint for timeout testing"""
    log_request()
    delay = int(request.args.get('delay', 5))
    time.sleep(min(delay, 30))  # Max 30 seconds
    return jsonify({"message": f"Responded after {delay} seconds"})

@app.route('/api/error', methods=['GET'])
def error_endpoint():
    """Intentionally returns an error for error handling testing"""
    log_request()
    code = int(request.args.get('code', 500))
    return jsonify({"error": "Simulated error"}), code

# ==============================================================================
# Documentation Endpoint
# ==============================================================================

@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
def api_documentation():
    """API documentation"""
    return jsonify({
        "name": "Mock API Server for AI Agent Testing",
        "version": "1.0.0",
        "endpoints": {
            "/api/weather": "GET - Get weather for location (?location=paris&units=celsius)",
            "/api/weather/forecast": "GET - Get 3-day forecast (?location=paris)",
            "/api/stocks/<symbol>": "GET - Get stock price",
            "/api/news": "GET - Search news (?q=query&limit=3)",
            "/api/db/<table>": "GET - Query database table (?filter_key=&filter_value=)",
            "/api/calculate": "POST - Calculate expression {\"expression\": \"2+2\"}",
            "/api/health": "GET - Health check",
            "/api/echo": "POST - Echo request body",
            "/api/slow": "GET - Slow response (?delay=5)",
            "/api/error": "GET - Return error (?code=500)",
        },
        "features": [
            "Simulated latency",
            "Random failures (5% chance)",
            "Mock data for testing",
            "No external dependencies",
            "Request logging"
        ]
    })

# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Mock API Server Starting")
    print("=" * 70)
    print("\nAvailable endpoints:")
    print("  - Weather: http://localhost:8000/api/weather?location=paris")
    print("  - Stocks:  http://localhost:8000/api/stocks/AAPL")
    print("  - News:    http://localhost:8000/api/news?q=AI")
    print("  - Database: http://localhost:8000/api/db/users")
    print("  - Docs:    http://localhost:8000/api")
    print("\n" + "=" * 70)
    print()
    
    app.run(host='0.0.0.0', port=8000, debug=True)


