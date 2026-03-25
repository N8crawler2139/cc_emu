#!/usr/bin/env python3
"""
FastMCP Server for SNES Emulator Control

Provides AI-accessible tools for controlling BizHawk emulator via natural language commands.
Integrates with existing Flask API and screenshot/OCR functionality.
"""

import asyncio
import json
import time
import requests
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from config import open_ai_apikey

# Initialize FastMCP server
mcp = FastMCP("SNES Emulator Controller")

# Configuration
FLASK_BASE_URL = "http://localhost:5000"
OPENAI_API_KEY = open_ai_apikey

@mcp.tool()
def press_button(button_name: str) -> Dict[str, Any]:
    """
    Press a specific SNES controller button.
    
    Args:
        button_name: The button to press (A, B, X, Y, Up, Down, Left, Right, L, R, Start, Select)
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate button name
        valid_buttons = ['A', 'B', 'X', 'Y', 'Up', 'Down', 'Left', 'Right', 'L', 'R', 'Start', 'Select']
        if button_name not in valid_buttons:
            return {
                "success": False,
                "message": f"Invalid button '{button_name}'. Valid buttons: {', '.join(valid_buttons)}"
            }
        
        # Make request to Flask API
        response = requests.post(f"{FLASK_BASE_URL}/press/{button_name}", timeout=5)
        response.raise_for_status()
        
        result = response.json()
        return {
            "success": result.get('success', False),
            "message": result.get('message', 'Unknown response'),
            "button": button_name
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to communicate with emulator: {str(e)}",
            "button": button_name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error pressing button: {str(e)}",
            "button": button_name
        }

@mcp.tool()
def hold_button(button_name: str, duration: float = -1) -> Dict[str, Any]:
    """
    Hold a specific SNES controller button for a duration or indefinitely.
    
    Args:
        button_name: The button to hold (A, B, X, Y, Up, Down, Left, Right, L, R, Start, Select)
        duration: Duration in seconds to hold the button. Use -1 for indefinite hold.
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate button name
        valid_buttons = ['A', 'B', 'X', 'Y', 'Up', 'Down', 'Left', 'Right', 'L', 'R', 'Start', 'Select']
        if button_name not in valid_buttons:
            return {
                "success": False,
                "message": f"Invalid button '{button_name}'. Valid buttons: {', '.join(valid_buttons)}"
            }
        
        # Make request to Flask API
        data = {"duration": duration} if duration != -1 else {}
        response = requests.post(f"{FLASK_BASE_URL}/hold/{button_name}", json=data, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        return {
            "success": result.get('success', False),
            "message": result.get('message', 'Unknown response'),
            "button": button_name,
            "duration": duration
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to communicate with emulator: {str(e)}",
            "button": button_name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error holding button: {str(e)}",
            "button": button_name
        }

@mcp.tool()
def release_button(button_name: str) -> Dict[str, Any]:
    """
    Release a held SNES controller button.
    
    Args:
        button_name: The button to release (A, B, X, Y, Up, Down, Left, Right, L, R, Start, Select)
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate button name
        valid_buttons = ['A', 'B', 'X', 'Y', 'Up', 'Down', 'Left', 'Right', 'L', 'R', 'Start', 'Select']
        if button_name not in valid_buttons:
            return {
                "success": False,
                "message": f"Invalid button '{button_name}'. Valid buttons: {', '.join(valid_buttons)}"
            }
        
        # Make request to Flask API
        response = requests.post(f"{FLASK_BASE_URL}/release/{button_name}", timeout=5)
        response.raise_for_status()
        
        result = response.json()
        return {
            "success": result.get('success', False),
            "message": result.get('message', 'Unknown response'),
            "button": button_name
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to communicate with emulator: {str(e)}",
            "button": button_name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error releasing button: {str(e)}",
            "button": button_name
        }

@mcp.tool()
def take_screenshot() -> Dict[str, Any]:
    """
    Take a screenshot of the BizHawk emulator window with OCR text recognition.
    
    Returns:
        Dictionary with screenshot information, OCR results, and visual feedback
    """
    try:
        # Make request to Flask API for screenshot with OCR
        response = requests.get(f"{FLASK_BASE_URL}/screenshot-ocr?regions=true", timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            # Extract and format OCR information for AI
            ocr_data = result.get('ocr_result', {})
            screenshot_path = result.get('screenshot_path', '')
            
            # Create a summary of text found
            words = ocr_data.get('words', [])
            text_summary = {
                'total_words_found': ocr_data.get('total_words', 0),
                'raw_text': ocr_data.get('raw_text', '').strip(),
                'confident_words': [w for w in words if w.get('confidence', 0) > 50],
                'screenshot_saved': screenshot_path
            }
            
            # Add region analysis if available
            if 'regions' in result:
                text_summary['regions'] = {}
                for region_name, region_data in result['regions'].items():
                    if region_data.get('total_words', 0) > 0:
                        text_summary['regions'][region_name] = {
                            'words': region_data.get('total_words', 0),
                            'text': region_data.get('raw_text', '').strip()[:200]  # First 200 chars
                        }
            
            return {
                "success": True,
                "message": "Screenshot captured and OCR completed successfully",
                "screenshot_data": text_summary,
                "image_size": result.get('image_size', [0, 0]),
                "timestamp": result.get('timestamp', time.time())
            }
        else:
            return {
                "success": False,
                "message": result.get('message', 'Failed to capture screenshot'),
                "screenshot_data": None
            }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to communicate with emulator: {str(e)}",
            "screenshot_data": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error taking screenshot: {str(e)}",
            "screenshot_data": None
        }

@mcp.tool()
def get_status() -> Dict[str, Any]:
    """
    Get the current status of the emulator and controller system.
    
    Returns:
        Dictionary with system status information
    """
    try:
        # Make request to Flask API for status
        response = requests.get(f"{FLASK_BASE_URL}/status", timeout=5)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "emulator_status": result.get('status', 'Unknown'),
            "connected": result.get('connected', False),
            "running": result.get('running', False),
            "queue_length": result.get('queue_length', 0),
            "frame": result.get('frame', 0),
            "message": "Status retrieved successfully"
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to communicate with emulator: {str(e)}",
            "emulator_status": "Disconnected",
            "connected": False,
            "running": False
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting status: {str(e)}",
            "emulator_status": "Error",
            "connected": False,
            "running": False
        }

@mcp.tool()
def launch_and_connect() -> Dict[str, Any]:
    """
    Launch BizHawk emulator and attempt to connect to it.
    
    Returns:
        Dictionary with launch and connection status
    """
    try:
        # First launch BizHawk
        launch_response = requests.post(f"{FLASK_BASE_URL}/launch", timeout=10)
        launch_response.raise_for_status()
        launch_result = launch_response.json()
        
        if not launch_result.get('success'):
            return {
                "success": False,
                "message": f"Failed to launch BizHawk: {launch_result.get('message', 'Unknown error')}",
                "launched": False,
                "connected": False
            }
        
        # Wait a moment for BizHawk to start
        time.sleep(3)
        
        # Then attempt to connect
        connect_response = requests.post(f"{FLASK_BASE_URL}/connect", timeout=15)
        connect_response.raise_for_status()
        connect_result = connect_response.json()
        
        return {
            "success": connect_result.get('success', False),
            "message": f"Launch: {launch_result.get('message', '')}. Connect: {connect_result.get('message', '')}",
            "launched": launch_result.get('success', False),
            "connected": connect_result.get('success', False)
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to communicate with emulator: {str(e)}",
            "launched": False,
            "connected": False
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error launching emulator: {str(e)}",
            "launched": False,
            "connected": False
        }

@mcp.tool()
def skip_intro() -> Dict[str, Any]:
    """
    Run the automated Final Fantasy III intro skip sequence.
    
    Returns:
        Dictionary with automation status
    """
    try:
        # Make request to Flask API to skip intro
        response = requests.post(f"{FLASK_BASE_URL}/skip-intro", timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return {
            "success": result.get('success', False),
            "message": result.get('message', 'Unknown response'),
            "automation": "FF3 intro skip"
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to communicate with emulator: {str(e)}",
            "automation": "FF3 intro skip"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error running intro skip: {str(e)}",
            "automation": "FF3 intro skip"
        }

# Natural language command parser
@mcp.tool()
def parse_command(natural_command: str) -> Dict[str, Any]:
    """
    Parse a natural language command into emulator actions.
    
    Args:
        natural_command: Natural language command like "press A", "hold down", "take screenshot"
    
    Returns:
        Dictionary with parsed action and execution result
    """
    try:
        command = natural_command.lower().strip()
        
        # Simple command parsing - direct button mapping
        if "screenshot" in command or "screen" in command or "capture" in command:
            result = take_screenshot()
            return {
                "success": result["success"],
                "message": f"Executed: take screenshot - {result['message']}",
                "parsed_command": "take_screenshot",
                "original_command": natural_command,
                "result": result
            }
        
        elif command.startswith("press "):
            button = command.replace("press ", "").strip().title()
            # Handle direction words
            button_mapping = {
                "up": "Up", "down": "Down", "left": "Left", "right": "Right",
                "a": "A", "b": "B", "x": "X", "y": "Y",
                "start": "Start", "select": "Select", "l": "L", "r": "R"
            }
            button = button_mapping.get(button.lower(), button)
            
            result = press_button(button)
            return {
                "success": result["success"],
                "message": f"Executed: press {button} - {result['message']}",
                "parsed_command": f"press_button({button})",
                "original_command": natural_command,
                "result": result
            }
        
        elif command.startswith("hold "):
            button = command.replace("hold ", "").strip().title()
            button_mapping = {
                "up": "Up", "down": "Down", "left": "Left", "right": "Right",
                "a": "A", "b": "B", "x": "X", "y": "Y",
                "start": "Start", "select": "Select", "l": "L", "r": "R"
            }
            button = button_mapping.get(button.lower(), button)
            
            result = hold_button(button)
            return {
                "success": result["success"],
                "message": f"Executed: hold {button} - {result['message']}",
                "parsed_command": f"hold_button({button})",
                "original_command": natural_command,
                "result": result
            }
        
        elif command.startswith("release "):
            button = command.replace("release ", "").strip().title()
            button_mapping = {
                "up": "Up", "down": "Down", "left": "Left", "right": "Right",
                "a": "A", "b": "B", "x": "X", "y": "Y",
                "start": "Start", "select": "Select", "l": "L", "r": "R"
            }
            button = button_mapping.get(button.lower(), button)
            
            result = release_button(button)
            return {
                "success": result["success"],
                "message": f"Executed: release {button} - {result['message']}",
                "parsed_command": f"release_button({button})",
                "original_command": natural_command,
                "result": result
            }
        
        elif "status" in command:
            result = get_status()
            return {
                "success": result["success"],
                "message": f"Executed: get status - {result['message']}",
                "parsed_command": "get_status",
                "original_command": natural_command,
                "result": result
            }
        
        elif "launch" in command or "start" in command:
            result = launch_and_connect()
            return {
                "success": result["success"],
                "message": f"Executed: launch and connect - {result['message']}",
                "parsed_command": "launch_and_connect",
                "original_command": natural_command,
                "result": result
            }
        
        elif "skip intro" in command:
            result = skip_intro()
            return {
                "success": result["success"],
                "message": f"Executed: skip intro - {result['message']}",
                "parsed_command": "skip_intro",
                "original_command": natural_command,
                "result": result
            }
        
        else:
            return {
                "success": False,
                "message": f"Could not parse command: '{natural_command}'. Try commands like 'press A', 'hold down', 'take screenshot', 'get status', 'launch emulator'.",
                "parsed_command": None,
                "original_command": natural_command,
                "result": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error parsing command: {str(e)}",
            "parsed_command": None,
            "original_command": natural_command,
            "result": None
        }

if __name__ == "__main__":
    print("Starting SNES Emulator FastMCP Server...")
    print("Available tools:")
    print("- press_button(button_name)")
    print("- hold_button(button_name, duration)")
    print("- release_button(button_name)")
    print("- take_screenshot()")
    print("- get_status()")
    print("- launch_and_connect()")
    print("- skip_intro()")
    print("- parse_command(natural_command)")
    print("\nServer will be available for AI agents to connect via MCP protocol.")
    print("Make sure Flask server is running on localhost:5000")
    
    # Run the FastMCP server
    mcp.run()