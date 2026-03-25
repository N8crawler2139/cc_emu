-- Simple BizHawk Communication Script
-- This version uses file-based communication instead of sockets
-- More compatible with different BizHawk versions

print("=== BizHawk Simple File Communication ===")
print("Compatible with BizHawk 2.10+ (no socket dependencies)")

-- Configuration
local COMMAND_FILE = "bizhawk_commands.txt"
local RESPONSE_FILE = "bizhawk_responses.txt" 
local running = true
local frame_count = 0

-- Initialize by clearing old command/response files
function init_file_comm()
    local cmd_file = io.open(COMMAND_FILE, "w")
    if cmd_file then
        cmd_file:close()
    end
    
    local resp_file = io.open(RESPONSE_FILE, "w")
    if resp_file then
        resp_file:write("READY\n")
        resp_file:close()
    end
    
    print("File communication initialized")
    print("Python can now send commands via: " .. COMMAND_FILE)
    print("Responses will be written to: " .. RESPONSE_FILE)
    return true
end

-- Read command from file
function read_command()
    local file = io.open(COMMAND_FILE, "r")
    if not file then return nil end
    
    local command = file:read("*line")
    file:close()
    
    if command and command ~= "" then
        -- Clear the command file after reading
        local clear_file = io.open(COMMAND_FILE, "w")
        if clear_file then clear_file:close() end
        return command
    end
    
    return nil
end

-- Write response to file
function write_response(response)
    local file = io.open(RESPONSE_FILE, "w")
    if file then
        file:write(response .. "\n")
        file:close()
        return true
    end
    return false
end

-- Process controller input command
function process_input_command(command)
    local parts = {}
    for part in command:gmatch("%S+") do
        table.insert(parts, part)
    end
    
    if #parts < 2 then return "ERROR: Invalid command format" end
    
    local action = parts[1]
    local button = parts[2]
    local duration = tonumber(parts[3]) or 6  -- Default 6 frames
    
    if action == "PRESS" then
        -- Create input table for SNES controller
        local input = {
            A = false, B = false, X = false, Y = false,
            Start = false, Select = false,
            Up = false, Down = false, Left = false, Right = false,
            L = false, R = false
        }
        
        -- Validate button exists
        if input[button] == nil then
            return "ERROR: Unknown button " .. button
        end
        
        -- Press the button for specified duration
        input[button] = true
        for frame = 1, duration do
            joypad.set(input, 1)  -- Player 1
            emu.frameadvance()
        end
        
        -- Release the button
        input[button] = false
        joypad.set(input, 1)
        emu.frameadvance()
        
        return "OK: Pressed " .. button .. " for " .. duration .. " frames"
    else
        return "ERROR: Unknown action " .. action
    end
end

-- Main loop
function main_loop()
    local command = read_command()
    if command then
        print("Received command: " .. command)
        
        local response
        if command == "PING" then
            response = "PONG"
        elseif command == "STATUS" then
            response = "CONNECTED:RUNNING:FRAME" .. frame_count
        elseif command == "STOP" then
            response = "STOPPING"
            running = false
        elseif command:match("^PRESS ") then
            response = process_input_command(command)
        else
            response = "ERROR: Unknown command"
        end
        
        write_response(response)
        print("Sent response: " .. response)
    end
end

-- Initialize file communication
if not init_file_comm() then
    print("Failed to initialize file communication")
    return
end

print("Script running - waiting for commands...")
print("Send STOP command to exit cleanly")

-- Main execution loop
while running do
    main_loop()
    
    -- Advance frame 
    emu.frameadvance()
    frame_count = frame_count + 1
    
    -- Periodic status update
    if frame_count % 3600 == 0 then  -- Every ~60 seconds at 60fps
        print("Script running - frame " .. frame_count)
    end
end

-- Cleanup
write_response("STOPPED")
print("Script stopped cleanly")