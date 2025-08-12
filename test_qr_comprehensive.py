#!/usr/bin/env python3

import zxingcpp
import cv2
from pyzbar import pyzbar
import sys
import os

def test_zxing_cpp(image_path):
    \"\"\"Test QR code reading with zxing-cpp\"\"\"
    print(\"Testing with zxing-cpp...\")
    try:
        # Read image with OpenCV and convert to RGB for zxing-cpp
        image = cv2.imread(image_path)
        if image is None:
            print(\"  FAILED: Could not load image\")
            return None
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Try to decode with zxing-cpp
        results = zxingcpp.read_barcode(image_rgb)
        
        if results and results.text:
            print(f\"  SUCCESS: {results.text}\")
            return results.text
        else:
            print(\"  FAILED: No QR code detected\")
            return None
    except Exception as e:
        print(f\"  ERROR: {e}\")
        return None

def test_opencv(image_path):
    \"\"\"Test QR code reading with OpenCV\"\"\"
    print(\"Testing with OpenCV...\")
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(\"  FAILED: Could not load image\")
            return None
            
        qrDecoder = cv2.QRCodeDetector()
        data, bbox, rectifiedImage = qrDecoder.detectAndDecode(image)
        
        if data:
            print(f\"  SUCCESS: {data}\")
            return data
        else:
            print(\"  FAILED: No QR code detected\")
            return None
    except Exception as e:
        print(f\"  ERROR: {e}\")
        return None

def test_pyzbar(image_path):
    \"\"\"Test QR code reading with pyzbar\"\"\"
    print(\"Testing with pyzbar...\")
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(\"  FAILED: Could not load image\")
            return None
            
        decoded_objects = pyzbar.decode(image)
        if decoded_objects:
            data = decoded_objects[0].data.decode(\"utf-8\")
            print(f\"  SUCCESS: {data}\")
            return data
        else:
            print(\"  FAILED: No QR code detected\")
            return None
    except Exception as e:
        print(f\"  ERROR: {e}\")
        return None

def main():
    if len(sys.argv) != 2:
        print(\"Usage: python3 test_qr_comprehensive.py <image_path>\")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f\"Error: File {image_path} does not exist\")
        sys.exit(1)
    
    print(f\"Testing QR code reading for image: {image_path}\")
    print(f\"File size: {os.path.getsize(image_path)} bytes\")
    print()
    
    # Test with different libraries
    results = {}
    
    results['zxing-cpp'] = test_zxing_cpp(image_path)
    print()
    
    results['OpenCV'] = test_opencv(image_path)
    print()
    
    results['pyzbar'] = test_pyzbar(image_path)
    print()
    
    # Summary
    print(\"Summary:\")
    for library, result in results.items():
        status = \"SUCCESS\" if result else \"FAILED\"
        print(f\"  {library}: {status}\")
    
    # Check if any library succeeded
    success_count = sum(1 for result in results.values() if result)
    if success_count > 0:
        print(f\"\\nAt least one library successfully read the QR code ({success_count}/{len(results)})\")
        sys.exit(0)
    else:
        print(f\"\\nAll libraries failed to read the QR code\")
        sys.exit(1)

if __name__ == \"__main__\":
    main()