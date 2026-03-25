-- Final Fantasy 6 Input Control Script
-- Basic input control for FF6 AI player

-- Simple test: Press A button every 60 frames (1 second)
local frame_counter = 0

while true do
    frame_counter = frame_counter + 1
    
    -- Create input table
    local input = {}
    
    -- Press A button every 60 frames
    if frame_counter % 60 == 0 then
        input["A"] = true
        console.log("Pressing A at frame " .. frame_counter)
    end
    
    -- Hold right for 30 frames, then left for 30 frames (simple movement test)
    if (frame_counter % 120) < 60 then
        input["Right"] = true
    else
        input["Left"] = true
    end
    
    -- Apply the input
    joypad.set(input, 1)
    
    -- Advance one frame
    emu.frameadvance()
    
    -- Reset counter to prevent overflow
    if frame_counter > 10000 then
        frame_counter = 0
    end
end