#!/usr/bin/env python3
"""
Debug script to check Flask routes
"""

from app import app

def check_routes():
    print("Available routes in Flask app:")
    print("="*50)
    
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        print(f"{rule.rule:<30} {methods}")
    
    print("\n" + "="*50)
    print(f"Total routes: {len(list(app.url_map.iter_rules()))}")
    
    # Check specifically for hold route
    hold_routes = [rule for rule in app.url_map.iter_rules() if 'hold' in rule.rule]
    print(f"Hold routes found: {len(hold_routes)}")
    for route in hold_routes:
        print(f"  {route.rule} - {','.join(route.methods)}")

if __name__ == "__main__":
    check_routes()