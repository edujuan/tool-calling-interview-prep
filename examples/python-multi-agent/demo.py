"""
Simple demo script for multi-agent system

This can be run with a real OpenAI API key to test the system.
"""

import os
from dotenv import load_dotenv
from main import create_software_team, Message

load_dotenv()


def simple_demo():
    """Run a simple demonstration with one task"""
    
    print("\n" + "="*70)
    print("🤖 Multi-Agent System - Simple Demo")
    print("="*70)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("This demo requires an OpenAI API key to run.")
        print("Create a .env file with: OPENAI_API_KEY=your_key_here")
        print("\nRunning in mock mode for demonstration...\n")
        return False
    
    print("\n✅ API key found")
    print("Creating software development team...\n")
    
    # Create the team
    manager = create_software_team(verbose=True)
    
    # Simple task
    task = "Research Python list comprehensions and write a simple example with documentation"
    
    print(f"\n📋 Task: {task}\n")
    
    # Create message and process
    task_message = Message(
        sender="user",
        receiver="manager",
        content=task
    )
    
    try:
        result = manager.process(task_message)
        
        print("\n" + "="*70)
        print("✅ Demo Complete!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        print("\nThis might be due to:")
        print("- Invalid API key")
        print("- Network issues")
        print("- API rate limits")
        return False


if __name__ == "__main__":
    success = simple_demo()
    
    if success:
        print("\n✨ The multi-agent system worked successfully!")
        print("\nNext steps:")
        print("1. Try running the full interactive demo: python main.py")
        print("2. Modify the agents to add new capabilities")
        print("3. Add your own specialized agents")
        print("4. Create custom tools for your use case\n")
    else:
        print("\n📝 To test with real API:")
        print("1. Get an OpenAI API key from https://platform.openai.com")
        print("2. Create .env file: OPENAI_API_KEY=your_key_here")
        print("3. Run: python demo.py")
        print("\n🧪 To test without API: python test_multiagent.py\n")



