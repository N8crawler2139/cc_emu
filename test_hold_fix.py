#!/usr/bin/env python3
"""
Test script to verify hold button duration fix
"""

import requests
import json
import time

FLASK_URL = "http://localhost:5000"

def test_hold_button_durations():
    """Test hold button with different durations"""
    
    print("Testing hold button duration fix...")
    
    test_cases = [
        {"duration": 3, "expected_frames": 180},    # 3 seconds = 180 frames
        {"duration": 30, "expected_frames": 1800},  # 30 seconds = 1800 frames  
        {"duration": 1, "expected_frames": 60},     # 1 second = 60 frames
    ]
    
    for case in test_cases:
        duration = case["duration"]
        expected_frames = case["expected_frames"]
        
        print(f"\n--- Testing {duration} second hold ---")
        
        # Test with Up button
        data = {"duration": duration}
        
        try:
            response = requests.post(f"{FLASK_URL}/hold/Up", json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API Response: {result}")
                print(f"   Expected frames: {expected_frames}")
                print(f"   Duration sent: {duration} seconds")
                
                if result.get("success"):
                    print(f"   ✅ Hold command accepted")
                else:
                    print(f"   ❌ Hold command failed: {result.get(\"message\")}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Wait a bit between tests
        time.sleep(1)

if __name__ == "__main__":
    test_hold_button_durations()
