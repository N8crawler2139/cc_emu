"""
AI Director - Strategic Agent for FF6 Expert Mode

Uses GPT-4o to make high-level strategic decisions.
Reads game state + walkthrough knowledge, outputs structured goals
for the Pilot agent to execute.

Runs every ~5-10 seconds or when the Pilot signals a state change.
"""

import json
import time
import base64
import io
from openai import OpenAI
from config import open_ai_apikey
from ff6_game_state import FF6GameStateReader
from ff6_walkthrough import get_director_context, get_current_objective
from screenshot_ocr import ScreenshotOCR


DIRECTOR_MODEL = "gpt-4o"

DIRECTOR_SYSTEM_PROMPT = """You are the DIRECTOR AI for playing Final Fantasy VI (FF3 US on SNES).
You are an expert who has beaten the game many times.

Your role is to analyze the current game state and provide CLEAR, SPECIFIC instructions
for a Pilot agent that will execute your commands by pressing buttons on the controller.

You will receive:
1. Current game state (party stats, position, inventory, map)
2. Walkthrough guidance for the current section
3. Character tips

You must output a JSON response with this EXACT structure:
{
    "situation": "Brief description of where we are and what's happening",
    "goal": "The immediate goal to accomplish RIGHT NOW (not future goals)",
    "instructions": [
        "Step-by-step instructions for the Pilot, in order",
        "Be VERY specific: 'Walk UP for 2 seconds' not 'go north'",
        "Include button-level detail when needed"
    ],
    "battle_plan": "What to do if a random battle starts (or null if not applicable)",
    "priority": "normal|urgent|careful",
    "notes": "Any additional context the Pilot should know"
}

CRITICAL RULES:
- Focus on what to do RIGHT NOW, not future objectives.
- In the FF6 opening: the party walks UP (north) through snow toward Narshe.
  The screen scrolls upward. Walking DOWN goes backwards toward the start.
- In SNES FF6, UP = north toward the top of the screen, DOWN = south.
- The Pilot can only do ONE small action at a time. Give the NEXT action.
- If dialog text is showing, the Pilot must press A to advance it.
- If position hasn't changed, we might be in dialog, battle, or blocked. Try pressing A.
- Be SPECIFIC with directions: UP, DOWN, LEFT, RIGHT only.
- X button opens the main menu on the field.
- A button confirms/talks/advances dialog.
- B button cancels/goes back.
- If we're in battle (position won't change, game_mode may change), use battle commands.
- Keep walk durations SHORT (0.5-2 seconds) so the Pilot can re-check state frequently.
- NEVER output anything except the JSON object. No markdown, no commentary."""


class AIDirector:
    """Strategic AI that decides what the party should do."""

    def __init__(self):
        self.client = OpenAI(api_key=open_ai_apikey)
        self.state_reader = FF6GameStateReader()
        self.screenshot = ScreenshotOCR()
        self.last_directive = None
        self.last_state_hash = None
        self.directive_count = 0
        self.history = []  # Recent directives for context

    def _capture_screenshot_b64(self):
        """Capture a screenshot and return as base64 JPEG string."""
        try:
            image = self.screenshot.capture_window()
            if image:
                # Resize to save tokens (256px wide is enough for GPT-4o)
                w, h = image.size
                new_w = 512
                new_h = int(h * new_w / w)
                image = image.resize((new_w, new_h))
                # Convert to JPEG base64
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=75)
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
        return None

    def _state_hash(self, state):
        """Quick hash to detect significant state changes."""
        if not state:
            return None
        return (
            state.map_id,
            state.gold,
            tuple(c.hp for c in state.party),
            state.game_mode,
        )

    def has_state_changed(self):
        """Check if game state has changed significantly since last directive."""
        state = self.state_reader.read()
        if not state:
            return False
        current_hash = self._state_hash(state)
        return current_hash != self.last_state_hash

    def get_directive(self, force=False):
        """
        Analyze game state and produce a directive for the Pilot.
        Returns a dict with situation, goal, instructions, battle_plan, etc.
        Returns None if state hasn't changed and force=False.
        """
        state = self.state_reader.read()
        if not state:
            return {
                "situation": "Cannot read game state",
                "goal": "Wait for game state to become available",
                "instructions": ["Wait 2 seconds and try again"],
                "battle_plan": None,
                "priority": "normal",
                "notes": "Game state file not found or unreadable"
            }

        # Check if state changed significantly
        current_hash = self._state_hash(state)
        if not force and current_hash == self.last_state_hash:
            return self.last_directive

        # Build context for the LLM
        context = get_director_context(state)

        # Add recent history for continuity
        history_text = ""
        if self.history:
            recent = self.history[-3:]  # Last 3 directives
            history_text = "\n\nRECENT HISTORY (what we've been doing):\n"
            for h in recent:
                history_text += f"- {h['situation']} -> {h['goal']}\n"

        # Add position tracking
        pos_text = ""
        if state:
            pos_text = f"\n\nKEY STATE: Map {state.map_id}, Position ({state.position['x']}, {state.position['y']}), Gold: {state.gold}"
            pos_text += f"\nGame mode: {state.game_mode}, Menu flag: {state.menu_flag}"

        user_message = f"""Current game state and walkthrough context:

{context}
{pos_text}
{history_text}

Focus on the IMMEDIATE next action. What should the Pilot do RIGHT NOW?
Respond with JSON only."""

        try:
            # Capture screenshot for visual context
            screenshot_b64 = self._capture_screenshot_b64()

            # Build messages with optional vision
            user_content = []
            if screenshot_b64:
                user_content.append({
                    "type": "text",
                    "text": user_message
                })
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{screenshot_b64}",
                        "detail": "low"
                    }
                })
            else:
                user_content = user_message

            response = self.client.chat.completions.create(
                model=DIRECTOR_MODEL,
                messages=[
                    {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            directive_text = response.choices[0].message.content
            directive = json.loads(directive_text)

            # Validate required fields
            required = ["situation", "goal", "instructions"]
            for field in required:
                if field not in directive:
                    directive[field] = "unknown"

            # Defaults
            directive.setdefault("battle_plan", None)
            directive.setdefault("priority", "normal")
            directive.setdefault("notes", "")

            self.last_directive = directive
            self.last_state_hash = current_hash
            self.directive_count += 1

            # Add to history
            self.history.append({
                "situation": directive["situation"],
                "goal": directive["goal"],
                "timestamp": time.time(),
            })
            # Keep history bounded
            if len(self.history) > 20:
                self.history = self.history[-10:]

            return directive

        except Exception as e:
            error_directive = {
                "situation": f"Director error: {str(e)}",
                "goal": "Continue with last known objective",
                "instructions": ["Continue previous action", "Press A to advance if stuck"],
                "battle_plan": "Attack with strongest available option",
                "priority": "normal",
                "notes": f"Error occurred: {str(e)}"
            }
            return error_directive

    def format_for_pilot(self, directive=None):
        """Format the directive as a clear text block for the Pilot."""
        if directive is None:
            directive = self.last_directive
        if directive is None:
            return "No directive available. Explore cautiously."

        lines = []
        lines.append(f"SITUATION: {directive['situation']}")
        lines.append(f"GOAL: {directive['goal']}")
        lines.append(f"PRIORITY: {directive.get('priority', 'normal')}")
        lines.append("")
        lines.append("INSTRUCTIONS:")
        instructions = directive.get("instructions", [])
        if isinstance(instructions, list):
            for i, inst in enumerate(instructions, 1):
                lines.append(f"  {i}. {inst}")
        else:
            lines.append(f"  {instructions}")

        if directive.get("battle_plan"):
            lines.append("")
            lines.append(f"BATTLE PLAN: {directive['battle_plan']}")

        if directive.get("notes"):
            lines.append("")
            lines.append(f"NOTES: {directive['notes']}")

        return "\n".join(lines)


if __name__ == "__main__":
    print("=== AI Director Test ===")
    director = AIDirector()

    state = director.state_reader.read()
    if state:
        print("Game state found:")
        print(state.party_summary())
        print()

        print("Getting directive...")
        directive = director.get_directive(force=True)
        print()
        print(director.format_for_pilot(directive))
    else:
        print("No game state available. Start BizHawk with the gamestate Lua script.")
