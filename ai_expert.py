"""
AI Expert - Orchestrator for FF6 Expert Mode

Runs the Director + Pilot game loop:
1. Director analyzes state and sets goals (every ~10 seconds or on state change)
2. Pilot executes actions to achieve those goals (every ~1-2 seconds)
3. State is monitored for significant changes
4. Loop continues until stopped

Can be run standalone or controlled via Flask API.
"""

import time
import threading
import json
from bizhawk_controller_file import BizHawkControllerFile
from ff6_game_state import FF6GameStateReader
from ai_director import AIDirector
from ai_pilot import AIPilot


class AIExpert:
    """
    Orchestrator that runs the Director + Pilot loop.
    """

    # How often Director re-evaluates (seconds)
    DIRECTOR_INTERVAL = 12

    # Minimum time between Pilot actions (seconds)
    PILOT_MIN_INTERVAL = 0.5

    # Max Pilot actions before forcing Director re-eval
    PILOT_MAX_ACTIONS_PER_DIRECTIVE = 15

    def __init__(self, controller=None):
        """
        controller: BizHawkControllerFile instance.
                    If None, creates one (caller must connect it).
        """
        self.controller = controller or BizHawkControllerFile()
        self.director = AIDirector()
        self.pilot = AIPilot(self.controller)
        self.state_reader = FF6GameStateReader()

        self.running = False
        self._thread = None
        self._lock = threading.Lock()

        # Logging / monitoring
        self.log = []
        self.max_log = 200
        self.stats = {
            "director_calls": 0,
            "pilot_actions": 0,
            "errors": 0,
            "start_time": None,
            "last_directive": None,
            "last_action": None,
        }

    def _log(self, level, message):
        """Add a log entry."""
        entry = {
            "time": time.time(),
            "level": level,
            "message": message,
        }
        self.log.append(entry)
        if len(self.log) > self.max_log:
            self.log = self.log[-self.max_log:]

        # Also print to console
        prefix = {"info": "[*]", "action": "[>]", "director": "[D]",
                  "error": "[!]", "state": "[S]"}.get(level, "[?]")
        print(f"{prefix} {message}")

    def _game_loop(self):
        """Main game loop running in a thread."""
        self._log("info", "Expert AI game loop started")
        self.stats["start_time"] = time.time()

        last_director_time = 0
        pilot_actions_since_director = 0
        current_directive_text = "No directive yet. Explore and advance dialog."

        while self.running:
            try:
                # --- Director Phase ---
                now = time.time()
                need_director = (
                    now - last_director_time > self.DIRECTOR_INTERVAL
                    or pilot_actions_since_director >= self.PILOT_MAX_ACTIONS_PER_DIRECTIVE
                    or self.director.has_state_changed()
                )

                if need_director:
                    self._log("director", "Director analyzing game state...")
                    directive = self.director.get_directive(force=True)

                    if directive:
                        current_directive_text = self.director.format_for_pilot(directive)
                        self.stats["last_directive"] = directive
                        self.stats["director_calls"] += 1
                        self._log("director",
                                  f"Goal: {directive.get('goal', '?')}")
                        self._log("director",
                                  f"Situation: {directive.get('situation', '?')}")

                    last_director_time = now
                    pilot_actions_since_director = 0

                # --- Pilot Phase ---
                action, result = self.pilot.step(current_directive_text)

                self.stats["pilot_actions"] += 1
                self.stats["last_action"] = action
                pilot_actions_since_director += 1

                self._log("action",
                          f"{action['action']}({action.get('params', {})}) "
                          f"-> {result} | {action.get('reasoning', '')}")

                # Brief pause between actions
                time.sleep(self.PILOT_MIN_INTERVAL)

            except KeyboardInterrupt:
                self._log("info", "Keyboard interrupt, stopping...")
                self.running = False
                break
            except Exception as e:
                self.stats["errors"] += 1
                self._log("error", f"Loop error: {str(e)}")
                time.sleep(2)  # Back off on error

        self._log("info", "Expert AI game loop stopped")

    def start(self):
        """Start the AI game loop in a background thread."""
        if self.running:
            return False

        if not self.controller.is_connected():
            self._log("error", "Controller not connected to BizHawk")
            return False

        self.running = True
        self._thread = threading.Thread(target=self._game_loop, daemon=True)
        self._thread.start()
        self._log("info", "Expert AI started")
        return True

    def stop(self):
        """Stop the AI game loop."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        self._log("info", "Expert AI stopped")
        return True

    def is_running(self):
        """Check if the AI is currently running."""
        return self.running

    def get_status(self):
        """Get current AI status for monitoring."""
        uptime = 0
        if self.stats["start_time"]:
            uptime = time.time() - self.stats["start_time"]

        return {
            "running": self.running,
            "uptime_seconds": round(uptime, 1),
            "director_calls": self.stats["director_calls"],
            "pilot_actions": self.stats["pilot_actions"],
            "errors": self.stats["errors"],
            "last_directive": self.stats["last_directive"],
            "last_action": self.stats["last_action"],
            "recent_log": [
                f"[{e['level']}] {e['message']}"
                for e in self.log[-20:]
            ],
        }


# =====================================================================
# Flask integration: add these endpoints to app.py
# =====================================================================

_expert_instance = None


def get_expert(controller=None):
    """Get or create the singleton expert instance."""
    global _expert_instance
    if _expert_instance is None and controller:
        _expert_instance = AIExpert(controller)
    return _expert_instance


def reset_expert():
    """Reset the expert instance."""
    global _expert_instance
    if _expert_instance and _expert_instance.is_running():
        _expert_instance.stop()
    _expert_instance = None


# =====================================================================
# Standalone runner
# =====================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  FF6 EXPERT AI - Standalone Runner")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Connect to BizHawk (must already be running)")
    print("  2. Start the Director + Pilot AI loop")
    print("  3. Play Final Fantasy VI automatically")
    print()
    print("Press Ctrl+C to stop.")
    print()

    # Check if Flask server is running (for launch/connect)
    import requests
    try:
        r = requests.get("http://localhost:5000/status", timeout=2)
        status = r.json()
        print(f"Flask server: running")
        print(f"BizHawk connected: {status.get('connected', False)}")

        if not status.get("connected"):
            print("\nBizHawk is not connected. Attempting to connect...")
            r = requests.post("http://localhost:5000/connect", timeout=30)
            result = r.json()
            if not result.get("success"):
                print("Failed to connect. Please start BizHawk and load the Lua script.")
                sys.exit(1)
            print("Connected!")

    except requests.ConnectionError:
        print("Flask server not running. Starting in direct mode...")
        print("(Start the Flask server with 'python app.py' for full functionality)")

    # Create controller and expert
    controller = BizHawkControllerFile()
    state_reader = FF6GameStateReader()

    # Check game state
    state = state_reader.read()
    if state:
        print(f"\nGame state found:")
        print(state.party_summary())
    else:
        print("\nNo game state file found. Make sure the Lua script is running.")
        # Try connecting directly
        if controller.connect(max_retries=3):
            print("Connected directly!")
        else:
            print("Cannot connect. Exiting.")
            sys.exit(1)

    # Ensure controller thinks it's connected (we're reading state, so it is)
    controller.connected = True

    # Start the expert
    expert = AIExpert(controller)
    expert.start()

    try:
        while expert.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping AI...")
        expert.stop()

    # Print final stats
    status = expert.get_status()
    print(f"\n{'=' * 60}")
    print(f"Session complete:")
    print(f"  Director calls: {status['director_calls']}")
    print(f"  Pilot actions:  {status['pilot_actions']}")
    print(f"  Errors:         {status['errors']}")
    print(f"  Uptime:         {status['uptime_seconds']}s")
