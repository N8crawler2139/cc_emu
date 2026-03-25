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

-- Command queue system
local command_queue = {}
local current_button_state = {}
local button_hold_frames = {}

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

-- Add command to queue
function queue_command(command)
    table.insert(command_queue, command)
end

-- Process next command from queue
function process_queue()
    if #command_queue > 0 then
        local command = table.remove(command_queue, 1)
        return command
    end
    return nil
end

-- Update button states for holding
function update_button_states()
    for button, frames_remaining in pairs(button_hold_frames) do
        if frames_remaining > 0 then
            current_button_state[button] = true
            button_hold_frames[button] = frames_remaining - 1
        else
            current_button_state[button] = false
            button_hold_frames[button] = nil
        end
    end
end

-- Apply current button state to joypad
function apply_button_state()
    local joypad_state = {}
    for button, is_pressed in pairs(current_button_state) do
        if is_pressed then
            joypad_state[button] = true
        end
    end
    if next(joypad_state) then
        joypad.set(joypad_state)
    end
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
    
    -- Complete SNES controller support with P1 prefix
    local button_map = {
        -- Action buttons
        ["A"] = "P1 A",
        ["B"] = "P1 B", 
        ["X"] = "P1 X",
        ["Y"] = "P1 Y",
        
        -- D-Pad
        ["Up"] = "P1 Up",
        ["Down"] = "P1 Down", 
        ["Left"] = "P1 Left",
        ["Right"] = "P1 Right",
        
        -- Shoulder buttons
        ["L"] = "P1 L",
        ["R"] = "P1 R",
        
        -- System buttons
        ["Start"] = "P1 Start",
        ["Select"] = "P1 Select"
    }
    
    local bizhawk_button = button_map[button]
    if not bizhawk_button then
        return "ERROR: Unsupported button " .. button .. ". Valid buttons: " .. table.concat({"A", "B", "X", "Y", "Up", "Down", "Left", "Right", "L", "R", "Start", "Select"}, ", ")
    end
    
    if action == "PRESS" then
        print("Processing PRESS command for button: " .. button .. " duration: " .. duration)
        
        -- Use new button state system for more reliable input
        button_hold_frames[bizhawk_button] = duration
        
        print("Queued button press: " .. button .. " for " .. duration .. " frames")
        return "OK: Queued " .. button .. " press for " .. duration .. " frames"
        
    elseif action == "HOLD" then
        print("Processing HOLD command for button: " .. button .. " duration: " .. duration)
        
        -- Start holding button indefinitely or for specified duration
        if duration == -1 then
            current_button_state[bizhawk_button] = true
            print("Started holding button: " .. button .. " (indefinite)")
            return "OK: Started holding " .. button
        else
            -- For finite duration holds, use the button hold frames system
            button_hold_frames[bizhawk_button] = duration
            print("Holding button: " .. button .. " for " .. duration .. " frames")
            return "OK: Holding " .. button .. " for " .. duration .. " frames"
        end
        
    elseif action == "RELEASE" then
        print("Processing RELEASE command for button: " .. button)
        
        -- Release button
        current_button_state[bizhawk_button] = false
        button_hold_frames[bizhawk_button] = nil
        
        print("Released button: " .. button)
        return "OK: Released " .. button
        
    else
        return "ERROR: Unknown action " .. action .. ". Valid actions: PRESS, HOLD, RELEASE"
    end
end

-- Main loop
function main_loop()
    -- Check for new commands from file
    local command = read_command()
    if command then
        print("Received command: " .. command)
        queue_command(command)
    end
    
    -- Process one queued command per frame
    local queued_command = process_queue()
    if queued_command then
        print("Processing queued command: " .. queued_command)
        
        local response
        if queued_command == "PING" then
            response = "PONG"
        elseif queued_command == "STATUS" then
            response = "CONNECTED:RUNNING:FRAME" .. frame_count .. ":QUEUE" .. #command_queue
        elseif queued_command == "STOP" then
            response = "STOPPING"
            running = false
        elseif queued_command:match("^PRESS ") or queued_command:match("^HOLD ") or queued_command:match("^RELEASE ") then
            response = process_input_command(queued_command)
        else
            response = "ERROR: Unknown command"
        end
        
        write_response(response)
        print("Sent response: " .. response)
    end
    
    -- Update button states and apply to joypad
    update_button_states()
    apply_button_state()
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