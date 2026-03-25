-- FF6 Socket Server for BizHawk
-- Simple socket server for Python communication
local socket = require("socket.core")

-- Configuration
local HOST = "localhost"
local PORT = 9999

-- Server state
local server = nil
local client = nil
local is_running = false

console.log("Starting FF6 Socket Server...")

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
            local input = {}
            input[button] = true
            joypad.set(input)
            response = "pressed_" .. button
        else
            response = "ERROR_missing_button"
        end
        
    elseif cmd == "press_direction" then
        local direction = parts[2]
        if direction then
            local input = {}
            input[direction] = true
            joypad.set(input)
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
        joypad.set({})
        response = "inputs_reset"
        
    elseif cmd == "savestate" then
        local slot = tonumber(parts[2]) or 0
        savestate.save("slot" .. slot)
        response = "savestate_success"
        
    elseif cmd == "loadstate" then
        local slot = tonumber(parts[2]) or 0
        savestate.load("slot" .. slot)
        response = "loadstate_success"
        
    else
        response = "ERROR_unknown_command"
    end
    
    send_response(response)
end

-- Send response back to Python
function send_response(response)
    if not client then return end
    
    local result, err = client:send(response .. "\n")
    if not result and err ~= "timeout" then
        console.log("Failed to send response: " .. tostring(err))
        client = nil
    end
end

-- Main update loop
function update()
    if not is_running then return end
    
    accept_client()
    process_messages()
end

-- Cleanup on exit
function cleanup()
    if client then
        client:close()
    end
    if server then
        server:close()
    end
    console.log("Socket server stopped")
end

-- Initialize server
if not init_server() then
    console.log("Failed to initialize socket server")
    return
end

console.log("Socket server ready - waiting for connections...")

-- Main loop (removed registerexit as it's not available in all BizHawk versions)
while true do
    update()
    emu.frameadvance()
end