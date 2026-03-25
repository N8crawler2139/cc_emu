#!/usr/bin/env python
"""
Simple test Flask app to verify screenshot routes work
"""

from flask import Flask, jsonify
import time
from screenshot_ocr import ScreenshotOCR

app = Flask(__name__)
screenshot_ocr = None

@app.route('/')
def index():
    return jsonify({"message": "Test Flask app running", "routes": ["/", "/test-screenshot", "/test-ocr"]})

@app.route('/test-screenshot', methods=['GET', 'POST'])
def test_screenshot():
    """Test screenshot capture"""
    global screenshot_ocr
    
    if not screenshot_ocr:
        screenshot_ocr = ScreenshotOCR()
    
    try:
        filename = f'test_screenshot_{int(time.time())}.png'
        image = screenshot_ocr.capture_window(filename)
        
        if image:
            return jsonify({
                'success': True,
                'message': 'Screenshot captured successfully',
                'filename': filename,
                'image_size': image.size
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to capture screenshot - BizHawk window not found'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/test-ocr', methods=['GET', 'POST'])
def test_ocr():
    """Test screenshot with OCR"""
    global screenshot_ocr
    
    if not screenshot_ocr:
        screenshot_ocr = ScreenshotOCR()
    
    try:
        result = screenshot_ocr.capture_and_ocr(f'test_ocr_{int(time.time())}.png')
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Screenshot and OCR completed',
                'ocr_result': result['ocr_result'],
                'screenshot_path': result['screenshot_path']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to capture screenshot or perform OCR'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

if __name__ == '__main__':
    print("Starting test Flask app on port 5001...")
    app.run(debug=True, host='0.0.0.0', port=5001)