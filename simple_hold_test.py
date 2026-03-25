#!/usr/bin/env python3
"""
Simple test script to check hold API response
"""

import requests

FLASK_BASE_URL = "http://localhost:5000"

def test_simple():
    print("Testing simple API calls...")
    
    # Test 1: Simple status call
    try:
        response = requests.get(f"{FLASK_BASE_URL}/status", timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Content: {response.text}")
        print(f"Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"Status error: {e}")
    
    print("\n" + "="*30 + "\n")
    
    # Test 2: Hold without duration
    try:
        response = requests.post(f"{FLASK_BASE_URL}/hold/A", timeout=5)
        print(f"Hold A - Status code: {response.status_code}")
        print(f"Hold A - Content: {response.text}")
        print(f"Hold A - Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"Hold A error: {e}")

if __name__ == "__main__":
    test_simple()