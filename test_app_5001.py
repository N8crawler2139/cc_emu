#!/usr/bin/env python
"""
Test app on port 5001 with screenshot functionality
"""

import sys
sys.path.append('.')

from app import app

if __name__ == '__main__':
    print("Starting SNES Emulator Controller Test Server on port 5001...")
    print("Access the web interface at: http://localhost:5001")
    print("This server includes screenshot endpoints")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")