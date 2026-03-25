# Implementation Plan

## Phase 1: Basic Emulator Control ✅ COMPLETED
Full web-based SNES emulator control system with file-based communication, reliable button inputs, and FF3 intro skip automation.

## Phase 2: AI Integration & Screenshot OCR ✅ COMPLETED

### Goal
Transform the emulator controller into an AI-accessible system with visual feedback and natural language control.

### Step 2.1: Screenshot & OCR Capability
- [x] Add screenshot capture of BizHawk emulator window
- [x] Implement OCR functionality for text recognition
- [x] Create API endpoints for screenshot + OCR data
- [x] Test screenshot quality and OCR accuracy

### Step 2.2: FastMCP Server Implementation
- [x] Install FastMCP dependencies: `pip install fastmcp`
- [x] Create MCP server (`emulator_mcp_server.py`) with tools:
  - `press_button(button_name)` - Press specific button
  - `hold_button(button_name, duration)` - Hold button for duration
  - `release_button(button_name)` - Release held button
  - `take_screenshot()` - Capture emulator screen with OCR
  - `get_status()` - Get emulator status
- [x] Configure OpenAI API integration using config.py key
- [x] Test basic language commands: "press down", "hold A for 2 seconds"

### Step 2.3: Natural Language Interface
- [x] Create simple command parser for basic button actions
- [x] Initial scope: Direct button mapping only ("press A" -> A button)
- [x] No complex game understanding - just literal command translation
- [x] Test AI can successfully control emulator via natural language

### Step 2.4: Integration Testing
- [x] Launch MCP server alongside Flask server
- [x] Verify AI can connect and control emulator
- [x] Test screenshot capture during gameplay
- [x] Document command syntax and limitations

## Phase 3: Advanced Features (Future)
- Complex game state understanding
- Multi-step automation sequences
- Memory reading integration
- Multiple game support

## Technical Requirements
- FastMCP protocol for AI integration
- OpenAI API key from config.py
- Screenshot capture via Windows APIs
- OCR library (Tesseract or similar)
- Maintain existing Flask web interface