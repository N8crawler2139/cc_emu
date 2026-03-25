"""
Flask Web Server for SNES Emulator Controller

Provides HTTP endpoints to control BizHawk emulator and automate Final Fantasy III intro skip.
"""

from flask import Flask, jsonify, request, render_template_string
import threading
import time
import os
from bizhawk_controller_file import BizHawkControllerFile as BizHawkController
from game_controller import FF3GameController
from screenshot_ocr import ScreenshotOCR
from ff6_game_state import FF6GameStateReader
from ff6_actions import FF6Actions
from ai_expert import get_expert, reset_expert
from ff6_agent import get_agent, reset_agent

app = Flask(__name__)

# Global controller instances
bizhawk_controller = None
game_controller = None
screenshot_ocr = None
is_running = False

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>SNES Emulator Controller</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .button { background-color: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; font-size: 16px; }
        .button:hover { background-color: #45a049; }
        .button.danger { background-color: #f44336; }
        .button.danger:hover { background-color: #da190b; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .status.success { background-color: #dff0d8; color: #3c763d; border: 1px solid #d6e9c6; }
        .status.error { background-color: #f2dede; color: #a94442; border: 1px solid #ebccd1; }
        .status.info { background-color: #d9edf7; color: #31708f; border: 1px solid #bce8f1; }
        .endpoint { margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; }
        .endpoint h3 { margin: 0 0 10px 0; color: #007bff; }
        .form { margin: 20px 0; }
        .form input, .form select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>SNES Emulator Controller</h1>
        <p>Control BizHawk emulator and automate Final Fantasy III gameplay.</p>
        
        <div id="status" class="status info">
            Status: Ready to connect
        </div>
        
        <div class="status info">
            <h4>Setup Instructions (File-Based Communication):</h4>
            <ol>
                <li>Click "Launch BizHawk & Connect" below</li>
                <li>In BizHawk: <strong>Tools → Lua Console</strong></li>
                <li>In Lua Console: <strong>Script → Open Script</strong></li>
                <li>Select: <strong>bizhawk_simple_server.lua</strong> from this project folder</li>
                <li>You should see: <em>"File communication initialized"</em></li>
                <li>Come back here and try "Connect" or "Skip FF3 Intro"</li>
            </ol>
            <p><strong>Note:</strong> Using file-based communication for maximum BizHawk compatibility.</p>
            <div style="margin-top: 10px; padding: 8px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;">
                <strong>Automatic:</strong> The Lua script should auto-load when BizHawk starts!
            </div>
        </div>
        
        <div class="form">
            <h3>Quick Actions</h3>
            <button class="button" onclick="launchAndConnect()">Launch BizHawk & Connect</button>
            <button class="button" onclick="connectOnly()">Connect to BizHawk</button>
            <button class="button" onclick="skipIntro()">Skip FF3 Intro</button>
            <button class="button" onclick="disconnect()">Disconnect</button>
            <button class="button danger" onclick="cleanup()">Cleanup</button>
        </div>
        
        <div class="form">
            <h3>Screenshot & OCR</h3>
            <button class="button" onclick="takeScreenshot()" style="background-color: #2196F3;">📷 Take Screenshot</button>
            <button class="button" onclick="screenshotWithOCR()" style="background-color: #FF9800;">📷 Screenshot + OCR</button>
            <button class="button" onclick="ocrLastImage()" style="background-color: #9C27B0;">🔍 OCR Last Image</button>
        </div>
        
        <div class="form">
            <h3>SNES Controller</h3>
            
            <h4>Action Buttons</h4>
            <button class="button" onclick="pressButton('A')">A</button>
            <button class="button" onclick="pressButton('B')">B</button>
            <button class="button" onclick="pressButton('X')">X</button>
            <button class="button" onclick="pressButton('Y')">Y</button>
            
            <h4>D-Pad (Hold/Release Support)</h4>
            <div style="display: inline-block; margin: 10px;">
                <button class="button" onclick="pressButton('Up')">↑ Press</button>
                <button class="button" onclick="holdButton('Up')" style="background-color: #ff9500;">↑ Hold</button>
                <button class="button" onclick="releaseButton('Up')" style="background-color: #888;">↑ Release</button>
            </div>
            <br>
            <div style="display: inline-block; margin: 10px;">
                <button class="button" onclick="pressButton('Down')">↓ Press</button>
                <button class="button" onclick="holdButton('Down')" style="background-color: #ff9500;">↓ Hold</button>
                <button class="button" onclick="releaseButton('Down')" style="background-color: #888;">↓ Release</button>
            </div>
            <br>
            <div style="display: inline-block; margin: 10px;">
                <button class="button" onclick="pressButton('Left')">← Press</button>
                <button class="button" onclick="holdButton('Left')" style="background-color: #ff9500;">← Hold</button>
                <button class="button" onclick="releaseButton('Left')" style="background-color: #888;">← Release</button>
            </div>
            <br>
            <div style="display: inline-block; margin: 10px;">
                <button class="button" onclick="pressButton('Right')">→ Press</button>
                <button class="button" onclick="holdButton('Right')" style="background-color: #ff9500;">→ Hold</button>
                <button class="button" onclick="releaseButton('Right')" style="background-color: #888;">→ Release</button>
            </div>
            
            <h4>Shoulder Buttons</h4>
            <button class="button" onclick="pressButton('L')">L</button>
            <button class="button" onclick="pressButton('R')">R</button>
            
            <h4>System Buttons</h4>
            <button class="button" onclick="pressButton('Start')">Start</button>
            <button class="button" onclick="pressButton('Select')">Select</button>
        </div>
        
        <div class="endpoint">
            <h3>Available API Endpoints</h3>
            <ul>
                <li><strong>GET /status</strong> - Check emulator status</li>
                <li><strong>POST /launch</strong> - Launch BizHawk with FF3 ROM</li>
                <li><strong>POST /connect</strong> - Connect to BizHawk</li>
                <li><strong>POST /skip-intro</strong> - Automate intro skip sequence</li>
                <li><strong>POST /press/:button</strong> - Press specific button</li>
                <li><strong>POST /hold/:button</strong> - Hold specific button indefinitely</li>
                <li><strong>POST /release/:button</strong> - Release held button</li>
                <li><strong>POST /disconnect</strong> - Disconnect from BizHawk</li>
                <li><strong>POST /cleanup</strong> - Clean up all resources</li>
            </ul>
            <p><strong>Improvements:</strong></p>
            <ul>
                <li>Command queue system prevents input loss during busy periods</li>
                <li>Button hold/release for precise directional control</li>
                <li>More reliable timing and better error handling</li>
            </ul>
        </div>
    </div>

    <script>
        function updateStatus(message, type = 'info') {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = 'Status: ' + message;
            statusDiv.className = 'status ' + type;
        }
        
        function apiCall(endpoint, method = 'POST') {
            return fetch(endpoint, {method: method})
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.message || data.status, data.success ? 'success' : 'error');
                    return data;
                })
                .catch(error => {
                    updateStatus('Error: ' + error.message, 'error');
                    console.error('Error:', error);
                });
        }
        
        function launchAndConnect() {
            updateStatus('Launching BizHawk...', 'info');
            apiCall('/launch')
                .then(data => {
                    if (data.success) {
                        setTimeout(() => {
                            updateStatus('Connecting to BizHawk...', 'info');
                            apiCall('/connect');
                        }, 3000);
                    }
                });
        }
        
        function connectOnly() {
            updateStatus('Connecting to BizHawk...', 'info');
            apiCall('/connect');
        }
        
        function skipIntro() {
            updateStatus('Starting intro skip sequence...', 'info');
            apiCall('/skip-intro');
        }
        
        function pressButton(button) {
            updateStatus(`Pressing ${button} button...`, 'info');
            apiCall(`/press/${button}`);
        }
        
        function holdButton(button) {
            updateStatus(`Holding ${button} button...`, 'info');
            apiCall(`/hold/${button}`);
        }
        
        function releaseButton(button) {
            updateStatus(`Releasing ${button} button...`, 'info');
            apiCall(`/release/${button}`);
        }
        
        function disconnect() {
            apiCall('/disconnect');
        }
        
        function cleanup() {
            apiCall('/cleanup');
        }
        
        function takeScreenshot() {
            updateStatus('Taking screenshot...', 'info');
            apiCall('/screenshot', 'GET');
        }
        
        function screenshotWithOCR() {
            updateStatus('Taking screenshot and performing OCR...', 'info');
            apiCall('/screenshot-ocr?regions=true', 'GET')
                .then(data => {
                    if (data.success && data.ocr_result) {
                        const ocr = data.ocr_result;
                        let ocrInfo = `Screenshot saved: ${data.screenshot_path}. `;
                        ocrInfo += `Found ${ocr.total_words} words. `;
                        if (ocr.raw_text && ocr.raw_text.length > 0) {
                            ocrInfo += `Text: "${ocr.raw_text.substring(0, 100)}${ocr.raw_text.length > 100 ? '...' : ''}"`;
                        }
                        updateStatus(ocrInfo, 'success');
                    }
                });
        }
        
        function ocrLastImage() {
            const filename = prompt('Enter image filename (or leave blank for most recent screenshot):');
            if (filename !== null) {
                updateStatus('Performing OCR on image...', 'info');
                const url = filename.trim() ? `/ocr-only?filename=${encodeURIComponent(filename)}` : '/ocr-only?filename=current_screen.png';
                apiCall(url, 'POST')
                    .then(data => {
                        if (data.success && data.ocr_result) {
                            const ocr = data.ocr_result;
                            let ocrInfo = `OCR completed on ${data.filename}. `;
                            ocrInfo += `Found ${ocr.total_words} words. `;
                            if (ocr.raw_text && ocr.raw_text.length > 0) {
                                ocrInfo += `Text: "${ocr.raw_text.substring(0, 100)}${ocr.raw_text.length > 100 ? '...' : ''}"`;
                            }
                            updateStatus(ocrInfo, 'success');
                        }
                    });
            }
        }
        
        // Check initial status
        apiCall('/status', 'GET');
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the main control interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    """Get current emulator status"""
    global bizhawk_controller, is_running
    
    if not bizhawk_controller:
        return jsonify({
            'status': 'Not initialized',
            'connected': False,
            'running': False,
            'queue_length': 0,
            'frame': 0
        })
    
    detailed_status = bizhawk_controller.get_status()
    
    return jsonify({
        'status': detailed_status['status'],
        'connected': bizhawk_controller.is_connected(),
        'running': is_running,
        'queue_length': detailed_status['queue_length'],
        'frame': detailed_status['frame']
    })

@app.route('/launch', methods=['POST'])
def launch_bizhawk():
    """Launch BizHawk with FF3 ROM"""
    global bizhawk_controller, game_controller, is_running
    
    try:
        data = request.get_json() if request.is_json else {}
        load_slot = data.get('load_slot') if data else None
        bizhawk_controller = BizHawkController(load_slot=load_slot)
        game_controller = FF3GameController(bizhawk_controller)
        
        success = bizhawk_controller.launch_bizhawk()
        if success:
            is_running = True
            return jsonify({
                'success': True,
                'message': 'BizHawk launched successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to launch BizHawk'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error launching BizHawk: {str(e)}'
        })

@app.route('/connect', methods=['POST'])
def connect_to_bizhawk():
    """Connect to BizHawk via Birds Eye"""
    global bizhawk_controller
    
    if not bizhawk_controller:
        return jsonify({
            'success': False,
            'message': 'BizHawk not launched yet'
        })
    
    try:
        success = bizhawk_controller.connect()
        if success:
            return jsonify({
                'success': True,
                'message': 'Connected to BizHawk successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to BizHawk'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error connecting to BizHawk: {str(e)}'
        })

@app.route('/skip-intro', methods=['POST'])
def skip_intro():
    """Run the FF3 intro skip automation"""
    global game_controller
    
    if not game_controller:
        return jsonify({
            'success': False,
            'message': 'Game controller not initialized'
        })
    
    if not game_controller.bizhawk.is_connected():
        return jsonify({
            'success': False,
            'message': 'Not connected to BizHawk'
        })
    
    def run_skip_intro():
        try:
            game_controller.skip_intro_sequence()
        except Exception as e:
            print(f"Error during intro skip: {e}")
    
    # Run in background thread to avoid blocking the web request
    thread = threading.Thread(target=run_skip_intro)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Intro skip sequence started'
    })

@app.route('/press/<button>', methods=['POST'])
def press_button(button):
    """Press a specific controller button"""
    global bizhawk_controller
    
    if not bizhawk_controller or not bizhawk_controller.is_connected():
        return jsonify({
            'success': False,
            'message': 'Not connected to BizHawk'
        })
    
    valid_buttons = ['A', 'B', 'X', 'Y', 'Up', 'Down', 'Left', 'Right', 'L', 'R', 'Start', 'Select']
    if button not in valid_buttons:
        return jsonify({
            'success': False,
            'message': f'Invalid button. Valid options: {valid_buttons}'
        })
    
    try:
        success = bizhawk_controller.press_button(button)
        if success:
            return jsonify({
                'success': True,
                'message': f'{button} button pressed'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to press {button} button'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error pressing {button}: {str(e)}'
        })

@app.route('/hold/<button>', methods=['POST'])
def hold_button(button):
    """Hold a specific controller button"""
    global bizhawk_controller
    
    if not bizhawk_controller or not bizhawk_controller.is_connected():
        return jsonify({
            'success': False,
            'message': 'Not connected to BizHawk'
        })
    
    valid_buttons = ['A', 'B', 'X', 'Y', 'Up', 'Down', 'Left', 'Right', 'L', 'R', 'Start', 'Select']
    if button not in valid_buttons:
        return jsonify({
            'success': False,
            'message': f'Invalid button. Valid options: {valid_buttons}'
        })
    
    try:
        # Get duration from request data if provided
        duration = -1  # Default to indefinite hold
        if request.is_json and 'duration' in request.json:
            duration = float(request.json['duration'])
        
        success = bizhawk_controller.hold_button(button, duration)
        if success:
            if duration == -1:
                message = f'{button} button held indefinitely'
            else:
                message = f'{button} button held for {duration} seconds'
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to hold {button} button'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error holding {button}: {str(e)}'
        })

@app.route('/release/<button>', methods=['POST'])
def release_button(button):
    """Release a held controller button"""
    global bizhawk_controller
    
    if not bizhawk_controller or not bizhawk_controller.is_connected():
        return jsonify({
            'success': False,
            'message': 'Not connected to BizHawk'
        })
    
    valid_buttons = ['A', 'B', 'X', 'Y', 'Up', 'Down', 'Left', 'Right', 'L', 'R', 'Start', 'Select']
    if button not in valid_buttons:
        return jsonify({
            'success': False,
            'message': f'Invalid button. Valid options: {valid_buttons}'
        })
    
    try:
        success = bizhawk_controller.release_button(button)
        if success:
            return jsonify({
                'success': True,
                'message': f'{button} button released'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to release {button} button'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error releasing {button}: {str(e)}'
        })

@app.route('/disconnect', methods=['POST'])
def disconnect_from_bizhawk():
    """Disconnect from BizHawk"""
    global bizhawk_controller
    
    if bizhawk_controller:
        bizhawk_controller.disconnect()
        return jsonify({
            'success': True,
            'message': 'Disconnected from BizHawk'
        })
    else:
        return jsonify({
            'success': True,
            'message': 'Already disconnected'
        })

@app.route('/screenshot', methods=['POST', 'GET'])
def take_screenshot():
    """Take a screenshot of the BizHawk emulator window"""
    global screenshot_ocr
    
    # Initialize screenshot module if needed
    if not screenshot_ocr:
        screenshot_ocr = ScreenshotOCR()
    
    try:
        filename = request.args.get('filename', f'bizhawk_screenshot_{int(time.time())}.png')
        
        # Capture screenshot
        image = screenshot_ocr.capture_window(filename)
        
        if image:
            return jsonify({
                'success': True,
                'message': 'Screenshot captured successfully',
                'filename': filename,
                'image_size': image.size,
                'path': filename
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to capture screenshot - BizHawk window not found or not accessible'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error taking screenshot: {str(e)}'
        })

@app.route('/screenshot-ocr', methods=['POST', 'GET'])
def screenshot_with_ocr():
    """Take screenshot and perform OCR text recognition"""
    global screenshot_ocr
    
    # Initialize screenshot module if needed
    if not screenshot_ocr:
        screenshot_ocr = ScreenshotOCR()
    
    try:
        filename = request.args.get('filename', f'bizhawk_ocr_{int(time.time())}.png')
        include_regions = request.args.get('regions', 'false').lower() == 'true'
        
        # Capture and perform OCR
        result = screenshot_ocr.capture_and_ocr(filename)
        
        if result:
            response_data = {
                'success': True,
                'message': 'Screenshot and OCR completed successfully',
                'screenshot_path': result['screenshot_path'],
                'image_size': result['image_size'],
                'timestamp': result['timestamp'],
                'ocr_result': result['ocr_result']
            }
            
            # Optionally include region-based OCR analysis
            if include_regions:
                image = screenshot_ocr.capture_window()  # Get image for region analysis
                if image:
                    regions = screenshot_ocr.get_game_text_regions(image)
                    response_data['regions'] = regions
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to capture screenshot or perform OCR'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error during screenshot/OCR: {str(e)}'
        })

@app.route('/ocr-only', methods=['POST'])
def ocr_existing_image():
    """Perform OCR on an existing image file"""
    global screenshot_ocr
    
    # Initialize screenshot module if needed
    if not screenshot_ocr:
        screenshot_ocr = ScreenshotOCR()
    
    try:
        # Get filename from request
        data = request.get_json() if request.is_json else {}
        filename = data.get('filename') or request.args.get('filename')
        
        if not filename:
            return jsonify({
                'success': False,
                'message': 'Filename parameter required'
            })
        
        # Check if file exists
        if not os.path.exists(filename):
            return jsonify({
                'success': False,
                'message': f'File not found: {filename}'
            })
        
        # Load image and perform OCR
        from PIL import Image
        image = Image.open(filename)
        ocr_result = screenshot_ocr.perform_ocr(image)
        
        return jsonify({
            'success': True,
            'message': 'OCR completed successfully',
            'filename': filename,
            'ocr_result': ocr_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error performing OCR: {str(e)}'
        })

# --- Game State Endpoints ---
game_state_reader = FF6GameStateReader()

@app.route('/gamestate', methods=['GET'])
def get_game_state():
    """Get full FF6 game state (party, inventory, location, etc.)"""
    state = game_state_reader.read()
    if state:
        return jsonify({
            'success': True,
            'state': state.to_dict(),
            'summary': state.full_summary(),
        })
    return jsonify({
        'success': False,
        'message': 'Game state not available. Is BizHawk running with bizhawk_gamestate_server.lua?'
    })

@app.route('/gamestate/party', methods=['GET'])
def get_party():
    """Get active party members."""
    state = game_state_reader.read()
    if state:
        return jsonify({
            'success': True,
            'party': [c.to_dict() for c in state.party],
            'summary': state.party_summary(),
        })
    return jsonify({'success': False, 'message': 'Game state not available'})

@app.route('/gamestate/inventory', methods=['GET'])
def get_inventory():
    """Get current inventory."""
    state = game_state_reader.read()
    if state:
        return jsonify({
            'success': True,
            'inventory': [i.to_dict() for i in state.inventory],
            'summary': state.inventory_summary(),
        })
    return jsonify({'success': False, 'message': 'Game state not available'})

@app.route('/gamestate/character/<name>', methods=['GET'])
def get_character(name):
    """Get a specific character's full state."""
    state = game_state_reader.read()
    if state:
        char = state.get_character(name)
        if char:
            return jsonify({
                'success': True,
                'character': char.to_dict(),
                'equipment': char.equipment_summary(),
                'summary': char.summary(),
            })
        return jsonify({
            'success': False,
            'message': f'Character "{name}" not found',
            'available': [c.name for c in state.all_characters],
        })
    return jsonify({'success': False, 'message': 'Game state not available'})

@app.route('/gamestate/summary', methods=['GET'])
def get_state_summary():
    """Get a text summary of game state (good for AI context)."""
    state = game_state_reader.read()
    if state:
        return jsonify({
            'success': True,
            'summary': state.full_summary(),
        })
    return jsonify({'success': False, 'message': 'Game state not available'})

# --- High-Level Action Endpoints ---
ff6_actions = None

def get_ff6_actions():
    """Get or create FF6Actions instance."""
    global ff6_actions, bizhawk_controller
    if ff6_actions is None and bizhawk_controller and bizhawk_controller.is_connected():
        ff6_actions = FF6Actions(bizhawk_controller)
    return ff6_actions

@app.route('/action/equip', methods=['POST'])
def action_equip():
    """Equip an item. JSON body: {character, slot, item}"""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    data = request.get_json() or {}
    character = data.get('character', '')
    slot = data.get('slot', 'weapon')
    item = data.get('item', '')
    if not character or not item:
        return jsonify({'success': False, 'message': 'Required: character, slot, item'})
    result = actions.equip_item(character, slot, item)
    return jsonify({'success': result, 'message': f'Equip {item} on {character} ({slot})'})

@app.route('/action/use-item', methods=['POST'])
def action_use_item():
    """Use an item. JSON body: {item, target (optional)}"""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    data = request.get_json() or {}
    item = data.get('item', '')
    target = data.get('target')
    if not item:
        return jsonify({'success': False, 'message': 'Required: item'})
    result = actions.use_item(item, target)
    return jsonify({'success': result, 'message': f'Use {item}' + (f' on {target}' if target else '')})

@app.route('/action/walk', methods=['POST'])
def action_walk():
    """Walk in a direction. JSON body: {direction, seconds}"""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    data = request.get_json() or {}
    direction = data.get('direction', 'up')
    seconds = float(data.get('seconds', 1.0))
    result = actions.walk(direction, seconds)
    return jsonify({'success': result, 'message': f'Walk {direction} for {seconds}s'})

@app.route('/action/open-menu', methods=['POST'])
def action_open_menu():
    """Open the main menu."""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    actions.open_menu()
    return jsonify({'success': True, 'message': 'Menu opened'})

@app.route('/action/close-menu', methods=['POST'])
def action_close_menu():
    """Close all menus."""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    actions.close_all_menus()
    return jsonify({'success': True, 'message': 'Menus closed'})

@app.route('/action/talk', methods=['POST'])
def action_talk():
    """Talk to NPC / advance dialog."""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    presses = int(request.args.get('presses', 1))
    actions.advance_dialog(presses)
    return jsonify({'success': True, 'message': f'Dialog advanced ({presses} presses)'})

@app.route('/action/save', methods=['POST'])
def action_save():
    """Save the game. JSON body: {slot (1-3)}"""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    data = request.get_json() or {}
    slot = int(data.get('slot', 1))
    actions.save_game(slot)
    return jsonify({'success': True, 'message': f'Game saved to slot {slot}'})

@app.route('/action/battle/attack', methods=['POST'])
def action_battle_attack():
    """Attack in battle."""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    actions.battle_attack()
    return jsonify({'success': True, 'message': 'Attack executed'})

@app.route('/action/battle/run', methods=['POST'])
def action_battle_run():
    """Attempt to run from battle."""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    actions.battle_run()
    return jsonify({'success': True, 'message': 'Run attempted'})

@app.route('/action/heal', methods=['POST'])
def action_heal():
    """Auto-heal party with available items."""
    actions = get_ff6_actions()
    if not actions:
        return jsonify({'success': False, 'message': 'Not connected to emulator'})
    actions.heal_party()
    return jsonify({'success': True, 'message': 'Heal party attempted'})

# --- Unified Agent Endpoints ---

@app.route('/agent/start', methods=['POST'])
def agent_start():
    """Start the unified game agent."""
    global bizhawk_controller
    if not bizhawk_controller or not bizhawk_controller.is_connected():
        return jsonify({'success': False, 'message': 'Not connected to BizHawk'})
    agent = get_agent(bizhawk_controller)
    if agent.running:
        return jsonify({'success': False, 'message': 'Agent already running'})
    data = request.get_json() if request.is_json else {}
    direction = data.get('direction', 'Up')
    agent.walk_direction = direction
    agent.start()
    return jsonify({'success': True, 'message': f'Agent started (walking {direction})'})

@app.route('/agent/stop', methods=['POST'])
def agent_stop():
    """Stop the unified game agent."""
    agent = get_agent()
    if agent and agent.running:
        agent.stop()
        return jsonify({'success': True, 'message': 'Agent stopped'})
    return jsonify({'success': True, 'message': 'Agent not running'})

@app.route('/agent/status', methods=['GET'])
def agent_status():
    """Get agent status."""
    agent = get_agent()
    if agent:
        return jsonify({'success': True, **agent.get_status()})
    return jsonify({'success': True, 'running': False, 'message': 'Agent not initialized'})

@app.route('/agent/direction', methods=['POST'])
def agent_direction():
    """Set the agent's walk direction."""
    agent = get_agent()
    if not agent:
        return jsonify({'success': False, 'message': 'Agent not initialized'})
    data = request.get_json() or {}
    direction = data.get('direction', 'Up')
    agent.walk_direction = direction
    return jsonify({'success': True, 'message': f'Direction set to {direction}'})

# --- Expert AI Endpoints ---

@app.route('/ai/start', methods=['POST'])
def ai_start():
    """Start the Expert AI (Director + Pilot loop)."""
    global bizhawk_controller
    if not bizhawk_controller or not bizhawk_controller.is_connected():
        return jsonify({'success': False, 'message': 'Not connected to BizHawk'})

    expert = get_expert(bizhawk_controller)
    if expert.is_running():
        return jsonify({'success': False, 'message': 'AI is already running'})

    success = expert.start()
    return jsonify({
        'success': success,
        'message': 'Expert AI started' if success else 'Failed to start AI'
    })

@app.route('/ai/stop', methods=['POST'])
def ai_stop():
    """Stop the Expert AI."""
    expert = get_expert()
    if expert and expert.is_running():
        expert.stop()
        return jsonify({'success': True, 'message': 'Expert AI stopped'})
    return jsonify({'success': True, 'message': 'AI was not running'})

@app.route('/ai/status', methods=['GET'])
def ai_status():
    """Get Expert AI status and recent activity."""
    expert = get_expert()
    if expert:
        return jsonify({'success': True, **expert.get_status()})
    return jsonify({
        'success': True,
        'running': False,
        'message': 'AI not initialized'
    })

@app.route('/ai/log', methods=['GET'])
def ai_log():
    """Get the AI activity log."""
    expert = get_expert()
    if expert:
        count = int(request.args.get('count', 50))
        return jsonify({
            'success': True,
            'log': [
                f"[{e['level']}] {e['message']}"
                for e in expert.log[-count:]
            ]
        })
    return jsonify({'success': True, 'log': []})

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up all resources"""
    global bizhawk_controller, game_controller, screenshot_ocr, is_running, ff6_actions
    
    reset_agent()
    reset_expert()

    if bizhawk_controller:
        bizhawk_controller.cleanup()

    bizhawk_controller = None
    game_controller = None
    screenshot_ocr = None
    ff6_actions = None
    is_running = False
    
    return jsonify({
        'success': True,
        'message': 'Cleanup completed'
    })

if __name__ == '__main__':
    print("Starting SNES Emulator Controller Flask Server...")
    print("Access the web interface at: http://localhost:5000")
    print("API endpoints available for external control")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if bizhawk_controller:
            bizhawk_controller.cleanup()
    except Exception as e:
        print(f"Server error: {e}")
        if bizhawk_controller:
            bizhawk_controller.cleanup()