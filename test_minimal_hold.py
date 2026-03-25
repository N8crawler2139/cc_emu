#!/usr/bin/env python3
"""
Minimal Flask server to test hold endpoint
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/test-hold/<button>', methods=['POST'])
def test_hold_button(button):
    """Test hold endpoint"""
    duration = -1
    if request.is_json and 'duration' in request.json:
        duration = float(request.json['duration'])
    
    return jsonify({
        'success': True,
        'button': button,
        'duration': duration,
        'message': f'Test hold for {button} with duration {duration}'
    })

@app.route('/status')
def status():
    return jsonify({'status': 'Test server running'})

if __name__ == '__main__':
    print("Starting test Flask server on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)