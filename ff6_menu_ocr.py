"""
FF6 Menu OCR and Navigation

Uses screenshot region cropping + GPT-4o-mini vision to read
menu options and cursor position. Then calculates exact button
presses to navigate to any target option.

No Tesseract or external OCR needed -- vision model reads game text directly.
"""

import base64
import io
import json
import time
from PIL import Image
from openai import OpenAI
from config import open_ai_apikey
from screenshot_ocr import ScreenshotOCR


# Screen region definitions (relative to game area, as fractions)
# These are calibrated for BizHawk's default SNES window
REGIONS = {
    # Battle command menu (bottom-left: MagiTek/Fight/Magic/Item etc.)
    "battle_commands": {
        "x1": 0.0, "y1": 0.62, "x2": 0.42, "y2": 1.0,
    },
    # Battle party HP (bottom-right: names + HP bars)
    "battle_party": {
        "x1": 0.42, "y1": 0.62, "x2": 1.0, "y2": 1.0,
    },
    # Dialog box (bottom portion of screen)
    "dialog": {
        "x1": 0.0, "y1": 0.60, "x2": 1.0, "y2": 1.0,
    },
    # Main menu (center of screen when X is pressed)
    "main_menu": {
        "x1": 0.0, "y1": 0.0, "x2": 0.45, "y2": 1.0,
    },
    # Full game screen (for general analysis)
    "full": {
        "x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0,
    },
}

# BizHawk chrome offsets (title bar, menu bar, status bar)
CHROME_TOP = 60      # title bar + menu bar
CHROME_BOTTOM = 25   # status bar


class FF6MenuOCR:
    """Reads FF6 menu text from screenshots using vision model."""

    def __init__(self):
        self.client = OpenAI(api_key=open_ai_apikey)
        self.screenshotter = ScreenshotOCR()
        self._last_screenshot = None

    def capture_game_area(self):
        """Capture just the game rendering area (no BizHawk chrome)."""
        self.screenshotter.bizhawk_window = None  # Re-find each time
        full = self.screenshotter.capture_window()
        if not full:
            return None

        w, h = full.size
        game_area = full.crop((0, CHROME_TOP, w, h - CHROME_BOTTOM))
        self._last_screenshot = game_area
        return game_area

    def crop_region(self, image, region_name):
        """Crop a named region from the game area image."""
        if region_name not in REGIONS:
            return image

        r = REGIONS[region_name]
        w, h = image.size
        x1 = int(w * r["x1"])
        y1 = int(h * r["y1"])
        x2 = int(w * r["x2"])
        y2 = int(h * r["y2"])
        return image.crop((x1, y1, x2, y2))

    def _image_to_b64(self, image):
        """Convert PIL Image to base64 JPEG."""
        # Upscale small crops for better vision model reading
        w, h = image.size
        if w < 400:
            scale = 400 // w + 1
            image = image.resize((w * scale, h * scale), Image.NEAREST)

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=90)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def read_menu(self, image, context="battle menu"):
        """
        Use GPT-4o-mini vision to read menu options from a cropped image.

        Returns dict:
        {
            "options": ["MagiTek", "Item"],
            "cursor_on": "MagiTek",   # which option the cursor points to
            "cursor_index": 0,         # 0-based index
        }
        """
        b64 = self._image_to_b64(image)

        prompt = f"""Look at this {context} from Final Fantasy VI (SNES).
List ALL menu options visible, in order from top to bottom.
Identify which option the cursor/arrow is currently pointing at.

Reply as JSON only:
{{"options": ["Option1", "Option2"], "cursor_on": "Option1", "cursor_index": 0}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "low"
                        }}
                    ]
                }],
                temperature=0.1,
                max_tokens=150,
            )

            text = response.choices[0].message.content
            if not text:
                return None

            # Strip markdown if present
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)

            return json.loads(text)

        except Exception as e:
            print(f"Menu OCR error: {e}")
            return None

    def read_screen_state(self, image=None):
        """
        Analyze the full game screen to determine what state we're in.

        Returns dict:
        {
            "state": "battle" | "dialog" | "field" | "menu" | "unknown",
            "description": "what's on screen",
        }
        """
        if image is None:
            image = self.capture_game_area()
        if image is None:
            return {"state": "unknown", "description": "no screenshot"}

        b64 = self._image_to_b64(image)

        prompt = """Look at this Final Fantasy VI game screenshot.
What state is the game in? Reply as JSON only:
{"state": "battle" or "dialog" or "field" or "menu" or "unknown", "description": "brief description"}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "low"
                        }}
                    ]
                }],
                temperature=0.1,
                max_tokens=100,
            )

            text = response.choices[0].message.content
            if not text:
                return {"state": "unknown", "description": "empty response"}

            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)

            return json.loads(text)

        except Exception as e:
            return {"state": "unknown", "description": f"error: {e}"}

    def navigate_to_option(self, current_index, target_index, total_options):
        """
        Calculate button presses to move cursor from current_index to target_index.
        Returns list of button names to press (e.g., ["Down", "Down", "A"]).
        """
        if current_index == target_index:
            return ["A"]  # Already on target, just confirm

        diff = target_index - current_index
        buttons = []

        if diff > 0:
            # Need to go down
            for _ in range(diff):
                buttons.append("Down")
        else:
            # Need to go up
            for _ in range(abs(diff)):
                buttons.append("Up")

        buttons.append("A")  # Confirm selection
        return buttons


class FF6BattleNavigator:
    """
    Handles battle menu navigation using OCR.

    In FF6 battle, the flow is:
    1. Character's ATB fills -> command menu appears
    2. Select command (Fight/MagiTek/Magic/Item/etc.)
    3. If MagiTek/Magic: select spell from submenu
    4. Select target (enemy or ally)

    This class reads the current menu state and executes the right inputs.
    """

    def __init__(self, controller):
        self.ctrl = controller
        self.menu_ocr = FF6MenuOCR()
        self.PRESS_DELAY = 0.15

    def _press(self, button):
        """Press a button with timing."""
        self.ctrl.press_button(button, 0.1)
        time.sleep(self.PRESS_DELAY)

    def execute_battle_turn(self, preferred_command="Fight"):
        """
        Execute one battle turn:
        1. Screenshot the battle menu
        2. OCR to find options and cursor
        3. Navigate to preferred command
        4. Confirm with A
        5. Confirm target with A

        preferred_command: "Fight", "MagiTek", "Magic", "Item", etc.
        Returns True if action was taken.
        """
        # Capture and crop the battle command menu
        game_img = self.menu_ocr.capture_game_area()
        if not game_img:
            # Fallback: just press A
            self._press("A")
            return True

        menu_crop = self.menu_ocr.crop_region(game_img, "battle_commands")
        menu_data = self.menu_ocr.read_menu(menu_crop, "battle command menu")

        if not menu_data or not menu_data.get("options"):
            # Can't read menu -- might be in animation or transition
            # Just press A and hope
            self._press("A")
            return True

        options = menu_data["options"]
        cursor_idx = menu_data.get("cursor_index", 0)

        print(f"  Battle menu: {options}, cursor on [{cursor_idx}]={options[cursor_idx] if cursor_idx < len(options) else '?'}")

        # Find the preferred command
        target_idx = None
        preferred_lower = preferred_command.lower()
        for i, opt in enumerate(options):
            if preferred_lower in opt.lower():
                target_idx = i
                break

        # If preferred not found, just select first option (usually Fight/MagiTek)
        if target_idx is None:
            target_idx = 0

        # Navigate to target
        buttons = self.menu_ocr.navigate_to_option(cursor_idx, target_idx, len(options))

        print(f"  Navigate: cursor {cursor_idx} -> target {target_idx}, buttons: {buttons}")

        for btn in buttons:
            self._press(btn)

        # After selecting command, we may need to:
        # - Select a spell (for MagiTek/Magic): just press A for first spell
        # - Select a target: press A for first target
        time.sleep(0.3)
        self._press("A")  # Select first spell/attack
        time.sleep(0.2)
        self._press("A")  # Select first target

        return True


if __name__ == "__main__":
    print("=== FF6 Menu OCR Test ===")

    ocr = FF6MenuOCR()

    # Test on saved battle screenshot
    try:
        img = Image.open("ai_mash_battle.png")
        w, h = img.size
        # Crop to game area
        game = img.crop((0, CHROME_TOP, w, h - CHROME_BOTTOM))

        # Read screen state
        print("\nScreen state:")
        state = ocr.read_screen_state(game)
        print(f"  {state}")

        # Read battle menu
        print("\nBattle menu:")
        menu_crop = ocr.crop_region(game, "battle_commands")
        menu = ocr.read_menu(menu_crop, "battle command menu")
        print(f"  {menu}")

        # Read party HP
        print("\nParty HP area:")
        hp_crop = ocr.crop_region(game, "battle_party")
        hp = ocr.read_menu(hp_crop, "battle party status showing character names and HP")
        print(f"  {hp}")

    except FileNotFoundError:
        print("No battle screenshot found. Run the AI to capture one.")
