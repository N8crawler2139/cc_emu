"""
FF6 Unified Game Agent

A single state-machine that plays FF6 by reading memory state
and making decisions. Uses memory for everything possible,
LLM only for strategic field navigation decisions.

States:
  FIELD    - Walking around, exploring (LLM decides direction)
  DIALOG   - Text on screen, press A to advance
  BATTLE   - In combat, press A deterministically
  MENU     - In game menu (X button), handle or close
  VICTORY  - Battle won, press A through rewards
  UNKNOWN  - Can't determine state, try A or wait

The agent reads bizhawk_gamestate.json every cycle and decides
what button to press based purely on memory state.
"""

import json
import time
import threading
from ff6_game_state import FF6GameStateReader
from bizhawk_controller_file import BizHawkControllerFile


class GameState:
    """Enum-like for game states."""
    FIELD = "field"
    DIALOG = "dialog"
    BATTLE = "battle"
    BATTLE_MENU = "battle_menu"
    BATTLE_ANIMATING = "battle_animating"
    VICTORY = "victory"
    MENU = "menu"
    TRANSITION = "transition"
    UNKNOWN = "unknown"


class FF6Agent:
    """
    Unified game-playing agent for FF6.

    Memory-driven state machine with LLM fallback for exploration.
    """

    def __init__(self, controller):
        self.ctrl = controller
        self.state_reader = FF6GameStateReader()
        self.running = False
        self._thread = None

        # State tracking
        self.current_state = GameState.UNKNOWN
        self.prev_state = GameState.UNKNOWN
        self.prev_position = None
        self.stuck_count = 0
        self.action_count = 0
        self.battles_won = 0
        self.state_history = []

        # Field navigation: default direction to walk
        # Updated by LLM or walkthrough logic
        self.walk_direction = "Up"
        self.walk_goal = "Walk north through Narshe"

        # Logging
        self.log = []
        self.max_log = 300

        # Timing
        self.CYCLE_DELAY = 0.25        # Time between action cycles
        self.BATTLE_PRESS_DELAY = 0.15 # Time between battle A-presses
        self.DIALOG_PRESS_DELAY = 0.20 # Time between dialog A-presses

    def _log(self, msg):
        """Log a message."""
        entry = {"time": time.time(), "msg": msg}
        self.log.append(entry)
        if len(self.log) > self.max_log:
            self.log = self.log[-self.max_log:]
        print(f"[Agent] {msg}")

    def _read_state(self):
        """Read the current game state from JSON file."""
        try:
            with open("bizhawk_gamestate.json") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def detect_state(self, data):
        """
        Determine current game state from memory data.

        This is the core state detection logic. Uses position,
        battle_menu, and other memory flags.
        """
        if not data:
            return GameState.UNKNOWN

        x = data.get("position", {}).get("x", -1)
        y = data.get("position", {}).get("y", -1)
        battle_menu = data.get("battle_menu", 0)
        menu_flag = data.get("menu_flag", 0)
        game_mode = data.get("game_mode", 0)

        # Battle detection: position x == 0 during battle
        if x == 0:
            if battle_menu > 0 and battle_menu < 200:
                # Menu is active -- a character can act
                return GameState.BATTLE_MENU
            else:
                # Animation playing or waiting for ATB
                return GameState.BATTLE_ANIMATING

        # Field state: position x > 0
        if x > 0:
            # Check if dialog is showing
            # In FF6, when dialog is active the player can't move
            # We detect this by checking if position hasn't changed
            # despite our input, but that requires history.
            # For now, treat field as field and handle dialog
            # via the stuck detection.
            return GameState.FIELD

        return GameState.UNKNOWN

    def _press(self, button, delay=None):
        """Press a button."""
        self.ctrl.press_button(button, 0.1)
        if delay:
            time.sleep(delay)

    def handle_field(self, data):
        """Handle field state: walk in current direction."""
        pos = data.get("position", {})
        current_pos = (pos.get("x", 0), pos.get("y", 0))

        # Check if we're stuck
        if current_pos == self.prev_position:
            self.stuck_count += 1
        else:
            self.stuck_count = 0

        self.prev_position = current_pos

        if self.stuck_count > 3:
            # Probably in dialog or blocked by obstacle
            if self.stuck_count <= 6:
                # First: try pressing A (dialog advance)
                self._log(f"Stuck at {current_pos} ({self.stuck_count}x), pressing A")
                self._press("A", self.DIALOG_PRESS_DELAY)
            elif self.stuck_count <= 10:
                # Then: try pressing B (exit menu)
                self._log(f"Still stuck ({self.stuck_count}x), pressing B")
                self._press("B", self.DIALOG_PRESS_DELAY)
            elif self.stuck_count <= 20:
                # Try alternate directions to get around obstacles
                # Cycle: Left, Right, Up (to unstick from walls)
                alt_dirs = ["Left", "Right", "Up", "Left", "Right"]
                idx = (self.stuck_count - 11) % len(alt_dirs)
                alt_dir = alt_dirs[idx]
                self._log(f"Obstacle? Trying {alt_dir} ({self.stuck_count}x)")
                self.ctrl.hold_button(alt_dir, duration=0.5)
                time.sleep(0.3)
            else:
                # Reset stuck counter and go back to primary direction
                self._log(f"Resetting stuck counter, back to {self.walk_direction}")
                self.stuck_count = 0
            return

        # Normal walking
        self._log(f"Field: walk {self.walk_direction} (pos {current_pos})")
        self.ctrl.hold_button(self.walk_direction, duration=0.5)
        time.sleep(0.3)

    def handle_battle_menu(self, data):
        """Handle battle with active menu: press A to select first option."""
        battle_menu = data.get("battle_menu", 0)
        self._log(f"Battle: menu active (menu={battle_menu}), press A")
        self._press("A", self.BATTLE_PRESS_DELAY)

    def handle_battle_animating(self, data):
        """Handle battle animation: wait briefly."""
        time.sleep(0.2)

    def handle_unknown(self, data):
        """Handle unknown state: press A and hope."""
        self._log("Unknown state, pressing A")
        self._press("A", self.CYCLE_DELAY)

    def step(self):
        """One step of the game loop."""
        data = self._read_state()
        state = self.detect_state(data)

        # Track state transitions
        if state != self.current_state:
            self._log(f"State: {self.current_state} -> {state}")
            self.prev_state = self.current_state
            self.current_state = state

            # Track battles won
            if self.prev_state in (GameState.BATTLE_MENU, GameState.BATTLE_ANIMATING) \
               and state == GameState.FIELD:
                self.battles_won += 1
                self._log(f"*** BATTLE WON (total: {self.battles_won}) ***")

        # Dispatch to handler
        if state == GameState.FIELD:
            self.handle_field(data)
        elif state == GameState.BATTLE_MENU:
            self.handle_battle_menu(data)
        elif state == GameState.BATTLE_ANIMATING:
            self.handle_battle_animating(data)
        else:
            self.handle_unknown(data)

        self.action_count += 1

    def _game_loop(self):
        """Main game loop running in a thread."""
        self._log("Game loop started")
        while self.running:
            try:
                self.step()
                time.sleep(self.CYCLE_DELAY)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self._log(f"Error: {e}")
                time.sleep(1)
        self._log("Game loop stopped")

    def start(self):
        """Start the agent in a background thread."""
        if self.running:
            return False
        self.running = True
        self._thread = threading.Thread(target=self._game_loop, daemon=True)
        self._thread.start()
        self._log("Agent started")
        return True

    def stop(self):
        """Stop the agent."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self._log("Agent stopped")
        return True

    def get_status(self):
        """Get agent status for monitoring."""
        return {
            "running": self.running,
            "state": self.current_state,
            "action_count": self.action_count,
            "battles_won": self.battles_won,
            "walk_direction": self.walk_direction,
            "walk_goal": self.walk_goal,
            "stuck_count": self.stuck_count,
            "recent_log": [e["msg"] for e in self.log[-20:]],
        }


# Singleton for Flask integration
_agent = None

def get_agent(controller=None):
    global _agent
    if _agent is None and controller:
        _agent = FF6Agent(controller)
    return _agent

def reset_agent():
    global _agent
    if _agent and _agent.running:
        _agent.stop()
    _agent = None


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("  FF6 Game Agent - Standalone Runner")
    print("=" * 50)

    ctrl = BizHawkControllerFile()

    # Check if we can read game state
    reader = FF6GameStateReader()
    state = reader.read()
    if state:
        print(f"Game state found: Map {state.map_id}, Pos {state.position}")
        print(state.party_summary())
    else:
        print("No game state. Make sure BizHawk + Lua script are running.")
        sys.exit(1)

    ctrl.connected = True

    agent = FF6Agent(ctrl)
    agent.start()

    try:
        while agent.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        agent.stop()

    status = agent.get_status()
    print(f"\nActions: {status['action_count']}")
    print(f"Battles won: {status['battles_won']}")
