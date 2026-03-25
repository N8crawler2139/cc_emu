"""
BizHawk Controller Module

Handles communication with BizHawk emulator via Birds Eye library.
Provides controller input functions and connection management.
"""

import time
import subprocess
import os
from pathlib import Path
from birdseyelib import Client, ControllerInput, SNESJoypad

class BizHawkController:
    def __init__(self, bizhawk_path=None, rom_path=None, ip="127.0.0.1", port=43882):
        self.bizhawk_path = bizhawk_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\EmuHawk.exe"
        self.rom_path = rom_path or r"C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\SNES\Final Fantasy III (USA).zip"
        self.ip = ip
        self.port = port
        self.client = None
        self.controller = None
        self.joypad = None
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
    
    def connect(self, max_retries=5, retry_delay=3):
        """Connect to BizHawk via Birds Eye"""
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to BizHawk (attempt {attempt + 1}/{max_retries})...")
                print(f"Connecting to {self.ip}:{self.port}")
                
                # Create client and connect
                self.client = Client(self.ip, self.port)
                self.client.connect()
                
                if self.client.is_connected():
                    # Initialize controller input and SNES joypad
                    self.controller = ControllerInput(self.client)
                    self.joypad = SNESJoypad()
                    self.controller.set_joypad(self.joypad)
                    
                    print("Successfully connected to BizHawk!")
                    return True
                else:
                    print(f"Connection attempt {attempt + 1} failed - not connected")
                    
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                    
        print("Failed to connect to BizHawk after all attempts")
        print("\n🔧 MANUAL SETUP REQUIRED:")
        print("1. In BizHawk, go to: Tools -> External Tool -> BirdsEye")
        print("2. In the BirdsEye window that opens, click 'Connect'")
        print("3. You should see 'Server started on port 43882'")
        print("4. Then try connecting from Python again")
        print("5. The BirdsEye window must remain open during automation")
        return False
    
    def disconnect(self):
        """Close connection to BizHawk"""
        if self.client:
            try:
                self.client.close()
                self.client = None
                self.controller = None
                self.joypad = None
                print("Disconnected from BizHawk")
            except Exception as e:
                print(f"Error disconnecting: {e}")
    
    def press_button(self, button, duration=0.1):
        """Press a controller button for specified duration"""
        if not self.is_connected():
            raise ConnectionError("Not connected to BizHawk")
            
        try:
            # Set the button to pressed state
            setattr(self.joypad, button, True)
            self.controller.set_controller_input(self.joypad)
            self.client.advance_frame()
            
            # Wait for the specified duration (in terms of frames)
            frames_to_wait = max(1, int(duration * 60))  # Assuming 60 FPS
            for _ in range(frames_to_wait):
                self.client.advance_frame()
            
            # Release the button
            setattr(self.joypad, button, False)
            self.controller.set_controller_input(self.joypad)
            self.client.advance_frame()
            
            print(f"Pressed {button} for ~{frames_to_wait} frames")
            return True
            
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
        """Check if connected to BizHawk"""
        return self.client is not None and self.client.is_connected()
    
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
    controller = BizHawkController()
    
    print("Testing BizHawk controller...")
    print("1. Launch BizHawk manually")
    print("2. Load Final Fantasy III ROM")
    print("3. Go to Tools -> External Tool -> BirdsEye")
    print("4. Click 'Connect' in BirdsEye tool")
    print("5. Press Enter here to continue...")
    
    input("Press Enter when BizHawk is ready...")
    
    if controller.connect():
        print("Connected successfully!")
        
        # Test pressing A button
        print("Testing A button press...")
        controller.press_a()
        
        time.sleep(2)
        controller.cleanup()
    else:
        print("Failed to connect")