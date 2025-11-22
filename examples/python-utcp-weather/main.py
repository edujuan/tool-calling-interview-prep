#!/usr/bin/env python3
"""
UTCP Weather Agent Example (Official v1.0.1 Library)
====================================================

Demonstrates UTCP (Universal Tool Calling Protocol) with a real weather API
using the official UTCP v1.0.1 Python library.

This example shows how to:
- Use the actual UTCP Python library (utcp, utcp-http)
- Load UTCP manuals from JSON files
- Integrate UTCP tools with OpenAI function calling
- Build a conversational weather agent

Get your API keys:
- OpenAI: https://platform.openai.com/api-keys
- OpenWeatherMap: https://openweathermap.org/api (free tier)
"""

import os
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# UTCP imports
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.data.call_template import CallTemplate

# OpenAI import
import openai  # pyright: ignore[reportMissingImports]

# =============================================================================
# WEATHER AGENT (Using Actual UTCP v1.0.1 Library)
# =============================================================================

class WeatherAgent:
    """Agent that uses UTCP weather tools via official library"""
    
    def __init__(self, openai_api_key: str, openweather_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.utcp_client = None
        self.openweather_api_key = openweather_api_key
        self.conversation_history: List[Dict] = []
        self.initialized = False
    
    async def initialize(self):
        """Initialize the UTCP client with weather manual"""
        if self.initialized:
            return
        
        # Set environment variable for UTCP to use
        os.environ['OPENWEATHER_API_KEY'] = self.openweather_api_key
        
        # Create UTCP configuration
        config = UtcpClientConfig(
            manual_call_templates=[
                CallTemplate(
                    name="weather_tools",
                    call_template_type="text",
                    file_path="./weather_manual.json"
                )
            ],
            variables={
                "OPENWEATHER_API_KEY": self.openweather_api_key
            }
        )
        
        # Create UTCP client
        self.utcp_client = await UtcpClient.create(config=config)
        
        # Get available tools
        tools = await self.utcp_client.get_tools()
        
        print("✓ Weather Agent initialized with UTCP v1.0.1 library")
        print(f"✓ Loaded {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}")
        
        self.initialized = True
    
    async def get_openai_tools(self) -> List[Dict]:
        """Convert UTCP tools to OpenAI function calling format"""
        utcp_tools = await self.utcp_client.get_tools()
        openai_tools = []
        
        for tool in utcp_tools:
            # Convert UTCP tool to OpenAI format
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputs
                }
            })
        
        return openai_tools
    
    async def chat(self, user_message: str, verbose: bool = True) -> str:
        """
        Chat with the weather agent.
        
        Args:
            user_message: User's question about weather
            verbose: Print execution details
        
        Returns:
            Agent's response
        """
        if not self.initialized:
            await self.initialize()
        
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
            
            # Get OpenAI tools
            openai_tools = await self.get_openai_tools()
            
            # Call LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.conversation_history,
                tools=openai_tools,
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
                    
                    # Execute via UTCP library
                    try:
                        result = await self.utcp_client.call_tool(tool_name, tool_args)
                        
                        # Parse result if it's a JSON string
                        if isinstance(result, str):
                            result_data = json.loads(result)
                        else:
                            result_data = result
                        
                        if verbose:
                            # Pretty print result
                            if 'error' not in result_data:
                                print(f"     ✓ Success")
                                if 'main' in result_data:
                                    print(f"       Temperature: {result_data['main']['temp']}°")
                                    print(f"       Condition: {result_data['weather'][0]['description']}")
                            else:
                                print(f"     ✗ Error: {result_data['error']}")
                            print()
                        
                        # Add tool result
                        self.conversation_history.append({
                            "role": "tool",
                            "content": json.dumps(result_data) if not isinstance(result, str) else result,
                            "tool_call_id": tool_call.id
                        })
                    
                    except Exception as e:
                        error_result = {"error": str(e)}
                        if verbose:
                            print(f"     ✗ Error: {e}")
                            print()
                        
                        self.conversation_history.append({
                            "role": "tool",
                            "content": json.dumps(error_result),
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

async def main():
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
    await agent.initialize()
    
    print("\n" + "="*60)
    print("UTCP Weather Agent - Interactive Mode")
    print("="*60)
    print("\nThis agent uses UTCP v1.0.1 Python library to call")
    print("OpenWeatherMap API directly. No server needed!")
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
        await agent.chat(example, verbose=True)
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
            await agent.chat(user_input, verbose=True)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
