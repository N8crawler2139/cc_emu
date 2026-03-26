"""
FF6 AI Brain - LLM makes strategic decisions, Lua executes them.

The Brain reads game state from bizhawk_gamestate.json, decides what
to do (attack, heal, which spell, which target), and sends specific
commands to the Lua agent for verified execution.

Uses GPT-4o-mini for fast, cheap decisions (~$0.002/call).
Only called when a decision is needed (new battle turn, field stuck).
"""

import json
import time
import threading
from openai import OpenAI
from config import open_ai_apikey
from bizhawk_controller_file import BizHawkControllerFile


BATTLE_MODEL = "gpt-4o-mini"

BATTLE_SYSTEM_PROMPT = """You are an expert FF6 battle strategist.

You receive party HP and available commands. Respond with EXACTLY one line:
COMMAND SPELL TARGET SLOT

The current party is in Magitek Armor. Available commands:
  MagiTek FireBeam enemy 0   - fire damage to one enemy
  MagiTek BoltBeam enemy 0   - lightning damage (strongest)
  MagiTek IceBeam enemy 0    - ice damage to one enemy
  MagiTek HealForce ally 0   - heal first party member
  MagiTek HealForce ally 1   - heal second party member
  MagiTek HealForce ally 2   - heal third party member

Rules:
- If ANY party member is below 40% HP, heal them with HealForce (use their slot number)
- Otherwise attack with BoltBeam (strongest)
- Only output the command. No explanation. One line only."""


class FF6AIBrain:
    """LLM-powered battle strategist + field navigator."""

    def __init__(self, controller):
        self.ctrl = controller
        self.client = OpenAI(api_key=open_ai_apikey)
        self.running = False
        self._thread = None

        # State
        self.battles_won = 0
        self.total_decisions = 0
        self.log = []
        self.max_log = 200

    def _log(self, msg):
        entry = {"time": time.time(), "msg": msg}
        self.log.append(entry)
        if len(self.log) > self.max_log:
            self.log = self.log[-self.max_log:]
        print(f"[Brain] {msg}")

    def _read_state(self):
        """Read current game state from JSON."""
        try:
            with open("bizhawk_gamestate.json") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _is_in_battle(self, state):
        if not state:
            return False
        return state.get("position", {}).get("x", 1) == 0

    def _format_battle_context(self, state):
        """Format battle state for the LLM."""
        lines = []
        lines.append("Party status:")

        for i, c in enumerate(state.get("characters", [])):
            name = c.get("name", "?")
            hp = c.get("hp", 0)
            hp_max = c.get("hp_max", 1)
            pct = round(hp / hp_max * 100) if hp_max > 0 else 0
            status = "OK" if pct > 40 else "LOW" if pct > 15 else "CRITICAL"
            lines.append(f"  Slot {i}: {name} HP {hp}/{hp_max} ({pct}%) [{status}]")

        return "\n".join(lines)

    def decide_battle_action(self, state):
        """Decide battle action based on party state.

        For Magitek battles, this is simple deterministic logic:
        - If any character below 40% HP -> HealForce on them
        - Otherwise -> BoltBeam (strongest attack)

        The LLM will be used for more complex decisions later
        (non-Magitek battles, boss strategies, etc.)
        """
        self.total_decisions += 1
        chars = state.get("characters", [])

        # Check for characters needing healing
        for i, c in enumerate(chars):
            hp = c.get("hp", 0)
            hp_max = c.get("hp_max", 1)
            if hp_max > 0 and hp > 0 and (hp / hp_max) < 0.40:
                return f"MagiTek HealForce ally {i}"

        # Default: BoltBeam (strongest Magitek attack)
        return "MagiTek BoltBeam enemy 0"

    def handle_battle_turn(self, state):
        """Handle one battle turn: decide + send command."""
        # Check if menu is ready (from Python side)
        menu = self.ctrl.read_memory(0x7BCA, 1)
        disabled = self.ctrl.read_memory(0x628B, 1)
        enemies = self.ctrl.read_memory(0x3A77, 1)

        if not menu or not disabled or not enemies:
            return

        # Victory: press A to clear
        if enemies[0] == 0:
            self.ctrl.press_button("A", 0.1)
            time.sleep(0.3)
            return

        # Menu not ready: wait
        if menu[0] == 0 or disabled[0] != 0:
            return

        # Menu ready! Get LLM decision
        cmd_str = self.decide_battle_action(state)
        self._log(f"Decision: {cmd_str}")

        # Send to Lua
        parts = cmd_str.split()
        if len(parts) >= 3:
            cmd = parts[0]
            spell = parts[1]
            target = parts[2] if len(parts) > 2 else "enemy"
            slot = parts[3] if len(parts) > 3 else "0"
            self.ctrl.battle_command(cmd, spell, target, int(slot))

            # Wait for execution
            time.sleep(5)

            # Verify it executed by checking if action changed
            new_state = self._read_state()
            if new_state:
                action = new_state.get("last_battle_action", "")
                self._log(f"Executed: {action}")

    def handle_field(self, state):
        """Handle field navigation. For now, just walk Up."""
        # The Lua agent handles field walking when enabled
        # We just need to make sure it's walking
        pass

    def _game_loop(self):
        """Main loop: read state, decide, act."""
        self._log("Brain started")
        last_battle_state = False

        while self.running:
            try:
                state = self._read_state()
                if not state:
                    time.sleep(0.5)
                    continue

                in_battle = self._is_in_battle(state)

                # Detect battle transitions
                if in_battle and not last_battle_state:
                    self._log("*** BATTLE START ***")
                elif not in_battle and last_battle_state:
                    self.battles_won += 1
                    self._log(f"*** BATTLE WON #{self.battles_won} ***")
                last_battle_state = in_battle

                if in_battle:
                    self.handle_battle_turn(state)
                    time.sleep(0.5)  # Don't spam battle checks
                else:
                    self.handle_field(state)
                    time.sleep(1.0)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self._log(f"Error: {e}")
                time.sleep(2)

        self._log("Brain stopped")

    def start(self):
        if self.running:
            return False
        # Enable Lua agent for field walking, manual battle for our commands
        self.ctrl.agent_on()
        time.sleep(0.3)
        self.ctrl.manual_battle_on()
        time.sleep(0.3)
        self.running = True
        self._thread = threading.Thread(target=self._game_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.ctrl.manual_battle_off()
        return True

    def get_status(self):
        state = self._read_state()
        return {
            "running": self.running,
            "battles_won": self.battles_won,
            "total_decisions": self.total_decisions,
            "in_battle": self._is_in_battle(state) if state else False,
            "recent_log": [e["msg"] for e in self.log[-15:]],
        }


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("  FF6 AI Brain - Standalone")
    print("=" * 50)

    ctrl = BizHawkControllerFile()
    ctrl.connected = True

    brain = FF6AIBrain(ctrl)
    brain.start()

    try:
        while brain.running:
            time.sleep(5)
            status = brain.get_status()
            print(f"Won: {status['battles_won']} | Decisions: {status['total_decisions']} | Battle: {status['in_battle']}")
    except KeyboardInterrupt:
        brain.stop()
        print(f"\nTotal decisions: {brain.total_decisions}")
        print(f"Battles won: {brain.battles_won}")
