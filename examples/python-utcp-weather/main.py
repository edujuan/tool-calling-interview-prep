#!/usr/bin/env python3
"""
UTCP Weather Agent Example
===========================

Demonstrates UTCP (Universal Tool Calling Protocol) with a real weather API.

UTCP allows agents to call APIs directly using JSON "manual" files that describe:
- Endpoint URLs
- HTTP methods
- Parameters
- Authentication
- Request/response formats

This is simpler than MCP because:
- No server to run
- Direct API calls
- Stateless
- Leverages existing REST APIs

This example uses OpenWeatherMap API (free tier available).
"""

import os
import json
import requests
import openai
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# UTCP MANUAL DEFINITION
# =============================================================================

WEATHER_UTCP_MANUAL = {
    "protocol": "utcp",
    "version": "1.0",
    "tool": {
        "name": "get_current_weather",
        "description": "Get current weather conditions for any city worldwide",
        "endpoint": {
            "url": "https://api.openweathermap.org/data/2.5/weather",
            "method": "GET"
        },
        "authentication": {
            "type": "api_key",
            "location": "query",
            "param_name": "appid",
            "env_var": "OPENWEATHER_API_KEY"
        },
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "City name, e.g., 'London' or 'New York,US'",
                    "required": True
                },
                "units": {
                    "type": "string",
                    "description": "Units of measurement: 'metric' (Celsius), 'imperial' (Fahrenheit), or 'standard' (Kelvin)",
                    "default": "metric",
                    "enum": ["metric", "imperial", "standard"]
                }
            }
        },
        "response": {
            "type": "object",
            "description": "Weather data including temperature, conditions, humidity, etc."
        }
    }
}

FORECAST_UTCP_MANUAL = {
    "protocol": "utcp",
    "version": "1.0",
    "tool": {
        "name": "get_weather_forecast",
        "description": "Get 5-day weather forecast with 3-hour intervals for any city",
        "endpoint": {
            "url": "https://api.openweathermap.org/data/2.5/forecast",
            "method": "GET"
        },
        "authentication": {
            "type": "api_key",
            "location": "query",
            "param_name": "appid",
            "env_var": "OPENWEATHER_API_KEY"
        },
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "City name",
                    "required": True
                },
                "units": {
                    "type": "string",
                    "description": "Units of measurement",
                    "default": "metric",
                    "enum": ["metric", "imperial", "standard"]
                },
                "cnt": {
                    "type": "integer",
                    "description": "Number of forecast entries to return (max 40)",
                    "default": 8
                }
            }
        },
        "response": {
            "type": "object",
            "description": "List of weather forecasts with timestamps"
        }
    }
}

# =============================================================================
# UTCP EXECUTOR
# =============================================================================

class UTCPExecutor:
    """Executes tools defined by UTCP manuals"""
    
    def __init__(self):
        self.manuals: Dict[str, Dict] = {}
    
    def load_manual(self, manual: Dict) -> str:
        """
        Load a UTCP manual and register the tool.
        
        Returns:
            Tool name
        """
        tool_name = manual['tool']['name']
        self.manuals[tool_name] = manual
        return tool_name
    
    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Execute a UTCP tool.
        
        Args:
            tool_name: Name of the tool from manual
            parameters: Tool parameters
        
        Returns:
            JSON string with result or error
        """
        if tool_name not in self.manuals:
            return json.dumps({"error": f"Tool '{tool_name}' not found"})
        
        manual = self.manuals[tool_name]
        tool = manual['tool']
        
        try:
            # Build request
            url = tool['endpoint']['url']
            method = tool['endpoint']['method']
            
            # Handle authentication
            if 'authentication' in tool:
                auth = tool['authentication']
                if auth['type'] == 'api_key':
                    api_key = os.getenv(auth['env_var'])
                    if not api_key:
                        return json.dumps({
                            "error": f"API key not found. Set {auth['env_var']} environment variable"
                        })
                    
                    if auth['location'] == 'query':
                        parameters[auth['param_name']] = api_key
                    elif auth['location'] == 'header':
                        # Would add to headers
                        pass
            
            # Make request
            if method == 'GET':
                response = requests.get(url, params=parameters, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=parameters, timeout=10)
            else:
                return json.dumps({"error": f"Unsupported method: {method}"})
            
            # Check response
            response.raise_for_status()
            
            return json.dumps(response.json())
        
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"API request failed: {str(e)}"})
        except Exception as e:
            return json.dumps({"error": f"Execution failed: {str(e)}"})
    
    def get_openai_tools(self) -> List[Dict]:
        """Convert UTCP manuals to OpenAI function calling format"""
        tools = []
        
        for tool_name, manual in self.manuals.items():
            tool = manual['tool']
            
            # Build parameters schema
            params_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param_def in tool['parameters']['properties'].items():
                # Skip auth parameters (handled internally)
                if 'authentication' in tool:
                    auth = tool['authentication']
                    if param_name == auth.get('param_name'):
                        continue
                
                params_schema['properties'][param_name] = {
                    "type": param_def['type'],
                    "description": param_def['description']
                }
                
                if param_def.get('enum'):
                    params_schema['properties'][param_name]['enum'] = param_def['enum']
                
                if param_def.get('default'):
                    params_schema['properties'][param_name]['default'] = param_def['default']
                
                if param_def.get('required', False):
                    params_schema['required'].append(param_name)
            
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool['description'],
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
        
        # Load UTCP manuals
        self.utcp_executor.load_manual(WEATHER_UTCP_MANUAL)
        self.utcp_executor.load_manual(FORECAST_UTCP_MANUAL)
        
        self.conversation_history: List[Dict] = []
        
        print("✓ Weather Agent initialized with UTCP tools:")
        print("  - get_current_weather")
        print("  - get_weather_forecast")
    
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

