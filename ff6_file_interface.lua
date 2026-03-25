-- FF6 File-based Interface for BizHawk
-- This uses file I/O instead of sockets for communication
print("Starting FF6 File Interface...")

local command_file = "emulator_commands.txt"
local response_file = "emulator_responses.txt"
local last_modified = 0

-- Clear existing files
local file = io.open(response_file, "w")
if file then
    file:write("ready\n")
    file:close()
end

-- Main processing loop
function process_commands()
    -- Check if command file exists and has been modified
    local file = io.open(command_file, "r")
    if not file then
        return
    end
    
    local content = file:read("*all")
    file:close()
    
    if not content or content == "" then
        return
    end
    
    -- Process command
    local parts = {}
    for part in content:gmatch("[^|]+") do
        table.insert(parts, part)
    end
    
    if #parts == 0 then
        return
    end
    
    local cmd = parts[1]
    local response = "OK"
    
    print("Processing command: " .. cmd)
    
    if cmd == "ping" then
        response = "pong"
        
    elseif cmd == "press_button" then
        local button = parts[2]
        if button then
            local input = {}
            input[button] = true
            joypad.set(input)
            response = "pressed_" .. button
            print("Pressed button: " .. button)
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
            print("Pressed direction: " .. direction)
        else
            response = "ERROR_missing_direction"
        end
        
    elseif cmd == "reset_inputs" then
        joypad.set({})
        response = "inputs_reset"
        
    elseif cmd == "get_frame" then
        local frame = emu.framecount()
        response = "frame_" .. frame
        
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
        
    else
        response = "ERROR_unknown_command"
    end
    
    -- Write response
    local resp_file = io.open(response_file, "w")
    if resp_file then
        resp_file:write(response .. "\n")
        resp_file:close()
        print("Response: " .. response)
    end
    
    -- Clear command file
    local cmd_file = io.open(command_file, "w")
    if cmd_file then
        cmd_file:write("")
        cmd_file:close()
    end
end

print("File interface ready. Monitoring for commands...")
print("Command file: " .. command_file)
print("Response file: " .. response_file)

-- Main loop - check for commands every frame
while true do
    process_commands()
    emu.frameadvance()
end