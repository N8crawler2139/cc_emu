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
import base64
import io
from ff6_game_state import FF6GameStateReader
from bizhawk_controller_file import BizHawkControllerFile
from screenshot_ocr import ScreenshotOCR
from openai import OpenAI
from config import open_ai_apikey


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
        self.prev_map = None
        self.stuck_count = 0
        self.action_count = 0
        self.battles_won = 0
        self.maps_visited = set()
        self.state_history = []

        # Battle progress tracking
        self.battle_action_count = 0  # Actions taken in current battle
        self.battle_last_hp_hash = None  # Detect if damage is happening

        # Field navigation: default direction to walk
        # Updated by LLM vision assist when stuck
        self.walk_direction = "Up"
        self.walk_goal = "Walk north through Narshe"

        # Vision navigation assist
        self.screenshotter = ScreenshotOCR()
        self.llm_client = OpenAI(api_key=open_ai_apikey)
        self.last_vision_time = 0
        self.VISION_COOLDOWN = 8  # Min seconds between vision calls

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

    def ask_vision_for_direction(self):
        """
        Take a screenshot and ask GPT-4o-mini which direction to walk.
        Returns a direction string ("Up", "Down", "Left", "Right") or None.
        Only called when stuck -- uses vision to see the actual screen.
        """
        # Rate limit vision calls
        now = time.time()
        if now - self.last_vision_time < self.VISION_COOLDOWN:
            return None
        self.last_vision_time = now

        try:
            # Capture screenshot
            self.screenshotter.bizhawk_window = None
            image = self.screenshotter.capture_window()
            if not image:
                return None

            # Resize for efficiency
            w, h = image.size
            new_w = 512
            new_h = int(h * new_w / w)
            image = image.resize((new_w, new_h))

            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=80)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            "I'm playing Final Fantasy VI. My character is stuck and can't "
                            "move forward. Look at this screenshot and tell me which direction "
                            "I should walk to make progress. The character is the sprite in "
                            "the middle of the screen.\n\n"
                            "Reply with ONLY one word: Up, Down, Left, or Right."
                        )},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "low"
                        }}
                    ]
                }],
                temperature=0.1,
                max_tokens=10,
            )

            answer = response.choices[0].message.content
            if not answer:
                return None

            answer = answer.strip().capitalize()
            valid = {"Up", "Down", "Left", "Right"}
            # Extract direction from response (might say "Up." or "Go Up")
            for d in valid:
                if d.lower() in answer.lower():
                    self._log(f"Vision says: walk {d}")
                    return d

            self._log(f"Vision unclear: '{answer}'")
            return None

        except Exception as e:
            self._log(f"Vision error: {e}")
            return None

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
            elif self.stuck_count <= 15:
                # Try alternate directions to get around obstacles
                alt_dirs = ["Left", "Right", "Up", "Left", "Right"]
                idx = (self.stuck_count - 11) % len(alt_dirs)
                alt_dir = alt_dirs[idx]
                self._log(f"Obstacle? Trying {alt_dir} ({self.stuck_count}x)")
                self.ctrl.hold_button(alt_dir, duration=0.5)
                time.sleep(0.3)
            elif self.stuck_count <= 25:
                # Ask vision for help -- take screenshot, ask LLM
                vision_dir = self.ask_vision_for_direction()
                if vision_dir:
                    self._log(f"*** VISION ASSIST: walk {vision_dir} ***")
                    self.walk_direction = vision_dir
                    self.stuck_count = 0  # Reset and try new direction
                else:
                    # Vision didn't help, keep trying alternates
                    alt_dirs = ["Down", "Left", "Right", "Up"]
                    idx = (self.stuck_count - 16) % len(alt_dirs)
                    self.ctrl.hold_button(alt_dirs[idx], duration=0.8)
                    time.sleep(0.3)
            else:
                # Full reset
                self._log(f"Resetting stuck counter, back to {self.walk_direction}")
                self.stuck_count = 0
            return

        # Normal walking
        self._log(f"Field: walk {self.walk_direction} (pos {current_pos})")
        self.ctrl.hold_button(self.walk_direction, duration=0.5)
        time.sleep(0.3)

    def _party_needs_healing(self, data):
        """Check if any party member has critically low HP."""
        for char in data.get("characters", []):
            hp = char.get("hp", 0)
            hp_max = char.get("hp_max", 1)
            if hp_max > 0 and hp > 0 and (hp / hp_max) < 0.25:
                return True
        return False

    def _get_hp_hash(self, data):
        """Get a hash of all party HP values to detect battle progress."""
        hp_vals = []
        for c in data.get("characters", []):
            hp_vals.append(c.get("hp", 0))
        return tuple(hp_vals)

    def handle_battle_menu(self, data):
        """Handle battle with active menu.

        Key insight: if we press A and nothing changes for many cycles,
        we're probably stuck in a submenu (like empty Item list).
        Press B to back out and try again.
        """
        battle_menu = data.get("battle_menu", 0)
        self.battle_action_count += 1

        # Check if HP has changed since last check
        hp_hash = self._get_hp_hash(data)
        if hp_hash == self.battle_last_hp_hash:
            # No damage dealt or received
            if self.battle_action_count > 20:
                # Stuck in battle for 20+ actions with no progress
                # Press B to back out of whatever submenu we're in
                self._log(f"Battle stuck ({self.battle_action_count} actions, no damage)! Pressing B to back out")
                self._press("B", self.BATTLE_PRESS_DELAY)
                self.battle_action_count = 0  # Reset counter
                return
        else:
            # Progress! Reset counter
            self.battle_action_count = 0
            self.battle_last_hp_hash = hp_hash

        # Simple approach that actually works: press A.
        # If no progress after 20 actions, press B to escape submenus.
        # The A-mash cycles through: command select -> spell/attack -> target.
        # It occasionally selects Item by accident, but the B-escape catches it.
        self._log(f"Battle: press A (menu={battle_menu}, actions={self.battle_action_count})")
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
                self.battle_action_count = 0
                self.battle_last_hp_hash = None
                self._log(f"*** BATTLE WON (total: {self.battles_won}) ***")

            # Reset battle tracking when entering battle
            if state in (GameState.BATTLE_MENU, GameState.BATTLE_ANIMATING) \
               and self.prev_state == GameState.FIELD:
                self.battle_action_count = 0
                self.battle_last_hp_hash = None

        # Track map changes
        current_map = data.get("map_id") if data else None
        if current_map and current_map != self.prev_map and current_map > 0:
            self._log(f"*** MAP CHANGE: {self.prev_map} -> {current_map} ***")
            self.maps_visited.add(current_map)
            self.prev_map = current_map

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
        # Get current party HP
        data = self._read_state()
        party_hp = []
        if data:
            for c in data.get("characters", []):
                party_hp.append(f"{c.get('name','?')}:{c.get('hp',0)}/{c.get('hp_max',0)}")

        return {
            "running": self.running,
            "state": self.current_state,
            "action_count": self.action_count,
            "battles_won": self.battles_won,
            "walk_direction": self.walk_direction,
            "walk_goal": self.walk_goal,
            "stuck_count": self.stuck_count,
            "maps_visited": sorted(self.maps_visited),
            "current_map": self.prev_map,
            "party_hp": party_hp,
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
