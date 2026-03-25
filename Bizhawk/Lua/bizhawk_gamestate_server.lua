-- FF6 BizHawk Game State Server
-- Enhanced version of bizhawk_simple_server.lua with memory reading
-- Reads FF6 SNES RAM and writes structured game state to a JSON file
-- while still processing button input commands

print("=== FF6 Game State Server ===")
print("BizHawk 2.10+ | File-based communication + Memory reading")

-- Configuration
-- Use absolute paths so files always land in the project root
local PROJECT_DIR = "C:/Users/Admin/anaconda3/envs/CC_Emu/"
local COMMAND_FILE = PROJECT_DIR .. "bizhawk_commands.txt"
local RESPONSE_FILE = PROJECT_DIR .. "bizhawk_responses.txt"
local GAMESTATE_FILE = PROJECT_DIR .. "bizhawk_gamestate.json"
local running = true
local frame_count = 0
local GAMESTATE_INTERVAL = 30  -- Write game state every 30 frames (~0.5 sec)

-- Held buttons tracking
local held_buttons = {}
local held_timers = {}

-- FF6 WRAM Address Map
-- Character data: 37 ($25) bytes per character, 16 characters max
local CHAR_BASE = 0x1600
local CHAR_SIZE = 37
local CHAR_COUNT = 16

-- Character field offsets within each 37-byte block
local CHAR_OFFSET = {
    ACTOR_ID    = 0x00,
    GRAPHIC_ID  = 0x01,
    NAME_START  = 0x02,  -- 6 bytes
    LEVEL       = 0x08,
    HP          = 0x09,  -- 2 bytes LE
    HP_MAX      = 0x0B,  -- 2 bytes LE
    MP          = 0x0D,  -- 2 bytes LE
    MP_MAX      = 0x0F,  -- 2 bytes LE
    EXP         = 0x11,  -- 3 bytes LE
    STATUS1     = 0x14,
    STATUS2     = 0x15,
    COMMAND1    = 0x16,
    COMMAND2    = 0x17,
    COMMAND3    = 0x18,
    COMMAND4    = 0x19,
    VIGOR       = 0x1A,
    SPEED       = 0x1B,
    STAMINA     = 0x1C,
    MAG_PWR     = 0x1D,
    ESPER       = 0x1E,
    WEAPON      = 0x1F,
    SHIELD      = 0x20,
    HELMET      = 0x21,
    ARMOR       = 0x22,
    RELIC1      = 0x23,
    RELIC2      = 0x24,
}

-- Party slots (which character indices are in active party)
local PARTY_ADDR = 0x1850  -- 4 bytes, $FF = empty

-- Gold
local GOLD_ADDR = 0x1860  -- 3 bytes LE

-- Steps
local STEPS_ADDR = 0x1866  -- 4 bytes LE

-- Inventory: 256 item slots
local ITEM_ADDR = 0x1869      -- Item IDs (256 bytes)
local ITEM_QTY_ADDR = 0x1969  -- Item quantities (256 bytes)

-- Game state detection addresses
local MAP_ID_ADDR = 0x1F64       -- Current map (2 bytes)
local BATTLE_FLAG_ADDR = 0x3000  -- Non-zero when in battle (approximate)
local MENU_FLAG_ADDR = 0x0026    -- Menu state indicator
local GAME_MODE_ADDR = 0x0004    -- Game mode byte

-- X/Y position on map
local POS_X_ADDR = 0x00AF
local POS_Y_ADDR = 0x00B0

-- Timer (in-game clock)
local TIMER_HOURS_ADDR = 0x1863
local TIMER_MINS_ADDR = 0x1864
local TIMER_SECS_ADDR = 0x1865

-- Actor name lookup (by actor ID)
local ACTOR_NAMES = {
    [0] = "Terra",   [1] = "Locke",  [2] = "Cyan",   [3] = "Shadow",
    [4] = "Edgar",   [5] = "Sabin",  [6] = "Celes",  [7] = "Strago",
    [8] = "Relm",    [9] = "Setzer", [10] = "Mog",   [11] = "Gau",
    [12] = "Gogo",   [13] = "Umaro", [14] = "Wedge",  [15] = "Vicks",
    [16] = "Leo",    [17] = "Banon", [18] = "Ghost"
}

-- FF6 text encoding to ASCII lookup (common chars)
local FF6_TEXT = {}
for i = 0, 25 do FF6_TEXT[0x80 + i] = string.char(65 + i) end  -- A-Z
for i = 0, 25 do FF6_TEXT[0x9A + i] = string.char(97 + i) end  -- a-z
for i = 0, 9 do  FF6_TEXT[0xB4 + i] = string.char(48 + i) end  -- 0-9
FF6_TEXT[0xBE] = "!"
FF6_TEXT[0xBF] = "?"
FF6_TEXT[0xC0] = "/"
FF6_TEXT[0xC1] = ":"
FF6_TEXT[0xC2] = "\""
FF6_TEXT[0xC6] = "'"
FF6_TEXT[0xC7] = "-"
FF6_TEXT[0xC8] = "."
FF6_TEXT[0xFF] = " "

-----------------------------------------------------------------------
-- Helper: Read 16-bit little-endian from WRAM
-----------------------------------------------------------------------
function read_u16(addr)
    local lo = mainmemory.read_u8(addr)
    local hi = mainmemory.read_u8(addr + 1)
    return lo + (hi * 256)
end

-----------------------------------------------------------------------
-- Helper: Read 24-bit little-endian from WRAM
-----------------------------------------------------------------------
function read_u24(addr)
    local lo = mainmemory.read_u8(addr)
    local mid = mainmemory.read_u8(addr + 1)
    local hi = mainmemory.read_u8(addr + 2)
    return lo + (mid * 256) + (hi * 65536)
end

-----------------------------------------------------------------------
-- Helper: Read FF6 encoded name (6 bytes)
-----------------------------------------------------------------------
function read_ff6_name(addr)
    local name = ""
    for i = 0, 5 do
        local byte = mainmemory.read_u8(addr + i)
        local ch = FF6_TEXT[byte]
        if ch and ch ~= " " then
            name = name .. ch
        end
    end
    return name
end

-----------------------------------------------------------------------
-- Helper: Escape a string for JSON output (no unicode)
-----------------------------------------------------------------------
function json_escape(s)
    if not s then return "" end
    s = s:gsub("\\", "\\\\")
    s = s:gsub("\"", "\\\"")
    s = s:gsub("\n", "\\n")
    s = s:gsub("\r", "\\r")
    s = s:gsub("\t", "\\t")
    return s
end

-----------------------------------------------------------------------
-- Read one character block from RAM
-----------------------------------------------------------------------
function read_character(index)
    local base = CHAR_BASE + (index * CHAR_SIZE)
    local actor_id = mainmemory.read_u8(base + CHAR_OFFSET.ACTOR_ID)

    -- Skip empty/invalid slots
    if actor_id == 0xFF then
        return nil
    end

    local name_raw = read_ff6_name(base + CHAR_OFFSET.NAME_START)
    local actor_name = ACTOR_NAMES[actor_id] or ("Actor" .. actor_id)

    -- Use raw name if available, fall back to actor name
    local display_name = name_raw
    if display_name == "" then
        display_name = actor_name
    end

    local hp = read_u16(base + CHAR_OFFSET.HP)
    local hp_max = read_u16(base + CHAR_OFFSET.HP_MAX)
    local mp = read_u16(base + CHAR_OFFSET.MP)
    local mp_max = read_u16(base + CHAR_OFFSET.MP_MAX)
    local level = mainmemory.read_u8(base + CHAR_OFFSET.LEVEL)
    local exp = read_u24(base + CHAR_OFFSET.EXP)

    local vigor = mainmemory.read_u8(base + CHAR_OFFSET.VIGOR)
    local speed = mainmemory.read_u8(base + CHAR_OFFSET.SPEED)
    local stamina = mainmemory.read_u8(base + CHAR_OFFSET.STAMINA)
    local mag_pwr = mainmemory.read_u8(base + CHAR_OFFSET.MAG_PWR)

    local weapon = mainmemory.read_u8(base + CHAR_OFFSET.WEAPON)
    local shield = mainmemory.read_u8(base + CHAR_OFFSET.SHIELD)
    local helmet = mainmemory.read_u8(base + CHAR_OFFSET.HELMET)
    local armor = mainmemory.read_u8(base + CHAR_OFFSET.ARMOR)
    local relic1 = mainmemory.read_u8(base + CHAR_OFFSET.RELIC1)
    local relic2 = mainmemory.read_u8(base + CHAR_OFFSET.RELIC2)
    local esper = mainmemory.read_u8(base + CHAR_OFFSET.ESPER)

    local status1 = mainmemory.read_u8(base + CHAR_OFFSET.STATUS1)
    local status2 = mainmemory.read_u8(base + CHAR_OFFSET.STATUS2)

    local cmd1 = mainmemory.read_u8(base + CHAR_OFFSET.COMMAND1)
    local cmd2 = mainmemory.read_u8(base + CHAR_OFFSET.COMMAND2)
    local cmd3 = mainmemory.read_u8(base + CHAR_OFFSET.COMMAND3)
    local cmd4 = mainmemory.read_u8(base + CHAR_OFFSET.COMMAND4)

    -- Build JSON string for this character
    local json = string.format(
        '{"index":%d,"actor_id":%d,"actor_name":"%s","name":"%s",' ..
        '"level":%d,"hp":%d,"hp_max":%d,"mp":%d,"mp_max":%d,"exp":%d,' ..
        '"vigor":%d,"speed":%d,"stamina":%d,"mag_pwr":%d,' ..
        '"weapon":%d,"shield":%d,"helmet":%d,"armor":%d,"relic1":%d,"relic2":%d,"esper":%d,' ..
        '"status1":%d,"status2":%d,' ..
        '"commands":[%d,%d,%d,%d]}',
        index, actor_id, json_escape(actor_name), json_escape(display_name),
        level, hp, hp_max, mp, mp_max, exp,
        vigor, speed, stamina, mag_pwr,
        weapon, shield, helmet, armor, relic1, relic2, esper,
        status1, status2,
        cmd1, cmd2, cmd3, cmd4
    )
    return json
end

-----------------------------------------------------------------------
-- Read active party (which character indices are in the 4 party slots)
-----------------------------------------------------------------------
function read_party()
    local slots = {}
    for i = 0, 3 do
        local char_index = mainmemory.read_u8(PARTY_ADDR + i)
        if char_index ~= 0xFF then
            table.insert(slots, char_index)
        end
    end
    return slots
end

-----------------------------------------------------------------------
-- Read inventory (non-empty slots only)
-----------------------------------------------------------------------
function read_inventory()
    local items = {}
    local count = 0
    for i = 0, 255 do
        local item_id = mainmemory.read_u8(ITEM_ADDR + i)
        if item_id ~= 0xFF and item_id ~= 0x00 then
            local qty = mainmemory.read_u8(ITEM_QTY_ADDR + i)
            if qty > 0 then
                table.insert(items, string.format('{"slot":%d,"id":%d,"qty":%d}', i, item_id, qty))
                count = count + 1
            end
        end
        -- Cap at 100 items to keep JSON manageable
        if count >= 100 then break end
    end
    return items
end

-----------------------------------------------------------------------
-- Detect current game context (field, battle, menu, dialog, etc.)
-----------------------------------------------------------------------
function read_game_context()
    local game_mode = mainmemory.read_u8(GAME_MODE_ADDR)
    local menu_flag = mainmemory.read_u8(MENU_FLAG_ADDR)

    -- Try multiple detection methods
    -- Game mode byte gives a rough indicator
    local context = "unknown"

    -- Check common game mode values
    -- These may need tuning per testing, but common FF6 values:
    -- 0 = field, 1 = battle, 2 = menu, 3 = cutscene, etc.
    -- The exact meaning depends on the ROM version

    -- We read a range of diagnostic bytes to help identify state
    local diag = {}
    for i = 0, 7 do
        diag[i] = mainmemory.read_u8(GAME_MODE_ADDR + i)
    end

    return game_mode, menu_flag, diag
end

-----------------------------------------------------------------------
-- Build full game state JSON and write to file
-----------------------------------------------------------------------
function write_game_state()
    -- Characters
    local chars = {}
    for i = 0, CHAR_COUNT - 1 do
        local char_json = read_character(i)
        if char_json then
            table.insert(chars, char_json)
        end
    end

    -- Party
    local party_slots = read_party()
    local party_json_parts = {}
    for _, slot in ipairs(party_slots) do
        table.insert(party_json_parts, tostring(slot))
    end

    -- Gold
    local gold = read_u24(GOLD_ADDR)

    -- Steps
    local steps = mainmemory.read_u8(STEPS_ADDR) +
                  (mainmemory.read_u8(STEPS_ADDR + 1) * 256) +
                  (mainmemory.read_u8(STEPS_ADDR + 2) * 65536) +
                  (mainmemory.read_u8(STEPS_ADDR + 3) * 16777216)

    -- Timer
    local timer_h = mainmemory.read_u8(TIMER_HOURS_ADDR)
    local timer_m = mainmemory.read_u8(TIMER_MINS_ADDR)
    local timer_s = mainmemory.read_u8(TIMER_SECS_ADDR)

    -- Map / Position
    local map_id = read_u16(MAP_ID_ADDR)
    local pos_x = mainmemory.read_u8(POS_X_ADDR)
    local pos_y = mainmemory.read_u8(POS_Y_ADDR)

    -- Game context
    local game_mode, menu_flag, diag = read_game_context()

    -- Inventory
    local inv_items = read_inventory()

    -- Build diagnostic bytes string
    local diag_parts = {}
    for i = 0, 7 do
        table.insert(diag_parts, tostring(diag[i]))
    end

    -- Assemble full JSON
    local json = '{\n'
    json = json .. '  "frame": ' .. frame_count .. ',\n'
    json = json .. '  "gold": ' .. gold .. ',\n'
    json = json .. '  "steps": ' .. steps .. ',\n'
    json = json .. '  "play_time": "' .. string.format("%02d:%02d:%02d", timer_h, timer_m, timer_s) .. '",\n'
    json = json .. '  "map_id": ' .. map_id .. ',\n'
    json = json .. '  "position": {"x": ' .. pos_x .. ', "y": ' .. pos_y .. '},\n'
    json = json .. '  "game_mode": ' .. game_mode .. ',\n'
    json = json .. '  "menu_flag": ' .. menu_flag .. ',\n'
    json = json .. '  "diag_bytes": [' .. table.concat(diag_parts, ",") .. '],\n'
    json = json .. '  "party_slots": [' .. table.concat(party_json_parts, ",") .. '],\n'
    json = json .. '  "characters": [\n    ' .. table.concat(chars, ",\n    ") .. '\n  ],\n'
    json = json .. '  "inventory": [\n    ' .. table.concat(inv_items, ",\n    ") .. '\n  ]\n'
    json = json .. '}'

    -- Write to file
    local file = io.open(GAMESTATE_FILE, "w")
    if file then
        file:write(json)
        file:close()
    end
end

-----------------------------------------------------------------------
-- File communication (same as bizhawk_simple_server.lua)
-----------------------------------------------------------------------
function init_file_comm()
    local cmd_file = io.open(COMMAND_FILE, "w")
    if cmd_file then cmd_file:close() end

    local resp_file = io.open(RESPONSE_FILE, "w")
    if resp_file then
        resp_file:write("READY\n")
        resp_file:close()
    end

    print("File communication initialized")
    print("Commands via: " .. COMMAND_FILE)
    print("Responses to: " .. RESPONSE_FILE)
    print("Game state to: " .. GAMESTATE_FILE)
    return true
end

function read_command()
    local file = io.open(COMMAND_FILE, "r")
    if not file then return nil end

    local command = file:read("*line")
    file:close()

    if command and command ~= "" then
        local clear_file = io.open(COMMAND_FILE, "w")
        if clear_file then clear_file:close() end
        return command
    end

    return nil
end

function write_response(response)
    local file = io.open(RESPONSE_FILE, "w")
    if file then
        file:write(response .. "\n")
        file:close()
        return true
    end
    return false
end

-----------------------------------------------------------------------
-- Process input commands (PRESS, HOLD, RELEASE)
-----------------------------------------------------------------------
function process_input_command(command)
    local parts = {}
    for part in command:gmatch("%S+") do
        table.insert(parts, part)
    end

    if #parts < 2 then return "ERROR: Invalid command format" end

    local action = parts[1]
    local button = parts[2]
    local duration = tonumber(parts[3]) or 6

    local valid_buttons = {
        A=true, B=true, X=true, Y=true,
        Start=true, Select=true,
        Up=true, Down=true, Left=true, Right=true,
        L=true, R=true
    }

    if not valid_buttons[button] then
        return "ERROR: Unknown button " .. button
    end

    if action == "PRESS" then
        local input = {}
        input[button] = true
        for frame = 1, duration do
            -- Also apply any held buttons
            for hb, _ in pairs(held_buttons) do
                input[hb] = true
            end
            joypad.set(input, 1)
            emu.frameadvance()
            frame_count = frame_count + 1
            -- Write game state during long presses
            if frame_count % GAMESTATE_INTERVAL == 0 then
                write_game_state()
            end
        end
        -- Release press but keep holds
        local release_input = {}
        for hb, _ in pairs(held_buttons) do
            release_input[hb] = true
        end
        joypad.set(release_input, 1)
        emu.frameadvance()
        frame_count = frame_count + 1
        return "OK: Pressed " .. button .. " for " .. duration .. " frames"

    elseif action == "HOLD" then
        held_buttons[button] = true
        if duration == -1 then
            held_timers[button] = -1
            return "OK: Holding " .. button .. " indefinitely"
        else
            held_timers[button] = duration
            return "OK: Holding " .. button .. " for " .. duration .. " frames"
        end

    elseif action == "RELEASE" then
        held_buttons[button] = nil
        held_timers[button] = nil
        return "OK: Released " .. button

    else
        return "ERROR: Unknown action " .. action
    end
end

-----------------------------------------------------------------------
-- Main loop
-----------------------------------------------------------------------
function main_loop()
    -- Process held button timers
    for button, timer in pairs(held_timers) do
        if timer ~= -1 then
            held_timers[button] = timer - 1
            if held_timers[button] <= 0 then
                held_buttons[button] = nil
                held_timers[button] = nil
                print("Hold expired: " .. button)
            end
        end
    end

    -- Apply held buttons
    if next(held_buttons) then
        local input = {}
        for button, _ in pairs(held_buttons) do
            input[button] = true
        end
        joypad.set(input, 1)
    end

    -- Check for commands
    local command = read_command()
    if command then
        print("CMD: " .. command)

        local response
        if command == "PING" then
            response = "PONG"
        elseif command == "STATUS" then
            response = "CONNECTED:RUNNING:FRAME" .. frame_count
        elseif command == "STOP" then
            response = "STOPPING"
            running = false
        elseif command == "GAMESTATE" then
            -- Force immediate game state write
            write_game_state()
            response = "OK: Game state written to " .. GAMESTATE_FILE
        elseif command:match("^PRESS ") or command:match("^HOLD ") or command:match("^RELEASE ") then
            response = process_input_command(command)
        elseif command:match("^READMEM ") then
            -- Read arbitrary memory: READMEM <addr> [count]
            local parts = {}
            for part in command:gmatch("%S+") do
                table.insert(parts, part)
            end
            local addr = tonumber(parts[2])
            local count = tonumber(parts[3]) or 1
            if addr then
                local values = {}
                for i = 0, count - 1 do
                    table.insert(values, tostring(mainmemory.read_u8(addr + i)))
                end
                response = "MEM:" .. table.concat(values, ",")
            else
                response = "ERROR: Invalid address"
            end
        else
            response = "ERROR: Unknown command"
        end

        write_response(response)
        print("RSP: " .. response)
    end
end

-----------------------------------------------------------------------
-- Initialize
-----------------------------------------------------------------------
if not init_file_comm() then
    print("Failed to initialize file communication")
    return
end

print("FF6 Game State Server running")
print("Dumping game state every " .. GAMESTATE_INTERVAL .. " frames")
print("Send STOP to exit")

-- Write initial game state
write_game_state()

-----------------------------------------------------------------------
-- Main execution loop
-----------------------------------------------------------------------
while running do
    main_loop()

    emu.frameadvance()
    frame_count = frame_count + 1

    -- Periodic game state dump
    if frame_count % GAMESTATE_INTERVAL == 0 then
        write_game_state()
    end

    -- Periodic status
    if frame_count % 3600 == 0 then
        print("Running - frame " .. frame_count)
    end
end

-- Cleanup
write_response("STOPPED")
print("Server stopped cleanly")
