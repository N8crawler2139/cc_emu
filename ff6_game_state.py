"""
FF6 Game State Reader
Reads bizhawk_gamestate.json written by the Lua script and provides
a clean, structured Python API for querying current game state.
"""

import json
import os
import time
from ff6_knowledge import (
    get_item_name, get_actor_name, get_esper_name,
    get_command_name, get_spell_name, decode_status,
    get_item_type, ITEMS
)


GAMESTATE_FILE = "bizhawk_gamestate.json"


class FF6Character:
    """Represents a single character's state."""

    def __init__(self, data):
        self.index = data.get("index", 0)
        self.actor_id = data.get("actor_id", 0)
        self.actor_name = data.get("actor_name", get_actor_name(self.actor_id))
        self.name = data.get("name", self.actor_name)
        self.level = data.get("level", 0)
        self.hp = data.get("hp", 0)
        self.hp_max = data.get("hp_max", 0)
        self.mp = data.get("mp", 0)
        self.mp_max = data.get("mp_max", 0)
        self.exp = data.get("exp", 0)
        self.vigor = data.get("vigor", 0)
        self.speed = data.get("speed", 0)
        self.stamina = data.get("stamina", 0)
        self.mag_pwr = data.get("mag_pwr", 0)
        # Equipment (raw IDs)
        self.weapon_id = data.get("weapon", 255)
        self.shield_id = data.get("shield", 255)
        self.helmet_id = data.get("helmet", 255)
        self.armor_id = data.get("armor", 255)
        self.relic1_id = data.get("relic1", 255)
        self.relic2_id = data.get("relic2", 255)
        self.esper_id = data.get("esper", 255)
        # Status
        self.status1 = data.get("status1", 0)
        self.status2 = data.get("status2", 0)
        # Commands
        self.command_ids = data.get("commands", [255, 255, 255, 255])

    @property
    def weapon(self):
        return get_item_name(self.weapon_id)

    @property
    def shield(self):
        return get_item_name(self.shield_id)

    @property
    def helmet(self):
        return get_item_name(self.helmet_id)

    @property
    def armor(self):
        return get_item_name(self.armor_id)

    @property
    def relic1(self):
        return get_item_name(self.relic1_id)

    @property
    def relic2(self):
        return get_item_name(self.relic2_id)

    @property
    def esper(self):
        return get_esper_name(self.esper_id)

    @property
    def statuses(self):
        return decode_status(self.status1, self.status2)

    @property
    def commands(self):
        return [get_command_name(c) for c in self.command_ids]

    @property
    def is_alive(self):
        return self.hp > 0 and not (self.status1 & 0x80)

    @property
    def hp_percent(self):
        if self.hp_max == 0:
            return 0
        return round(self.hp / self.hp_max * 100, 1)

    @property
    def display_name(self):
        """Best name to show -- prefer in-game name, append actor if different."""
        if self.name and self.name != "?????" and self.name.strip():
            return self.name
        return self.actor_name

    def summary(self):
        """One-line summary of this character."""
        status_str = ""
        if self.statuses:
            status_str = " [" + ", ".join(self.statuses) + "]"
        return (
            f"{self.display_name} Lv{self.level} "
            f"HP:{self.hp}/{self.hp_max} MP:{self.mp}/{self.mp_max}"
            f"{status_str}"
        )

    def equipment_summary(self):
        """Summary of equipped items."""
        parts = []
        if self.weapon_id != 255:
            parts.append(f"Weapon: {self.weapon}")
        if self.shield_id != 255:
            parts.append(f"Shield: {self.shield}")
        if self.helmet_id != 255:
            parts.append(f"Helmet: {self.helmet}")
        if self.armor_id != 255:
            parts.append(f"Armor: {self.armor}")
        if self.relic1_id != 255:
            parts.append(f"Relic1: {self.relic1}")
        if self.relic2_id != 255:
            parts.append(f"Relic2: {self.relic2}")
        if self.esper_id != 255:
            parts.append(f"Esper: {self.esper}")
        return ", ".join(parts) if parts else "(nothing equipped)"

    def to_dict(self):
        """Full dict representation for API responses."""
        return {
            "index": self.index,
            "actor_id": self.actor_id,
            "name": self.name,
            "level": self.level,
            "hp": self.hp,
            "hp_max": self.hp_max,
            "mp": self.mp,
            "mp_max": self.mp_max,
            "exp": self.exp,
            "vigor": self.vigor,
            "speed": self.speed,
            "stamina": self.stamina,
            "mag_pwr": self.mag_pwr,
            "weapon": self.weapon,
            "shield": self.shield,
            "helmet": self.helmet,
            "armor": self.armor,
            "relic1": self.relic1,
            "relic2": self.relic2,
            "esper": self.esper,
            "statuses": self.statuses,
            "commands": self.commands,
            "is_alive": self.is_alive,
            "hp_percent": self.hp_percent,
        }


class FF6InventoryItem:
    """Represents an inventory slot."""

    def __init__(self, data):
        self.slot = data.get("slot", 0)
        self.id = data.get("id", 255)
        self.qty = data.get("qty", 0)

    @property
    def name(self):
        return get_item_name(self.id)

    @property
    def item_type(self):
        return get_item_type(self.id)

    def to_dict(self):
        return {
            "slot": self.slot,
            "id": self.id,
            "name": self.name,
            "qty": self.qty,
            "type": self.item_type,
        }


class FF6GameState:
    """
    Complete snapshot of FF6 game state.
    Read from bizhawk_gamestate.json written by the Lua script.
    """

    def __init__(self, raw_data=None):
        if raw_data is None:
            raw_data = {}
        self.frame = raw_data.get("frame", 0)
        self.gold = raw_data.get("gold", 0)
        self.steps = raw_data.get("steps", 0)
        self.play_time = raw_data.get("play_time", "00:00:00")
        self.map_id = raw_data.get("map_id", 0)
        self.position = raw_data.get("position", {"x": 0, "y": 0})
        self.game_mode = raw_data.get("game_mode", 0)
        self.menu_flag = raw_data.get("menu_flag", 0)
        self.diag_bytes = raw_data.get("diag_bytes", [])
        self.party_slots = raw_data.get("party_slots", [])
        self._raw = raw_data

        # Parse characters
        self.all_characters = []
        for char_data in raw_data.get("characters", []):
            self.all_characters.append(FF6Character(char_data))

        # Parse inventory
        self.inventory = []
        for item_data in raw_data.get("inventory", []):
            self.inventory.append(FF6InventoryItem(item_data))

        self._read_time = time.time()

    @property
    def party(self):
        """Get active party members.

        Tries party_slots mapping first; falls back to returning all
        characters with valid data (hp_max > 0, level > 0).
        """
        # Try slot-based mapping
        party_chars = []
        seen = set()
        for slot_idx in self.party_slots:
            for char in self.all_characters:
                if char.index == slot_idx and char.index not in seen:
                    party_chars.append(char)
                    seen.add(char.index)
                    break
        # Validate: party members should have HP > 0
        party_chars = [c for c in party_chars if c.hp_max > 0]
        # Fallback: if slot mapping failed or returned < expected,
        # use all characters with valid stats
        if len(party_chars) < 2:
            party_chars = [c for c in self.all_characters
                          if c.hp_max > 0 and c.level > 0]
        return party_chars

    @property
    def age_seconds(self):
        """How old this state snapshot is, in seconds."""
        return time.time() - self._read_time

    def get_character(self, name_or_id):
        """Find a character by name (case-insensitive) or actor ID."""
        if isinstance(name_or_id, int):
            for char in self.all_characters:
                if char.actor_id == name_or_id or char.index == name_or_id:
                    return char
        else:
            search = name_or_id.lower()
            for char in self.all_characters:
                if char.name.lower() == search or char.actor_name.lower() == search:
                    return char
        return None

    def find_item_in_inventory(self, name_or_id):
        """Find an item in inventory by name (partial match) or ID."""
        if isinstance(name_or_id, int):
            for item in self.inventory:
                if item.id == name_or_id:
                    return item
        else:
            search = name_or_id.lower()
            for item in self.inventory:
                if search in item.name.lower():
                    return item
        return None

    def has_item(self, name_or_id):
        """Check if an item exists in inventory."""
        return self.find_item_in_inventory(name_or_id) is not None

    def party_summary(self):
        """Quick text summary of party state."""
        lines = []
        lines.append(f"Party ({len(self.party)} members) | Gold: {self.gold} | {self.play_time}")
        for char in self.party:
            lines.append(f"  {char.summary()}")
        return "\n".join(lines)

    def inventory_summary(self, max_items=20):
        """Quick text summary of inventory."""
        lines = [f"Inventory ({len(self.inventory)} items):"]
        for item in self.inventory[:max_items]:
            lines.append(f"  {item.name} x{item.qty}")
        if len(self.inventory) > max_items:
            lines.append(f"  ... and {len(self.inventory) - max_items} more")
        return "\n".join(lines)

    def full_summary(self):
        """Complete text summary for AI context."""
        lines = []
        lines.append("=== FF6 Game State ===")
        lines.append(f"Frame: {self.frame} | Map: {self.map_id} | "
                      f"Pos: ({self.position['x']}, {self.position['y']})")
        lines.append(f"Gold: {self.gold} | Steps: {self.steps} | Time: {self.play_time}")
        lines.append(f"Mode: {self.game_mode} | Menu: {self.menu_flag}")
        lines.append("")
        lines.append(self.party_summary())
        lines.append("")
        for char in self.party:
            lines.append(f"  {char.name}: {char.equipment_summary()}")
        lines.append("")
        lines.append(self.inventory_summary())
        return "\n".join(lines)

    def to_dict(self):
        """Full dict for JSON API response."""
        return {
            "frame": self.frame,
            "gold": self.gold,
            "steps": self.steps,
            "play_time": self.play_time,
            "map_id": self.map_id,
            "position": self.position,
            "game_mode": self.game_mode,
            "menu_flag": self.menu_flag,
            "party": [c.to_dict() for c in self.party],
            "all_characters": [c.to_dict() for c in self.all_characters],
            "inventory": [i.to_dict() for i in self.inventory],
        }


class FF6GameStateReader:
    """
    Reads game state from the JSON file written by the Lua script.
    Provides caching so rapid reads don't re-parse the same file.
    """

    def __init__(self, gamestate_file=None):
        self.gamestate_file = gamestate_file or GAMESTATE_FILE
        self._cached_state = None
        self._cached_mtime = 0

    def read(self, force=False):
        """
        Read current game state. Returns FF6GameState or None if file
        doesn't exist or can't be parsed.
        Uses file mtime caching to avoid re-reading unchanged data.
        """
        if not os.path.exists(self.gamestate_file):
            return None

        try:
            mtime = os.path.getmtime(self.gamestate_file)
            if not force and mtime == self._cached_mtime and self._cached_state:
                return self._cached_state

            with open(self.gamestate_file, "r") as f:
                raw = json.load(f)

            state = FF6GameState(raw)
            self._cached_state = state
            self._cached_mtime = mtime
            return state

        except (json.JSONDecodeError, IOError, KeyError) as e:
            # File might be mid-write, return cached version if available
            if self._cached_state:
                return self._cached_state
            return None

    def wait_for_state(self, timeout=10):
        """Block until a valid game state is available."""
        start = time.time()
        while time.time() - start < timeout:
            state = self.read(force=True)
            if state:
                return state
            time.sleep(0.2)
        return None

    def is_available(self):
        """Check if game state file exists and is recent."""
        if not os.path.exists(self.gamestate_file):
            return False
        age = time.time() - os.path.getmtime(self.gamestate_file)
        return age < 5.0  # Less than 5 seconds old


if __name__ == "__main__":
    print("FF6 Game State Reader")
    print("=" * 40)

    reader = FF6GameStateReader()

    if not reader.is_available():
        print("No game state file found.")
        print("Make sure BizHawk is running with bizhawk_gamestate_server.lua")
        print(f"Looking for: {os.path.abspath(GAMESTATE_FILE)}")
    else:
        state = reader.read()
        if state:
            print(state.full_summary())
        else:
            print("Failed to parse game state.")
