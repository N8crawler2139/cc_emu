-- Simple test to check if socket library is available in BizHawk
print("Testing Lua socket library...")

local socket_available, socket = pcall(require, "socket")

if socket_available then
    print("Socket library is available!")
    print("Socket version: " .. tostring(socket._VERSION))
    
    -- Try to create a simple server
    local server = socket.tcp()
    if server then
        print("TCP socket created successfully")
        
        local result, err = server:bind("localhost", 9999)
        if result then
            print("Bind successful on localhost:9999")
            
            result, err = server:listen()
            if result then
                print("Server is now listening on port 9999")
                print("SUCCESS: Socket server is working!")
                
                -- Keep server running for a bit
                server:settimeout(5) -- 5 second timeout
                local client, err = server:accept()
                if client then
                    print("Client connected!")
                    client:close()
                else
                    print("No client connected within timeout")
                end
                
                server:close()
            else
                print("Listen failed: " .. tostring(err))
            end
        else
            print("Bind failed: " .. tostring(err))
        end
    else
        print("Failed to create TCP socket")
    end
else
    print("Socket library is NOT available!")
    print("Error: " .. tostring(socket))
    print("BizHawk may not have socket support enabled")
end

print("Test complete")