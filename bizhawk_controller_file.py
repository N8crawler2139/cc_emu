"""
BizHawk Controller Module - File-based Communication Version

Uses file-based communication instead of sockets for better BizHawk compatibility.
Compatible with all BizHawk versions that support Lua scripting.
"""

import time
import subprocess
import os
from pathlib import Path
from ff6_game_state import FF6GameStateReader

class BizHawkControllerFile:
    def __init__(self, bizhawk_path=None, rom_path=None, lua_script_path=None, load_slot=None):
        self.bizhawk_path = bizhawk_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\EmuHawk.exe"
        self.rom_path = rom_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\SNES\Final Fantasy III (USA).zip"
        self.lua_script_path = lua_script_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\Lua\ff6_agent.lua"
        self.command_file = "bizhawk_commands.txt"
        self.response_file = "bizhawk_responses.txt"
        self.process = None
        self.connected = False
        self.load_slot = load_slot  # Quicksave slot to load on launch (1-10)
        self.game_state_reader = FF6GameStateReader()
        
    def launch_bizhawk(self):
        """Launch BizHawk with the specified ROM"""
        try:
            if not os.path.exists(self.bizhawk_path):
                raise FileNotFoundError(f"BizHawk not found at: {self.bizhawk_path}")
                
            if not os.path.exists(self.rom_path):
                raise FileNotFoundError(f"ROM not found at: {self.rom_path}")
            
            print(f"Launching BizHawk with ROM: {self.rom_path}")
            
            # Launch BizHawk with the ROM and auto-load Lua script
            # ROM must be LAST argument per BizHawk docs
            # Use our project dir as cwd so Lua file I/O lands here
            project_dir = os.path.dirname(os.path.abspath(__file__))
            args = [
                self.bizhawk_path,
                "--lua", self.lua_script_path,
            ]
            if self.load_slot is not None:
                args.extend(["--load-slot", str(self.load_slot)])
            args.append(self.rom_path)
            self.process = subprocess.Popen(args, cwd=project_dir)
            
            # Wait a moment for BizHawk to start
            print("Waiting for BizHawk to start...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"Error launching BizHawk: {e}")
            return False
    
    def connect(self, max_retries=10, retry_delay=2):
        """Connect to BizHawk via file communication"""
        print("MANUAL SETUP REQUIRED:")
        print("1. In BizHawk, go to: Tools -> Lua Console")
        print("2. In Lua Console, click 'Script' -> 'Open Script'")
        print(f"3. Select the file: {self.lua_script_path}")
        print("4. The script will initialize file communication")
        print("5. You should see: 'File communication initialized'")
        print("6. Then this Python script will connect automatically")
        print()
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect via file communication (attempt {attempt + 1}/{max_retries})...")
                
                # Check if response file exists and contains "READY"
                if os.path.exists(self.response_file):
                    with open(self.response_file, 'r') as f:
                        response = f.read().strip()
                    
                    if response == "READY":
                        # Test connection with ping
                        self._send_command("PING")
                        time.sleep(0.5)  # Give Lua time to process
                        
                        ping_response = self._receive_response()
                        if ping_response == "PONG":
                            print("Successfully connected to BizHawk file communication!")
                            self.connected = True
                            # Clear response file after successful connection
                            self._clear_response_file()
                            return True
                        else:
                            print(f"Ping test failed, got: {ping_response}")
                    else:
                        print(f"Response file exists but contains: {response}")
                        # Clear stale response and retry
                        self._clear_response_file()
                        time.sleep(1)
                else:
                    print("Response file not found - Lua script may not be running")
                    
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                    
        print("Failed to connect to BizHawk after all attempts")
        print("\nTROUBLESHOOTING:")
        print("- Make sure BizHawk is running")
        print("- Load the bizhawk_simple_server.lua script in BizHawk's Lua Console")
        print("- Check that the script shows 'File communication initialized'")
        print("- Verify bizhawk_responses.txt file exists and contains 'READY'")
        return False
    
    def disconnect(self):
        """Disconnect from BizHawk"""
        try:
            if self.connected:
                self._send_command("STOP")
                self.connected = False
            print("Disconnected from BizHawk file communication")
        except Exception as e:
            print(f"Error disconnecting: {e}")
            self.connected = False
    
    def _send_command(self, command):
        """Send command via file"""
        try:
            with open(self.command_file, 'w') as f:
                f.write(command)
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def _clear_response_file(self):
        """Clear the response file"""
        try:
            with open(self.response_file, 'w') as f:
                f.write("")
        except Exception as e:
            print(f"Error clearing response file: {e}")
    
    def _receive_response(self, timeout=5):
        """Receive response via file"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if os.path.exists(self.response_file):
                    with open(self.response_file, 'r') as f:
                        response = f.read().strip()
                    
                    if response and response not in ["READY", ""]:
                        # Clear the response file after reading
                        self._clear_response_file()
                        return response
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                print(f"Error receiving response: {e}")
                return "ERROR"
        
        return "TIMEOUT"
    
    def press_button(self, button, duration=0.1):
        """Press a controller button for specified duration"""
        if not self.is_connected():
            print(f"Connection check failed - connected flag is: {self.connected}")
            return False
            
        try:
            # Convert duration to frames (assuming 60 FPS)
            frames = max(1, int(duration * 60))
            
            # Send press command
            command = f"PRESS {button} {frames}"
            print(f"Sending command: {command}")
            success = self._send_command(command)
            
            if not success:
                print("Failed to send command")
                return False
                
            # Wait for response with shorter timeout since commands are now queued
            print("Waiting for response...")
            response = self._receive_response(timeout=5)
            print(f"Received response: {response}")
            
            if response.startswith("OK"):
                print(f"Queued {button} press for {frames} frames")
                return True
            else:
                print(f"Button press failed: {response}")
                return False
            
        except Exception as e:
            print(f"Error pressing {button}: {e}")
            return False

    def hold_button(self, button, duration=-1):
        """Hold a controller button (indefinite if duration=-1, or specific duration in seconds)"""
        if not self.is_connected():
            print(f"Connection check failed - connected flag is: {self.connected}")
            return False
            
        try:
            # Convert duration to frames for finite holds, use -1 for infinite
            if duration == -1:
                frames = -1
            else:
                frames = max(1, int(duration * 60))
            
            command = f"HOLD {button} {frames}"
            print(f"Sending command: {command}")
            success = self._send_command(command)
            
            if not success:
                print("Failed to send command")
                return False
                
            response = self._receive_response(timeout=5)
            print(f"Received response: {response}")
            
            if response.startswith("OK"):
                if duration == -1:
                    print(f"Started holding {button} indefinitely")
                else:
                    print(f"Holding {button} for {duration} seconds")
                return True
            else:
                print(f"Button hold failed: {response}")
                return False
            
        except Exception as e:
            print(f"Error holding {button}: {e}")
            return False

    def release_button(self, button):
        """Release a held controller button"""
        if not self.is_connected():
            print(f"Connection check failed - connected flag is: {self.connected}")
            return False
            
        try:
            command = f"RELEASE {button}"
            print(f"Sending command: {command}")
            success = self._send_command(command)
            
            if not success:
                print("Failed to send command")
                return False
                
            response = self._receive_response(timeout=5)
            print(f"Received response: {response}")
            
            if response.startswith("OK"):
                print(f"Released {button}")
                return True
            else:
                print(f"Button release failed: {response}")
                return False
            
        except Exception as e:
            print(f"Error releasing {button}: {e}")
            return False
    
    # Action buttons
    def press_a(self, duration=0.1):
        """Press the A button"""
        return self.press_button('A', duration)
    
    def press_b(self, duration=0.1):
        """Press the B button"""
        return self.press_button('B', duration)
        
    def press_x(self, duration=0.1):
        """Press the X button"""
        return self.press_button('X', duration)
        
    def press_y(self, duration=0.1):
        """Press the Y button"""
        return self.press_button('Y', duration)
    
    # D-Pad buttons
    def press_up(self, duration=0.1):
        """Press the Up button"""
        return self.press_button('Up', duration)
        
    def press_down(self, duration=0.1):
        """Press the Down button"""
        return self.press_button('Down', duration)
        
    def press_left(self, duration=0.1):
        """Press the Left button"""
        return self.press_button('Left', duration)
        
    def press_right(self, duration=0.1):
        """Press the Right button"""
        return self.press_button('Right', duration)
    
    # Shoulder buttons
    def press_l(self, duration=0.1):
        """Press the L button"""
        return self.press_button('L', duration)
        
    def press_r(self, duration=0.1):
        """Press the R button"""
        return self.press_button('R', duration)
    
    # System buttons
    def press_start(self, duration=0.1):
        """Press the Start button"""
        return self.press_button('Start', duration)
    
    def press_select(self, duration=0.1):
        """Press the Select button"""
        return self.press_button('Select', duration)
    
    def is_connected(self):
        """Check if connected to BizHawk"""
        return self.connected

    def get_game_state(self):
        """Read current FF6 game state from the Lua script's JSON output."""
        return self.game_state_reader.read()

    def request_game_state(self):
        """Send GAMESTATE command to force an immediate state dump, then read it."""
        if not self.is_connected():
            return None
        self._send_command("GAMESTATE")
        time.sleep(0.3)
        self._receive_response(timeout=2)
        return self.game_state_reader.read(force=True)

    def read_memory(self, address, count=1):
        """Read raw memory bytes from emulator. Returns list of byte values."""
        if not self.is_connected():
            return None
        self._send_command(f"READMEM {address} {count}")
        response = self._receive_response(timeout=3)
        if response and response.startswith("MEM:"):
            values_str = response[4:]
            return [int(v) for v in values_str.split(",")]
        return None

    # --- High-level agent commands (Lua handles execution) ---

    def agent_on(self):
        """Enable the Lua agent (autonomous play)."""
        self._send_command("AGENT ON")
        return self._receive_response(timeout=2)

    def agent_off(self):
        """Disable the Lua agent (manual control)."""
        self._send_command("AGENT OFF")
        return self._receive_response(timeout=2)

    def set_walk_direction(self, direction):
        """Set the agent's walk direction (Up/Down/Left/Right)."""
        self._send_command(f"WALK {direction}")
        return self._receive_response(timeout=2)

    def manual_battle_on(self):
        """Enable manual battle mode (only Python commands, no autonomous)."""
        self._send_command("MANUAL BATTLE ON")
        return self._receive_response(timeout=2)

    def manual_battle_off(self):
        """Disable manual battle mode (autonomous AI decides)."""
        self._send_command("MANUAL BATTLE OFF")
        return self._receive_response(timeout=2)

    def battle_command(self, cmd, spell="none", target="enemy", slot=0):
        """Send a battle command. E.g. battle_command('MagiTek', 'BoltBeam', 'enemy', 0)"""
        self._send_command(f"BATTLE {cmd} {spell} {target} {slot}")
        return self._receive_response(timeout=2)

    def wait_for_battle(self, timeout=60):
        """Block until enemies are detected (battle started)."""
        import time
        start = time.time()
        while time.time() - start < timeout:
            v = self.read_memory(0x3A77, 1)
            if v and v[0] > 0 and v[0] < 10:
                return v[0]
            time.sleep(1)
        return 0

    def wait_for_menu_ready(self, timeout=10):
        """Block until battle menu is open and ready for input."""
        import time
        start = time.time()
        while time.time() - start < timeout:
            menu = self.read_memory(0x7BCA, 1)
            disabled = self.read_memory(0x628B, 1)
            if menu and disabled and menu[0] != 0 and disabled[0] == 0:
                return True
            time.sleep(0.3)
        return False
    
    def get_status(self):
        """Get emulator status"""
        if not self.is_connected():
            return {"status": "DISCONNECTED", "queue_length": 0, "frame": 0}
            
        try:
            self._send_command("STATUS")
            response = self._receive_response()
            
            # Parse response like "CONNECTED:RUNNING:FRAME1234:QUEUE2"
            if response.startswith("CONNECTED"):
                parts = response.split(":")
                frame = 0
                queue_length = 0
                
                for part in parts:
                    if part.startswith("FRAME"):
                        frame = int(part[5:])
                    elif part.startswith("QUEUE"):
                        queue_length = int(part[5:])
                
                return {
                    "status": "CONNECTED",
                    "queue_length": queue_length,
                    "frame": frame
                }
            else:
                return {"status": response, "queue_length": 0, "frame": 0}
        except Exception as e:
            print(f"Error getting status: {e}")
            return {"status": "ERROR", "queue_length": 0, "frame": 0}
    
    def cleanup(self):
        """Clean up resources"""
        self.disconnect()
        
        # Clean up communication files
        for file in [self.command_file, self.response_file]:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
                
        if self.process:
            try:
                # Don't force kill BizHawk, let it close naturally
                pass
            except Exception as e:
                print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    # Basic test
    controller = BizHawkControllerFile()
    
    print("Testing BizHawk File Communication Controller...")
    print("This version uses file-based communication (no sockets needed)")
    print("Compatible with all BizHawk versions that support Lua")
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