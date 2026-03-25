"""
FF6 Knowledge Base
Complete data tables for Final Fantasy VI (FF3 US SNES)
Used by both the Expert AI and game state parser to resolve IDs to names.
"""

# Character actor IDs
ACTORS = {
    0: "Terra",    1: "Locke",    2: "Cyan",     3: "Shadow",
    4: "Edgar",    5: "Sabin",    6: "Celes",    7: "Strago",
    8: "Relm",     9: "Setzer",   10: "Mog",     11: "Gau",
    12: "Gogo",    13: "Umaro",   14: "Wedge",   15: "Vicks",
    16: "Leo",     17: "Banon",   18: "Ghost",
    # Extended actor IDs used in some ROM versions
    32: "Wedge",   33: "Vicks",
}

# Battle commands by ID
COMMANDS = {
    0: "Fight",       1: "Item",        2: "Magic",       3: "Morph",
    4: "Revert",      5: "Steal",       6: "Capture",     7: "SwdTech",
    8: "Throw",       9: "Tools",       10: "Blitz",      11: "Runic",
    12: "Lore",       13: "Sketch",     14: "Control",    15: "Slot",
    16: "Rage",       17: "Leap",       18: "Mimic",      19: "Dance",
    20: "Row",        21: "Def",        22: "Jump",       23: "X Magic",
    24: "GP Rain",    25: "Summon",     26: "Health",     27: "Shock",
    28: "Possess",    29: "MagiTek",
    255: "(empty)",
}

# Items by ID (comprehensive list of all FF6 items)
# Weapons: 0-92, Shields: 93-107, Helmets: 108-127, Armor: 128-155,
# Relics: 156-210, Items: 211-255
ITEMS = {
    # --- Dirks/Daggers ---
    0: "Dirk",             1: "MithrilKnife",    2: "Guardian",
    3: "Air Lancet",       4: "ThiefKnife",      5: "Assassin",
    6: "Man Eater",        7: "SwordBreaker",    8: "Graedus",
    9: "ValiantKnife",
    # --- Swords ---
    10: "MithrilBlade",    11: "RegalCutlass",   12: "Rune Edge",
    13: "Flame Sabre",     14: "Blizzard",       15: "ThunderBlade",
    16: "Epee",            17: "Break Blade",    18: "Drainer",
    19: "Enhancer",        20: "Crystal",        21: "Falchion",
    22: "Soul Sabre",      23: "Ogre Nix",       24: "Excalibur",
    25: "Scimitar",        26: "Illumina",       27: "Ragnarok",
    28: "Atma Weapon",
    # --- Lances ---
    29: "Mithril Pike",    30: "Trident",        31: "Stout Spear",
    32: "Partisan",        33: "Pearl Lance",    34: "Gold Lance",
    35: "Aura Lance",      36: "Imp Halberd",
    # --- Dirks/Knives continued ---
    37: "Imperial",        38: "Kodachi",        39: "Blossom",
    40: "Hardened",        41: "Striker",         42: "Stunner",
    # --- Katanas ---
    43: "Ashura",          44: "Kotetsu",        45: "Forged",
    46: "Tempest",         47: "Murasame",       48: "Aura",
    49: "Strato",          50: "Sky Render",
    # --- Rods ---
    51: "Heal Rod",        52: "Mithril Rod",    53: "Fire Rod",
    54: "Ice Rod",         55: "Thunder Rod",    56: "Poison Rod",
    57: "Pearl Rod",       58: "Gravity Rod",    59: "Punisher",
    60: "Magus Rod",
    # --- Brushes ---
    61: "Chocobo Brsh",    62: "DaVinci Brsh",   63: "Magical Brsh",
    64: "Rainbow Brsh",
    # --- Stars ---
    65: "Shuriken",        66: "Ninja Star",     67: "Tack Star",
    68: "Flail",           69: "Full Moon",      70: "Morning Star",
    71: "Boomerang",       72: "Rising Sun",     73: "Hawk Eye",
    74: "Bone Club",       75: "Sniper",         76: "Wing Edge",
    # --- Gambler weapons ---
    77: "Cards",           78: "Darts",          79: "Doom Darts",
    80: "Trump",           81: "Dice",           82: "Fixed Dice",
    # --- Claws ---
    83: "MetalKnuckle",    84: "Mithril Claw",   85: "Kaiser",
    86: "Poison Claw",     87: "Fire Knuckle",   88: "Dragon Claw",
    89: "Tiger Fangs",
    # --- Other weapons ---
    90: "Buckler",         91: "Heavy Shld",     92: "Mithril Shld",
    # --- Shields ---
    93: "Gold Shld",       94: "Aegis Shld",     95: "Diamond Shld",
    96: "Flame Shld",      97: "Ice Shld",       98: "Thunder Shld",
    99: "Crystal Shld",   100: "Genji Shld",    101: "TortoiseShld",
    102: "Cursed Shld",   103: "Paladin Shld",  104: "Force Shld",
    # --- Helmets ---
    105: "Leather Hat",   106: "Hair Band",     107: "Plumed Hat",
    108: "Beret",         109: "Magus Hat",      110: "Bandana",
    111: "Iron Helmet",   112: "Coronet",       113: "Bard's Hat",
    114: "Green Beret",   115: "Head Band",     116: "Mithril Helm",
    117: "Tiara",         118: "Gold Helmet",   119: "Tiger Mask",
    120: "Red Cap",       121: "Mystery Veil",  122: "Circlet",
    123: "Regal Crown",   124: "Diamond Helm",  125: "Dark Hood",
    126: "Crystal Helm",  127: "Oath Veil",     128: "Cat Hood",
    129: "Genji Helmet",  130: "Thornlet",      131: "Titanium",
    # --- Body Armor ---
    132: "LeatherArmor",  133: "Cotton Robe",   134: "Kung Fu Suit",
    135: "Iron Armor",    136: "Silk Robe",     137: "Mithril Vest",
    138: "Ninja Gear",    139: "White Dress",   140: "Mithril Mail",
    141: "Gaia Gear",     142: "Mirage Vest",   143: "Gold Armor",
    144: "Power Sash",    145: "Light Robe",    146: "Diamond Vest",
    147: "Red Jacket",    148: "Force Armor",   149: "DiamondArmor",
    150: "Dark Gear",     151: "Tao Robe",      152: "Crystal Mail",
    153: "Czarina Gown",  154: "Genji Armor",   155: "Imp's Armor",
    156: "Minerva",       157: "Tabby Suit",    158: "Snow Muffler",
    159: "Nutkin Suit",   160: "Behemoth Suit", 161: "Prism Dress",
    # --- Relics ---
    162: "Economizer",    163: "Gold Hairpin",  164: "Exp. Egg",
    165: "Tintinabar",    166: "Sprint Shoes",  167: "Rename Card",
    168: "Charm Bangle",  169: "Marvel Shoes",  170: "Back Guard",
    171: "Gale Hairpin",  172: "Sniper Sight",  173: "Earrings",
    174: "Atlas Armlet",  175: "Blizzard Orb",  176: "Rage Ring",
    177: "Sneak Ring",    178: "Pod Bracelet",  179: "Peace Ring",
    180: "Ribbon",        181: "Muscle Belt",   182: "Crystal Orb",
    183: "Gold Hairpin",  184: "Zephyr Cape",   185: "Czarina Ring",
    186: "Cursed Ring",   187: "Safety Ring",   188: "Relic Ring",
    189: "Moogle Charm",  190: "Charm Bangle",  191: "Dried Meat",
    192: "True Knight",   193: "DragoonBoots",  194: "Zephyr Cape",
    195: "Offering",      196: "Beads",         197: "Black Belt",
    198: "Coin Toss",     199: "FakeMustache",  200: "Gem Box",
    201: "Dragon Horn",   202: "Merit Award",   203: "Memento Ring",
    204: "Safety Bit",    205: "Relic Ring",     206: "Moogle Charm",
    207: "Thief Glove",   208: "Gauntlet",      209: "Genji Glove",
    210: "Hyper Wrist",   211: "Offering",
    # --- Consumable Items ---
    212: "Tonic",         213: "Potion",        214: "X-Potion",
    215: "Tincture",      216: "Ether",         217: "X-Ether",
    218: "Elixir",        219: "Megalixir",     220: "Fenix Down",
    221: "Revivify",      222: "Antidote",      223: "Eyedrop",
    224: "Soft",          225: "Remedy",        226: "Sleeping Bag",
    227: "Tent",          228: "Green Cherry",  229: "Magicite",
    230: "Super Ball",    231: "Echo Screen",   232: "Smoke Bomb",
    233: "Warp Stone",    234: "Dried Meat",    235: "Rename Card",
    # --- Skeans (for Throw) ---
    236: "Bolt Edge",     237: "Fire Skean",    238: "Water Edge",
    239: "Inviz Edge",    240: "Shadow Edge",
    # --- Other ---
    241: "Empty",
    255: "(empty)",
}

# Esper names by ID
ESPERS = {
    0: "Ramuh",       1: "Ifrit",       2: "Shiva",       3: "Siren",
    4: "Terrato",     5: "Shoat",       6: "Maduin",      7: "Bismark",
    8: "Stray",       9: "Palidor",    10: "Tritoch",    11: "Odin",
    12: "Raiden",     13: "Bahamut",   14: "Alexandr",   15: "Crusader",
    16: "Ragnarok",   17: "Kirin",     18: "ZoneSeek",   19: "Carbunkl",
    20: "Phantom",    21: "Sraphim",   22: "Golem",      23: "Unicorn",
    24: "Fenrir",     25: "Starlet",   26: "Phoenix",
    255: "(none)",
}

# Status effects (bitfield values for status1/status2)
STATUS1_FLAGS = {
    0x01: "Dark",
    0x02: "Zombie",
    0x04: "Poison",
    0x08: "Magitek",
    0x10: "Vanish",
    0x20: "Imp",
    0x40: "Petrify",
    0x80: "Death",
}

STATUS2_FLAGS = {
    0x01: "Condemned",
    0x02: "Near Fatal",
    0x04: "Image",
    0x08: "Mute",
    0x10: "Berserk",
    0x20: "Muddle",
    0x40: "Seizure",
    0x80: "Sleep",
}

# Spell names by ID (for magic command)
SPELLS = {
    0: "Fire",        1: "Ice",         2: "Bolt",        3: "Poison",
    4: "Drain",       5: "Fire 2",      6: "Ice 2",       7: "Bolt 2",
    8: "Bio",         9: "Fire 3",     10: "Ice 3",      11: "Bolt 3",
    12: "Break",      13: "Doom",       14: "Pearl",      15: "Flare",
    16: "Demi",       17: "Quartr",     18: "X-Zone",     19: "Meteor",
    20: "Ultima",     21: "Quake",      22: "W Wind",     23: "Merton",
    24: "Cure",       25: "Cure 2",     26: "Cure 3",     27: "Life",
    28: "Life 2",     29: "Antdot",     30: "Remedy",     31: "Regen",
    32: "Life 3",     33: "Haste",      34: "Haste 2",    35: "Slow",
    36: "Slow 2",     37: "Stop",       38: "Shell",      39: "Safe",
    40: "Reflect",    41: "Osmose",     42: "Warp",       43: "Quick",
    44: "Dispel",     45: "Muddle",     46: "Vanish",     47: "Imp",
    48: "Float",      49: "Bserk",      50: "Mute",       51: "Scan",
}

# Equipment types for categorizing items
WEAPON_RANGE = range(0, 90)
SHIELD_RANGE = range(90, 105)
HELMET_RANGE = range(105, 132)
ARMOR_RANGE = range(132, 162)
RELIC_RANGE = range(162, 212)
CONSUMABLE_RANGE = range(212, 241)


def get_item_name(item_id):
    """Get item name by ID, with fallback."""
    return ITEMS.get(item_id, f"Item#{item_id}")


def get_actor_name(actor_id):
    """Get character name by actor ID."""
    return ACTORS.get(actor_id, f"Actor#{actor_id}")


def get_esper_name(esper_id):
    """Get esper name by ID."""
    return ESPERS.get(esper_id, f"Esper#{esper_id}")


def get_command_name(cmd_id):
    """Get battle command name by ID."""
    return COMMANDS.get(cmd_id, f"Cmd#{cmd_id}")


def get_spell_name(spell_id):
    """Get spell name by ID."""
    return SPELLS.get(spell_id, f"Spell#{spell_id}")


def decode_status(status1, status2):
    """Decode status bitfields into list of active status names."""
    statuses = []
    for bit, name in STATUS1_FLAGS.items():
        if status1 & bit:
            statuses.append(name)
    for bit, name in STATUS2_FLAGS.items():
        if status2 & bit:
            statuses.append(name)
    return statuses


def get_item_type(item_id):
    """Categorize an item by its ID."""
    if item_id in WEAPON_RANGE:
        return "weapon"
    elif item_id in SHIELD_RANGE:
        return "shield"
    elif item_id in HELMET_RANGE:
        return "helmet"
    elif item_id in ARMOR_RANGE:
        return "armor"
    elif item_id in RELIC_RANGE:
        return "relic"
    elif item_id in CONSUMABLE_RANGE:
        return "consumable"
    return "unknown"


def get_equippable_items(inventory, slot_type):
    """Filter inventory to items equippable in a given slot type."""
    type_map = {
        "weapon": WEAPON_RANGE,
        "shield": SHIELD_RANGE,
        "helmet": HELMET_RANGE,
        "armor": ARMOR_RANGE,
        "relic": RELIC_RANGE,
    }
    valid_range = type_map.get(slot_type)
    if not valid_range:
        return []
    return [item for item in inventory if item["id"] in valid_range]
