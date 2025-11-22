# Build Your First MCP Server - Step-by-Step Tutorial

> **Learn MCP by building a complete weather server from scratch**

---

## What You'll Build

A fully functional MCP server that provides weather tools to AI agents.

**Features:**
- Current weather lookup
- 3-day forecast
- Weather alerts
- Proper error handling
- Both STDIO and HTTP transports

**Time**: ~30 minutes

---

## Prerequisites

```bash
# Install MCP SDK
pip install mcp

# Install additional dependencies
pip install requests aiohttp
```

---

## Step 1: Basic Server Structure

Create `weather_server.py`:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

class WeatherServer(Server):
    """MCP server for weather information"""
    
    def __init__(self):
        super().__init__("weather-server")
        print("Weather Server initialized")
    
    async def list_tools_impl(self) -> list[Tool]:
        """
        Return list of available tools.
        This is called when client sends tools/list request.
        """
        return []  # We'll add tools next
    
    async def call_tool_impl(
        self,
        name: str,
        arguments: dict
    ) -> list[TextContent]:
        """
        Execute a tool.
        This is called when client sends tools/call request.
        """
        raise ValueError(f"Unknown tool: {name}")

# Entry point
if __name__ == "__main__":
    print("Starting Weather MCP Server...")
    # We'll add the run logic next
```

**Test it compiles:**
```bash
python weather_server.py
```

---

## Step 2: Add Your First Tool

Add the current weather tool:

```python
async def list_tools_impl(self) -> list[Tool]:
    """Return available tools"""
    return [
        Tool(
            name="get_current_weather",
            description="Get current weather conditions for a location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or zip code (e.g., 'Paris', '10001')"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature units",
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        )
    ]
```

---

## Step 3: Implement Tool Logic

Add the weather fetching logic:

```python
import requests
from typing import Dict, Any

class WeatherServer(Server):
    
    def __init__(self):
        super().__init__("weather-server")
        # Use OpenWeather API (free tier)
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "demo")
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def _fetch_weather(
        self,
        location: str,
        units: str = "celsius"
    ) -> Dict[str, Any]:
        """Fetch weather from OpenWeather API"""
        
        # Convert units
        api_units = "metric" if units == "celsius" else "imperial"
        
        # Make API request
        url = f"{self.base_url}/weather"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": api_units
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant data
            return {
                "location": data["name"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "condition": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "units": units
            }
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch weather: {str(e)}")
    
    async def call_tool_impl(
        self,
        name: str,
        arguments: dict
    ) -> list[TextContent]:
        """Execute tool"""
        
        if name == "get_current_weather":
            location = arguments["location"]
            units = arguments.get("units", "celsius")
            
            # Fetch weather data
            weather = await asyncio.to_thread(
                self._fetch_weather,
                location,
                units
            )
            
            # Format response
            temp_unit = "°C" if units == "celsius" else "°F"
            response_text = f"""Weather in {weather['location']}:
Temperature: {weather['temperature']}{temp_unit} (feels like {weather['feels_like']}{temp_unit})
Condition: {weather['condition'].title()}
Humidity: {weather['humidity']}%
Wind Speed: {weather['wind_speed']} m/s"""
            
            return [TextContent(
                type="text",
                text=response_text
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
```

---

## Step 4: Add More Tools

Add forecast tool to `list_tools_impl`:

```python
async def list_tools_impl(self) -> list[Tool]:
    return [
        # ... existing get_current_weather tool ...
        
        Tool(
            name="get_forecast",
            description="Get 3-day weather forecast for a location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or zip code"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        )
    ]
```

Implement forecast in `call_tool_impl`:

```python
async def call_tool_impl(self, name: str, arguments: dict) -> list[TextContent]:
    
    if name == "get_current_weather":
        # ... existing implementation ...
    
    elif name == "get_forecast":
        location = arguments["location"]
        units = arguments.get("units", "celsius")
        
        forecast_data = await asyncio.to_thread(
            self._fetch_forecast,
            location,
            units
        )
        
        # Format forecast
        lines = [f"3-Day Forecast for {forecast_data['location']}:"]
        for day in forecast_data['days']:
            temp_unit = "°C" if units == "celsius" else "°F"
            lines.append(
                f"\n{day['date']}: {day['temp']}{temp_unit}, {day['condition']}"
            )
        
        return [TextContent(
            type="text",
            text="\n".join(lines)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def _fetch_forecast(self, location: str, units: str) -> Dict[str, Any]:
    """Fetch 3-day forecast"""
    api_units = "metric" if units == "celsius" else "imperial"
    
    url = f"{self.base_url}/forecast"
    params = {
        "q": location,
        "appid": self.api_key,
        "units": api_units,
        "cnt": 24  # 3 days (8 entries per day)
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    # Group by day
    days = []
    for i in range(0, 24, 8):
        day_data = data['list'][i]
        days.append({
            "date": day_data['dt_txt'].split()[0],
            "temp": day_data['main']['temp'],
            "condition": day_data['weather'][0]['description']
        })
    
    return {
        "location": data['city']['name'],
        "days": days
    }
```

---

## Step 5: Run the Server (STDIO)

Add the main entry point:

```python
from mcp.server.stdio import stdio_server

async def main():
    """Run server with STDIO transport"""
    server = WeatherServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    print("Starting Weather MCP Server (STDIO)...")
    asyncio.run(main())
```

**Run it:**
```bash
export OPENWEATHER_API_KEY=your_api_key_here
python weather_server.py
```

---

## Step 6: Create a Test Client

Create `test_weather_client.py`:

```python
from mcp.client import ClientSession, StdioServerParameters
from mcp import ClientSession
import asyncio

async def test_weather_server():
    """Test the weather server"""
    
    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["weather_server.py"],
        env=None
    )
    
    # Connect to server
    async with ClientSession(server_params) as session:
        
        # Initialize
        await session.initialize()
        
        # List tools
        tools_result = await session.list_tools()
        print("\n📋 Available Tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test: Get current weather
        print("\n🌤️  Testing: Get Current Weather")
        result = await session.call_tool(
            "get_current_weather",
            arguments={"location": "Paris", "units": "celsius"}
        )
        print(result.content[0].text)
        
        # Test: Get forecast
        print("\n📅 Testing: Get Forecast")
        result = await session.call_tool(
            "get_forecast",
            arguments={"location": "London", "units": "celsius"}
        )
        print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_weather_server())
```

**Run test:**
```bash
python test_weather_client.py
```

---

## Step 7: Add Error Handling

Improve error handling in your server:

```python
async def call_tool_impl(self, name: str, arguments: dict) -> list[TextContent]:
    """Execute tool with proper error handling"""
    
    try:
        # Validate arguments
        if name == "get_current_weather":
            if not arguments.get("location"):
                raise ValueError("Location is required")
            
            location = arguments["location"]
            units = arguments.get("units", "celsius")
            
            # Validate units
            if units not in ["celsius", "fahrenheit"]:
                raise ValueError(f"Invalid units: {units}")
            
            # Fetch weather
            weather = await asyncio.to_thread(
                self._fetch_weather,
                location,
                units
            )
            
            # ... format response ...
        
        elif name == "get_forecast":
            # Similar validation and execution
            pass
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except ValueError as e:
        # Validation errors
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    
    except requests.exceptions.HTTPError as e:
        # API errors
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"Error: Location '{location}' not found"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Error: Weather API returned {e.response.status_code}"
            )]
    
    except Exception as e:
        # Unexpected errors
        return [TextContent(
            type="text",
            text=f"Internal error: {str(e)}"
        )]
```

---

## Step 8: Add HTTP Transport (Optional)

For remote access, add HTTP support:

```python
# Create http_server.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()
weather_server = WeatherServer()

@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """Handle MCP JSON-RPC requests over HTTP"""
    
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")
    
    try:
        if method == "tools/list":
            tools = await weather_server.list_tools_impl()
            result = {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.inputSchema
                    }
                    for t in tools
                ]
            }
        
        elif method == "tools/call":
            name = params["name"]
            arguments = params["arguments"]
            content = await weather_server.call_tool_impl(name, arguments)
            result = {
                "content": [
                    {"type": c.type, "text": c.text}
                    for c in content
                ]
            }
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })
    
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Run HTTP server:**
```bash
python http_server.py
```

**Test with curl:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

---

## Complete Code

Your final `weather_server.py` should look like this:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import asyncio
import requests
import os
from typing import Dict, Any

class WeatherServer(Server):
    """Complete MCP weather server"""
    
    def __init__(self):
        super().__init__("weather-server")
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "demo")
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def list_tools_impl(self) -> list[Tool]:
        return [
            Tool(
                name="get_current_weather",
                description="Get current weather conditions for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            ),
            Tool(
                name="get_forecast",
                description="Get 3-day forecast",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            )
        ]
    
    async def call_tool_impl(self, name: str, arguments: dict) -> list[TextContent]:
        # Implementation from steps above
        pass
    
    # Helper methods from steps above
    async def _fetch_weather(self, location: str, units: str) -> Dict[str, Any]:
        pass
    
    async def _fetch_forecast(self, location: str, units: str) -> Dict[str, Any]:
        pass

async def main():
    server = WeatherServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Testing Your Server

### Manual Testing

```bash
# Terminal 1: Start server
python weather_server.py

# Terminal 2: Run test client
python test_weather_client.py
```

### Automated Testing

```python
# test_weather_server.py
import pytest
from weather_server import WeatherServer

@pytest.mark.asyncio
async def test_list_tools():
    server = WeatherServer()
    tools = await server.list_tools_impl()
    assert len(tools) == 2
    assert tools[0].name == "get_current_weather"

@pytest.mark.asyncio
async def test_get_weather():
    server = WeatherServer()
    result = await server.call_tool_impl(
        "get_current_weather",
        {"location": "Paris", "units": "celsius"}
    )
    assert len(result) == 1
    assert "Paris" in result[0].text
```

---

## Next Steps

### Enhancements

1. **Add more tools:**
   - Weather alerts
   - Historical data
   - Air quality

2. **Improve error handling:**
   - Retry logic
   - Better error messages
   - Logging

3. **Add caching:**
   - Cache API responses
   - Reduce API calls

4. **Deploy to production:**
   - Use HTTP transport
   - Add authentication
   - Monitor usage

### Resources

- [MCP Specification](./specification.md)
- [Official MCP Docs](https://modelcontextprotocol.io/)
- [MCP Examples](../../examples/python-mcp-files/)
- [OpenWeather API](https://openweathermap.org/api)

---

## Common Issues

**"Module 'mcp' not found"**
```bash
pip install mcp
```

**"API key not working"**
- Get a free key from OpenWeather
- Set environment variable: `export OPENWEATHER_API_KEY=your_key`

**"Connection refused"**
- Make sure server is running
- Check if port is available (for HTTP)

**"Tool not found"**
- Verify tool name matches exactly
- Check `list_tools_impl` returns your tool

---

**Congratulations!** You've built a complete MCP server. 🎉

Try building your own server for different APIs or services!


