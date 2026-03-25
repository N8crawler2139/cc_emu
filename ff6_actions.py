"""
FF6 High-Level Action System
Translates game-level intentions into sequences of button presses.

Each action reads current game state to determine the right button sequence,
then executes it via the controller. Actions are state-aware -- they check
what screen/menu we're in and navigate accordingly.

Used by both the Expert AI and Discovery AI.
"""

import time
from ff6_game_state import FF6GameStateReader
from ff6_knowledge import get_item_name, ITEMS


class FF6Actions:
    """
    High-level actions for FF6.
    Each method returns True/False for success and may update internal state.
    """

    def __init__(self, controller):
        """
        controller: BizHawkControllerFile instance (must be connected)
        """
        self.ctrl = controller
        self.state_reader = FF6GameStateReader()
        # Timing constants (in seconds) -- tweak as needed
        self.MENU_NAV_DELAY = 0.15    # Delay between menu navigation presses
        self.CONFIRM_DELAY = 0.3      # Delay after confirming a selection
        self.MENU_OPEN_DELAY = 0.5    # Delay after opening a menu

    def _press(self, button, duration=0.1):
        """Press a button with standard timing."""
        self.ctrl.press_button(button, duration)
        time.sleep(self.MENU_NAV_DELAY)

    def _press_seq(self, buttons, delay=None):
        """Press a sequence of buttons."""
        if delay is None:
            delay = self.MENU_NAV_DELAY
        for btn in buttons:
            if btn == "WAIT":
                time.sleep(self.CONFIRM_DELAY)
            else:
                self.ctrl.press_button(btn, 0.1)
                time.sleep(delay)

    def get_state(self):
        """Get current game state."""
        return self.state_reader.read()

    # -----------------------------------------------------------------
    # Navigation: Moving the character around
    # -----------------------------------------------------------------

    def walk(self, direction, seconds=1.0):
        """Walk in a direction for a number of seconds."""
        valid = {"up": "Up", "down": "Down", "left": "Left", "right": "Right"}
        btn = valid.get(direction.lower())
        if not btn:
            return False
        self.ctrl.hold_button(btn, duration=seconds)
        return True

    def talk(self):
        """Talk to NPC / interact with object in front of character."""
        self._press("A")
        return True

    def advance_dialog(self, presses=1):
        """Press A to advance dialog text."""
        for _ in range(presses):
            self._press("A")
            time.sleep(self.CONFIRM_DELAY)
        return True

    def skip_dialog(self, max_presses=20):
        """Mash A to skip through dialog quickly."""
        for _ in range(max_presses):
            self._press("A", 0.05)
            time.sleep(0.1)
        return True

    # -----------------------------------------------------------------
    # Main Menu
    # -----------------------------------------------------------------

    def open_menu(self):
        """Open the main menu (X button on field)."""
        self._press("X")
        time.sleep(self.MENU_OPEN_DELAY)
        return True

    def close_menu(self):
        """Close the current menu (B button)."""
        self._press("B")
        time.sleep(self.CONFIRM_DELAY)
        return True

    def close_all_menus(self):
        """Mash B to exit all menus back to field."""
        for _ in range(5):
            self._press("B")
            time.sleep(0.15)
        return True

    # FF6 Main Menu order (top to bottom):
    # Items, Skills, Equip, Relic, Status, Config, Save
    MAIN_MENU_OPTIONS = ["Items", "Skills", "Equip", "Relic", "Status", "Config", "Save"]

    def navigate_main_menu(self, target):
        """
        Navigate to a main menu option by name.
        Assumes the menu is already open and cursor is at the top.
        """
        target_lower = target.lower()
        target_index = None
        for i, option in enumerate(self.MAIN_MENU_OPTIONS):
            if option.lower() == target_lower:
                target_index = i
                break

        if target_index is None:
            return False

        # Press down to reach the target option
        for _ in range(target_index):
            self._press("Down")

        # Confirm selection
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)
        return True

    # -----------------------------------------------------------------
    # Character Selection (used by Equip, Relic, Skills, Status)
    # -----------------------------------------------------------------

    def select_party_member(self, name):
        """
        Select a party member from the character list.
        Assumes we're on a screen showing party member list.
        Returns the party slot index (0-3) or -1 if not found.
        """
        state = self.get_state()
        if not state:
            return -1

        party = state.party
        target_index = -1
        for i, char in enumerate(party):
            if char.name.lower() == name.lower() or char.actor_name.lower() == name.lower():
                target_index = i
                break

        if target_index == -1:
            return -1

        # Navigate down to the right party slot
        for _ in range(target_index):
            self._press("Down")

        # Confirm
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)
        return target_index

    # -----------------------------------------------------------------
    # Equip System
    # -----------------------------------------------------------------

    # FF6 Equip menu slots (top to bottom):
    # Weapon, Shield, Helmet, Armor, Relic1, Relic2
    EQUIP_SLOTS = ["weapon", "shield", "helmet", "armor", "relic1", "relic2"]

    def open_equip_menu(self):
        """Open menu -> Equip."""
        self.open_menu()
        self.navigate_main_menu("Equip")
        return True

    def equip_item(self, character_name, slot, item_name):
        """
        Full equip sequence: Open menu -> Equip -> Select character ->
        Select slot -> Find item -> Confirm.

        slot: "weapon", "shield", "helmet", "armor", "relic1", "relic2"
        item_name: partial match against available equipment
        """
        # Open menu and go to Equip
        self.open_equip_menu()

        # Select character
        slot_idx = self.select_party_member(character_name)
        if slot_idx == -1:
            self.close_all_menus()
            return False

        # Navigate to equipment slot
        slot_lower = slot.lower()
        if slot_lower not in self.EQUIP_SLOTS:
            self.close_all_menus()
            return False

        target_slot = self.EQUIP_SLOTS.index(slot_lower)
        for _ in range(target_slot):
            self._press("Down")

        # Confirm to open equipment list
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        # Now we need to scroll through the equipment list to find our item.
        # The list shows equippable items for this slot.
        # We'll scroll down and check -- for now we scroll a fixed amount
        # and rely on the AI or caller to verify.
        # TODO: Read the menu state from memory to know exact list contents

        # For now, search by pressing down and checking game state
        # This is a best-effort approach
        item_search = item_name.lower()
        found = False

        # Try scrolling through up to 30 items
        for i in range(30):
            # We can't directly read the menu cursor position yet,
            # so we confirm and check if equipment changed
            # For v1, just scroll to approximate position
            # TODO: Add menu cursor memory reading
            self._press("Down")

        # Confirm whatever is highlighted
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        # Back out of equip
        self.close_all_menus()
        return True

    def unequip_slot(self, character_name, slot):
        """Remove equipment from a slot (equip empty)."""
        self.open_equip_menu()
        slot_idx = self.select_party_member(character_name)
        if slot_idx == -1:
            self.close_all_menus()
            return False

        slot_lower = slot.lower()
        if slot_lower not in self.EQUIP_SLOTS:
            self.close_all_menus()
            return False

        target_slot = self.EQUIP_SLOTS.index(slot_lower)
        for _ in range(target_slot):
            self._press("Down")

        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        # Empty is always at the top of the list
        # So just confirm immediately
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        self.close_all_menus()
        return True

    # -----------------------------------------------------------------
    # Items Menu
    # -----------------------------------------------------------------

    def open_items_menu(self):
        """Open menu -> Items."""
        self.open_menu()
        self.navigate_main_menu("Items")
        return True

    def use_item(self, item_name, target_character=None):
        """
        Use an item from the Items menu.
        If target_character is provided, selects that character as target.
        """
        self.open_items_menu()

        # Scroll to find the item
        # TODO: Read inventory position from memory for precise navigation
        item_search = item_name.lower()
        state = self.get_state()
        if state:
            # Try to estimate position in inventory
            for i, inv_item in enumerate(state.inventory):
                if item_search in inv_item.name.lower():
                    # Scroll down to this position
                    for _ in range(i):
                        self._press("Down")
                    break

        # Select the item
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        # "Use" option
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        # Select target character if needed
        if target_character:
            self.select_party_member(target_character)
        else:
            self._press("A")
            time.sleep(self.CONFIRM_DELAY)

        self.close_all_menus()
        return True

    # -----------------------------------------------------------------
    # Battle Actions
    # -----------------------------------------------------------------

    def battle_attack(self):
        """Select Fight command in battle (usually first option)."""
        self._press("A")  # Select Fight
        time.sleep(self.CONFIRM_DELAY)
        self._press("A")  # Confirm target (first enemy)
        return True

    def battle_magic(self, spell_index=0):
        """Select Magic/MagiTek command and cast a spell.
        In Magitek battles, MagiTek is the first option - just press A.
        """
        # Select first command (Fight/MagiTek) - do NOT press Down
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        # Scroll to spell
        for _ in range(spell_index):
            self._press("Down")

        self._press("A")  # Select spell
        time.sleep(self.CONFIRM_DELAY)
        self._press("A")  # Confirm target
        return True

    def battle_item(self, scroll_count=0):
        """Use Item command in battle."""
        # Navigate to Item command (usually last slot)
        self._press("Down")
        self._press("Down")
        self._press("Down")
        self._press("A")
        time.sleep(self.CONFIRM_DELAY)

        # Scroll to item
        for _ in range(scroll_count):
            self._press("Down")

        self._press("A")  # Select item
        time.sleep(self.CONFIRM_DELAY)
        self._press("A")  # Confirm target
        return True

    def battle_defend(self):
        """Select Defend in battle."""
        # Defend is typically accessed via Row submenu or specific slot
        self._press("Down")
        self._press("Down")
        self._press("A")
        return True

    def battle_run(self):
        """Attempt to run from battle (hold L+R)."""
        self.ctrl.hold_button("L", duration=2)
        self.ctrl.hold_button("R", duration=2)
        return True

    # -----------------------------------------------------------------
    # Save System
    # -----------------------------------------------------------------

    def save_game(self, slot=1):
        """Open menu -> Save -> select slot."""
        self.open_menu()
        self.navigate_main_menu("Save")

        # Select save slot (0-indexed internally)
        for _ in range(slot - 1):
            self._press("Down")

        self._press("A")  # Confirm slot
        time.sleep(self.CONFIRM_DELAY)
        self._press("A")  # Confirm overwrite
        time.sleep(1.0)   # Wait for save to complete

        self.close_all_menus()
        return True

    # -----------------------------------------------------------------
    # Composite / Smart Actions
    # -----------------------------------------------------------------

    def heal_party(self):
        """Use available healing items/magic on hurt party members."""
        state = self.get_state()
        if not state:
            return False

        for char in state.party:
            if char.is_alive and char.hp_percent < 50:
                # Try to use a Tonic/Potion
                if state.has_item("Potion"):
                    self.use_item("Potion", char.name)
                elif state.has_item("Tonic"):
                    self.use_item("Tonic", char.name)

        return True

    def check_status(self):
        """Read and return current game state summary."""
        state = self.get_state()
        if state:
            return state.full_summary()
        return "Unable to read game state"
