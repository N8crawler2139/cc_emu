"""
Screenshot and OCR Module for BizHawk Emulator

Captures screenshots of the BizHawk emulator window and performs OCR text recognition.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageGrab
import win32gui
import win32ui
import win32con
import os
import time
import json

class ScreenshotOCR:
    def __init__(self):
        self.bizhawk_window = None
        self.last_screenshot_path = None
        
    def find_bizhawk_window(self):
        """Find the BizHawk emulator window"""
        def window_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if "BizHawk" in window_title or "EmuHawk" in window_title:
                    windows.append((hwnd, window_title))
            return True
        
        windows = []
        win32gui.EnumWindows(window_callback, windows)
        
        if windows:
            self.bizhawk_window = windows[0][0]  # Use first BizHawk window found
            print(f"Found BizHawk window: {windows[0][1]}")
            return True
        else:
            print("BizHawk window not found")
            return False
    
    def capture_window(self, filename=None):
        """Capture screenshot of BizHawk window.

        Uses screen-region grab (ImageGrab) which works with hardware-
        accelerated renderers like BizHawk's OpenGL/D3D output.
        Falls back to PrintWindow API if grab fails.
        """
        if not self.bizhawk_window:
            if not self.find_bizhawk_window():
                return None

        try:
            # Get window rect (screen coordinates)
            # NOTE: Do NOT call SetForegroundWindow here -- it steals
            # focus and can cause keyboard input to go to the BizHawk
            # UI menus instead of the game.
            rect = win32gui.GetWindowRect(self.bizhawk_window)
            x, y, x1, y1 = rect

            # Use ImageGrab to capture the screen region - works with
            # hardware-accelerated renderers that BitBlt misses
            im = ImageGrab.grab(bbox=(x, y, x1, y1))

            # Check if the capture is mostly blank (all white/black)
            # If so, try PrintWindow as fallback
            pixels = list(im.getdata())
            sample = pixels[:100]
            avg_brightness = sum(sum(p[:3]) for p in sample) / (len(sample) * 3)
            if avg_brightness > 250 or avg_brightness < 5:
                # Likely a blank capture, try PrintWindow
                im_alt = self._capture_printwindow()
                if im_alt:
                    im = im_alt

            # Save to file if specified
            if filename:
                im.save(filename)
                self.last_screenshot_path = filename

            return im

        except Exception as e:
            print(f"Error capturing window: {e}")
            return None

    def _capture_printwindow(self):
        """Fallback capture using PrintWindow API."""
        try:
            rect = win32gui.GetWindowRect(self.bizhawk_window)
            x, y, x1, y1 = rect
            width = x1 - x
            height = y1 - y

            hwndDC = win32gui.GetWindowDC(self.bizhawk_window)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Use PrintWindow instead of BitBlt - asks window to paint itself
            import ctypes
            ctypes.windll.user32.PrintWindow(
                self.bizhawk_window, saveDC.GetSafeHdc(), 2  # PW_RENDERFULLCONTENT
            )

            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )

            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.bizhawk_window, hwndDC)

            return im
        except Exception as e:
            print(f"PrintWindow fallback failed: {e}")
            return None
    
    def perform_ocr(self, image, lang='eng'):
        """Perform OCR on PIL Image"""
        try:
            # Convert PIL Image to OpenCV format for preprocessing
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Increase contrast and reduce noise
            gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
            
            # Apply threshold to get binary image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Perform OCR
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(thresh, config=custom_config, lang=lang)
            
            # Also get detailed information
            data = pytesseract.image_to_data(thresh, config=custom_config, lang=lang, output_type=pytesseract.Output.DICT)
            
            # Filter out low confidence results and organize text by position
            confident_words = []
            for i, conf in enumerate(data['conf']):
                if int(conf) > 30:  # Only words with >30% confidence
                    word_text = data['text'][i].strip()
                    if word_text:
                        confident_words.append({
                            'text': word_text,
                            'confidence': int(conf),
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'w': data['width'][i],
                            'h': data['height'][i]
                        })
            
            return {
                'raw_text': text.strip(),
                'words': confident_words,
                'total_words': len(confident_words)
            }
            
        except Exception as e:
            print(f"Error performing OCR: {e}")
            return {
                'raw_text': '',
                'words': [],
                'total_words': 0,
                'error': str(e)
            }
    
    def capture_and_ocr(self, filename=None, lang='eng'):
        """Capture screenshot and perform OCR in one step"""
        if not filename:
            timestamp = int(time.time())
            filename = f"bizhawk_screenshot_{timestamp}.png"
            
        # Capture screenshot
        image = self.capture_window(filename)
        if not image:
            return None
            
        # Perform OCR
        ocr_result = self.perform_ocr(image, lang)
        
        return {
            'screenshot_path': filename,
            'ocr_result': ocr_result,
            'timestamp': time.time(),
            'image_size': image.size
        }
    
    def get_game_text_regions(self, image):
        """Identify common game text regions for better OCR"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Common game UI text regions (approximate positions)
            height, width = gray.shape
            
            regions = {
                'dialog_box': gray[int(height*0.7):int(height*0.95), int(width*0.05):int(width*0.95)],
                'menu_area': gray[int(height*0.1):int(height*0.6), int(width*0.1):int(width*0.9)],
                'status_bar': gray[int(height*0.05):int(height*0.15), int(width*0.05):int(width*0.95)],
                'full_screen': gray
            }
            
            results = {}
            for region_name, region_img in regions.items():
                if region_img.size > 0:
                    # Convert back to PIL for OCR
                    region_pil = Image.fromarray(region_img)
                    ocr_result = self.perform_ocr(region_pil)
                    results[region_name] = ocr_result
            
            return results
            
        except Exception as e:
            print(f"Error analyzing text regions: {e}")
            return {}

if __name__ == "__main__":
    # Test the screenshot and OCR functionality
    screenshot_ocr = ScreenshotOCR()
    
    print("Testing Screenshot and OCR functionality...")
    
    # Test capturing BizHawk window
    result = screenshot_ocr.capture_and_ocr("test_screenshot.png")
    
    if result:
        print(f"Screenshot saved: {result['screenshot_path']}")
        print(f"Image size: {result['image_size']}")
        print(f"OCR found {result['ocr_result']['total_words']} words")
        print(f"Raw text: {result['ocr_result']['raw_text'][:100]}...")  # First 100 chars
        
        # Print individual words with confidence
        for word in result['ocr_result']['words'][:10]:  # First 10 words
            print(f"  '{word['text']}' (confidence: {word['confidence']}%)")
    else:
        print("Failed to capture screenshot")