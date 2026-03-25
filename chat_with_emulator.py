#!/usr/bin/env python3
"""
Enhanced Chat with OpenAI LLM that can control the SNES emulator.

Combines the best features from both chat_with_emulator.py and enhanced_chat_emulator.py:
- Fixed hold_button functionality with duration parameter passing
- Multi-command queuing system for complex sequences
- Auto port detection (5000/5001)
- Enhanced error handling and user experience
"""

import asyncio
import json
import subprocess
import sys
import time
import threading
from typing import Dict, List, Any, Optional
import openai
import requests
from config import open_ai_apikey

# Configure OpenAI
openai.api_key = open_ai_apikey

class CommandQueue:
    """Handles sequential execution of multiple emulator commands"""
    
    def __init__(self, chat_bot):
        self.chat_bot = chat_bot
        self.queue = []
        self.is_executing = False
    
    def add_command(self, command_type: str, **kwargs) -> None:
        """Add a command to the queue"""
        self.queue.append({"type": command_type, "args": kwargs})
    
    async def execute_queue(self) -> List[Dict]:
        """Execute all queued commands sequentially"""
        if self.is_executing:
            return [{"error": "Commands already executing"}]
        
        if not self.queue:
            return [{"message": "No commands to execute"}]
        
        self.is_executing = True
        results = []
        
        try:
            for i, command in enumerate(self.queue):
                print(f"🔧 Executing command {i+1}/{len(self.queue)}: {command['type']}")
                
                if command["type"] == "wait":
                    duration = command["args"].get("duration", 1)
                    print(f"   ⏱️  Waiting {duration} seconds...")
                    await asyncio.sleep(duration)
                    results.append({"success": True, "message": f"Waited {duration} seconds"})
                
                elif command["type"] == "press_button":
                    result = self.chat_bot.call_emulator_function("press_button", command["args"])
                    results.append(result)
                
                elif command["type"] == "hold_button":
                    result = self.chat_bot.call_emulator_function("hold_button", command["args"])
                    results.append(result)
                
                elif command["type"] == "release_button":
                    result = self.chat_bot.call_emulator_function("release_button", command["args"])
                    results.append(result)
                
                elif command["type"] == "take_screenshot":
                    result = self.chat_bot.call_emulator_function("take_screenshot", command["args"])
                    results.append(result)
                
                else:
                    results.append({"error": f"Unknown command type: {command['type']}"})
                
                # Small delay between commands for stability
                if i < len(self.queue) - 1:  # Don't wait after the last command
                    await asyncio.sleep(0.1)
        
        finally:
            self.queue.clear()
            self.is_executing = False
        
        return results

class EmulatorChatBot:
    def __init__(self, flask_port=5000):
        self.flask_port = flask_port
        self.conversation_history = []
        self.command_queue = CommandQueue(self)
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
                                "description": "The button to press",
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
                    "description": "Launch BizHawk emulator and connect to it",
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
                    "name": "execute_command_sequence",
                    "description": "Execute multiple emulator commands in sequence. Use this for complex multi-step actions like 'go up for 3 seconds then go left'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commands": {
                                "type": "array",
                                "description": "List of commands to execute in sequence",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "action": {
                                            "type": "string",
                                            "enum": ["press", "hold", "release", "wait", "screenshot"],
                                            "description": "Type of action to perform"
                                        },
                                        "button": {
                                            "type": "string",
                                            "enum": ["A", "B", "X", "Y", "Up", "Down", "Left", "Right", "L", "R", "Start", "Select"],
                                            "description": "Button to act on (not needed for wait/screenshot)"
                                        },
                                        "duration": {
                                            "type": "number",
                                            "description": "Duration in seconds (for hold or wait actions)"
                                        }
                                    },
                                    "required": ["action"]
                                }
                            }
                        },
                        "required": ["commands"]
                    }
                }
            }
        ]
    
    def call_emulator_function(self, function_name: str, arguments: Dict) -> Dict:
        """Call an emulator function via Flask API"""
        try:
            base_url = f"http://localhost:{self.flask_port}"
            
            # Map function calls to direct API calls
            if function_name == "press_button":
                response = requests.post(f"{base_url}/press/{arguments['button_name']}", timeout=5)
                return response.json()
            
            elif function_name == "hold_button":
                button_name = arguments['button_name']
                duration = arguments.get('duration', -1)
                
                # Try Flask API first
                try:
                    data = {"duration": duration} if duration != -1 else {}
                    response = requests.post(f"{base_url}/hold/{button_name}", json=data, timeout=5)
                    
                    if response.status_code == 404:
                        # Hold endpoint not available, fall back to direct file communication
                        raise Exception("Hold endpoint not found, using fallback")
                    
                    result = response.json()
                    
                    # If a specific duration was requested (not indefinite), set up auto-release
                    if duration > 0 and result.get('success'):
                        import threading
                        import time
                        
                        def auto_release():
                            time.sleep(duration)
                            try:
                                requests.post(f"{base_url}/release/{button_name}", timeout=5)
                            except:
                                pass  # Ignore release errors
                        
                        thread = threading.Thread(target=auto_release)
                        thread.daemon = True
                        thread.start()
                        
                        # Update the result message
                        if result.get('success'):
                            result['message'] = f'{button_name} button held for {duration} seconds'
                    
                    return result
                    
                except Exception as e:
                    # FALLBACK: Direct file communication with BizHawk
                    print(f"Flask hold endpoint failed ({e}), using direct file communication...")
                    
                    try:
                        # Convert duration to frames (60 FPS)
                        if duration == -1:
                            frames = -1
                        else:
                            frames = max(1, int(duration * 60))
                        
                        # Write command directly to BizHawk command file
                        command = f"HOLD {button_name} {frames}"
                        with open("bizhawk_commands.txt", "w") as f:
                            f.write(command)
                        
                        # Wait for response
                        import time
                        time.sleep(0.2)
                        
                        # Check response file
                        try:
                            with open("bizhawk_responses.txt", "r") as f:
                                response_text = f.read().strip()
                            
                            if "OK" in response_text:
                                # Set up auto-release if duration specified
                                if duration > 0:
                                    import threading
                                    
                                    def auto_release():
                                        time.sleep(duration)
                                        try:
                                            with open("bizhawk_commands.txt", "w") as f:
                                                f.write(f"RELEASE {button_name}")
                                        except:
                                            pass
                                    
                                    thread = threading.Thread(target=auto_release)
                                    thread.daemon = True
                                    thread.start()
                                
                                return {
                                    "success": True,
                                    "message": f"{button_name} button held for {duration} seconds (direct)" if duration > 0 else f"{button_name} button held indefinitely (direct)"
                                }
                            else:
                                return {
                                    "success": False,
                                    "message": f"Failed to hold {button_name}: {response_text}"
                                }
                        
                        except FileNotFoundError:
                            return {
                                "success": False,
                                "message": "BizHawk not connected (no response file)"
                            }
                    
                    except Exception as file_error:
                        return {
                            "error": f"Both Flask API and direct file communication failed: {str(file_error)}"
                        }
            
            elif function_name == "release_button":
                response = requests.post(f"{base_url}/release/{arguments['button_name']}", timeout=5)
                return response.json()
            
            elif function_name == "take_screenshot":
                response = requests.get(f"{base_url}/screenshot-ocr?regions=true", timeout=10)
                return response.json()
            
            elif function_name == "get_status":
                response = requests.get(f"{base_url}/status", timeout=5)
                return response.json()
            
            elif function_name == "launch_and_connect":
                response = requests.post(f"{base_url}/launch", timeout=10)
                return response.json()
            
            elif function_name == "skip_intro":
                response = requests.post(f"{base_url}/skip-intro", timeout=30)
                return response.json()
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": f"Cannot connect to Flask server on port {self.flask_port}. Make sure it's running."}
        except Exception as e:
            return {"error": f"Function call failed: {str(e)}"}
    
    async def execute_command_sequence(self, commands: List[Dict]) -> Dict:
        """Execute a sequence of commands"""
        self.command_queue.queue.clear()  # Clear any existing queue
        
        for cmd in commands:
            action = cmd.get("action")
            button = cmd.get("button")
            duration = cmd.get("duration", 1)
            
            if action == "press":
                self.command_queue.add_command("press_button", button_name=button)
            elif action == "hold":
                self.command_queue.add_command("hold_button", button_name=button, duration=duration)
            elif action == "release":
                self.command_queue.add_command("release_button", button_name=button)
            elif action == "wait":
                self.command_queue.add_command("wait", duration=duration)
            elif action == "screenshot":
                self.command_queue.add_command("take_screenshot")
        
        results = await self.command_queue.execute_queue()
        
        success_count = sum(1 for r in results if r.get('success', False))
        total_commands = len(results)
        
        return {
            "success": success_count == total_commands,
            "message": f"Executed {success_count}/{total_commands} commands successfully",
            "results": results
        }
    
    async def chat_with_llm(self, user_message: str) -> str:
        """Send message to LLM and handle function calls"""
        
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Enhanced system message
        system_message = {
            "role": "system",
            "content": """You are an AI assistant that can control a SNES emulator running Final Fantasy III.

IMPORTANT: For complex multi-step commands, use execute_command_sequence instead of individual function calls.

Available functions:
- press_button(button_name): Single button press
- hold_button(button_name, duration): Hold button for duration (or -1 for indefinite)
- release_button(button_name): Release a held button
- take_screenshot(): Capture screen with OCR
- get_status(): Check emulator status
- launch_and_connect(): Start BizHawk and connect
- skip_intro(): Automated FF3 intro skip
- execute_command_sequence(commands): Execute multiple commands in sequence

For multi-step requests like "go up for 3 seconds then go left", use execute_command_sequence with:
[
  {"action": "hold", "button": "Up", "duration": 3},
  {"action": "release", "button": "Up"},
  {"action": "wait", "duration": 0.2},
  {"action": "press", "button": "Left"}
]

Always be helpful and explain what you're doing. Take screenshots when you need to see the current game state."""
        }
        
        messages = [system_message] + self.conversation_history
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
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
                    
                    # Special handling for command sequences
                    if function_name == "execute_command_sequence":
                        result = await self.execute_command_sequence(function_args.get("commands", []))
                    else:
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

async def main():
    """Main chat loop"""
    print("🎮 Enhanced SNES Emulator AI Chat")
    print("=" * 50)
    print("Features:")
    print("✅ Fixed hold button functionality with proper duration support")
    print("✅ Multi-command sequences: 'go up for 3 seconds then go left'") 
    print("✅ Auto port detection and better error handling")
    print("✅ Launch, connect, and intro skip automation")
    print()
    print("Checking for Flask server...")
    
    # Try both ports to find the right server
    bot = None
    for port in [5000, 5001]:
        try:
            response = requests.get(f"http://localhost:{port}/status", timeout=2)
            if response.status_code == 200:
                print(f"✅ Found Flask server on port {port}")
                bot = EmulatorChatBot(flask_port=port)
                break
        except:
            continue
    
    if not bot:
        print("❌ No Flask server found on ports 5000 or 5001")
        print("Please start your server with: python app.py")
        return
    
    print("Type 'quit' to exit\n")
    
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

if __name__ == "__main__":
    asyncio.run(main())