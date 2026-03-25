#!/usr/bin/env python3
"""
Test the updated Flask app on port 5002
"""

# Copy the exact app code but run on different port
from flask import Flask, jsonify, request
import sys
import os

# Add the current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bizhawk_controller_file import BizHawkControllerFile

app = Flask(__name__)

# Global controller instance
bizhawk_controller = None

@app.route('/status')
def status():
    """Get emulator status"""
    return jsonify({
        'connected': True if bizhawk_controller and bizhawk_controller.is_connected() else False,
        'running': True,
        'status': 'Connected' if bizhawk_controller and bizhawk_controller.is_connected() else 'Disconnected'
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

if __name__ == '__main__':
    print("Starting test Flask server on port 5002...")
    print("This server tests the updated hold_button functionality")
    
    # Initialize controller (but don't connect for testing)
    bizhawk_controller = BizHawkControllerFile()
    
    app.run(host='0.0.0.0', port=5002, debug=False)