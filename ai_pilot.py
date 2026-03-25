"""
AI Pilot - Tactical Executor for FF6 Expert Mode

Uses GPT-4o-mini for fast, cheap decision-making.
Takes the Director's goal + real-time game state and outputs
specific button actions to execute.

Runs in a tight loop, making rapid decisions.
"""

import json
import time
from openai import OpenAI
from config import open_ai_apikey
from ff6_game_state import FF6GameStateReader
from ff6_actions import FF6Actions


PILOT_MODEL = "gpt-4o-mini"

PILOT_SYSTEM_PROMPT = """You are the PILOT AI for Final Fantasy VI on SNES.
You execute specific button commands on the controller to achieve goals set by the Director.

You receive:
1. The Director's current goal and instructions
2. Current game state (party, position, HP/MP, inventory)
3. Your last few actions and their results

You must output a JSON response with this EXACT structure:
{
    "action": "one of the action types listed below",
    "params": {"parameter": "value"},
    "reasoning": "Very brief reason for this action (max 10 words)"
}

Available actions and their params:
- {"action": "walk", "params": {"direction": "up|down|left|right", "seconds": 1.5}}
- {"action": "press", "params": {"button": "A|B|X|Y|Start|Select|L|R|Up|Down|Left|Right"}}
- {"action": "hold", "params": {"button": "A|B|X|Y|Up|Down|Left|Right", "seconds": 2.0}}
- {"action": "open_menu", "params": {}}
- {"action": "close_menu", "params": {}}
- {"action": "talk", "params": {"presses": 1}}
- {"action": "advance_dialog", "params": {"presses": 5}}
- {"action": "battle_attack", "params": {}}
- {"action": "battle_magic", "params": {"spell_index": 0}}
- {"action": "battle_item", "params": {"scroll_count": 0}}
- {"action": "battle_run", "params": {}}
- {"action": "wait", "params": {"seconds": 1.0}}
- {"action": "save", "params": {"slot": 1}}
- {"action": "equip", "params": {"character": "Terra", "slot": "weapon", "item": "Enhancer"}}
- {"action": "use_item", "params": {"item": "Potion", "target": "Terra"}}

Rules:
- Execute ONE action at a time. You'll be called again immediately after.
- Be precise with directions. UP/DOWN/LEFT/RIGHT only.
- In battle: default to "battle_attack" unless the Director says otherwise.
- If dialog is showing, use "advance_dialog" to get through it.
- If the screen seems stuck, try "press" A or B.
- Keep walk durations short (0.5-2 seconds) so you can re-evaluate frequently.
- NEVER output anything except the JSON object."""


class AIPilot:
    """Tactical AI that executes specific button commands."""

    def __init__(self, controller):
        """
        controller: BizHawkControllerFile instance (must be connected)
        """
        self.client = OpenAI(api_key=open_ai_apikey)
        self.state_reader = FF6GameStateReader()
        self.actions = FF6Actions(controller)
        self.ctrl = controller
        self.action_history = []
        self.action_count = 0
        self.last_position = None
        self.stuck_counter = 0

    def _get_state_summary(self):
        """Get a compact state summary for the Pilot."""
        state = self.state_reader.read()
        if not state:
            return "Game state unavailable", None

        # Detect if we're likely in battle
        in_battle = self._detect_battle(state)

        lines = []
        if in_battle:
            lines.append("*** IN BATTLE ***")
        lines.append(f"Map:{state.map_id} Pos:({state.position['x']},{state.position['y']}) "
                      f"Mode:{state.game_mode} Menu:{state.menu_flag}")
        lines.append(f"Gold:{state.gold}")

        for c in state.party:
            lines.append(f"  {c.display_name} Lv{c.level} HP:{c.hp}/{c.hp_max} MP:{c.mp}/{c.mp_max}"
                         + (f" [{','.join(c.statuses)}]" if c.statuses else ""))

        if state.inventory:
            item_str = ", ".join(f"{i.name}x{i.qty}" for i in state.inventory[:10])
            lines.append(f"Items: {item_str}")

        return "\n".join(lines), state

    def _detect_battle(self, state):
        """Detect if we're in battle.

        The $0201 battle_phase flag is unreliable. Instead use:
        - position.x == 0 (field always has x > 0, battle screen uses x=0)
        - battle_menu > 0 (menu is active in battle)
        """
        if not state:
            return False
        x = state.position.get('x', -1)
        menu = getattr(state, 'battle_menu', 0)
        return x == 0 or menu > 0

    def _check_stuck(self, state):
        """Detect if we're stuck (position hasn't changed for multiple actions)."""
        if not state:
            return False
        current_pos = (state.map_id, state.position['x'], state.position['y'])
        if current_pos == self.last_position:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
            self.last_position = current_pos
        return self.stuck_counter > 5

    def _format_history(self):
        """Format recent action history for context."""
        if not self.action_history:
            return "No previous actions."
        recent = self.action_history[-5:]
        lines = []
        for h in recent:
            lines.append(f"- {h['action']}({h.get('params', {})}) -> {h.get('result', 'ok')}")
        return "\n".join(lines)

    def decide_action(self, director_instructions):
        """
        Given the Director's instructions and current state,
        decide the next single action to take.

        Returns an action dict: {action, params, reasoning}
        """
        state_text, state = self._get_state_summary()
        is_stuck = self._check_stuck(state)
        in_battle = self._detect_battle(state) if state else False

        # BATTLE OVERRIDE: Use memory to handle battles deterministically.
        # No LLM needed -- read menu state and press the right button.
        if in_battle:
            battle_menu = getattr(state, 'battle_menu', 0)
            if battle_menu > 0:
                # A menu is active (command/spell/target selection).
                # Press A to confirm the first option which is always
                # Fight or MagiTek -- the cursor starts there.
                return {
                    "action": "press",
                    "params": {"button": "A"},
                    "reasoning": f"Battle menu active (menu={battle_menu}), pressing A"
                }
            else:
                # Animation playing or waiting for ATB. Just wait briefly.
                return {
                    "action": "wait",
                    "params": {"seconds": 0.3},
                    "reasoning": "Battle animation playing, waiting"
                }

        stuck_note = ""
        if is_stuck:
            stuck_note = "\nWARNING: Position hasn't changed in several actions. Try a different approach (press A/B, change direction, interact)."

        user_message = f"""DIRECTOR'S INSTRUCTIONS:
{director_instructions}

CURRENT STATE:
{state_text}

RECENT ACTIONS:
{self._format_history()}
{stuck_note}

What is the SINGLE next action to take? Respond with JSON only."""

        try:
            response = self.client.chat.completions.create(
                model=PILOT_MODEL,
                messages=[
                    {"role": "system", "content": PILOT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=150,
                response_format={"type": "json_object"},
            )

            action_text = response.choices[0].message.content
            action = json.loads(action_text)

            # Validate
            if "action" not in action:
                action = {"action": "press", "params": {"button": "A"}, "reasoning": "fallback"}

            action.setdefault("params", {})
            action.setdefault("reasoning", "")

            return action

        except Exception as e:
            return {
                "action": "wait",
                "params": {"seconds": 1.0},
                "reasoning": f"Error: {str(e)}"
            }

    def execute_action(self, action):
        """
        Execute a single action dict.
        Returns a result string.
        """
        act = action["action"]
        params = action.get("params", {})

        try:
            if act == "walk":
                direction = params.get("direction", "up")
                seconds = float(params.get("seconds", 1.0))
                seconds = min(seconds, 3.0)  # Cap walk time
                self.actions.walk(direction, seconds)
                result = f"Walked {direction} for {seconds}s"

            elif act == "press":
                button = params.get("button", "A")
                self.ctrl.press_button(button, 0.1)
                result = f"Pressed {button}"

            elif act == "hold":
                button = params.get("button", "A")
                seconds = float(params.get("seconds", 1.0))
                seconds = min(seconds, 5.0)
                self.ctrl.hold_button(button, seconds)
                result = f"Held {button} for {seconds}s"

            elif act == "open_menu":
                self.actions.open_menu()
                result = "Opened menu"

            elif act == "close_menu":
                self.actions.close_all_menus()
                result = "Closed menus"

            elif act == "talk":
                presses = int(params.get("presses", 1))
                self.actions.advance_dialog(presses)
                result = f"Talked ({presses} presses)"

            elif act == "advance_dialog":
                presses = int(params.get("presses", 5))
                self.actions.advance_dialog(presses)
                result = f"Advanced dialog ({presses} presses)"

            elif act == "battle_attack":
                self.actions.battle_attack()
                result = "Battle: attacked"

            elif act == "battle_magic":
                spell_idx = int(params.get("spell_index", 0))
                self.actions.battle_magic(spell_idx)
                result = f"Battle: magic (spell {spell_idx})"

            elif act == "battle_item":
                scroll = int(params.get("scroll_count", 0))
                self.actions.battle_item(scroll)
                result = f"Battle: used item (scroll {scroll})"

            elif act == "battle_run":
                self.actions.battle_run()
                result = "Battle: attempted run"

            elif act == "wait":
                seconds = float(params.get("seconds", 1.0))
                seconds = min(seconds, 5.0)
                time.sleep(seconds)
                result = f"Waited {seconds}s"

            elif act == "save":
                slot = int(params.get("slot", 1))
                self.actions.save_game(slot)
                result = f"Saved to slot {slot}"

            elif act == "equip":
                char = params.get("character", "")
                slot = params.get("slot", "weapon")
                item = params.get("item", "")
                self.actions.equip_item(char, slot, item)
                result = f"Equipped {item} on {char} ({slot})"

            elif act == "use_item":
                item = params.get("item", "")
                target = params.get("target")
                self.actions.use_item(item, target)
                result = f"Used {item}" + (f" on {target}" if target else "")

            else:
                # Unknown action, default to press A
                self.ctrl.press_button("A", 0.1)
                result = f"Unknown action '{act}', pressed A"

            # Record in history
            self.action_history.append({
                "action": act,
                "params": params,
                "result": result,
                "timestamp": time.time(),
            })
            # Keep history bounded
            if len(self.action_history) > 50:
                self.action_history = self.action_history[-30:]

            self.action_count += 1
            return result

        except Exception as e:
            result = f"Error executing {act}: {str(e)}"
            self.action_history.append({
                "action": act,
                "params": params,
                "result": result,
                "timestamp": time.time(),
            })
            return result

    def step(self, director_instructions):
        """
        One full Pilot step: decide + execute.
        Returns (action_dict, result_string).
        """
        action = self.decide_action(director_instructions)
        result = self.execute_action(action)
        return action, result
