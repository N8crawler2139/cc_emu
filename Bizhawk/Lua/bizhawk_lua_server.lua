-- BizHawk Lua Socket Server for Python Communication
-- This script runs inside BizHawk and listens for commands from Python
-- Compatible with BizHawk 2.10+

-- Try different socket libraries that might be available
local socket = nil
pcall(function() socket = require("socket.core") end)
if not socket then
    pcall(function() socket = require("socket") end)
end

if not socket then
    print("ERROR: Socket library not available in this BizHawk build")
    print("BizHawk may not have Lua socket support compiled in")
    return
end

-- Configuration
local HOST = "127.0.0.1"
local PORT = 43883  -- Using different port than BirdsEye to avoid conflicts
local server = nil
local client = nil
local connected = false
local should_exit = false

-- Initialize socket server
function init_server()
    server = socket.tcp()
    if not server then
        print("Failed to create socket")
        return false
    end
    
    -- Try to enable socket reuse to avoid "address already in use" errors
    pcall(function() server:setoption("reuseaddr", true) end)
    
    local result, err = server:bind(HOST, PORT)
    if not result then
        if err and err:find("already in use") then
            print("Port " .. PORT .. " is already in use")
            print("Please stop any previous Lua scripts and try again")
            print("Or restart BizHawk to free the port")
        else
            print("Failed to bind socket: " .. (err or "unknown error"))
        end
        return false
    end
    
    local result, err = server:listen(1)
    if not result then
        print("Failed to listen on socket: " .. (err or "unknown error"))
        return false
    end
    
    server:settimeout(0)  -- Non-blocking
    print("Lua socket server started on " .. HOST .. ":" .. PORT)
    print("Waiting for Python client connection...")
    return true
end

-- Accept client connection
function accept_client()
    if not server then return false end
    
    local new_client, err = server:accept()
    if new_client then
        client = new_client
        client:settimeout(0)  -- Non-blocking
        connected = true
        print("Python client connected!")
        return true
    end
    return false
end

-- Send message to client
function send_message(message)
    if not client or not connected then return false end
    
    local result, err = client:send(message .. "\n")
    if not result then
        print("Send failed: " .. (err or "unknown error"))
        connected = false
        client = nil
        return false
    end
    return true
end

-- Receive message from client
function receive_message()
    if not client or not connected then return nil end
    
    local message, err = client:receive()
    if message then
        return message
    elseif err == "closed" then
        print("Client disconnected")
        connected = false
        client = nil
    end
    return nil
end

-- Process controller input command
function process_input_command(command)
    local parts = {}
    for part in command:gmatch("%S+") do
        table.insert(parts, part)
    end
    
    if #parts < 2 then return false end
    
    local action = parts[1]
    local button = parts[2]
    local duration = tonumber(parts[3]) or 6  -- Default 6 frames (0.1s at 60fps)
    
    if action == "PRESS" then
        -- Create input table for SNES controller
        local input = {
            A = false,
            B = false,
            X = false,
            Y = false,
            Start = false,
            Select = false,
            Up = false,
            Down = false,
            Left = false,
            Right = false,
            L = false,
            R = false
        }
        
        -- Set the requested button
        if input[button] ~= nil then
            input[button] = true
            
            -- Press the button for specified duration
            for frame = 1, duration do
                joypad.set(input, 1)  -- Player 1
                emu.frameadvance()
            end
            
            -- Release the button
            input[button] = false
            joypad.set(input, 1)
            emu.frameadvance()
            
            print("Pressed " .. button .. " for " .. duration .. " frames")
            return true
        else
            print("Unknown button: " .. button)
            return false
        end
    end
    
    return false
end

-- Main loop function
function main_loop()
    -- Try to accept client if not connected
    if not connected and server then
        accept_client()
    end
    
    -- Process incoming messages
    if connected then
        local message = receive_message()
        if message then
            print("Received: " .. message)
            
            if message == "PING" then
                send_message("PONG")
            elseif message == "STATUS" then
                local status = "CONNECTED:" .. (emu.islagged() and "LAGGED" or "RUNNING")
                send_message(status)
            elseif message:match("^PRESS ") then
                local success = process_input_command(message)
                send_message(success and "OK" or "ERROR")
            else
                send_message("UNKNOWN_COMMAND")
            end
        end
    end
end

-- Cleanup function
function cleanup()
    if client then
        pcall(function() client:close() end)
        client = nil
    end
    if server then
        pcall(function() server:close() end)
        server = nil
    end
    connected = false
    should_exit = true
    print("Socket server shut down")
end

-- Initialize on script start
print("=== BizHawk Lua Socket Server ===")
print("Compatible with BizHawk 2.10+")

if init_server() then
    print("Server initialized successfully")
    print("Run this script and connect from Python")
    print("Press ESC or stop the script to exit")
else
    print("Failed to initialize server")
    return
end

-- Main execution loop - runs while the script is active
local frame_count = 0
while not should_exit do
    main_loop()
    
    -- Advance frame if emulator is running, otherwise just wait
    if emu and emu.frameadvance then
        emu.frameadvance()
    else
        -- If frameadvance is not available, add a small delay
        os.execute("ping 127.0.0.1 -n 1 -w 16 > nul")  -- ~16ms delay
    end
    
    -- Periodic status update
    frame_count = frame_count + 1
    if frame_count % 3600 == 0 then  -- Every ~60 seconds at 60fps
        print("Socket server running - frame " .. frame_count)
    end
end

cleanup()