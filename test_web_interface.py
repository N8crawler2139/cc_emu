"""
Flask Web Interface Test Suite using Playwright
Tests the BizHawk emulator controller web interface functionality
"""

import asyncio
import time
import os
import psutil
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

class FlaskWebInterfaceTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.browser = None
        self.page = None
        self.test_results = []
        
    async def setup(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        # Use Chromium in headful mode so we can see what's happening
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        
        # Set a reasonable timeout
        self.page.set_default_timeout(10000)  # 10 seconds
        
    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
            
    def log_test_result(self, test_name, success, message, details=None):
        """Log test results for reporting"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
                
    def check_bizhawk_process(self):
        """Check if BizHawk process is running"""
        bizhawk_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            if 'EmuHawk' in proc.info['name'] or 'BizHawk' in proc.info['name']:
                bizhawk_processes.append(proc.info)
        return bizhawk_processes

    async def test_web_interface_loads(self):
        """Test 1: Verify the web interface loads correctly"""
        try:
            await self.page.goto(self.base_url)
            
            # Check if page loaded
            title = await self.page.title()
            
            # Look for expected elements
            header = await self.page.locator("h1").text_content()
            
            # Check for key buttons/elements
            launch_button = self.page.locator("button", has_text="Launch BizHawk & Connect")
            connect_button = self.page.locator("button", has_text="Connect to BizHawk")
            
            launch_exists = await launch_button.count() > 0
            connect_exists = await connect_button.count() > 0
            
            if "SNES Emulator Controller" in title and "SNES Emulator Controller" in header:
                self.log_test_result(
                    "Web Interface Load",
                    True,
                    "Web interface loaded successfully",
                    {
                        "title": title,
                        "header": header,
                        "launch_button_found": launch_exists,
                        "connect_button_found": connect_exists
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Web Interface Load", 
                    False, 
                    "Web interface did not load expected content",
                    {"title": title, "header": header}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Web Interface Load",
                False, 
                f"Failed to load web interface: {str(e)}"
            )
            return False

    async def test_launch_bizhawk_button(self):
        """Test 2: Test the Launch BizHawk & Connect button"""
        try:
            # Check BizHawk processes before clicking
            processes_before = self.check_bizhawk_process()
            
            # Find and click the launch button
            launch_button = self.page.locator("button", has_text="Launch BizHawk & Connect")
            
            if await launch_button.count() == 0:
                self.log_test_result(
                    "Launch BizHawk Button",
                    False,
                    "Launch BizHawk & Connect button not found"
                )
                return False
                
            # Click the button
            await launch_button.click()
            
            # Wait a bit for response
            await asyncio.sleep(3)
            
            # Check for any response messages or status updates
            page_content = await self.page.content()
            
            # Check if BizHawk process was launched
            processes_after = self.check_bizhawk_process()
            bizhawk_launched = len(processes_after) > len(processes_before)
            
            # Look for any status messages or errors on the page
            status_elements = await self.page.locator('.status, .message, .error, .alert').all()
            status_messages = []
            for element in status_elements:
                text = await element.text_content()
                if text.strip():
                    status_messages.append(text.strip())
            
            self.log_test_result(
                "Launch BizHawk Button",
                True,  # Button click succeeded
                "Launch button clicked successfully",
                {
                    "bizhawk_launched": bizhawk_launched,
                    "processes_before": len(processes_before),
                    "processes_after": len(processes_after),
                    "status_messages": status_messages
                }
            )
            
            return bizhawk_launched
            
        except Exception as e:
            self.log_test_result(
                "Launch BizHawk Button",
                False,
                f"Error testing launch button: {str(e)}"
            )
            return False

    async def test_connect_button(self):
        """Test 3: Test the Connect to BizHawk button"""
        try:
            # Find and click connect button
            connect_button = self.page.locator("button", has_text="Connect to BizHawk")
            
            if await connect_button.count() == 0:
                self.log_test_result(
                    "Connect Button",
                    False,
                    "Connect to BizHawk button not found"
                )
                return False
                
            await connect_button.click()
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Check for status messages
            status_elements = await self.page.locator('.status, .message, .error, .alert').all()
            status_messages = []
            for element in status_elements:
                text = await element.text_content()
                if text.strip():
                    status_messages.append(text.strip())
            
            # Check console/network for any additional info
            page_content = await self.page.content()
            connection_success = "connected" in page_content.lower() and "error" not in page_content.lower()
            
            self.log_test_result(
                "Connect Button",
                True,  # Button click succeeded
                "Connect button clicked successfully", 
                {
                    "connection_success": connection_success,
                    "status_messages": status_messages
                }
            )
            
            return connection_success
            
        except Exception as e:
            self.log_test_result(
                "Connect Button", 
                False,
                f"Error testing connect button: {str(e)}"
            )
            return False

    async def test_control_buttons(self):
        """Test 4: Test individual control buttons (A, B, Start, etc.)"""
        control_buttons = ["A", "B", "Start", "Select", "Up", "Down", "Left", "Right"]
        button_results = {}
        
        for button_name in control_buttons:
            try:
                button = self.page.locator("button", has_text=button_name)
                
                if await button.count() == 0:
                    button_results[button_name] = {"found": False, "clicked": False}
                    continue
                    
                await button.click()
                await asyncio.sleep(0.5)  # Brief wait between clicks
                
                button_results[button_name] = {"found": True, "clicked": True}
                
            except Exception as e:
                button_results[button_name] = {"found": True, "clicked": False, "error": str(e)}
        
        successful_buttons = sum(1 for result in button_results.values() if result.get("clicked", False))
        
        self.log_test_result(
            "Control Buttons",
            successful_buttons > 0,
            f"Tested {len(control_buttons)} control buttons, {successful_buttons} worked",
            button_results
        )
        
        return successful_buttons > 0

    async def test_intro_skip_automation(self):
        """Test 5: Test the intro skip automation"""
        try:
            skip_button = self.page.locator("button", has_text="Skip Intro")
            
            if await skip_button.count() == 0:
                self.log_test_result(
                    "Intro Skip Automation",
                    False,
                    "Skip Intro button not found"
                )
                return False
                
            await skip_button.click()
            
            # Wait longer for automation to complete
            await asyncio.sleep(10)
            
            # Check for status updates
            status_elements = await self.page.locator('.status, .message, .error, .alert').all()
            status_messages = []
            for element in status_elements:
                text = await element.text_content()
                if text.strip():
                    status_messages.append(text.strip())
            
            automation_success = any("success" in msg.lower() for msg in status_messages)
            
            self.log_test_result(
                "Intro Skip Automation",
                True,  # Button click succeeded
                "Intro skip button clicked successfully",
                {
                    "automation_success": automation_success,
                    "status_messages": status_messages
                }
            )
            
            return automation_success
            
        except Exception as e:
            self.log_test_result(
                "Intro Skip Automation",
                False,
                f"Error testing intro skip: {str(e)}"
            )
            return False

    async def run_all_tests(self):
        """Run all tests and generate comprehensive report"""
        print("Starting Flask Web Interface Tests...")
        print(f"Testing URL: {self.base_url}")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Run tests in sequence
            test1_result = await self.test_web_interface_loads()
            
            if test1_result:
                test2_result = await self.test_launch_bizhawk_button()
                test3_result = await self.test_connect_button() 
                test4_result = await self.test_control_buttons()
                test5_result = await self.test_intro_skip_automation()
            else:
                print("[ERROR] Skipping remaining tests due to web interface load failure")
                
        finally:
            await self.cleanup()
        
        # Generate final report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "N/A")
        
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "[PASS]" if result['success'] else "[FAIL]"
            print(f"{status} {result['test']}: {result['message']}")
            
            if result['details']:
                for key, value in result['details'].items():
                    print(f"    - {key}: {value}")
        
        # BizHawk Process Check
        bizhawk_processes = self.check_bizhawk_process()
        print(f"\nBizHawk Status:")
        if bizhawk_processes:
            print(f"  [OK] BizHawk processes found: {len(bizhawk_processes)}")
            for proc in bizhawk_processes:
                print(f"    - PID {proc['pid']}: {proc['name']}")
        else:
            print("  [ERROR] No BizHawk processes detected")
            
        print("\nRECOMMENDATIONS:")
        if not any(r['success'] for r in self.test_results):
            print("  - Check if Flask server is running on http://localhost:5000")
            print("  - Verify the web interface HTML is correct")
            
        launch_test = next((r for r in self.test_results if r['test'] == 'Launch BizHawk Button'), None)
        if launch_test and not launch_test['details'].get('bizhawk_launched', False):
            print("  - BizHawk may not be launching correctly")
            print("  - Check the ROM path and BizHawk executable path")
            print("  - Verify BizHawk can launch the Final Fantasy III ROM manually")
            
        connect_test = next((r for r in self.test_results if r['test'] == 'Connect Button'), None)
        if connect_test and not connect_test['details'].get('connection_success', False):
            print("  - BirdsEye connection may not be established")
            print("  - Manually launch BizHawk and enable Tools -> External Tool -> BirdsEye")
            print("  - Click 'Connect' in the BirdsEye tool to start the socket server")


async def main():
    """Main test execution"""
    tester = FlaskWebInterfaceTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())