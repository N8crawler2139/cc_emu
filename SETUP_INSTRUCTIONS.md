# 🎮 BizHawk SNES Controller Setup Instructions (Updated for BizHawk 2.10+)

## ⚠️ IMPORTANT: New Lua Socket Approach
This project now uses **Lua scripting** instead of BirdsEye external tool due to BizHawk 2.10 compatibility issues.

## Quick Start Guide

### Step 1: Start the Flask Server
```bash
python app.py
```
The server will start at: http://localhost:5000

### Step 2: Launch BizHawk
Either:
- **Option A:** Use the web interface "🚀 Launch BizHawk & Connect" button
- **Option B:** Manually launch BizHawk with Final Fantasy III ROM

### Step 3: Load Lua Script (CRITICAL!)
This is the **most important step** - without this, Python cannot control BizHawk:

1. In BizHawk, go to: **Tools → Lua Console**
2. In the Lua Console window: **Script → Open Script**
3. Navigate to the project folder and select: **`bizhawk_lua_server.lua`**
4. The script will start and you should see: `"Lua socket server started on 127.0.0.1:43883"`
5. **Keep the Lua Console window open** during automation

### Step 4: Connect Python to BizHawk
- Use the "🔗 Connect to BizHawk" button in the web interface
- Or try the "⏩ Skip FF3 Intro" button directly

## Troubleshooting

### "Connection failed" error:
- Make sure Lua script is loaded and running (Step 3)
- Check that Lua Console shows "Lua socket server started on 127.0.0.1:43883"
- Verify the Lua Console window stays open
- Check Windows firewall isn't blocking port 43883

### BizHawk won't launch:
- Check that ROM path is correct: `Bizhawk\SNES\Final Fantasy III (USA).zip`
- Verify BizHawk executable exists: `Bizhawk\EmuHawk.exe`

### ROM won't load:
- Make sure the ROM file isn't corrupted
- Try loading the ROM manually first to test

## Files Created:
- `bizhawk_controller_lua.py` - Core BizHawk integration via Lua sockets
- `bizhawk_lua_server.lua` - Lua script that runs inside BizHawk
- `game_controller.py` - FF3 automation logic  
- `app.py` - Flask web server
- ~~`Bizhawk\ExternalTools\BirdsEye.dll`~~ - No longer needed (BizHawk 2.10 incompatible)

## Web Interface:
- **Status area** - Shows connection status and errors
- **Launch BizHawk & Connect** - Automated setup attempt
- **Connect to BizHawk** - Manual connection after BirdsEye setup
- **Skip FF3 Intro** - Main automation feature
- **Press A/B/Start/Select** - Manual controller testing
- **Disconnect/Cleanup** - Clean shutdown