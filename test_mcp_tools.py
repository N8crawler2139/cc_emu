#!/usr/bin/env python3
"""
Test MCP tools directly without the MCP protocol layer.
This allows us to test the tool functionality independently.
"""

import sys
import os

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the tool functions directly from the MCP server
from emulator_mcp_server import (
    press_button, hold_button, release_button, 
    take_screenshot, get_status, launch_and_connect,
    skip_intro, parse_command
)

def test_tool_functionality():
    """Test each MCP tool function directly"""
    print("Testing MCP Tool Functions Directly")
    print("=" * 50)
    
    # Test 1: Get Status (should work without emulator)
    print("\n1. Testing get_status()...")
    result = get_status()
    print(f"Result: {result}")
    
    # Test 2: Take Screenshot (will fail without BizHawk, but tests the function)
    print("\n2. Testing take_screenshot()...")
    result = take_screenshot()
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    # Test 3: Parse Command
    print("\n3. Testing parse_command()...")
    test_commands = [
        "press A",
        "hold down",
        "take screenshot",
        "get status",
        "invalid command"
    ]
    
    for cmd in test_commands:
        print(f"\nTesting command: '{cmd}'")
        result = parse_command(cmd)
        print(f"  Parsed: {result['parsed_command']}")
        print(f"  Success: {result['success']}")
        print(f"  Message: {result['message'][:100]}...")
    
    # Test 4: Button press (will fail without emulator connection)
    print("\n4. Testing press_button()...")
    result = press_button("A")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    print("\n" + "=" * 50)
    print("Tool testing complete!")
    print("Note: Some tests will fail without BizHawk running and connected.")

if __name__ == "__main__":
    test_tool_functionality()