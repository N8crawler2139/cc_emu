#!/usr/bin/env python3
"""
Chat with OpenAI LLM that can control the SNES emulator via MCP server.

This script connects to the running emulator_mcp_server.py and allows you to 
chat with an LLM that has access to emulator control tools.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Any
import openai
from config import open_ai_apikey

# Configure OpenAI
openai.api_key = open_ai_apikey

class EmulatorChatBot:
    def __init__(self):
        self.mcp_process = None
        self.conversation_history = []
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "press_button",
                    "description": "Press a specific SNES controller button",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "button_name": {
                                "type": "string",
                                "description": "The button to press (A, B, X, Y, Up, Down, Left, Right, L, R, Start, Select)",
                                "enum": ["A", "B", "X", "Y", "Up", "Down", "Left", "Right", "L", "R", "Start", "Select"]
                            }
                        },
                        "required": ["button_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "hold_button",
                    "description": "Hold a specific SNES controller button for a duration or indefinitely",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "button_name": {
                                "type": "string",
                                "description": "The button to hold",
                                "enum": ["A", "B", "X", "Y", "Up", "Down", "Left", "Right", "L", "R", "Start", "Select"]
                            },
                            "duration": {
                                "type": "number",
                                "description": "Duration in seconds to hold the button. Use -1 for indefinite hold.",
                                "default": -1
                            }
                        },
                        "required": ["button_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "release_button",
                    "description": "Release a held SNES controller button",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "button_name": {
                                "type": "string",
                                "description": "The button to release",
                                "enum": ["A", "B", "X", "Y", "Up", "Down", "Left", "Right", "L", "R", "Start", "Select"]
                            }
                        },
                        "required": ["button_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Take a screenshot of the BizHawk emulator window with OCR text recognition",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_status",
                    "description": "Get the current status of the emulator and controller system",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "launch_and_connect",
                    "description": "Launch BizHawk emulator and attempt to connect to it",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "skip_intro",
                    "description": "Run the automated Final Fantasy III intro skip sequence",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "parse_command",
                    "description": "Parse a natural language command into emulator actions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "natural_command": {
                                "type": "string",
                                "description": "Natural language command like 'press A', 'hold down', 'take screenshot'"
                            }
                        },
                        "required": ["natural_command"]
                    }
                }
            }
        ]
    
    def start_mcp_server(self):
        """Start the MCP server process"""
        try:
            print("Starting MCP server...")
            self.mcp_process = subprocess.Popen(
                [sys.executable, "emulator_mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            return True
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            return False
    
    def send_mcp_request(self, method: str, params: Dict = None) -> Dict:
        """Send a request to the MCP server"""
        if not self.mcp_process:
            return {"error": "MCP server not running"}
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            # Send request
            request_str = json.dumps(request) + "\n"
            self.mcp_process.stdin.write(request_str)
            self.mcp_process.stdin.flush()
            
            # Read response
            response_str = self.mcp_process.stdout.readline()
            if response_str:
                return json.loads(response_str.strip())
            else:
                return {"error": "No response from MCP server"}
                
        except Exception as e:
            return {"error": f"MCP communication error: {str(e)}"}
    
    def call_emulator_function(self, function_name: str, arguments: Dict) -> Dict:
        """Call an emulator function via MCP server"""
        # For now, we'll simulate the MCP call by importing and calling directly
        # This is a simplified approach since proper MCP protocol is complex
        try:
            import requests
            
            # Map function calls to direct API calls
            if function_name == "press_button":
                response = requests.post(f"http://localhost:5000/press/{arguments['button_name']}", timeout=5)
                return response.json()
            elif function_name == "hold_button":
                button_name = arguments['button_name']
                duration = arguments.get('duration', -1)
                
                # Start holding the button with duration parameter
                data = {"duration": duration} if duration != -1 else {}
                response = requests.post(f"http://localhost:5000/hold/{button_name}", json=data, timeout=5)
                result = response.json()
                
                # If a specific duration was requested (not indefinite), set up auto-release
                if duration > 0 and result.get('success'):
                    import threading
                    import time
                    
                    def auto_release():
                        time.sleep(duration)
                        try:
                            requests.post(f"http://localhost:5000/release/{button_name}", timeout=5)
                        except:
                            pass  # Ignore release errors
                    
                    thread = threading.Thread(target=auto_release)
                    thread.daemon = True
                    thread.start()
                    
                    # Update the result message
                    if result.get('success'):
                        result['message'] = f'{button_name} button held for {duration} seconds'
                
                return result
            elif function_name == "release_button":
                response = requests.post(f"http://localhost:5000/release/{arguments['button_name']}", timeout=5)
                return response.json()
            elif function_name == "take_screenshot":
                response = requests.get("http://localhost:5000/screenshot-ocr?regions=true", timeout=10)
                return response.json()
            elif function_name == "get_status":
                response = requests.get("http://localhost:5000/status", timeout=5)
                return response.json()
            elif function_name == "launch_and_connect":
                response = requests.post("http://localhost:5000/launch", timeout=10)
                return response.json()
            elif function_name == "skip_intro":
                response = requests.post("http://localhost:5000/skip-intro", timeout=30)
                return response.json()
            elif function_name == "parse_command":
                # For parse_command, we'll just return the command as-is for now
                return {"success": True, "parsed_command": arguments.get("natural_command", "")}
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": f"Function call failed: {str(e)}"}
    
    async def chat_with_llm(self, user_message: str) -> str:
        """Send message to LLM and handle function calls"""
        
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # System message with emulator context
        system_message = {
            "role": "system",
            "content": """You are an AI assistant that can control a SNES emulator running Final Fantasy III. 

You have access to the following emulator functions:
- press_button(button_name): Press SNES buttons (A, B, X, Y, Up, Down, Left, Right, L, R, Start, Select)
- hold_button(button_name, duration): Hold a button for a duration or indefinitely (-1)
- release_button(button_name): Release a held button
- take_screenshot(): Capture the emulator screen with OCR text recognition
- get_status(): Check emulator connection status
- launch_and_connect(): Start BizHawk and connect
- skip_intro(): Automated FF3 intro skip
- parse_command(natural_command): Parse natural language commands

You can help the user:
1. Control the game with button presses
2. Take screenshots to see what's happening
3. Read text from the game using OCR
4. Navigate menus and gameplay
5. Automate sequences like skipping the intro

Always be helpful and explain what you're doing. If you need to see the current screen, take a screenshot first."""
        }
        
        messages = [system_message] + self.conversation_history
        
        try:
            # Call OpenAI with function calling
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Handle function calls
            if message.tool_calls:
                # Add assistant message to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls]
                })
                
                # Execute function calls
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 Executing: {function_name}({function_args})")
                    
                    # Call the emulator function
                    result = self.call_emulator_function(function_name, function_args)
                    
                    # Add function result to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Get final response from LLM
                messages = [system_message] + self.conversation_history
                final_response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
                
                final_message = final_response.choices[0].message.content
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": final_message
                })
                
                return final_message
            else:
                # No function calls, just return the message
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content
                })
                return message.content
                
        except Exception as e:
            error_msg = f"Error communicating with LLM: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def cleanup(self):
        """Clean up resources"""
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process = None

async def main():
    """Main chat loop"""
    print("🎮 SNES Emulator AI Chat")
    print("=" * 50)
    print("This chat connects you to an AI that can control your SNES emulator!")
    print("Make sure your Flask server is running on localhost:5000")
    print("Type 'quit' to exit")
    print()
    
    bot = EmulatorChatBot()
    
    try:
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🤖 AI: ", end="", flush=True)
            response = await bot.chat_with_llm(user_input)
            print(response)
            print()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())