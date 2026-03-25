"""
Game Controller Module

Handles game-specific automation logic, starting with Final Fantasy III intro screen navigation.
"""

import time
from bizhawk_controller_file import BizHawkControllerFile as BizHawkController

class FF3GameController:
    def __init__(self, bizhawk_controller=None):
        self.bizhawk = bizhawk_controller or BizHawkController()
        
    def skip_intro_sequence(self, max_attempts=10):
        """
        Automate getting past the Final Fantasy III intro screens.
        
        This will repeatedly press A to skip through various intro screens:
        - Square logo
        - Game title screen
        - Opening story sequences
        - Until we reach the main menu or new game screen
        """
        if not self.bizhawk.is_connected():
            print("Error: Not connected to BizHawk")
            return False
            
        print("Starting Final Fantasy III intro skip sequence...")
        
        # Wait a moment for the ROM to fully load
        print("Waiting for ROM to load...")
        time.sleep(5)
        
        # Repeatedly press A to skip through intro screens
        for attempt in range(max_attempts):
            print(f"Intro skip attempt {attempt + 1}/{max_attempts}")
            
            # Press A to skip current screen
            success = self.bizhawk.press_a(duration=0.2)
            if not success:
                print("Failed to press A button")
                return False
                
            # Wait for screen transition
            time.sleep(2)
            
            # Optional: Could add screen detection logic here in the future
            # For now, we'll just press A multiple times to get through everything
            
        print("Intro skip sequence completed!")
        print("The game should now be past the intro screens.")
        print("You may need to manually navigate to start a new game.")
        
        return True
    
    def press_a_repeatedly(self, count=5, delay=1.5):
        """Press A button multiple times with delay"""
        if not self.bizhawk.is_connected():
            print("Error: Not connected to BizHawk")
            return False
            
        print(f"Pressing A button {count} times with {delay}s delays...")
        
        for i in range(count):
            print(f"Press {i + 1}/{count}")
            success = self.bizhawk.press_a(duration=0.2)
            if not success:
                print(f"Failed to press A on attempt {i + 1}")
                return False
                
            if i < count - 1:  # Don't sleep after the last press
                time.sleep(delay)
                
        return True
    
    def wait_and_start_game(self):
        """Wait a bit then try to start a new game"""
        print("Waiting before attempting to start new game...")
        time.sleep(3)
        
        # Try pressing Start button to access menu
        print("Pressing Start to access main menu...")
        self.bizhawk.press_start(duration=0.2)
        time.sleep(2)
        
        # Press A to select "New Game" (assuming it's the default option)
        print("Pressing A to select New Game...")
        self.bizhawk.press_a(duration=0.2)
        time.sleep(2)
        
        print("New game start sequence completed!")
        return True

def main():
    """Test the game controller independently"""
    print("Testing FF3 Game Controller...")
    
    # Create controller instance
    bizhawk = BizHawkController()
    game_controller = FF3GameController(bizhawk)
    
    try:
        # Launch BizHawk and connect
        print("Launching BizHawk...")
        if not bizhawk.launch_bizhawk():
            print("Failed to launch BizHawk")
            return
            
        print("Connecting to BizHawk...")
        if not bizhawk.connect():
            print("Failed to connect to BizHawk")
            return
            
        # Run the intro skip sequence
        game_controller.skip_intro_sequence()
        
        # Optional: Try to start a new game
        user_input = input("Try to start a new game? (y/n): ").lower()
        if user_input == 'y':
            game_controller.wait_and_start_game()
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleaning up...")
        bizhawk.cleanup()

if __name__ == "__main__":
    main()