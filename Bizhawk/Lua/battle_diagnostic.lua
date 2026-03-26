-- Battle Menu Diagnostic Script
-- Walks through each step of a battle turn and logs memory values.
-- Load this while in a battle with the command menu showing.
-- Results written to battle_diag_log.txt
--
-- This script does NOT play the game. It traces one complete turn
-- so we know EXACTLY which memory addresses to watch.

print("=== Battle Menu Diagnostic ===")
print("Make sure you are IN A BATTLE with a command menu visible!")

local PROJECT_DIR = "C:/Users/Admin/anaconda3/envs/CC_Emu/"
local LOG_FILE = PROJECT_DIR .. "battle_diag_log.txt"
local log_lines = {}

function log(msg)
    print(msg)
    table.insert(log_lines, msg)
end

function read_u16(addr)
    return mainmemory.read_u8(addr) + (mainmemory.read_u8(addr + 1) * 256)
end

function dump_battle_state(label)
    log("--- " .. label .. " ---")
    -- Key addresses to watch
    local addrs = {
        {0x0026, "MenuState"},
        {0x0028, "Cursor"},
        {0x0029, "CursorB"},
        {0x002A, "Unknown2A"},
        {0x002B, "Unknown2B"},
        {0x002C, "Unknown2C"},
        {0x002F, "Unknown2F"},
        {0x0014, "Unknown14"},
        {0x0015, "Unknown15"},
        {0x0016, "Unknown16"},
        {0x0017, "Unknown17"},
        {0x0018, "Unknown18"},
        {0x0019, "Unknown19"},
        {0x001A, "Unknown1A"},
        {0x001B, "Unknown1B"},
        {0x007B, "Unknown7B"},
        {0x007C, "Unknown7C"},
        {0x007E, "Unknown7E"},
        {0x00AF, "PosX"},
        {0x00B0, "PosY"},
    }

    -- Also dump $0024-$003F as a block
    local block1 = {}
    for i = 0x0024, 0x003F do
        table.insert(block1, string.format("%02X", mainmemory.read_u8(i)))
    end
    log("  $0024-$003F: " .. table.concat(block1, " "))

    -- Dump $0060-$0070
    local block2 = {}
    for i = 0x0060, 0x006F do
        table.insert(block2, string.format("%02X", mainmemory.read_u8(i)))
    end
    log("  $0060-$006F: " .. table.concat(block2, " "))

    -- Dump $7B00-$7B1F
    local block3 = {}
    for i = 0x7B00, 0x7B1F do
        table.insert(block3, string.format("%02X", mainmemory.read_u8(i)))
    end
    log("  $7B00-$7B1F: " .. table.concat(block3, " "))

    -- Individual key values
    for _, pair in ipairs(addrs) do
        local val = mainmemory.read_u8(pair[1])
        log(string.format("  $%04X (%s) = %d (0x%02X)", pair[1], pair[2], val, val))
    end
    log("")
end

function write_log()
    local f = io.open(LOG_FILE, "w")
    if f then
        f:write(table.concat(log_lines, "\n"))
        f:close()
        print("Log written to " .. LOG_FILE)
    end
end

-- Wait a few frames for things to settle
for i = 1, 30 do emu.frameadvance() end

-- STEP 0: Capture initial state (should be command menu visible)
dump_battle_state("INITIAL STATE (command menu should be visible)")

-- STEP 1: Press Down to move cursor
log(">>> Pressing DOWN...")
local input = {Down = true}
for f = 1, 8 do
    joypad.set(input, 1)
    emu.frameadvance()
end
joypad.set({}, 1)
for f = 1, 15 do emu.frameadvance() end
dump_battle_state("AFTER DOWN (cursor should have moved)")

-- STEP 2: Press Up to move back
log(">>> Pressing UP...")
input = {Up = true}
for f = 1, 8 do
    joypad.set(input, 1)
    emu.frameadvance()
end
joypad.set({}, 1)
for f = 1, 15 do emu.frameadvance() end
dump_battle_state("AFTER UP (cursor should be back at top)")

-- STEP 3: Press A to select first command (MagiTek)
log(">>> Pressing A (select command)...")
input = {A = true}
for f = 1, 8 do
    joypad.set(input, 1)
    emu.frameadvance()
end
joypad.set({}, 1)
-- Wait progressively and dump at intervals
for f = 1, 10 do emu.frameadvance() end
dump_battle_state("AFTER A +10 frames (submenu opening?)")
for f = 1, 20 do emu.frameadvance() end
dump_battle_state("AFTER A +30 frames (submenu should be open)")
for f = 1, 30 do emu.frameadvance() end
dump_battle_state("AFTER A +60 frames (definitely open now)")

-- STEP 4: We should be in MagiTek submenu now. Press Right.
log(">>> Pressing RIGHT (Fire Beam -> Bolt Beam)...")
input = {Right = true}
for f = 1, 8 do
    joypad.set(input, 1)
    emu.frameadvance()
end
joypad.set({}, 1)
for f = 1, 15 do emu.frameadvance() end
dump_battle_state("AFTER RIGHT (should be on Bolt Beam)")

-- STEP 5: Press Down (Bolt Beam -> Heal Force)
log(">>> Pressing DOWN (Bolt Beam -> Heal Force)...")
input = {Down = true}
for f = 1, 8 do
    joypad.set(input, 1)
    emu.frameadvance()
end
joypad.set({}, 1)
for f = 1, 15 do emu.frameadvance() end
dump_battle_state("AFTER DOWN (should be on Heal Force)")

-- STEP 6: Press B to cancel (back out of submenu)
log(">>> Pressing B (cancel/back out)...")
input = {B = true}
for f = 1, 8 do
    joypad.set(input, 1)
    emu.frameadvance()
end
joypad.set({}, 1)
for f = 1, 30 do emu.frameadvance() end
dump_battle_state("AFTER B (should be back at command menu)")

-- Done
log("=== DIAGNOSTIC COMPLETE ===")
write_log()
print("Diagnostic complete! Check " .. LOG_FILE)
