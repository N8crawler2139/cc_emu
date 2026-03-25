#!/usr/bin/env python
"""
Simple test script to verify screenshot endpoints work correctly
"""

import requests
import json
import time

def test_screenshot_endpoints():
    base_url = "http://localhost:5000"
    
    print("Testing Screenshot API Endpoints...")
    
    # Test 1: Basic screenshot endpoint
    print("\n1. Testing /screenshot endpoint...")
    try:
        response = requests.get(f"{base_url}/screenshot")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if 'filename' in data:
                print(f"Screenshot saved: {data['filename']}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 2: Screenshot with OCR
    print("\n2. Testing /screenshot-ocr endpoint...")
    try:
        response = requests.get(f"{base_url}/screenshot-ocr")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if 'ocr_result' in data:
                ocr = data['ocr_result']
                print(f"OCR found {ocr.get('total_words', 0)} words")
                if ocr.get('raw_text'):
                    print(f"Sample text: {ocr['raw_text'][:100]}...")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 3: Check if BizHawk is running (expected to fail)
    print("\n3. Testing screenshot without BizHawk (expected to report no window found)...")
    try:
        response = requests.get(f"{base_url}/screenshot")
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print(f"Expected failure: {data.get('message')}")
            else:
                print("Unexpected success - is BizHawk running?")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_screenshot_endpoints()