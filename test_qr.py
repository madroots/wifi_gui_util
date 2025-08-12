#!/usr/bin/env python3

import zxingcpp
import cv2
import sys

def test_qr_reading(image_path):
    """Test QR code reading with zxing-cpp"""
    print(f"Testing QR code reading for image: {image_path}")
    
    try:
        # Read image with OpenCV
        image = cv2.imread(image_path)
        if image is None:
            print("ERROR: Could not load image")
            return False
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Try to decode with zxing-cpp
        results = zxingcpp.read_barcode(image_rgb)
        
        if results and results.text:
            print(f"SUCCESS: QR code detected!")
            print(f"Decoded text: {results.text}")
            print(f"Format: {results.format}")
            print(f"Content type: {results.content_type}")
            return True
        else:
            print("FAILED: No QR code detected with zxing-cpp")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception occurred while reading QR code: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_qr.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = test_qr_reading(image_path)
    sys.exit(0 if success else 1)