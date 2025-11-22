#!/usr/bin/env python3
"""
Test script to verify the UTCP weather example works with the actual library.
"""

import asyncio
import os
import sys

async def test_utcp_weather_example():
    """Test that the example can initialize properly"""
    print("Testing UTCP Weather Example...")
    print("="*60)
    
    # Set dummy keys for testing
    os.environ["OPENAI_API_KEY"] = "sk-test"
    os.environ["OPENWEATHER_API_KEY"] = "test-key"
    
    try:
        # Import the agent
        from main import WeatherAgent
        
        print("✓ Imports successful")
        
        # Create agent (don't initialize yet as that requires API calls)
        agent = WeatherAgent("sk-test", "test-key")
        print("✓ Agent creation successful")
        
        # Test UTCP client configuration
        from utcp.data.utcp_client_config import UtcpClientConfig
        from utcp.data.call_template import CallTemplate
        
        config = UtcpClientConfig(
            manual_call_templates=[
                CallTemplate(
                    name="weather_tools",
                    call_template_type="text",
                    file_path="./weather_manual.json"
                )
            ],
            variables={
                "OPENWEATHER_API_KEY": "test-key"
            }
        )
        print("✓ UTCP configuration creation successful")
        
        # Verify manual exists
        from pathlib import Path
        if Path("./weather_manual.json").exists():
            print("✓ weather_manual.json exists")
        else:
            print("✗ weather_manual.json not found")
            return False
        
        # Validate manual format
        import json
        with open("./weather_manual.json") as f:
            manual = json.load(f)
        
        assert "utcp_version" in manual, "Missing utcp_version"
        assert "tools" in manual, "Missing tools"
        assert len(manual["tools"]) > 0, "No tools defined"
        print(f"✓ Manual valid with {len(manual['tools'])} tools")
        
        # Check variable syntax in manual
        for tool in manual["tools"]:
            template = tool["tool_call_template"]
            if "query_params" in template:
                for key, value in template["query_params"].items():
                    if isinstance(value, str) and "${" in value:
                        # Should use ${VAR} not {{VAR}}
                        if value.count("${") != value.count("}"):
                            print(f"✗ Invalid variable syntax in {tool['name']}: {value}")
                            return False
        print("✓ Variable substitution syntax correct (${VAR})")
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        print("\nThe example is ready to run with:")
        print("  export OPENAI_API_KEY=your_key")
        print("  export OPENWEATHER_API_KEY=your_key")
        print("  python main.py")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("\nInstall requirements:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_utcp_weather_example())
    sys.exit(0 if result else 1)

