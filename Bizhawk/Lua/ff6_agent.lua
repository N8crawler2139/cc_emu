-- FF6 Lua-First Agent
-- ALL gameplay logic runs here with frame-perfect timing.
-- Python only sends high-level commands (WALK, AGENT ON/OFF).
--
-- The agent is a state machine:
--   FIELD:  Walk in commanded direction, press A for NPCs/dialog
--   BATTLE: Execute full attack/heal turns with frame-perfect timing
--   DIALOG: Press A to advance text
--   IDLE:   Do nothing (manual control or waiting for Python)

print("=== FF6 Lua Agent ===")

-----------------------------------------------------------------------
-- CONFIG
-----------------------------------------------------------------------
local PROJECT_DIR = "C:/Users/Admin/anaconda3/envs/CC_Emu/"
local COMMAND_FILE = PROJECT_DIR .. "bizhawk_commands.txt"
local RESPONSE_FILE = PROJECT_DIR .. "bizhawk_responses.txt"
local GAMESTATE_FILE = PROJECT_DIR .. "bizhawk_gamestate.json"

local GAMESTATE_INTERVAL = 30   -- Write JSON every 30 frames
local BATTLE_TURN_COOLDOWN = 90 -- Frames between battle turn attempts
local WALK_FRAMES = 30          -- Frames to hold direction when walking
local DIALOG_PRESS_INTERVAL = 20 -- Frames between A presses in dialog

-----------------------------------------------------------------------
-- MEMORY ADDRESSES
-----------------------------------------------------------------------
local CHAR_BASE = 0x1600
local CHAR_SIZE = 37
local MAP_ID_ADDR = 0x1F64
local POS_X_ADDR = 0x00AF
local POS_Y_ADDR = 0x00B0
local GOLD_ADDR = 0x1860

-- Character offsets
local OFF_HP     = 0x09
local OFF_HP_MAX = 0x0B
local OFF_MP     = 0x0D
local OFF_MP_MAX = 0x0F
local OFF_LEVEL  = 0x08
local OFF_ACTOR  = 0x00
local OFF_NAME   = 0x02
local OFF_STATUS1 = 0x14

-----------------------------------------------------------------------
-- STATE
-----------------------------------------------------------------------
local agent_enabled = true  -- Agent autonomous mode
local walk_direction = "Up" -- Current walk direction
local frame_count = 0
local running = true

-- Battle state
local in_battle = false
local battle_turn_timer = 0
local last_battle_hp = ""
local battle_stuck_count = 0
local battles_won = 0

-- Field state
local last_field_pos = ""
local field_stuck_count = 0
local walk_timer = 0

-- Dialog state
local dialog_timer = 0

-- Stats
local agent_state = "idle"
local maps_visited = {}

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

function get_char_hp(char_index)
    local base = CHAR_BASE + (char_index * CHAR_SIZE)
    return read_u16(base + OFF_HP)
end

function get_char_hp_max(char_index)
    local base = CHAR_BASE + (char_index * CHAR_SIZE)
    return read_u16(base + OFF_HP_MAX)
end

function get_char_level(char_index)
    return mainmemory.read_u8(CHAR_BASE + (char_index * CHAR_SIZE) + OFF_LEVEL)
end

function get_char_actor_id(char_index)
    return mainmemory.read_u8(CHAR_BASE + (char_index * CHAR_SIZE) + OFF_ACTOR)
end

-- Check if any party character is below threshold HP %
function party_needs_healing(threshold)
    -- Check first 3 character slots (typical party size in opening)
    for _, ci in ipairs({0, 14, 15}) do  -- Terra=0, Wedge=14, Vicks=15
        local hp = get_char_hp(ci)
        local hp_max = get_char_hp_max(ci)
        if hp_max > 0 and hp > 0 and (hp / hp_max) < threshold then
            return true
        end
    end
    return false
end

-- Get a string hash of party HP for stuck detection
function get_hp_hash()
    local parts = {}
    for _, ci in ipairs({0, 14, 15}) do
        table.insert(parts, tostring(get_char_hp(ci)))
    end
    return table.concat(parts, ",")
end

-- Press a button for N frames (frame-perfect, no file I/O)
function press_button(button, frames)
    frames = frames or 6
    local input = {}
    input[button] = true
    for f = 1, frames do
        joypad.set(input, 1)
        emu.frameadvance()
        frame_count = frame_count + 1
    end
    -- Release
    joypad.set({}, 1)
    emu.frameadvance()
    frame_count = frame_count + 1
end

-- Hold a direction for N frames
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

-- Wait N frames (just advance without input)
function wait_frames(n)
    for f = 1, n do
        emu.frameadvance()
        frame_count = frame_count + 1
    end
end

-----------------------------------------------------------------------
-- STATE DETECTION
-----------------------------------------------------------------------
function detect_game_state()
    local x = get_pos_x()
    local y = get_pos_y()

    -- Battle: position x == 0 during battle screens
    if x == 0 then
        return "battle"
    end

    -- Field: normal gameplay with movement
    return "field"
end

-----------------------------------------------------------------------
-- BATTLE LOGIC (frame-perfect, all in Lua)
-----------------------------------------------------------------------
function execute_attack_turn()
    -- Full MagiTek attack: A (command) -> wait -> A (spell) -> wait -> A (target)
    -- In Magitek menu: first command = MagiTek, first spell = Fire Beam
    print("  BATTLE: Attack turn")
    press_button("A", 6)    -- Select MagiTek (first command)
    wait_frames(15)          -- Wait for submenu to open
    press_button("A", 6)    -- Select Fire Beam (first spell)
    wait_frames(15)          -- Wait for target select
    press_button("A", 6)    -- Select first target
end

function execute_heal_turn()
    -- Heal Force: A (MagiTek) -> Down Down Down (to Heal Force) -> A -> A (target)
    print("  BATTLE: Heal turn")
    press_button("A", 6)       -- Select MagiTek
    wait_frames(15)             -- Wait for submenu
    press_button("Down", 4)    -- Past Fire Beam
    wait_frames(3)
    press_button("Down", 4)    -- Past Bolt Beam
    wait_frames(3)
    press_button("Down", 4)    -- Past Ice Beam -> on Heal Force
    wait_frames(3)
    press_button("A", 6)       -- Select Heal Force
    wait_frames(15)
    press_button("A", 6)       -- Select target
end

function handle_battle()
    agent_state = "battle"

    -- Only attempt a turn every BATTLE_TURN_COOLDOWN frames
    -- This gives time for ATB to fill and animations to play
    if battle_turn_timer > 0 then
        battle_turn_timer = battle_turn_timer - 1
        return
    end

    -- Check if battle is progressing (HP changing)
    local hp_hash = get_hp_hash()
    if hp_hash == last_battle_hp then
        battle_stuck_count = battle_stuck_count + 1
        if battle_stuck_count > 5 then
            -- Stuck in battle (probably in wrong submenu)
            -- Press B to back out, then wait
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

    -- Decide: heal or attack
    if party_needs_healing(0.30) then
        execute_heal_turn()
    else
        execute_attack_turn()
    end

    -- Cooldown before next turn attempt
    battle_turn_timer = BATTLE_TURN_COOLDOWN
end

-----------------------------------------------------------------------
-- FIELD LOGIC
-----------------------------------------------------------------------
function handle_field()
    agent_state = "field"
    local pos_key = get_pos_x() .. "," .. get_pos_y()

    -- Track map changes
    local map = get_map_id()
    if not maps_visited[map] then
        maps_visited[map] = true
        print("  MAP CHANGE: now on map " .. map)
    end

    -- Check if position changed
    if pos_key == last_field_pos then
        field_stuck_count = field_stuck_count + 1
    else
        field_stuck_count = 0
        last_field_pos = pos_key
    end

    -- Stuck handling
    if field_stuck_count > 5 and field_stuck_count <= 10 then
        -- Might be dialog - press A
        press_button("A", 6)
        wait_frames(10)
        return
    elseif field_stuck_count > 10 and field_stuck_count <= 15 then
        -- Press B (menu overlay?)
        press_button("B", 6)
        wait_frames(10)
        return
    elseif field_stuck_count > 15 and field_stuck_count <= 25 then
        -- Try alternate directions to get around obstacles
        local dirs = {"Right", "Left", "Down", "Up", "Right", "Left", "Down", "Up", "Right", "Left"}
        local idx = field_stuck_count - 15
        if idx >= 1 and idx <= #dirs then
            local alt = dirs[idx]
            print("  FIELD: Trying " .. alt .. " to get around obstacle")
            hold_direction(alt, 30)
            wait_frames(5)
        end
        return
    elseif field_stuck_count > 25 then
        -- Reset and try again
        field_stuck_count = 0
    end

    -- Normal walking
    hold_direction(walk_direction, WALK_FRAMES)
end

-----------------------------------------------------------------------
-- BATTLE END DETECTION
-----------------------------------------------------------------------
local was_in_battle = false

function check_battle_transitions()
    local current = detect_game_state()

    if was_in_battle and current == "field" then
        -- Battle just ended!
        battles_won = battles_won + 1
        battle_stuck_count = 0
        battle_turn_timer = 0
        last_battle_hp = ""
        print("*** BATTLE WON! Total: " .. battles_won .. " ***")

        -- Press A a few times to clear victory screen
        for i = 1, 10 do
            press_button("A", 6)
            wait_frames(10)
            -- Check if we're back on field with position
            if get_pos_x() > 0 then
                break
            end
        end
    end

    if current == "battle" and not was_in_battle then
        print("*** BATTLE START ***")
        battle_turn_timer = 30  -- Short initial delay
        battle_stuck_count = 0
        last_battle_hp = ""
    end

    was_in_battle = (current == "battle")
    in_battle = was_in_battle
end

-----------------------------------------------------------------------
-- GAME STATE JSON (for Python monitoring)
-----------------------------------------------------------------------
-- FF6 text encoding
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
        local actor_id = mainmemory.read_u8(base + OFF_ACTOR)
        if actor_id ~= 0xFF then
            local hp = read_u16(base + OFF_HP)
            local hp_max = read_u16(base + OFF_HP_MAX)
            if hp_max > 0 then
                local name = read_ff6_name(base + OFF_NAME)
                local level = mainmemory.read_u8(base + OFF_LEVEL)
                local mp = read_u16(base + OFF_MP)
                local mp_max = read_u16(base + OFF_MP_MAX)
                table.insert(chars, string.format(
                    '{"index":%d,"actor_id":%d,"name":"%s","level":%d,"hp":%d,"hp_max":%d,"mp":%d,"mp_max":%d}',
                    ci, actor_id, json_escape(name), level, hp, hp_max, mp, mp_max
                ))
            end
        end
    end

    -- Map visited list
    local map_list = {}
    for m, _ in pairs(maps_visited) do
        table.insert(map_list, tostring(m))
    end

    local json = '{\n'
    json = json .. '  "frame": ' .. frame_count .. ',\n'
    json = json .. '  "agent_state": "' .. agent_state .. '",\n'
    json = json .. '  "agent_enabled": ' .. (agent_enabled and "true" or "false") .. ',\n'
    json = json .. '  "walk_direction": "' .. walk_direction .. '",\n'
    json = json .. '  "battles_won": ' .. battles_won .. ',\n'
    json = json .. '  "maps_visited": [' .. table.concat(map_list, ",") .. '],\n'
    json = json .. '  "field_stuck": ' .. field_stuck_count .. ',\n'
    json = json .. '  "gold": ' .. get_gold() .. ',\n'
    json = json .. '  "map_id": ' .. get_map_id() .. ',\n'
    json = json .. '  "position": {"x": ' .. get_pos_x() .. ', "y": ' .. get_pos_y() .. '},\n'
    json = json .. '  "in_battle": ' .. (in_battle and "true" or "false") .. ',\n'
    json = json .. '  "characters": [\n    ' .. table.concat(chars, ",\n    ") .. '\n  ]\n'
    json = json .. '}'

    local file = io.open(GAMESTATE_FILE, "w")
    if file then
        file:write(json)
        file:close()
    end
end

-----------------------------------------------------------------------
-- COMMAND FILE (Python -> Lua, high-level only)
-----------------------------------------------------------------------
function init_file_comm()
    local f = io.open(COMMAND_FILE, "w")
    if f then f:close() end
    local r = io.open(RESPONSE_FILE, "w")
    if r then r:write("READY\n"); r:close() end
    print("File comm ready")
    return true
end

function check_commands()
    local file = io.open(COMMAND_FILE, "r")
    if not file then return end
    local cmd = file:read("*line")
    file:close()
    if not cmd or cmd == "" then return end

    -- Clear command file
    local cf = io.open(COMMAND_FILE, "w")
    if cf then cf:close() end

    print("CMD: " .. cmd)
    local response = "OK"

    -- High-level commands
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
    elseif cmd == "GAMESTATE" then
        write_game_state()
        response = "OK: State written"
    elseif cmd:match("^PRESS ") then
        -- Still support manual button presses for Python control
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
    print("Failed to init")
    return
end

print("Agent running. Walk direction: " .. walk_direction)
write_game_state()

while running do
    -- Check for Python commands (high-level only)
    check_commands()

    -- Agent logic
    if agent_enabled then
        check_battle_transitions()

        local state = detect_game_state()
        if state == "battle" then
            handle_battle()
        else
            handle_field()
        end
    end

    -- Write game state periodically
    if frame_count % GAMESTATE_INTERVAL == 0 then
        write_game_state()
    end

    -- Normal frame advance (only if agent didn't already advance frames)
    emu.frameadvance()
    frame_count = frame_count + 1

    -- Status report
    if frame_count % 1800 == 0 then
        print("Frame " .. frame_count .. " | State: " .. agent_state ..
              " | Won: " .. battles_won .. " | Map: " .. get_map_id())
    end
end

write_game_state()
print("Agent stopped")
