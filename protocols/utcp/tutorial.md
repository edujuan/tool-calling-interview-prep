# Build Your First UTCP Integration - Step-by-Step Tutorial

> **Learn UTCP by creating a complete weather tool integration from scratch**

---

## What You'll Build

A fully functional UTCP manual that enables AI agents to access weather data directly from OpenWeather API.

**Features:**
- Current weather lookup
- 3-day forecast
- Location search
- Direct HTTP calls (no server needed)
- Complete authentication setup
- Error handling

**Time**: ~20 minutes

---

## Prerequisites

```bash
# Install UTCP client and HTTP plugin
pip install utcp utcp-http

# Get a free API key
# Sign up at: https://openweathermap.org/api
# Free tier includes 60 calls/minute
```

**Note:** This tutorial uses the official UTCP v1.0.1 Python library from the [universal-tool-calling-protocol](https://github.com/universal-tool-calling-protocol) organization.

---

## Step 1: Create Your First Manual

Create `weather_manual.json`:

```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "info": {
    "title": "Weather API",
    "version": "1.0.0",
    "description": "Get current weather and forecasts for any location"
  },
  "tools": []
}
```

**What this does:**
- `utcp_version`: Specifies UTCP protocol version
- `manual_version`: Your manual's version (semantic versioning)
- `info`: Metadata about your API
- `tools`: Array of tools (we'll add these next)

---

## Step 2: Add Your First Tool

Add the current weather tool:

```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "info": {
    "title": "Weather API",
    "version": "1.0.0",
    "description": "Get current weather and forecasts for any location"
  },
  "tools": [
    {
      "name": "get_current_weather",
      "description": "Get current weather conditions for a location. Returns temperature, humidity, wind speed, and weather conditions. Data is updated every 10 minutes.",
      "tags": ["weather", "current", "realtime"],
      "inputs": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name, state code (US only), and country code divided by comma. Use ISO 3166 country codes. Examples: 'Paris', 'London,UK', 'New York,NY,US'"
          },
          "units": {
            "type": "string",
            "description": "Units of measurement",
            "enum": ["metric", "imperial", "standard"],
            "default": "metric"
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "http_method": "GET",
        "query_params": {
          "q": "${location}",
          "units": "${units}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    }
  ]
}
```

**Key Points:**
- `name`: Unique identifier for the tool
- `description`: Clear explanation for the AI agent
- `tags`: Help with tool discovery
- `inputs`: JSON Schema defining parameters
- `tool_call_template`: How to make the API call

---

## Step 3: Add Authentication

Add global authentication configuration:

```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "info": {
    "title": "Weather API",
    "version": "1.0.0",
    "description": "Get current weather and forecasts for any location"
  },
  "auth": {
    "auth_type": "api_key",
    "api_key": "${WEATHER_API_KEY}",
    "var_name": "appid",
    "location": "query"
  },
  "tools": [
    {
      "name": "get_current_weather",
      "description": "Get current weather conditions for a location. Returns temperature, humidity, wind speed, and weather conditions. Data is updated every 10 minutes.",
      "tags": ["weather", "current", "realtime"],
      "inputs": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name or coordinates (lat,lon)"
          },
          "units": {
            "type": "string",
            "enum": ["metric", "imperial", "standard"],
            "default": "metric"
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "http_method": "GET",
        "query_params": {
          "q": "${location}",
          "units": "${units}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    }
  ]
}
```

**Authentication explained:**
- `auth_type`: Type of authentication (api_key, basic, oauth2)
- `api_key`: Variable reference (from environment)
- `var_name`: Parameter name expected by API
- `location`: Where to send the key (query, header, cookie)

---

## Step 4: Test Your Manual

Create `test_weather.py`:

```python
import asyncio
import json
import os
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.data.call_template import CallTemplate

async def test_weather():
    # Set up API key
    os.environ["WEATHER_API_KEY"] = "your_api_key_here"
    
    # Create UTCP client with config
    config = UtcpClientConfig(
        manual_call_templates=[
            CallTemplate(
                name="weather_manual",
                call_template_type="text",
                file_path="./weather_manual.json"
            )
        ],
        variables={"WEATHER_API_KEY": os.environ["WEATHER_API_KEY"]}
    )
    
    client = await UtcpClient.create(config=config)
    
    print("📋 Registered Manual")
    print(f"   Client initialized with weather tools")
    print()
    
    # List available tools
    tools = await client.get_tools()
    print("🔧 Available Tools:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description}")
    print()
    
    # Get tool details
    tool = await client.get_tool("get_current_weather")
    print("📖 Tool Details:")
    print(f"   Name: {tool.name}")
    print(f"   Inputs: {list(tool.inputs['properties'].keys())}")
    print()
    
    # Call the tool
    print("🌤️  Calling: get_current_weather")
    result = await client.call_tool(
        "get_current_weather",
        {"location": "Paris", "units": "metric"}
    )
    
    print("✅ Result:")
    result_data = json.loads(result) if isinstance(result, str) else result
    print(f"   Temperature: {result_data['main']['temp']}°C")
    print(f"   Feels like: {result_data['main']['feels_like']}°C")
    print(f"   Condition: {result_data['weather'][0]['description']}")
    print(f"   Humidity: {result_data['main']['humidity']}%")
    print(f"   Wind: {result_data['wind']['speed']} m/s")

if __name__ == "__main__":
    asyncio.run(test_weather())
```

**Run it:**
```bash
python test_weather.py
```

**Expected Output:**
```
📋 Registered Manual
   Manual: weather_manual
   Tools: 1

🔧 Available Tools:
   - get_current_weather: Get current weather conditions...

📖 Tool Details:
   Name: get_current_weather
   Inputs: dict_keys(['location', 'units'])

🌤️  Calling: get_current_weather
✅ Result:
   Temperature: 18.5°C
   Feels like: 17.2°C
   Condition: scattered clouds
   Humidity: 65%
   Wind: 3.5 m/s
```

---

## Step 5: Add More Tools

Add a forecast tool:

```json
{
  "name": "get_forecast",
  "description": "Get 3-day weather forecast for a location. Returns temperature, conditions, and precipitation probability for each day.",
  "tags": ["weather", "forecast", "prediction"],
  "inputs": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or coordinates"
      },
      "units": {
        "type": "string",
        "enum": ["metric", "imperial", "standard"],
        "default": "metric"
      },
      "days": {
        "type": "integer",
        "description": "Number of days (1-5)",
        "minimum": 1,
        "maximum": 5,
        "default": 3
      }
    },
    "required": ["location"]
  },
  "tool_call_template": {
    "call_template_type": "http",
    "url": "https://api.openweathermap.org/data/2.5/forecast",
    "http_method": "GET",
    "query_params": {
      "q": "${location}",
      "units": "${units}",
      "cnt": "${days}",
      "appid": "${WEATHER_API_KEY}"
    }
  }
}
```

Add location search tool:

```json
{
  "name": "search_location",
  "description": "Search for locations by name. Returns a list of matching places with coordinates and country information.",
  "tags": ["location", "search", "geocoding"],
  "inputs": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Location name to search for"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of results",
        "minimum": 1,
        "maximum": 10,
        "default": 5
      }
    },
    "required": ["query"]
  },
  "tool_call_template": {
    "call_template_type": "http",
    "url": "https://api.openweathermap.org/geo/1.0/direct",
    "http_method": "GET",
    "query_params": {
      "q": "${query}",
      "limit": "${limit}",
      "appid": "${WEATHER_API_KEY}"
    }
  }
}
```

---

## Step 6: Add Output Schemas

Enhance tools with output schemas for better documentation:

```json
{
  "name": "get_current_weather",
  "description": "Get current weather conditions for a location",
  "inputs": {
    "type": "object",
    "properties": {
      "location": {"type": "string"},
      "units": {
        "type": "string",
        "enum": ["metric", "imperial", "standard"],
        "default": "metric"
      }
    },
    "required": ["location"]
  },
  "outputs": {
    "type": "object",
    "properties": {
      "main": {
        "type": "object",
        "properties": {
          "temp": {"type": "number", "description": "Temperature"},
          "feels_like": {"type": "number", "description": "Feels like temperature"},
          "humidity": {"type": "integer", "description": "Humidity percentage"}
        }
      },
      "weather": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "description": {"type": "string", "description": "Weather condition"}
          }
        }
      },
      "wind": {
        "type": "object",
        "properties": {
          "speed": {"type": "number", "description": "Wind speed"}
        }
      }
    }
  },
  "tool_call_template": {
    "call_template_type": "http",
    "url": "https://api.openweathermap.org/data/2.5/weather",
    "http_method": "GET",
    "query_params": {
      "q": "${location}",
      "units": "${units}",
      "appid": "${WEATHER_API_KEY}"
    }
  }
}
```

---

## Step 7: Test All Tools

Update `test_weather.py`:

```python
from utcp import UTCPClient
import asyncio
import os
import json

async def test_all_tools():
    # Setup
    os.environ["WEATHER_API_KEY"] = "your_api_key_here"
    client = UTCPClient()
    
    # Load manual
    await client.register_manual_from_file("./weather_manual.json")
    
    print("=" * 60)
    print("UTCP Weather Tools Test")
    print("=" * 60)
    print()
    
    # Test 1: Search location
    print("🔍 Test 1: Search Location")
    result = await client.call_tool(
        "search_location",
        {"query": "Paris", "limit": 3}
    )
    for loc in result:
        print(f"   - {loc['name']}, {loc['country']}")
        print(f"     Coordinates: {loc['lat']}, {loc['lon']}")
    print()
    
    # Test 2: Current weather
    print("🌤️  Test 2: Current Weather (Paris)")
    result = await client.call_tool(
        "get_current_weather",
        {"location": "Paris,FR", "units": "metric"}
    )
    print(f"   Temperature: {result['main']['temp']}°C")
    print(f"   Condition: {result['weather'][0]['description']}")
    print(f"   Humidity: {result['main']['humidity']}%")
    print()
    
    # Test 3: Forecast
    print("📅 Test 3: 3-Day Forecast (London)")
    result = await client.call_tool(
        "get_forecast",
        {"location": "London,UK", "units": "metric", "days": 3}
    )
    for idx, forecast in enumerate(result['list'][:3]):
        print(f"   Day {idx+1}:")
        print(f"      Temp: {forecast['main']['temp']}°C")
        print(f"      Condition: {forecast['weather'][0]['description']}")
    print()
    
    # Test 4: Different units
    print("🌡️  Test 4: Imperial Units (New York)")
    result = await client.call_tool(
        "get_current_weather",
        {"location": "New York,US", "units": "imperial"}
    )
    print(f"   Temperature: {result['main']['temp']}°F")
    print(f"   Condition: {result['weather'][0]['description']}")
    print()
    
    print("=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_all_tools())
```

---

## Step 8: Add Error Handling

Create a robust wrapper:

```python
import asyncio
import json
import os
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.data.call_template import CallTemplate

class WeatherClient:
    """Robust weather client with error handling"""
    
    def __init__(self, api_key: str):
        self.client = None
        self.api_key = api_key
    
    async def setup(self):
        """Initialize client and load manuals"""
        os.environ["WEATHER_API_KEY"] = self.api_key
        
        try:
            config = UtcpClientConfig(
                manual_call_templates=[
                    CallTemplate(
                        name="weather_manual",
                        call_template_type="text",
                        file_path="./weather_manual.json"
                    )
                ],
                variables={"WEATHER_API_KEY": self.api_key}
            )
            
            self.client = await UtcpClient.create(config=config)
            tools = await self.client.get_tools()
            print(f"✅ Loaded {len(tools)} weather tools")
        except FileNotFoundError:
            print("❌ Error: weather_manual.json not found")
            raise
        except Exception as e:
            print(f"❌ Error loading manual: {e}")
            raise
    
    async def get_weather(self, location: str, units: str = "metric"):
        """Get current weather with error handling"""
        try:
            result = await self.client.call_tool(
                "get_current_weather",
                {"location": location, "units": units}
            )
            
            # Parse result if it's a JSON string
            data = json.loads(result) if isinstance(result, str) else result
            
            return {
                "success": True,
                "data": {
                    "temperature": data['main']['temp'],
                    "feels_like": data['main']['feels_like'],
                    "condition": data['weather'][0]['description'],
                    "humidity": data['main']['humidity'],
                    "wind_speed": data['wind']['speed']
                }
            }
        except KeyError as e:
            return {"success": False, "error": f"Unexpected response format: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Error: {e}"}
    
    async def search_location(self, query: str, limit: int = 5):
        """Search location with error handling"""
        try:
            result = await self.client.call_tool(
                "search_location",
                {"query": query, "limit": limit}
            )
            
            data = json.loads(result) if isinstance(result, str) else result
            
            if not data:
                return {"success": False, "error": "No locations found"}
            
            return {
                "success": True,
                "data": [
                    {
                        "name": loc['name'],
                        "country": loc['country'],
                        "lat": loc['lat'],
                        "lon": loc['lon']
                    }
                    for loc in data
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Usage
async def main():
    client = WeatherClient(api_key="your_key_here")
    await client.setup()
    
    # Get weather
    result = await client.get_weather("Paris", "metric")
    if result["success"]:
        print(f"Temperature: {result['data']['temperature']}°C")
    else:
        print(f"Error: {result['error']}")

asyncio.run(main())
```

---

## Step 9: Integrate with an AI Agent

Simple agent integration:

```python
import asyncio
import json
import os
import anthropic
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.data.call_template import CallTemplate

async def weather_agent(query: str):
    """AI agent that uses weather tools"""
    
    # Setup UTCP
    os.environ["WEATHER_API_KEY"] = "your_key_here"
    
    config = UtcpClientConfig(
        manual_call_templates=[
            CallTemplate(
                name="weather_manual",
                call_template_type="text",
                file_path="./weather_manual.json"
            )
        ],
        variables={"WEATHER_API_KEY": os.environ["WEATHER_API_KEY"]}
    )
    
    utcp = await UtcpClient.create(config=config)
    
    # Get tools for Claude
    tools = await utcp.get_tools()
    claude_tools = []
    
    for tool in tools:
        claude_tools.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputs
        })
    
    # Setup Claude
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Initial request
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=claude_tools,
        messages=[{"role": "user", "content": query}]
    )
    
    # Handle tool use
    if response.stop_reason == "tool_use":
        tool_use = next(
            block for block in response.content 
            if block.type == "tool_use"
        )
        
        # Execute tool via UTCP
        tool_result = await utcp.call_tool(
            tool_use.name,
            tool_use.input
        )
        
        # Parse result if string
        result_content = tool_result if isinstance(tool_result, str) else json.dumps(tool_result)
        
        # Continue conversation
        final_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=claude_tools,
            messages=[
                {"role": "user", "content": query},
                {"role": "assistant", "content": response.content},
                {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result_content
                    }]
                }
            ]
        )
        
        return final_response.content[0].text
    
    return response.content[0].text

# Usage
async def main():
    result = await weather_agent("What's the weather like in Paris?")
    print(result)

asyncio.run(main())
```

---

## Complete Manual

Your final `weather_manual.json`:

```json
{
  "utcp_version": "1.0.1",
  "manual_version": "1.0.0",
  "info": {
    "title": "Weather API",
    "version": "1.0.0",
    "description": "Get current weather and forecasts for any location"
  },
  "auth": {
    "auth_type": "api_key",
    "api_key": "${WEATHER_API_KEY}",
    "var_name": "appid",
    "location": "query"
  },
  "tools": [
    {
      "name": "get_current_weather",
      "description": "Get current weather conditions for a location. Returns temperature, humidity, wind speed, and weather conditions.",
      "tags": ["weather", "current", "realtime"],
      "inputs": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name or coordinates"
          },
          "units": {
            "type": "string",
            "enum": ["metric", "imperial", "standard"],
            "default": "metric"
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "http_method": "GET",
        "query_params": {
          "q": "${location}",
          "units": "${units}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    },
    {
      "name": "get_forecast",
      "description": "Get weather forecast for a location",
      "tags": ["weather", "forecast"],
      "inputs": {
        "type": "object",
        "properties": {
          "location": {"type": "string"},
          "units": {
            "type": "string",
            "enum": ["metric", "imperial", "standard"],
            "default": "metric"
          },
          "days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
            "default": 3
          }
        },
        "required": ["location"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/data/2.5/forecast",
        "http_method": "GET",
        "query_params": {
          "q": "${location}",
          "units": "${units}",
          "cnt": "${days}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    },
    {
      "name": "search_location",
      "description": "Search for locations by name",
      "tags": ["location", "search"],
      "inputs": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "default": 5
          }
        },
        "required": ["query"]
      },
      "tool_call_template": {
        "call_template_type": "http",
        "url": "https://api.openweathermap.org/geo/1.0/direct",
        "http_method": "GET",
        "query_params": {
          "q": "${query}",
          "limit": "${limit}",
          "appid": "${WEATHER_API_KEY}"
        }
      }
    }
  ]
}
```

---

## Next Steps

### Enhancements

1. **Add more tools:**
   - Air quality data
   - Weather alerts
   - Historical weather
   - UV index

2. **Advanced features:**
   - Response caching
   - Rate limiting
   - Retry logic
   - Timeout configuration

3. **Other protocols:**
   - CLI tools (local weather scripts)
   - WebSocket (real-time updates)
   - SSE (weather alerts stream)

### Resources

- [UTCP Specification](./specification.md)
- [UTCP README](./README.md)
- [OpenWeather API Docs](https://openweathermap.org/api)
- [UTCP Examples](../../examples/python-utcp-weather/)

---

## Common Issues

**"Manual validation error"**
- Check JSON syntax (use a JSON validator)
- Ensure required fields are present
- Verify `utcp_version` is valid

**"Tool call failed"**
- Check API key is set correctly: `echo $WEATHER_API_KEY`
- Verify location format (e.g., "Paris,FR" not just "Paris")
- Check internet connectivity

**"Missing protocol plugin"**
```bash
pip install utcp-http
```

**"Variable not found"**
- Set environment variable: `export WEATHER_API_KEY=your_key`
- Or pass via client: `UTCPClient(variables={"WEATHER_API_KEY": "..."})`

---

## Comparison: UTCP vs MCP for This Use Case

| Aspect | UTCP Approach | MCP Approach |
|--------|---------------|--------------|
| **Setup** | JSON manual + API key | Server + client code |
| **Code** | 30 lines manual | 200+ lines server code |
| **Deploy** | No deployment needed | Server must be running |
| **Latency** | Direct API call (~100ms) | Additional hop (~150ms) |
| **Maintenance** | Update JSON file | Update server code, restart |

**For this weather use case**, UTCP is simpler because:
- OpenWeather already has an HTTP API
- No need for wrapper server
- Manual describes existing API
- Direct protocol access

---

**Congratulations!** You've created your first UTCP integration. 🎉

Now try exposing your own APIs as UTCP tools!

