-- BizHawk Diagnostic Script
-- This script will test different joypad methods and report what works

print("=== BizHawk Diagnostic Script ===")
print("Testing different joypad control methods...")

-- Test 1: Check if joypad functions exist
print("1. Checking joypad functions:")
if joypad then
    print("  - joypad table exists")
    if joypad.set then
        print("  - joypad.set function exists")
    else
        print("  - joypad.set function MISSING")
    end
    if joypad.get then
        print("  - joypad.get function exists")
    else
        print("  - joypad.get function MISSING")
    end
else
    print("  - joypad table MISSING")
end

-- Test 2: Check current input state
print("2. Current joypad state:")
if joypad and joypad.get then
    local current_input = joypad.get()
    for key, value in pairs(current_input) do
        print("  - " .. key .. ": " .. tostring(value))
    end
else
    print("  - Cannot read joypad state")
end

-- Test 3: Try setting A button with different methods
print("3. Testing A button press methods:")

-- Method 1: Basic joypad.set
if joypad and joypad.set then
    print("  Method 1: joypad.set({A = true})")
    joypad.set({A = true})
    emu.frameadvance()
    joypad.set({A = false})
    print("  - Executed without error")
end

-- Method 2: joypad.set with player number
if joypad and joypad.set then
    print("  Method 2: joypad.set({A = true}, 1)")
    joypad.set({A = true}, 1)
    emu.frameadvance()
    joypad.set({A = false}, 1)
    print("  - Executed without error")
end

-- Test 4: Check available controllers
print("4. Checking movie/input system:")
if movie then
    print("  - movie table exists")
    if movie.getinput then
        print("  - movie.getinput exists")
    end
else
    print("  - movie table missing")
end

print("5. Testing manual button press sequence...")
print("Pressing A button for 30 frames...")

for i = 1, 30 do
    joypad.set({A = true}, 1)
    emu.frameadvance()
end

joypad.set({A = false}, 1)
emu.frameadvance()

print("Button press sequence completed!")
print("=== Diagnostic Complete ===")