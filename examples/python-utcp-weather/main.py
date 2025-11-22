#!/usr/bin/env python3
"""
UTCP Weather Agent Example (Official v1.0.1 Format)
====================================================

Demonstrates UTCP (Universal Tool Calling Protocol) with a real weather API.

This example uses the OFFICIAL UTCP v1.0.1 specification format, compatible with
standard UTCP clients and libraries.

UTCP allows agents to call APIs directly using JSON "manual" files that describe:
- Tool definitions with inputs schema
- HTTP call templates with URL, method, query parameters
- Authentication via environment variables
- Response formats

Key advantages over MCP:
- No server to run - direct API calls
- Stateless protocol
- Leverages existing REST APIs
- Simple JSON configuration

This example uses OpenWeatherMap API (free tier available).
Get your API key at: https://openweathermap.org/api
"""

import os
import json
import requests
import openai
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# UTCP MANUAL DEFINITION (Official v1.0.1 Format)
# =============================================================================

WEATHER_UTCP_MANUAL = {
    "manual_version": "1.0.0",
    "utcp_version": "1.0.1",
    "info": {
        "title": "OpenWeatherMap Current Weather API",
        "version": "1.0.0",
        "description": "Get current weather conditions for any location worldwide"
    },
    "tools": [
        {
            "name": "get_current_weather",
            "description": "Get current weather conditions for any city worldwide. Returns temperature, humidity, wind speed, and weather conditions.",
            "inputs": {
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": "City name, e.g., 'London' or 'New York,US' or coordinates 'lat,lon'"
                    },
                    "units": {
                        "type": "string",
                        "description": "Units of measurement: 'metric' (Celsius), 'imperial' (Fahrenheit), or 'standard' (Kelvin)",
                        "enum": ["metric", "imperial", "standard"],
                        "default": "metric"
                    }
                },
                "required": ["q"]
            },
            "tool_call_template": {
                "call_template_type": "http",
                "url": "https://api.openweathermap.org/data/2.5/weather",
                "http_method": "GET",
                "query_params": {
                    "q": "{{q}}",
                    "units": "{{units}}",
                    "appid": "${OPENWEATHER_API_KEY}"
                }
            },
            "response_schema": {
                "type": "object",
                "description": "Weather data including temperature, conditions, humidity, wind, etc."
            }
        }
    ]
}

FORECAST_UTCP_MANUAL = {
    "manual_version": "1.0.0",
    "utcp_version": "1.0.1",
    "info": {
        "title": "OpenWeatherMap Forecast API",
        "version": "1.0.0",
        "description": "Get 5-day weather forecast with 3-hour intervals"
    },
    "tools": [
        {
            "name": "get_weather_forecast",
            "description": "Get 5-day weather forecast with 3-hour intervals for any city. Returns list of forecasts with temperature, conditions, and timestamps.",
            "inputs": {
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": "City name, e.g., 'London' or 'New York,US'"
                    },
                    "units": {
                        "type": "string",
                        "description": "Units of measurement: 'metric', 'imperial', or 'standard'",
                        "enum": ["metric", "imperial", "standard"],
                        "default": "metric"
                    },
                    "cnt": {
                        "type": "integer",
                        "description": "Number of forecast entries to return (max 40, ~5 days with 3-hour intervals)",
                        "default": 8,
                        "minimum": 1,
                        "maximum": 40
                    }
                },
                "required": ["q"]
            },
            "tool_call_template": {
                "call_template_type": "http",
                "url": "https://api.openweathermap.org/data/2.5/forecast",
                "http_method": "GET",
                "query_params": {
                    "q": "{{q}}",
                    "units": "{{units}}",
                    "cnt": "{{cnt}}",
                    "appid": "${OPENWEATHER_API_KEY}"
                }
            },
            "response_schema": {
                "type": "object",
                "description": "List of weather forecasts with timestamps"
            }
        }
    ]
}

# =============================================================================
# UTCP EXECUTOR (UTCP v1.0.1 Compatible)
# =============================================================================

class UTCPExecutor:
    """Executes tools defined by UTCP v1.0.1 manuals"""
    
    def __init__(self):
        self.tools: Dict[str, Dict] = {}  # tool_name -> tool definition
        self.manuals: Dict[str, Dict] = {}  # tool_name -> full manual
    
    def load_manual(self, manual: Dict) -> List[str]:
        """
        Load a UTCP v1.0.1 manual and register all tools.
        
        Args:
            manual: UTCP manual dictionary with 'tools' array
        
        Returns:
            List of tool names loaded
        """
        tool_names = []
        
        # Validate manual structure
        if "tools" not in manual:
            raise ValueError("Invalid UTCP manual: missing 'tools' array")
        
        if not isinstance(manual["tools"], list):
            raise ValueError("Invalid UTCP manual: 'tools' must be an array")
        
        # Load each tool
        for tool in manual["tools"]:
            tool_name = tool["name"]
            self.tools[tool_name] = tool
            self.manuals[tool_name] = manual
            tool_names.append(tool_name)
        
        return tool_names
    
    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Execute a UTCP tool.
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters (will be substituted into template)
        
        Returns:
            JSON string with result or error
        """
        if tool_name not in self.tools:
            return json.dumps({"error": f"Tool '{tool_name}' not found"})
        
        tool = self.tools[tool_name]
        
        try:
            # Get call template
            call_template = tool["tool_call_template"]
            call_type = call_template["call_template_type"]
            
            if call_type != "http":
                return json.dumps({"error": f"Unsupported call_template_type: {call_type}"})
            
            # Build HTTP request
            url = call_template["url"]
            method = call_template["http_method"]
            
            # Prepare query parameters with template substitution
            query_params = {}
            if "query_params" in call_template:
                for key, value_template in call_template["query_params"].items():
                    # Substitute {{parameter}} from inputs
                    if isinstance(value_template, str):
                        if value_template.startswith("{{") and value_template.endswith("}}"):
                            param_name = value_template[2:-2]
                            if param_name in parameters:
                                query_params[key] = parameters[param_name]
                            # Skip if parameter not provided (might be optional)
                        elif value_template.startswith("${") and value_template.endswith("}"):
                            # Environment variable
                            env_var = value_template[2:-1]
                            env_value = os.getenv(env_var)
                            if not env_value:
                                return json.dumps({
                                    "error": f"Environment variable {env_var} not set"
                                })
                            query_params[key] = env_value
                        else:
                            # Static value
                            query_params[key] = value_template
                    else:
                        query_params[key] = value_template
            
            # Prepare headers
            headers = {}
            if "headers" in call_template:
                for key, value in call_template["headers"].items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var = value[2:-1]
                        env_value = os.getenv(env_var)
                        if env_value:
                            headers[key] = env_value
                    else:
                        headers[key] = value
            
            # Prepare body (for POST/PUT)
            body = None
            if "body_template" in call_template:
                body = {}
                for key, value_template in call_template["body_template"].items():
                    if isinstance(value_template, str):
                        if value_template.startswith("{{") and value_template.endswith("}}"):
                            param_name = value_template[2:-2]
                            if param_name in parameters:
                                body[key] = parameters[param_name]
                        else:
                            body[key] = value_template
                    else:
                        body[key] = value_template
            
            # Make HTTP request
            if method == "GET":
                response = requests.get(url, params=query_params, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, params=query_params, json=body, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, params=query_params, json=body, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, params=query_params, headers=headers, timeout=10)
            else:
                return json.dumps({"error": f"Unsupported HTTP method: {method}"})
            
            # Check response
            response.raise_for_status()
            
            return json.dumps(response.json())
        
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"API request failed: {str(e)}"})
        except KeyError as e:
            return json.dumps({"error": f"Invalid UTCP manual structure: missing {str(e)}"})
        except Exception as e:
            return json.dumps({"error": f"Execution failed: {str(e)}"})
    
    def get_openai_tools(self) -> List[Dict]:
        """Convert UTCP tools to OpenAI function calling format"""
        tools = []
        
        for tool_name, tool in self.tools.items():
            # Build parameters schema from inputs
            params_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            if "inputs" in tool:
                inputs = tool["inputs"]
                
                # Copy properties
                if "properties" in inputs:
                    for param_name, param_def in inputs["properties"].items():
                        params_schema["properties"][param_name] = {
                            "type": param_def.get("type", "string"),
                            "description": param_def.get("description", "")
                        }
                        
                        if "enum" in param_def:
                            params_schema["properties"][param_name]["enum"] = param_def["enum"]
                        
                        if "default" in param_def:
                            params_schema["properties"][param_name]["default"] = param_def["default"]
                
                # Copy required fields
                if "required" in inputs:
                    params_schema["required"] = inputs["required"]
            
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.get("description", ""),
                    "parameters": params_schema
                }
            })
        
        return tools

# =============================================================================
# WEATHER AGENT
# =============================================================================

class WeatherAgent:
    """Agent that uses UTCP weather tools"""
    
    def __init__(self, openai_api_key: str, openweather_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.utcp_executor = UTCPExecutor()
        
        # Store API key in environment (UTCP executor reads from env)
        os.environ['OPENWEATHER_API_KEY'] = openweather_api_key
        
        # Load UTCP manuals (v1.0.1 format)
        weather_tools = self.utcp_executor.load_manual(WEATHER_UTCP_MANUAL)
        forecast_tools = self.utcp_executor.load_manual(FORECAST_UTCP_MANUAL)
        
        self.conversation_history: List[Dict] = []
        
        print("✓ Weather Agent initialized with UTCP v1.0.1 tools:")
        for tool in weather_tools + forecast_tools:
            print(f"  - {tool}")
    
    def chat(self, user_message: str, verbose: bool = True) -> str:
        """
        Chat with the weather agent.
        
        Args:
            user_message: User's question about weather
            verbose: Print execution details
        
        Returns:
            Agent's response
        """
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"USER: {user_message}")
            print(f"{'='*60}\n")
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                print(f"[Iteration {iteration}]")
            
            # Call LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=self.conversation_history,
                tools=self.utcp_executor.get_openai_tools(),
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check if agent wants to use tools
            if message.tool_calls:
                # Add assistant message
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # Execute tool calls
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"  🌤️  Calling UTCP tool: {tool_name}")
                        print(f"     Parameters: {json.dumps(tool_args, indent=6)}")
                    
                    # Execute via UTCP
                    result = self.utcp_executor.execute(tool_name, tool_args)
                    
                    if verbose:
                        # Pretty print result
                        try:
                            result_data = json.loads(result)
                            if 'error' not in result_data:
                                print(f"     ✓ Success")
                                if 'main' in result_data:
                                    print(f"       Temperature: {result_data['main']['temp']}°")
                                    print(f"       Condition: {result_data['weather'][0]['description']}")
                            else:
                                print(f"     ✗ Error: {result_data['error']}")
                        except:
                            print(f"     Result: {result[:200]}...")
                        print()
                    
                    # Add tool result
                    self.conversation_history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id
                    })
                
                continue
            
            else:
                # Final answer
                final_answer = message.content
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
                
                if verbose:
                    print(f"{'='*60}")
                    print(f"AGENT: {final_answer}")
                    print(f"{'='*60}\n")
                
                return final_answer
        
        return "I couldn't complete the request within the iteration limit."
    
    def reset(self):
        """Reset conversation history"""
        self.conversation_history.clear()

# =============================================================================
# FORMATTING HELPERS
# =============================================================================

def format_current_weather(data: Dict) -> str:
    """Format current weather data for display"""
    try:
        return f"""
📍 Location: {data['name']}, {data['sys']['country']}
🌡️  Temperature: {data['main']['temp']}°C (feels like {data['main']['feels_like']}°C)
☁️  Condition: {data['weather'][0]['description'].title()}
💧 Humidity: {data['main']['humidity']}%
💨 Wind: {data['wind']['speed']} m/s
👁️  Visibility: {data.get('visibility', 'N/A')} meters
🕐 Last updated: {datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S')}
"""
    except KeyError:
        return json.dumps(data, indent=2)

def format_forecast(data: Dict, days: int = 3) -> str:
    """Format forecast data for display"""
    try:
        output = [f"\n📅 {days}-Day Forecast for {data['city']['name']}, {data['city']['country']}\n"]
        
        # Group by date
        forecasts_by_date = {}
        for item in data['list'][:days * 8]:  # 8 entries per day (3-hour intervals)
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            if date not in forecasts_by_date:
                forecasts_by_date[date] = []
            forecasts_by_date[date].append(item)
        
        # Format each day
        for date, forecasts in list(forecasts_by_date.items())[:days]:
            temps = [f['main']['temp'] for f in forecasts]
            conditions = [f['weather'][0]['description'] for f in forecasts]
            
            output.append(f"{date}:")
            output.append(f"  🌡️  {min(temps):.1f}°C - {max(temps):.1f}°C")
            output.append(f"  ☁️  {conditions[len(conditions)//2].title()}")
            output.append("")
        
        return "\n".join(output)
    except KeyError:
        return json.dumps(data, indent=2)

# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def main():
    """Run weather agent examples"""
    
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    openweather_key = os.getenv("OPENWEATHER_API_KEY")
    
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set")
        print("Get your key at: https://platform.openai.com/api-keys")
        return
    
    if not openweather_key:
        print("ERROR: OPENWEATHER_API_KEY not set")
        print("Get your free key at: https://openweathermap.org/api")
        return
    
    # Initialize agent
    agent = WeatherAgent(openai_key, openweather_key)
    
    print("\n" + "="*60)
    print("UTCP Weather Agent - Interactive Mode")
    print("="*60)
    print("\nThis agent uses UTCP to call OpenWeatherMap API directly.")
    print("No server needed - just JSON manuals!")
    print("\nType 'quit' to exit, 'reset' to start new conversation")
    print("="*60)
    
    # Example queries (uncomment to run)
    examples = [
        # "What's the weather in Tokyo?",
        # "Compare the weather in London and Paris",
        # "Give me a 3-day forecast for New York",
        # "Is it raining in Seattle right now?"
    ]
    
    for example in examples:
        print(f"\n🎯 Example: {example}")
        agent.chat(example, verbose=True)
        agent.reset()
    
    # Interactive mode
    while True:
        try:
            user_input = input("\n💬 Ask about weather: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset()
                print("✓ Conversation reset")
                continue
            
            # Process query
            agent.chat(user_input, verbose=True)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

