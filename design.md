# SNES Emulator Controller Design

## Architecture Overview
Web-based Python controller for BizHawk SNES emulator with file-based communication.

## Core Components (Phase 1 - Complete)
- **Flask Web Server** (`app.py`) - HTTP API and web interface
- **BizHawk Integration** (`bizhawk_controller_file.py`) - File-based communication via Lua
- **Game Logic** (`game_controller.py`) - Game-specific automation
- **Lua Bridge** (`bizhawk_simple_server.lua`) - BizHawk command processor

## Communication Flow
```
Web Interface -> Flask API -> File Commands -> Lua Script -> BizHawk Emulator
```

## Design Philosophy
- **File-based communication** for maximum compatibility
- **Modular components** for easy extension
- **Queue-based input** for reliability
- **Frame-accurate timing** for precise control

## Key Features
- Web interface at http://localhost:5000
- Press/Hold/Release button controls
- Command queue system
- Automatic emulator launching
- Game-specific automation (FF3 intro skip)

## Phase 2 Architecture - AI Integration & OCR

### New Components
- **Screenshot System** - Capture BizHawk emulator window
- **OCR Engine** - Text recognition from screenshots (Tesseract)
- **FastMCP Server** (`emulator_mcp_server.py`) - AI-accessible control interface
- **Natural Language Parser** - Convert simple commands to button actions

### Extended Communication Flow
```
AI Agent -> FastMCP Protocol -> MCP Server -> Flask API -> Lua Script -> BizHawk
                                     |
                              Screenshot + OCR
                                     |
                              Visual Feedback -> AI Agent
```

### MCP Tools Interface
- `press_button(button_name)` - Execute button press
- `hold_button(button_name, duration)` - Hold button with timing
- `release_button(button_name)` - Release held button  
- `take_screenshot()` - Capture screen with OCR text
- `get_status()` - System health and queue status

### AI Integration Goals
- **Simple Language Control**: "press down" -> Down button press
- **Visual Feedback**: Screenshot + OCR for AI decision making
- **Direct Command Mapping**: No complex game interpretation
- **Maintain Human Interface**: Flask web UI remains functional

### Technical Stack Additions
- FastMCP for AI protocol communication
- OpenAI API for natural language processing
- PIL/PyAutoGUI for screenshot capture
- Tesseract OCR for text recognition
- Dual server architecture (Flask + MCP)