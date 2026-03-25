"""
BizHawk Controller Module - Lua Socket Version

Handles communication with BizHawk emulator via Lua socket script.
Compatible with BizHawk 2.10+ (bypasses BirdsEye compatibility issues).
"""

import time
import subprocess
import os
import socket
import threading
from pathlib import Path

class BizHawkControllerLua:
    def __init__(self, bizhawk_path=None, rom_path=None, lua_script_path=None, ip="127.0.0.1", port=43883):
        self.bizhawk_path = bizhawk_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\EmuHawk.exe"
        self.rom_path = rom_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\SNES\Final Fantasy III (USA).zip"
        self.lua_script_path = lua_script_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\bizhawk_lua_server.lua"
        self.ip = ip
        self.port = port
        self.socket = None
        self.process = None
        
    def launch_bizhawk(self):
        """Launch BizHawk with the specified ROM"""
        try:
            if not os.path.exists(self.bizhawk_path):
                raise FileNotFoundError(f"BizHawk not found at: {self.bizhawk_path}")
                
            if not os.path.exists(self.rom_path):
                raise FileNotFoundError(f"ROM not found at: {self.rom_path}")
            
            print(f"Launching BizHawk with ROM: {self.rom_path}")
            
            # Launch BizHawk with the ROM
            self.process = subprocess.Popen([
                self.bizhawk_path,
                self.rom_path
            ])
            
            # Wait a moment for BizHawk to start
            print("Waiting for BizHawk to start...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"Error launching BizHawk: {e}")
            return False
    
    def connect(self, max_retries=10, retry_delay=2):
        """Connect to BizHawk via Lua socket"""
        print("🔧 MANUAL SETUP REQUIRED:")
        print("1. In BizHawk, go to: Tools -> Lua Console")
        print("2. In Lua Console, click 'Script' -> 'Open Script'")
        print(f"3. Select the file: {self.lua_script_path}")
        print("4. The script will start the socket server")
        print("5. You should see: 'Lua socket server started on 127.0.0.1:43883'")
        print("6. Then this Python script will connect automatically")
        print()
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to BizHawk Lua server (attempt {attempt + 1}/{max_retries})...")
                print(f"Connecting to {self.ip}:{self.port}")
                
                # Create socket and connect
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5)
                self.socket.connect((self.ip, self.port))
                
                # Test connection with ping
                self._send_command("PING")
                response = self._receive_response()
                
                if response == "PONG":
                    print("Successfully connected to BizHawk Lua server!")
                    return True
                else:
                    print(f"Unexpected response: {response}")
                    
            except socket.timeout:
                print(f"Connection attempt {attempt + 1} timed out")
            except ConnectionRefusedError:
                print(f"Connection attempt {attempt + 1} refused - Lua server not running")
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                
            if self.socket:
                self.socket.close()
                self.socket = None
                
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                    
        print("Failed to connect to BizHawk Lua server after all attempts")
        print("\n🔧 TROUBLESHOOTING:")
        print("- Make sure BizHawk is running")
        print("- Load the Lua script in BizHawk's Lua Console")
        print("- Check that the script shows 'server started' message")
        print("- Ensure no firewall is blocking the connection")
        return False
    
    def disconnect(self):
        """Close connection to BizHawk"""
        if self.socket:
            try:
                self.socket.close()
                self.socket = None
                print("Disconnected from BizHawk Lua server")
            except Exception as e:
                print(f"Error disconnecting: {e}")
    
    def _send_command(self, command):
        """Send command to Lua server"""
        if not self.socket:
            raise ConnectionError("Not connected to BizHawk Lua server")
        
        try:
            self.socket.send((command + "\n").encode())
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def _receive_response(self, timeout=5):
        """Receive response from Lua server"""
        if not self.socket:
            raise ConnectionError("Not connected to BizHawk Lua server")
        
        try:
            self.socket.settimeout(timeout)
            data = self.socket.recv(1024).decode().strip()
            return data
        except socket.timeout:
            return "TIMEOUT"
        except Exception as e:
            print(f"Error receiving response: {e}")
            return "ERROR"
    
    def press_button(self, button, duration=0.1):
        """Press a controller button for specified duration"""
        if not self.is_connected():
            raise ConnectionError("Not connected to BizHawk Lua server")
            
        try:
            # Convert duration to frames (assuming 60 FPS)
            frames = max(1, int(duration * 60))
            
            # Send press command
            command = f"PRESS {button} {frames}"
            success = self._send_command(command)
            
            if not success:
                return False
                
            # Wait for response
            response = self._receive_response()
            
            if response == "OK":
                print(f"Pressed {button} for {frames} frames")
                return True
            else:
                print(f"Button press failed: {response}")
                return False
            
        except Exception as e:
            print(f"Error pressing {button}: {e}")
            return False
    
    def press_a(self, duration=0.1):
        """Press the A button"""
        return self.press_button('A', duration)
    
    def press_b(self, duration=0.1):
        """Press the B button"""
        return self.press_button('B', duration)
    
    def press_start(self, duration=0.1):
        """Press the Start button"""
        return self.press_button('Start', duration)
    
    def press_select(self, duration=0.1):
        """Press the Select button"""
        return self.press_button('Select', duration)
    
    def is_connected(self):
        """Check if connected to BizHawk Lua server"""
        if not self.socket:
            return False
            
        try:
            # Test connection with ping
            self._send_command("PING")
            response = self._receive_response(timeout=2)
            return response == "PONG"
        except:
            return False
    
    def get_status(self):
        """Get emulator status"""
        if not self.is_connected():
            return "DISCONNECTED"
            
        try:
            self._send_command("STATUS")
            response = self._receive_response()
            return response
        except:
            return "ERROR"
    
    def cleanup(self):
        """Clean up resources"""
        self.disconnect()
        if self.process:
            try:
                # Don't force kill BizHawk, let it close naturally
                pass
            except Exception as e:
                print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    # Basic test
    controller = BizHawkControllerLua()
    
    print("Testing BizHawk Lua Socket Controller...")
    print("This version bypasses BirdsEye and uses Lua scripting instead")
    print("Compatible with BizHawk 2.10+")
    print()
    
    # Launch BizHawk
    print("Step 1: Launch BizHawk...")
    if controller.launch_bizhawk():
        print("✅ BizHawk launched successfully")
    else:
        print("❌ Failed to launch BizHawk")
        exit(1)
    
    print("\nStep 2: Load Lua script manually...")
    print("Please follow the instructions that will be shown during connection")
    input("Press Enter when you're ready to connect...")
    
    # Connect
    if controller.connect():
        print("✅ Connected successfully!")
        
        # Test pressing A button
        print("\nStep 3: Testing A button press...")
        if controller.press_a():
            print("✅ A button press successful")
        else:
            print("❌ A button press failed")
        
        # Get status
        status = controller.get_status()
        print(f"Emulator status: {status}")
        
        time.sleep(2)
        controller.cleanup()
    else:
        print("❌ Failed to connect")
        controller.cleanup()