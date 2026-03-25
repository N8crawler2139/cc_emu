"""
FF6 Expert Walkthrough Knowledge Base

Structured game progression data for the Director AI.
Each objective has conditions for when it's active, what to do,
and tips for the Pilot. The Director LLM already knows FF6 --
this provides structured anchoring to prevent hallucination.

The walkthrough is organized as a list of sequential objectives.
The Director matches the current game state to figure out which
objective is active, then provides instructions to the Pilot.
"""

WALKTHROUGH = [
    # ===================================================================
    # ACT 1: THE BEGINNING
    # ===================================================================
    {
        "id": "narshe_approach",
        "name": "Narshe Approach - Magitek March",
        "act": 1,
        "conditions": {
            "map_ids": [18, 19, 20],
            "party_contains": ["Terra", "Wedge", "Vicks"],
            "notes": "Opening scene. Three Magitek armors walking toward Narshe."
        },
        "objective": "Walk UP (north) through the snowfield toward Narshe. Direction is UP on the controller.",
        "instructions": [
            "Walk UP (north) along the path. UP means toward top of screen.",
            "Keep pressing/holding UP. The path goes north to Narshe.",
            "If dialog appears, press A to advance it.",
            "Random encounters may happen. Use Fight command (press A).",
            "The party is in Magitek armor - attacks are very powerful.",
            "Keep walking UP until the scene changes or guards appear."
        ],
        "battle_strategy": {
            "default": "Press A to select Fight, then press A to confirm target. One-shots everything.",
            "priority": "Just attack. These battles are trivial with Magitek."
        },
    },
    {
        "id": "narshe_guards",
        "name": "Narshe Guards Battle",
        "act": 1,
        "conditions": {
            "map_ids": list(range(21, 30)),
            "party_contains": ["Terra", "Wedge", "Vicks"],
            "notes": "Reached Narshe entrance. Guards attack. Map IDs 21+."
        },
        "objective": "Defeat the Narshe guards blocking the gate.",
        "instructions": [
            "Two guard fights happen automatically.",
            "Use Magitek commands - Bolt Beam destroys them.",
            "After the guards, you enter the Narshe mines."
        ],
        "battle_strategy": {
            "default": "Bolt Beam or Fire Beam. One shot kills.",
        },
    },
    {
        "id": "narshe_mines",
        "name": "Narshe Mines - To the Esper",
        "act": 1,
        "conditions": {
            "map_ids": list(range(23, 40)),
            "party_contains": ["Terra"],
            "notes": "Inside Narshe mines. Navigate to the frozen Esper."
        },
        "objective": "Navigate through the Narshe mines to reach the frozen Esper.",
        "instructions": [
            "Follow the mine path. It's mostly linear.",
            "Continue north/right through the caves.",
            "Random encounters: use Magitek attacks.",
            "Save point available - consider saving.",
            "At the end, you'll find the frozen Esper (Tritoch).",
            "Approaching the Esper triggers the Whelk boss fight."
        ],
        "battle_strategy": {
            "default": "Magitek attacks one-shot everything in the mines.",
        },
    },
    {
        "id": "whelk_boss",
        "name": "Boss: Whelk",
        "act": 1,
        "conditions": {
            "notes": "Boss fight triggered by approaching the frozen Esper. Whelk is a giant snail."
        },
        "objective": "Defeat the Whelk boss.",
        "instructions": [
            "IMPORTANT: Attack the HEAD only, NOT the shell!",
            "When Whelk retreats into its shell, STOP attacking.",
            "If you hit the shell, it counters with Mega Volt (heavy damage).",
            "Use Bolt Beam on the head when it's exposed.",
            "Heal with Heal Force if HP gets low.",
            "The head pops out periodically - attack during those windows."
        ],
        "battle_strategy": {
            "default": "Bolt Beam the HEAD. Do NOT attack the shell.",
            "heal_threshold": 30,
            "notes": "Whelk has 1600 HP on the head. Shell has 50000 HP - don't bother."
        },
    },
    {
        "id": "terra_alone_narshe",
        "name": "Terra Alone in Narshe",
        "act": 1,
        "conditions": {
            "party_size_max": 1,
            "party_contains": ["Terra"],
            "map_ids": list(range(40, 60)),
            "notes": "After the Esper scene, Terra wakes up alone in Arvis's house."
        },
        "objective": "Escape through the Narshe mines. Guards are chasing Terra.",
        "instructions": [
            "Talk to the old man (Arvis) in the house.",
            "He tells you to escape through the mines.",
            "Go through the back door into the mines.",
            "Navigate through the mines going north/right.",
            "Avoid or fight the guards chasing you.",
            "At a dead end, the floor collapses and Terra falls.",
            "Locke arrives to help."
        ],
        "battle_strategy": {
            "default": "Terra has Fire and Cure magic. Use Fire on enemies, Cure to heal.",
        },
    },
    {
        "id": "locke_rescue",
        "name": "Locke's Rescue - Narshe",
        "act": 1,
        "conditions": {
            "party_contains": ["Terra", "Locke"],
            "notes": "Locke has joined. Moogles may help in a battle."
        },
        "objective": "Escape Narshe with Locke's help.",
        "instructions": [
            "Locke joins the party.",
            "A multi-party battle may occur with Moogles.",
            "After escaping Narshe, head south to Figaro Castle.",
            "Cross the world map heading south/southwest."
        ],
        "battle_strategy": {
            "default": "Use Fight. Locke can Steal items from enemies.",
        },
    },
    {
        "id": "figaro_castle",
        "name": "Figaro Castle",
        "act": 1,
        "conditions": {
            "party_contains": ["Terra", "Locke"],
            "notes": "Large castle in the desert. Edgar is the king here."
        },
        "objective": "Meet Edgar at Figaro Castle. Rest and re-equip.",
        "instructions": [
            "Enter Figaro Castle from the south.",
            "Talk to people to find Edgar (upstairs in the throne room).",
            "Edgar joins the party.",
            "Shop for equipment and items if gold allows.",
            "Rest at the inn (free because Edgar is king).",
            "After events with Kefka, the castle dives underground.",
            "Head south toward South Figaro."
        ],
        "battle_strategy": {
            "default": "Edgar's Tools are powerful. Use AutoCrossbow for groups.",
        },
    },
    {
        "id": "south_figaro_cave",
        "name": "South Figaro Cave & Mt. Kolts",
        "act": 1,
        "conditions": {
            "party_contains": ["Edgar"],
            "notes": "After Figaro Castle events, heading toward South Figaro and Mt. Kolts."
        },
        "objective": "Travel through South Figaro Cave and climb Mt. Kolts to find Sabin.",
        "instructions": [
            "Pass through South Figaro Cave (short dungeon).",
            "Visit South Figaro town for shopping if needed.",
            "Head northeast to Mt. Kolts.",
            "Navigate up the mountain.",
            "Sabin is at the top - he joins after the Vargas boss."
        ],
        "battle_strategy": {
            "default": "Edgar: AutoCrossbow. Terra: Fire magic. Locke: Fight/Steal.",
            "boss_vargas": "Sabin appears mid-fight. Use his Blitz: Pummel (Left, Right, Left, A)."
        },
    },
    {
        "id": "returner_hideout",
        "name": "Returner Hideout & Lete River",
        "act": 1,
        "conditions": {
            "party_contains": ["Sabin"],
            "notes": "After Mt. Kolts, heading to the Returner Hideout."
        },
        "objective": "Visit the Returner Hideout, then raft down the Lete River.",
        "instructions": [
            "Enter the Returner Hideout (cave entrance).",
            "Talk to Banon. Accept his offer (say Yes for Gauntlet relic).",
            "Banon joins temporarily.",
            "Take the raft down the Lete River.",
            "On the raft: hold Up+A to auto-battle efficiently.",
            "At the river split, go LEFT to loop for EXP, or RIGHT to proceed.",
            "Boss: Ultros appears on the raft."
        ],
        "battle_strategy": {
            "default": "Banon's Health command heals the party for free. Use it every turn.",
            "boss_ultros": "Everyone attacks. Use Fire (Terra), AutoCrossbow (Edgar), Pummel (Sabin). Banon heals."
        },
    },
]

# General battle strategies the Director can reference
BATTLE_TIPS = {
    "magitek": "In Magitek armor, all characters have powerful beam attacks. Use them freely.",
    "healing_priority": "Keep HP above 50%. Use Cure/Potions/Tonics between battles if needed.",
    "boss_general": "Bosses telegraph attacks. Watch for pattern changes and heal proactively.",
    "steal": "Locke should try Steal on bosses - they often have rare items.",
    "save_often": "Save at every save point. Use Tent/Sleeping Bag to restore HP/MP before bosses.",
    "equipment": "Always equip the best available gear. Check shops in every town.",
    "grind": "If the party is struggling, grind a few levels near a save point.",
}

# Character-specific tips for the Director
CHARACTER_TIPS = {
    "Terra": "Strongest magic user early game. Use Fire on groups. Morph doubles magic damage but is temporary.",
    "Locke": "Fast attacker. Steal from enemies and bosses for rare items. Equip best weapon available.",
    "Edgar": "Tools are amazing: AutoCrossbow hits all enemies, Drill does big single-target damage. No MP cost.",
    "Sabin": "Blitz commands are powerful. Pummel (Left Right Left A) early. AuraBolt (Down Down Left A) at Lv6.",
    "Celes": "Runic absorbs enemy magic. Great for magic-heavy fights. Good magic user.",
    "Cyan": "SwdTech charges up. SwdTech 1 (Dispatch) is fast and strong. Higher techs take long to charge.",
    "Shadow": "Can Throw weapons/scrolls for big damage. Has a chance to randomly leave the party early game.",
    "Gau": "Leap on the Veldt to learn Rages. Stray Cat rage is great early (Catscratch = 4x damage).",
}


def get_current_objective(game_state):
    """
    Given the current game state, determine which walkthrough
    objective is most likely active.

    Returns the objective dict or None.
    """
    if not game_state:
        return None

    map_id = game_state.map_id
    party_names = [c.actor_name.lower() for c in game_state.party]

    for obj in WALKTHROUGH:
        conds = obj["conditions"]

        # Check map_ids if specified
        if "map_ids" in conds:
            if map_id not in conds["map_ids"]:
                continue

        # Check party composition if specified
        if "party_contains" in conds:
            required = [n.lower() for n in conds["party_contains"]]
            if not all(r in party_names for r in required):
                continue

        # Check party size constraints
        if "party_size_max" in conds:
            if len(game_state.party) > conds["party_size_max"]:
                continue

        return obj

    return None


def format_objective_for_director(objective):
    """Format an objective into a string the Director LLM can use."""
    if not objective:
        return "No matching walkthrough objective found. Use general FF6 knowledge to decide next action."

    lines = []
    lines.append(f"CURRENT OBJECTIVE: {objective['name']}")
    lines.append(f"Goal: {objective['objective']}")
    lines.append("")
    lines.append("Instructions:")
    for inst in objective["instructions"]:
        lines.append(f"  {inst}")

    if "battle_strategy" in objective:
        lines.append("")
        lines.append("Battle Strategy:")
        strat = objective["battle_strategy"]
        for key, val in strat.items():
            lines.append(f"  {key}: {val}")

    return "\n".join(lines)


def get_director_context(game_state):
    """
    Build the full context string for the Director, combining
    game state + walkthrough + tips.
    """
    lines = []

    # Game state
    if game_state:
        lines.append(game_state.full_summary())
        lines.append("")

    # Current objective from walkthrough (if matched)
    objective = get_current_objective(game_state)
    if objective:
        lines.append(format_objective_for_director(objective))
    else:
        lines.append("No specific walkthrough objective matched.")
        lines.append("Use your FF6 expert knowledge to decide what to do.")
    lines.append("")

    # General FF6 opening context (always included early game)
    if game_state and game_state.gold <= 3000:
        lines.append("FF6 OPENING SEQUENCE REMINDER:")
        lines.append("  1. Three Magitek armors (Terra, Wedge, Vicks) walk NORTH through snow to Narshe")
        lines.append("  2. They fight guards at the Narshe gate")
        lines.append("  3. Inside the mines, they find the frozen Esper")
        lines.append("  4. Whelk boss fight near the Esper")
        lines.append("  5. After Esper event, Terra wakes up alone")
        lines.append("  DIRECTION: Walk UP to go north toward Narshe. UP = toward top of screen.")
        lines.append("")

    # Relevant character tips
    if game_state:
        lines.append("CHARACTER TIPS:")
        for char in game_state.party:
            name = char.actor_name
            if name in CHARACTER_TIPS:
                lines.append(f"  {name}: {CHARACTER_TIPS[name]}")

    return "\n".join(lines)
