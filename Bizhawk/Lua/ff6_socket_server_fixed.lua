-- FF6 Socket Server for BizHawk (Fixed Version)
-- Enhanced socket server with proper button mapping for SNES
local socket = require("socket.core")

-- Configuration
local HOST = "localhost"
local PORT = 9999

-- Server state
local server = nil
local client = nil
local is_running = false

-- SNES button mapping (BizHawk uses specific names)
local button_map = {
    -- Face buttons
    ["A"] = "A",
    ["B"] = "B", 
    ["X"] = "X",
    ["Y"] = "Y",
    -- Shoulder buttons
    ["L"] = "L",
    ["R"] = "R",
    -- Control buttons
    ["Start"] = "Start",
    ["Select"] = "Select",
    -- D-pad (case insensitive handling)
    ["up"] = "Up",
    ["down"] = "Down",
    ["left"] = "Left", 
    ["right"] = "Right",
    ["Up"] = "Up",
    ["Down"] = "Down",
    ["Left"] = "Left",
    ["Right"] = "Right"
}

console.log("Starting FF6 Socket Server (Fixed)...")

-- Initialize server
function init_server()
    server = socket.tcp()
    if not server then
        console.log("Failed to create TCP server")
        return false
    end
    
    server:settimeout(0) -- Non-blocking
    local result, err = server:bind(HOST, PORT)
    if not result then
        console.log("Failed to bind to " .. HOST .. ":" .. PORT .. " - " .. tostring(err))
        return false
    end
    
    result, err = server:listen()
    if not result then
        console.log("Failed to listen - " .. tostring(err))
        return false
    end
    
    console.log("Socket server started on " .. HOST .. ":" .. PORT)
    is_running = true
    return true
end

-- Accept client connections
function accept_client()
    if not server then return end
    
    local new_client, err = server:accept()
    if new_client then
        console.log("Client connected")
        client = new_client
        client:settimeout(0) -- Non-blocking
    end
end

-- Simple message parser (no JSON)
function parse_message(data)
    local parts = {}
    for part in data:gmatch("[^|]+") do
        table.insert(parts, part)
    end
    return parts
end

-- Process client messages
function process_messages()
    if not client then return end
    
    local data, err = client:receive("*l")
    if data then
        console.log("Received: " .. data)  -- Debug logging
        local parts = parse_message(data)
        if #parts > 0 then
            handle_message(parts)
        end
    elseif err == "closed" then
        console.log("Client disconnected")
        client = nil
    end
end

-- Handle incoming messages from Python
function handle_message(parts)
    local cmd = parts[1]
    local response = "OK"
    
    if cmd == "ping" then
        response = "pong"
        
    elseif cmd == "press_button" then
        local button = parts[2]
        if button then
            local mapped_button = button_map[button] or button
            console.log("Pressing button: " .. mapped_button)
            
            -- Create input table for this frame
            local input = {}
            input[mapped_button] = true
            
            -- Set the input
            joypad.set(input, 1)  -- Player 1
            
            -- Hold for a few frames to ensure registration
            for i = 1, 3 do
                emu.frameadvance()
                joypad.set(input, 1)
            end
            
            -- Release
            joypad.set({}, 1)
            
            response = "pressed_" .. button
        else
            response = "ERROR_missing_button"
        end
        
    elseif cmd == "press_direction" or cmd == "send_input" then
        local direction = parts[2]
        if direction then
            local mapped_direction = button_map[direction] or direction
            console.log("Pressing direction: " .. mapped_direction)
            
            -- Create input table
            local input = {}
            input[mapped_direction] = true
            
            -- Set the input
            joypad.set(input, 1)  -- Player 1
            
            -- Hold for specified frames (default 10)
            local frames = tonumber(parts[3]) or 10
            for i = 1, frames do
                emu.frameadvance()
                joypad.set(input, 1)
            end
            
            -- Release
            joypad.set({}, 1)
            
            response = "pressed_" .. direction
        else
            response = "ERROR_missing_direction"
        end
        
    elseif cmd == "read_memory" then
        local address_str = parts[2]
        if address_str then
            local address = tonumber(address_str)
            if address then
                local value = memory.read_u8(address)
                response = "memory_" .. tostring(value)
            else
                response = "ERROR_invalid_address"
            end
        else
            response = "ERROR_missing_address"
        end
        
    elseif cmd == "advance_frame" then
        emu.frameadvance()
        response = "frame_advanced"
        
    elseif cmd == "get_state" then
        local frame = emu.framecount()
        local paused = emu.ispaused() and "true" or "false"
        response = "state_" .. frame .. "_" .. paused
        
    elseif cmd == "reset_inputs" then
        joypad.set({}, 1)
        response = "inputs_reset"
        
    elseif cmd == "savestate" then
        local slot = tonumber(parts[2]) or 0
        savestate.save(slot)
        response = "savestate_success"
        
    elseif cmd == "loadstate" then
        local slot = tonumber(parts[2]) or 0
        savestate.load(slot)
        response = "loadstate_success"
        
    elseif cmd == "combo" then
        -- Handle combo inputs like "Up|A" or "Left|B"
        local combo_str = parts[2]
        if combo_str then
            local combo_parts = {}
            for part in combo_str:gmatch("[^+]+") do
                table.insert(combo_parts, part)
            end
            
            local input = {}
            for _, button in ipairs(combo_parts) do
                local mapped = button_map[button] or button
                input[mapped] = true
            end
            
            console.log("Combo input: " .. combo_str)
            joypad.set(input, 1)
            
            -- Hold combo for a few frames
            for i = 1, 5 do
                emu.frameadvance()
                joypad.set(input, 1)
            end
            
            joypad.set({}, 1)
            response = "combo_executed"
        else
            response = "ERROR_missing_combo"
        end
        
    else
        response = "ERROR_unknown_command: " .. cmd
    end
    
    send_response(response)
end

-- Send response back to client
function send_response(message)
    if client then
        client:send(message .. "\n")
        console.log("Sent: " .. message)
    end
end

-- Main loop
function main_loop()
    if not is_running then
        if not init_server() then
            console.log("Failed to initialize server")
            return
        end
    end
    
    accept_client()
    process_messages()
end

-- Register the main loop to run each frame
event.onframestart(main_loop)

console.log("FF6 Socket Server ready! Waiting for connections...")
console.log("Make sure Python client connects to localhost:9999")