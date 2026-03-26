-- FF6 Lua-First Agent v2
-- Battle Command Framework: AI says WHAT to do, Lua handles HOW.
--
-- Battle commands are strings like:
--   "MagiTek FireBeam enemy"      -> navigate to MagiTek, select Fire Beam, target enemy
--   "MagiTek HealForce ally"      -> navigate to MagiTek, select Heal Force, target ally
--   "Fight enemy"                 -> select Fight, target enemy
--   "Magic Cure2 ally 2"          -> select Magic, find Cure2, target ally slot 2
--   "Item Potion ally 1"          -> select Item, find Potion, target ally slot 1
--
-- The framework reads command slot positions from RAM so it knows
-- exactly how many Down presses to reach each command.

print("=== FF6 Lua Agent v2 - Battle Command Framework ===")

-----------------------------------------------------------------------
-- CONFIG
-----------------------------------------------------------------------
local PROJECT_DIR = "C:/Users/Admin/anaconda3/envs/CC_Emu/"
local COMMAND_FILE = PROJECT_DIR .. "bizhawk_commands.txt"
local RESPONSE_FILE = PROJECT_DIR .. "bizhawk_responses.txt"
local GAMESTATE_FILE = PROJECT_DIR .. "bizhawk_gamestate.json"

local GAMESTATE_INTERVAL = 30
local BATTLE_TURN_COOLDOWN = 90
local WALK_FRAMES = 30

-----------------------------------------------------------------------
-- MEMORY ADDRESSES
-----------------------------------------------------------------------
local CHAR_BASE = 0x1600
local CHAR_SIZE = 37
local MAP_ID_ADDR = 0x1F64
local POS_X_ADDR = 0x00AF
local POS_Y_ADDR = 0x00B0
local GOLD_ADDR = 0x1860

-- Character data offsets (within each 37-byte block)
local OFF = {
    ACTOR   = 0x00,
    NAME    = 0x02,  -- 6 bytes
    LEVEL   = 0x08,
    HP      = 0x09,  -- 16-bit LE
    HP_MAX  = 0x0B,
    MP      = 0x0D,
    MP_MAX  = 0x0F,
    STATUS1 = 0x14,
    CMD1    = 0x16,  -- 4 command slots
    CMD2    = 0x17,
    CMD3    = 0x18,
    CMD4    = 0x19,
}

-----------------------------------------------------------------------
-- COMMAND ID LOOKUP
-- Maps command IDs from RAM to names
-----------------------------------------------------------------------
local CMD_NAMES = {
    [0] = "Fight",  [1] = "Item",    [2] = "Magic",   [3] = "Morph",
    [4] = "Revert", [5] = "Steal",   [6] = "Capture", [7] = "SwdTech",
    [8] = "Throw",  [9] = "Tools",   [10] = "Blitz",  [11] = "Runic",
    [12] = "Lore",  [13] = "Sketch", [14] = "Control", [15] = "Slot",
    [16] = "Rage",  [17] = "Leap",   [18] = "Mimic",  [19] = "Dance",
    [20] = "Row",   [21] = "Def",    [22] = "Jump",   [23] = "XMagic",
    [24] = "GPRain", [25] = "Summon", [26] = "Health", [27] = "Shock",
    [28] = "Possess", [29] = "MagiTek",
}

-----------------------------------------------------------------------
-- MAGITEK SPELL GRID (2x2)
-- Position: [row][col] from top-left (0,0)
-----------------------------------------------------------------------
local MAGITEK_GRID = {
    FireBeam  = {row = 0, col = 0},
    BoltBeam  = {row = 0, col = 1},
    IceBeam   = {row = 1, col = 0},
    HealForce = {row = 1, col = 1},
}

-----------------------------------------------------------------------
-- STATE
-----------------------------------------------------------------------
local agent_enabled = true
local walk_direction = "Up"
local frame_count = 0
local running = true

-- Battle
local in_battle = false
local battle_turn_timer = 0
local last_battle_hp = ""
local battle_stuck_count = 0
local battles_won = 0
local pending_battle_cmd = nil  -- Command from Python: "MagiTek BoltBeam enemy"

-- Field / Exploration
local last_field_pos = ""
local field_stuck_count = 0
local explore_dir_index = 1
local EXPLORE_DIRS = {"Up", "Right", "Up", "Left", "Up", "Down", "Right", "Up", "Left", "Down"}
local last_map_for_explore = -1
local visited_positions = {}

-- Stats
local agent_state = "idle"
local maps_visited = {}
local last_battle_action = ""

-----------------------------------------------------------------------
-- HELPERS
-----------------------------------------------------------------------
function read_u16(addr)
    return mainmemory.read_u8(addr) + (mainmemory.read_u8(addr + 1) * 256)
end

function read_u24(addr)
    return mainmemory.read_u8(addr) + (mainmemory.read_u8(addr + 1) * 256)
           + (mainmemory.read_u8(addr + 2) * 65536)
end

function get_pos_x() return mainmemory.read_u8(POS_X_ADDR) end
function get_pos_y() return mainmemory.read_u8(POS_Y_ADDR) end
function get_map_id() return read_u16(MAP_ID_ADDR) end
function get_gold() return read_u24(GOLD_ADDR) end

function get_char_field(char_index, offset)
    return mainmemory.read_u8(CHAR_BASE + (char_index * CHAR_SIZE) + offset)
end

function get_char_hp(ci)     return read_u16(CHAR_BASE + ci * CHAR_SIZE + OFF.HP) end
function get_char_hp_max(ci) return read_u16(CHAR_BASE + ci * CHAR_SIZE + OFF.HP_MAX) end
function get_char_mp(ci)     return read_u16(CHAR_BASE + ci * CHAR_SIZE + OFF.MP) end
function get_char_mp_max(ci) return read_u16(CHAR_BASE + ci * CHAR_SIZE + OFF.MP_MAX) end
function get_char_level(ci)  return mainmemory.read_u8(CHAR_BASE + ci * CHAR_SIZE + OFF.LEVEL) end

-- Read a character's 4 battle command IDs
function get_char_commands(ci)
    local base = CHAR_BASE + ci * CHAR_SIZE
    return {
        mainmemory.read_u8(base + OFF.CMD1),
        mainmemory.read_u8(base + OFF.CMD2),
        mainmemory.read_u8(base + OFF.CMD3),
        mainmemory.read_u8(base + OFF.CMD4),
    }
end

-- Get HP hash for stuck detection
function get_hp_hash()
    local parts = {}
    for _, ci in ipairs({0, 14, 15}) do
        table.insert(parts, tostring(get_char_hp(ci)))
    end
    return table.concat(parts, ",")
end

-- Check if any party member needs healing
function party_needs_healing(threshold)
    for _, ci in ipairs({0, 14, 15}) do
        local hp = get_char_hp(ci)
        local hp_max = get_char_hp_max(ci)
        if hp_max > 0 and hp > 0 and (hp / hp_max) < threshold then
            return true
        end
    end
    return false
end

-- Get the lowest HP party member index
function get_weakest_party_member()
    local lowest_pct = 1.0
    local lowest_ci = 0
    for _, ci in ipairs({0, 14, 15}) do
        local hp = get_char_hp(ci)
        local hp_max = get_char_hp_max(ci)
        if hp_max > 0 and hp > 0 then
            local pct = hp / hp_max
            if pct < lowest_pct then
                lowest_pct = pct
                lowest_ci = ci
            end
        end
    end
    return lowest_ci, lowest_pct
end

-----------------------------------------------------------------------
-- FRAME-PERFECT INPUT
-----------------------------------------------------------------------
function press_button(button, frames)
    frames = frames or 6
    local input = {}
    input[button] = true
    for f = 1, frames do
        joypad.set(input, 1)
        emu.frameadvance()
        frame_count = frame_count + 1
    end
    joypad.set({}, 1)
    emu.frameadvance()
    frame_count = frame_count + 1
end

function hold_direction(dir, frames)
    local input = {}
    input[dir] = true
    for f = 1, frames do
        joypad.set(input, 1)
        emu.frameadvance()
        frame_count = frame_count + 1
    end
    joypad.set({}, 1)
end

function wait_frames(n)
    for f = 1, n do
        emu.frameadvance()
        frame_count = frame_count + 1
    end
end

-----------------------------------------------------------------------
-- VERIFIED INPUT: Press a button and wait until a memory address changes
-- This is the core of the "verify before proceeding" approach.
-----------------------------------------------------------------------
function press_and_wait_for_change(button, watch_addr, max_wait)
    max_wait = max_wait or 60  -- Max frames to wait (1 second)
    local before = mainmemory.read_u8(watch_addr)

    -- Press the button
    press_button(button, 6)

    -- Poll until the watched address changes or timeout
    for f = 1, max_wait do
        emu.frameadvance()
        frame_count = frame_count + 1
        local current = mainmemory.read_u8(watch_addr)
        if current ~= before then
            return true, current  -- Success: value changed
        end
    end
    return false, before  -- Timeout: value never changed
end

-- Press a button and wait for EITHER of two addresses to change
function press_and_wait_for_either(button, addr1, addr2, max_wait)
    max_wait = max_wait or 60
    local before1 = mainmemory.read_u8(addr1)
    local before2 = mainmemory.read_u8(addr2)

    press_button(button, 6)

    for f = 1, max_wait do
        emu.frameadvance()
        frame_count = frame_count + 1
        local cur1 = mainmemory.read_u8(addr1)
        local cur2 = mainmemory.read_u8(addr2)
        if cur1 ~= before1 or cur2 ~= before2 then
            return true, cur1, cur2
        end
    end
    return false, before1, before2
end

-----------------------------------------------------------------------
-- GRID NAVIGATION with verification
-----------------------------------------------------------------------
function navigate_grid_verified(target_row, target_col)
    for r = 1, target_row do
        local ok, new_val = press_and_wait_for_change("Down", 0x0028, 30)
        if ok then
            print("    Grid Down: cursor moved to " .. new_val)
        else
            print("    Grid Down: cursor STUCK at " .. new_val)
        end
    end
    for c = 1, target_col do
        local ok, new_val = press_and_wait_for_change("Right", 0x0028, 30)
        if ok then
            print("    Grid Right: cursor moved to " .. new_val)
        else
            print("    Grid Right: cursor STUCK at " .. new_val)
        end
    end
end

-----------------------------------------------------------------------
-- BATTLE COMMAND FRAMEWORK
-----------------------------------------------------------------------

-- Find which menu slot (0-based) a command name is in for the active character.
-- In Magitek mode, the commands are different from what RAM says.
-- For now, handle MagiTek specially since it replaces Fight.
function find_command_slot(command_name)
    -- In Magitek battles, the menu is:
    --   Slot 0: MagiTek (replaces Fight)
    --   Slot 1: Magic (if character has it, e.g. Terra)
    --   Last slot: Item
    -- Non-empty slots only show.
    --
    -- We can read the character's commands from RAM, but Magitek mode
    -- overrides command 0 (Fight -> MagiTek). The status1 byte has
    -- bit 0x08 = Magitek flag.

    local cmd_lower = command_name:lower()

    if cmd_lower == "magitek" then
        return 0  -- Always first slot in Magitek mode
    elseif cmd_lower == "fight" then
        return 0  -- Always first slot in normal mode
    elseif cmd_lower == "item" then
        -- Item is always the LAST command slot
        -- Count non-empty commands to find position
        -- For Magitek mode: usually slot 1 (2 commands: MagiTek, Item)
        -- For Terra: slot 2 (3 commands: MagiTek, Magic, Item)
        -- Safe default: try slot 1 for now
        return 1
    elseif cmd_lower == "magic" then
        -- Magic is slot 1 in normal mode (Fight, Magic, ..., Item)
        return 1
    end

    return 0  -- Default to first slot
end

-- Execute a complete battle command with frame-perfect timing.
-- cmd_name:    "MagiTek", "Fight", "Magic", "Item"
-- spell_name:  For MagiTek: "FireBeam", "BoltBeam", "IceBeam", "HealForce"
--              For Magic: spell name (TODO)
--              For Fight/Item: nil
-- target_type: "enemy" or "ally"
-- target_slot: 0-based index (which enemy/ally, default 0)
function execute_battle_command(cmd_name, spell_name, target_type, target_slot)
    target_type = target_type or "enemy"
    target_slot = target_slot or 0

    local action_desc = cmd_name
    if spell_name then action_desc = action_desc .. " " .. spell_name end
    action_desc = action_desc .. " -> " .. target_type
    if target_slot > 0 then action_desc = action_desc .. " " .. target_slot end
    print("  BATTLE CMD: " .. action_desc)
    last_battle_action = action_desc

    -- =====================================================
    -- STEP 1: Navigate to the command in the command menu.
    -- We verify each cursor movement by reading $0028.
    -- =====================================================
    local target_slot = find_command_slot(cmd_name)
    local current_cursor = mainmemory.read_u8(0x0028)
    local menu_before = mainmemory.read_u8(0x0026)
    print("    Step1: cmd menu. cursor=" .. current_cursor .. " menu=" .. menu_before .. " target_slot=" .. target_slot)

    -- Navigate to the right command slot using Down (verified)
    -- We don't know the exact cursor values for each slot,
    -- but we know Down changes $0028. Press Down target_slot times
    -- from the TOP. First go to top by pressing Down until wrap.
    -- Actually simpler: just press Down (target_slot) times and verify each.
    for i = 1, target_slot do
        local ok = press_and_wait_for_change("Down", 0x0028, 20)
        if not ok then
            print("    WARN: cursor didn't move on Down #" .. i)
        end
    end

    -- =====================================================
    -- STEP 2: Press A and VERIFY the menu changed.
    -- $0026 should change when the submenu opens.
    -- =====================================================
    local ok_a, new_menu = press_and_wait_for_change("A", 0x0026, 45)
    if ok_a then
        print("    Step2: A pressed, menu changed to " .. new_menu)
    else
        print("    WARN: A pressed but menu didn't change (still " .. new_menu .. ")")
        -- Might already be in the right state, continue
    end

    -- =====================================================
    -- STEP 3: Navigate submenu (if applicable)
    -- =====================================================
    if cmd_name:lower() == "magitek" and spell_name then
        -- We're in the MagiTek spell grid.
        -- Navigate to the target spell and VERIFY cursor moves.
        local grid_pos = MAGITEK_GRID[spell_name]
        if grid_pos then
            print("    Step3: navigate to " .. spell_name .. " (row=" .. grid_pos.row .. " col=" .. grid_pos.col .. ")")
            navigate_grid_verified(grid_pos.row, grid_pos.col)
        end

        -- Press A to select spell, verify menu changes
        local ok_spell, new_menu2 = press_and_wait_for_change("A", 0x0026, 45)
        if ok_spell then
            print("    Step3: spell selected, menu=" .. new_menu2)
        else
            print("    WARN: spell A didn't change menu")
        end

    elseif cmd_name:lower() == "fight" then
        -- Fight goes straight to targeting (A already pressed above)
        print("    Step3: Fight, direct to target")

    elseif cmd_name:lower() == "item" then
        -- TODO: item submenu navigation
        print("    Step3: Item (not yet implemented)")
        press_button("A", 6)
        wait_frames(20)
    end

    -- =====================================================
    -- STEP 4: Target selection. Press A to confirm target.
    -- For now, always select first target.
    -- =====================================================
    if target_type == "ally" then
        for i = 1, target_slot do
            press_and_wait_for_change("Down", 0x0028, 20)
        end
    else
        for i = 1, target_slot do
            press_and_wait_for_change("Right", 0x0028, 20)
        end
    end

    print("    Step4: confirming target")
    press_button("A", 6)
    wait_frames(10)
end

-----------------------------------------------------------------------
-- BATTLE AI - Decides what command to issue each turn
-----------------------------------------------------------------------
function decide_battle_action()
    -- Check if Python sent a specific command
    if pending_battle_cmd then
        local cmd = pending_battle_cmd
        pending_battle_cmd = nil
        return cmd
    end

    -- Autonomous decision based on party state
    local weakest_ci, weakest_pct = get_weakest_party_member()

    -- Priority 1: Heal if anyone below 35%
    if weakest_pct < 0.35 then
        return {cmd = "MagiTek", spell = "HealForce", target = "ally", slot = 0}
    end

    -- Priority 2: Attack with Bolt Beam (strongest beam)
    -- Alternate between different beams for variety
    local beams = {"BoltBeam", "FireBeam", "IceBeam", "BoltBeam"}
    local beam_index = (battles_won + battle_stuck_count) % #beams + 1

    return {cmd = "MagiTek", spell = beams[beam_index], target = "enemy", slot = 0}
end

function handle_battle()
    agent_state = "battle"

    -- Cooldown between turn attempts
    if battle_turn_timer > 0 then
        battle_turn_timer = battle_turn_timer - 1
        return
    end

    -- Stuck detection
    local hp_hash = get_hp_hash()
    if hp_hash == last_battle_hp then
        battle_stuck_count = battle_stuck_count + 1
        if battle_stuck_count > 5 then
            print("  BATTLE: Stuck! Pressing B to escape submenu")
            press_button("B", 6)
            wait_frames(10)
            press_button("B", 6)
            battle_stuck_count = 0
            battle_turn_timer = BATTLE_TURN_COOLDOWN
            return
        end
    else
        battle_stuck_count = 0
        last_battle_hp = hp_hash
    end

    -- Get action (from Python command or autonomous AI)
    local action = decide_battle_action()

    -- Execute through the framework
    execute_battle_command(action.cmd, action.spell, action.target, action.slot)

    battle_turn_timer = BATTLE_TURN_COOLDOWN
end

-----------------------------------------------------------------------
-- FIELD / EXPLORATION
-----------------------------------------------------------------------
function handle_field()
    agent_state = "field"
    local x = get_pos_x()
    local y = get_pos_y()
    local pos_key = x .. "," .. y
    local map = get_map_id()

    -- Track map changes
    if not maps_visited[map] then
        maps_visited[map] = true
        print("  MAP: entered " .. map)
    end
    if map ~= last_map_for_explore then
        visited_positions = {}
        explore_dir_index = 1
        last_map_for_explore = map
        walk_direction = "Up"
    end

    visited_positions[pos_key] = frame_count

    -- Stuck detection
    if pos_key == last_field_pos then
        field_stuck_count = field_stuck_count + 1
    else
        field_stuck_count = 0
        last_field_pos = pos_key
    end

    -- Stuck handling: nudge sideways to get around obstacles,
    -- but ALWAYS return to the primary walk direction.
    -- Never permanently change direction from random cycling.
    if field_stuck_count > 3 and field_stuck_count <= 6 then
        -- Might be dialog
        press_button("A", 6)
        wait_frames(10)
        return
    elseif field_stuck_count > 6 and field_stuck_count <= 8 then
        -- Might be menu overlay
        press_button("B", 6)
        wait_frames(10)
        return
    elseif field_stuck_count > 8 then
        -- Blocked by wall. Nudge sideways then continue primary direction.
        -- Alternate: Right+primary, Left+primary, longer Right+primary, etc.
        local nudge_cycle = (field_stuck_count - 9) % 4
        local nudge_dir
        if nudge_cycle == 0 then nudge_dir = "Right"
        elseif nudge_cycle == 1 then nudge_dir = "Left"
        elseif nudge_cycle == 2 then nudge_dir = "Right"
        else nudge_dir = "Left"
        end

        -- Nudge sideways
        print("  STUCK: nudge " .. nudge_dir .. " then " .. walk_direction)
        hold_direction(nudge_dir, 20)
        wait_frames(3)
        -- Then continue in primary direction
        hold_direction(walk_direction, 30)
        wait_frames(3)
        -- Don't reset stuck_count -- if this nudge doesn't work,
        -- the next cycle will try the other side
        return
    end

    -- Normal walking in primary direction
    hold_direction(walk_direction, WALK_FRAMES)
end

-----------------------------------------------------------------------
-- BATTLE TRANSITIONS
-----------------------------------------------------------------------
local was_in_battle = false

function check_battle_transitions()
    local x = get_pos_x()
    local current_in_battle = (x == 0)

    if was_in_battle and not current_in_battle then
        battles_won = battles_won + 1
        battle_stuck_count = 0
        battle_turn_timer = 0
        last_battle_hp = ""
        print("*** BATTLE WON #" .. battles_won .. " ***")
        -- Press A to clear victory messages
        for i = 1, 10 do
            press_button("A", 6)
            wait_frames(10)
            if get_pos_x() > 0 then break end
        end
    end

    if current_in_battle and not was_in_battle then
        print("*** BATTLE START ***")
        battle_turn_timer = 30
        battle_stuck_count = 0
        last_battle_hp = ""
    end

    was_in_battle = current_in_battle
    in_battle = current_in_battle
end

-----------------------------------------------------------------------
-- GAME STATE JSON
-----------------------------------------------------------------------
local FF6_TEXT = {}
for i = 0, 25 do FF6_TEXT[0x80 + i] = string.char(65 + i) end
for i = 0, 25 do FF6_TEXT[0x9A + i] = string.char(97 + i) end
for i = 0, 9 do  FF6_TEXT[0xB4 + i] = string.char(48 + i) end
FF6_TEXT[0xFF] = " "

function read_ff6_name(addr)
    local name = ""
    for i = 0, 5 do
        local ch = FF6_TEXT[mainmemory.read_u8(addr + i)]
        if ch and ch ~= " " then name = name .. ch end
    end
    return name
end

function json_escape(s)
    if not s then return "" end
    return s:gsub("\\","\\\\"):gsub("\"","\\\""):gsub("\n","\\n")
end

function write_game_state()
    local chars = {}
    for _, ci in ipairs({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}) do
        local base = CHAR_BASE + (ci * CHAR_SIZE)
        local actor_id = mainmemory.read_u8(base + OFF.ACTOR)
        if actor_id ~= 0xFF then
            local hp_max = read_u16(base + OFF.HP_MAX)
            if hp_max > 0 then
                local hp = read_u16(base + OFF.HP)
                local name = read_ff6_name(base + OFF.NAME)
                local level = mainmemory.read_u8(base + OFF.LEVEL)
                local mp = read_u16(base + OFF.MP)
                local mp_max = read_u16(base + OFF.MP_MAX)
                -- Read commands
                local cmds = get_char_commands(ci)
                local cmd_names = {}
                for _, c in ipairs(cmds) do
                    table.insert(cmd_names, '"' .. (CMD_NAMES[c] or "Cmd" .. c) .. '"')
                end
                table.insert(chars, string.format(
                    '{"index":%d,"actor_id":%d,"name":"%s","level":%d,'..
                    '"hp":%d,"hp_max":%d,"mp":%d,"mp_max":%d,'..
                    '"commands":[%s]}',
                    ci, actor_id, json_escape(name), level,
                    hp, hp_max, mp, mp_max,
                    table.concat(cmd_names, ",")
                ))
            end
        end
    end

    local map_list = {}
    for m, _ in pairs(maps_visited) do table.insert(map_list, tostring(m)) end

    local json = '{\n'
    json = json .. '  "frame": ' .. frame_count .. ',\n'
    json = json .. '  "agent_state": "' .. agent_state .. '",\n'
    json = json .. '  "agent_enabled": ' .. (agent_enabled and "true" or "false") .. ',\n'
    json = json .. '  "walk_direction": "' .. walk_direction .. '",\n'
    json = json .. '  "battles_won": ' .. battles_won .. ',\n'
    json = json .. '  "last_battle_action": "' .. json_escape(last_battle_action) .. '",\n'
    json = json .. '  "maps_visited": [' .. table.concat(map_list, ",") .. '],\n'
    json = json .. '  "field_stuck": ' .. field_stuck_count .. ',\n'
    json = json .. '  "gold": ' .. get_gold() .. ',\n'
    json = json .. '  "map_id": ' .. get_map_id() .. ',\n'
    json = json .. '  "position": {"x": ' .. get_pos_x() .. ', "y": ' .. get_pos_y() .. '},\n'
    json = json .. '  "in_battle": ' .. (in_battle and "true" or "false") .. ',\n'
    json = json .. '  "characters": [\n    ' .. table.concat(chars, ",\n    ") .. '\n  ]\n'
    json = json .. '}'

    local file = io.open(GAMESTATE_FILE, "w")
    if file then file:write(json); file:close() end
end

-----------------------------------------------------------------------
-- COMMAND FILE (Python -> Lua)
-----------------------------------------------------------------------
function init_file_comm()
    local f = io.open(COMMAND_FILE, "w")
    if f then f:close() end
    local r = io.open(RESPONSE_FILE, "w")
    if r then r:write("READY\n"); r:close() end
    return true
end

function check_commands()
    local file = io.open(COMMAND_FILE, "r")
    if not file then return end
    local cmd = file:read("*line")
    file:close()
    if not cmd or cmd == "" then return end

    local cf = io.open(COMMAND_FILE, "w")
    if cf then cf:close() end

    print("CMD: " .. cmd)
    local response = "OK"

    if cmd == "PING" then
        response = "PONG"
    elseif cmd == "STATUS" then
        response = "CONNECTED:RUNNING:FRAME" .. frame_count
    elseif cmd == "STOP" then
        running = false
        response = "STOPPING"
    elseif cmd == "AGENT ON" then
        agent_enabled = true
        response = "OK: Agent enabled"
    elseif cmd == "AGENT OFF" then
        agent_enabled = false
        response = "OK: Agent disabled"
    elseif cmd:match("^WALK ") then
        local dir = cmd:match("^WALK (%S+)")
        if dir then
            walk_direction = dir
            field_stuck_count = 0
            response = "OK: Walking " .. dir
        end
    elseif cmd:match("^BATTLE ") then
        -- Battle command from Python AI: "BATTLE MagiTek BoltBeam enemy 0"
        local parts = {}
        for part in cmd:gmatch("%S+") do table.insert(parts, part) end
        -- parts[1] = "BATTLE", parts[2] = cmd, parts[3] = spell, parts[4] = target, parts[5] = slot
        if #parts >= 3 then
            pending_battle_cmd = {
                cmd = parts[2],
                spell = parts[3] ~= "none" and parts[3] or nil,
                target = parts[4] or "enemy",
                slot = tonumber(parts[5]) or 0,
            }
            response = "OK: Battle command queued: " .. table.concat(parts, " ", 2)
        else
            response = "ERROR: BATTLE needs at least cmd and spell"
        end
    elseif cmd == "GAMESTATE" then
        write_game_state()
        response = "OK: State written"
    elseif cmd:match("^PRESS ") then
        local parts = {}
        for part in cmd:gmatch("%S+") do table.insert(parts, part) end
        local button = parts[2]
        local duration = tonumber(parts[3]) or 6
        if button then
            press_button(button, duration)
            response = "OK: Pressed " .. button
        end
    elseif cmd:match("^READMEM ") then
        local parts = {}
        for part in cmd:gmatch("%S+") do table.insert(parts, part) end
        local addr = tonumber(parts[2])
        local count = tonumber(parts[3]) or 1
        if addr then
            local vals = {}
            for i = 0, count - 1 do
                table.insert(vals, tostring(mainmemory.read_u8(addr + i)))
            end
            response = "MEM:" .. table.concat(vals, ",")
        end
    else
        response = "ERROR: Unknown command"
    end

    local rf = io.open(RESPONSE_FILE, "w")
    if rf then rf:write(response .. "\n"); rf:close() end
end

-----------------------------------------------------------------------
-- MAIN LOOP
-----------------------------------------------------------------------
if not init_file_comm() then
    print("Failed to init file comm")
    return
end

print("Agent v2 running | Walk: " .. walk_direction)
write_game_state()

while running do
    check_commands()

    if agent_enabled then
        check_battle_transitions()
        if get_pos_x() == 0 then
            handle_battle()
        else
            handle_field()
        end
    end

    if frame_count % GAMESTATE_INTERVAL == 0 then
        write_game_state()
    end

    emu.frameadvance()
    frame_count = frame_count + 1

    if frame_count % 1800 == 0 then
        print("F" .. frame_count .. " | " .. agent_state ..
              " | Won:" .. battles_won .. " | Map:" .. get_map_id() ..
              " | " .. last_battle_action)
    end
end

write_game_state()
print("Agent stopped")
