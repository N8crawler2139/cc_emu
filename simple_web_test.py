"""
Simple Flask Web Interface Test
Tests basic functionality without unicode issues
"""

import asyncio
import time
import sys
import io
import os
import psutil
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Set console encoding to handle unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class SimpleWebTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.browser = None
        self.page = None
        self.test_results = []
        
    async def setup(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        # Use Chromium in headless mode for CI/automation
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(10000)
        
    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
            
    def log_result(self, test_name, success, message):
        """Simple logging without unicode issues"""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
    def check_bizhawk_running(self):
        """Check if BizHawk is running"""
        for proc in psutil.process_iter(['pid', 'name']):
            if 'EmuHawk' in proc.info['name'] or 'BizHawk' in proc.info['name']:
                return True, proc.info
        return False, None

    async def test_page_load(self):
        """Test if page loads correctly"""
        try:
            response = await self.page.goto(self.base_url)
            
            if response.status == 200:
                title = await self.page.title()
                
                # Check for basic elements without reading text (avoid unicode)
                buttons = await self.page.locator("button").count()
                
                if "SNES" in title and buttons > 0:
                    self.log_result("Page Load", True, f"Page loaded with {buttons} buttons")
                    return True
                else:
                    self.log_result("Page Load", False, f"Unexpected content - Title: {title}")
                    return False
            else:
                self.log_result("Page Load", False, f"HTTP {response.status}")
                return False
                
        except Exception as e:
            self.log_result("Page Load", False, f"Exception: {str(e)}")
            return False

    async def test_launch_button(self):
        """Test launch button functionality"""
        try:
            # Count BizHawk processes before
            bizhawk_before, _ = self.check_bizhawk_running()
            
            # Look for launch-related buttons
            launch_buttons = await self.page.locator("button").all()
            launch_button = None
            
            for button in launch_buttons:
                text = await button.inner_text()
                if "Launch" in text or "Start" in text:
                    launch_button = button
                    break
                    
            if not launch_button:
                self.log_result("Launch Button", False, "No launch button found")
                return False
                
            # Click the button
            await launch_button.click()
            
            # Wait for potential launch
            await asyncio.sleep(5)
            
            # Check if BizHawk launched
            bizhawk_after, proc_info = self.check_bizhawk_running()
            
            if bizhawk_after and not bizhawk_before:
                self.log_result("Launch Button", True, f"BizHawk launched - PID: {proc_info['pid']}")
                return True
            elif bizhawk_after and bizhawk_before:
                self.log_result("Launch Button", True, "BizHawk already running")
                return True
            else:
                self.log_result("Launch Button", False, "BizHawk not launched")
                return False
                
        except Exception as e:
            self.log_result("Launch Button", False, f"Exception: {str(e)}")
            return False

    async def test_connect_button(self):
        """Test connect button functionality"""
        try:
            # Look for connect-related buttons
            buttons = await self.page.locator("button").all()
            connect_button = None
            
            for button in buttons:
                text = await button.inner_text()
                if "Connect" in text:
                    connect_button = button
                    break
                    
            if not connect_button:
                self.log_result("Connect Button", False, "No connect button found")
                return False
                
            # Click connect button
            await connect_button.click()
            
            # Wait for response
            await asyncio.sleep(3)
            
            self.log_result("Connect Button", True, "Connect button clicked successfully")
            return True
            
        except Exception as e:
            self.log_result("Connect Button", False, f"Exception: {str(e)}")
            return False

    async def test_control_buttons(self):
        """Test control buttons exist and are clickable"""
        try:
            control_names = ["A", "B", "Start", "Select"]
            found_controls = 0
            
            buttons = await self.page.locator("button").all()
            
            for button in buttons:
                text = await button.inner_text()
                if text in control_names:
                    try:
                        await button.click()
                        found_controls += 1
                        await asyncio.sleep(0.2)  # Brief delay
                    except:
                        pass
                        
            if found_controls > 0:
                self.log_result("Control Buttons", True, f"Found and tested {found_controls} control buttons")
                return True
            else:
                self.log_result("Control Buttons", False, "No control buttons found")
                return False
                
        except Exception as e:
            self.log_result("Control Buttons", False, f"Exception: {str(e)}")
            return False

    async def run_tests(self):
        """Run all tests"""
        print("Starting Simple Web Interface Tests...")
        print(f"Testing: {self.base_url}")
        print("=" * 50)
        
        await self.setup()
        
        try:
            # Run tests in sequence
            page_ok = await self.test_page_load()
            
            if page_ok:
                await self.test_launch_button()
                await self.test_connect_button()
                await self.test_control_buttons()
            else:
                print("[SKIP] Other tests skipped due to page load failure")
                
        finally:
            await self.cleanup()
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        print(f"Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        if total > 0:
            print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nResults:")
        for result in self.test_results:
            status = "PASS" if result['success'] else "FAIL"
            print(f"  [{status}] {result['test']}: {result['message']}")
            
        # Final BizHawk status
        is_running, proc_info = self.check_bizhawk_running()
        print(f"\nBizHawk Status: {'Running' if is_running else 'Not Running'}")
        if is_running:
            print(f"  Process: {proc_info['name']} (PID: {proc_info['pid']})")


async def main():
    """Main execution"""
    tester = SimpleWebTest()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())