import qrcode
import cv2
from pyzbar import pyzbar
import zxingcpp  # Add zxing-cpp import
import re

class QRHandler:
    """
    Handles QR code generation and scanning.
    """

    @staticmethod
    def generate_wifi_qr_code(ssid, password, security="WPA"):
        """
        Generates a QR code for a Wi-Fi network.

        Args:
            ssid (str): The network SSID.
            password (str): The network password.
            security (str, optional): The security type (WPA, WEP, nopass). Defaults to "WPA".

        Returns:
            qrcode.image.pil.PilImage: The generated QR code image, or None on error.
        """
        try:
            # Format according to the standard
            # WIFI:S:<SSID>;T:<WPA|WEP|nopass>;P:<PASSWORD>;H:<true|false|blank>;;
            # H:false or blank means not hidden. We'll assume not hidden.
            if not security:
                security = "nopass"
            
            # Normalize security type for better compatibility
            # Some devices expect specific values like "WPA2" instead of "WPA"
            if security.upper() == "WPA":
                # Using "WPA" as it's a common value that works with many devices
                # If you specifically want to target WPA2, you could use "WPA2"
                # but "WPA" is generally more universally accepted
                security_type = "WPA"
            elif security.upper() == "WEP":
                security_type = "WEP"
            else:
                # For open networks or any other type
                security_type = security
            
            # Construct the WiFi string
            # For open networks, we can omit the password field or leave it empty
            if security_type.upper() == "NOPASS":
                wifi_string = f"WIFI:T:nopass;S:{ssid};;"
            else:
                wifi_string = f"WIFI:T:{security_type};S:{ssid};P:{password};;"
            
            # Debug output
            print(f"Generating QR code with string: {wifi_string}")
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(wifi_string)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            return img
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None

    @staticmethod
    def scan_qr_from_image_data(image_data):
        """
        Scans a QR code from image data in memory.

        Args:
            image_data (numpy.ndarray): The image data.

        Returns:
            dict or None: A dictionary with 'ssid', 'password', 'security' if a valid
                          Wi-Fi QR code is found, otherwise None.
        """
        try:
            print("Attempting to decode image data with zxing-cpp...")
            
            # Convert BGR to RGB for zxing-cpp if needed
            if len(image_data.shape) == 3 and image_data.shape[2] == 3:
                image_rgb = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                print(f"Image converted to RGB. Shape: {image_rgb.shape}, dtype: {image_rgb.dtype}")
            else:
                image_rgb = image_data
                print(f"Image is already in the correct format. Shape: {image_rgb.shape}, dtype: {image_rgb.dtype}")
            
            # Try to decode with zxing-cpp
            results = zxingcpp.read_barcode(image_rgb)
            print(f"zxing-cpp returned results: {results}")
            
            if results and results.text:
                data = results.text
                print(f"Decoded data with zxing-cpp: {data}")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    print("Successfully parsed Wi-Fi QR code data with zxing-cpp")
                    return parsed_data
            else:
                print("No QR code detected with zxing-cpp")
                
            # If zxing-cpp fails, try OpenCV QRCodeDetector as a fallback
            print("zxing-cpp failed. Trying OpenCV QRCodeDetector...")
            qrDecoder = cv2.QRCodeDetector()
            data, bbox, rectifiedImage = qrDecoder.detectAndDecode(image_data)
            
            if data:
                print(f"Decoded data with OpenCV QRCodeDetector: {data}")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    print("Successfully parsed Wi-Fi QR code data with OpenCV QRCodeDetector")
                    return parsed_data
            else:
                print("No QR code detected with OpenCV QRCodeDetector")
                
            # If OpenCV's detector fails, try pyzbar as a fallback
            print("OpenCV QRCodeDetector failed. Trying pyzbar as fallback...")
            decoded_objects = pyzbar.decode(image_data)
            print(f"Found {len(decoded_objects)} QR codes with pyzbar")
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                print(f"Decoded data with pyzbar: {data}")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    print("Successfully parsed Wi-Fi QR code data with pyzbar")
                    return parsed_data
            
            # If that fails, try some preprocessing techniques with pyzbar
            print("pyzbar also failed. Trying preprocessing techniques with pyzbar...")
            
            # Convert to grayscale if needed
            if len(image_data.shape) == 3:
                gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
                print(f"Image converted to grayscale. Shape: {gray.shape}, dtype: {gray.dtype}")
            else:
                gray = image_data
                print(f"Image is already grayscale. Shape: {gray.shape}, dtype: {gray.dtype}")
            
            # Try decoding grayscale
            decoded_objects = pyzbar.decode(gray)
            print(f"Found {len(decoded_objects)} QR codes in grayscale image")
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                print(f"Decoded data from grayscale image: {data}")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    print("Successfully parsed Wi-Fi QR code data from grayscale image")
                    return parsed_data
            
            print("No valid QR code found after all attempts")
            return None # No valid QR code found after all attempts
        except Exception as e:
            print(f"Error scanning QR code from image data: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def scan_qr_from_image(image_path):
        """
        Scans a QR code from an image file.

        Args:
            image_path (str): The path to the image file.

        Returns:
            dict or None: A dictionary with 'ssid', 'password', 'security' if a valid
                          Wi-Fi QR code is found, otherwise None.
        """
        try:
            print(f"Attempting to load image from {image_path}")
            
            # Try to decode with zxing-cpp first (most robust)
            print("Attempting to decode with zxing-cpp...")
            
            # Read image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                print(f"Error: Could not load image from {image_path}")
                return None
            
            print(f"Image loaded successfully. Shape: {image.shape}, dtype: {image.dtype}")
            
            # Use the new method for scanning image data
            return QRHandler.scan_qr_from_image_data(image)
            
        except Exception as e:
            print(f"Error scanning QR code from image: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def scan_qr_from_frame(frame):
        """
        Scans a QR code from a single video frame (numpy array).

        Args:
            frame (numpy.ndarray): The video frame.

        Returns:
            dict or None: A dictionary with 'ssid', 'password', 'security' if a valid
                          Wi-Fi QR code is found, otherwise None.
        """
        try:
            # Try to decode with zxing-cpp first (most robust)
            # Convert BGR to RGB for zxing-cpp
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = zxingcpp.read_barcode(frame_rgb)
            
            if results and results.text:
                data = results.text
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    return parsed_data
                    
            # If zxing-cpp fails, try OpenCV QRCodeDetector as a fallback
            qrDecoder = cv2.QRCodeDetector()
            data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
            
            if data:
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    return parsed_data
                    
            # If OpenCV's detector fails, try pyzbar as a fallback
            # Try to decode the original frame
            decoded_objects = pyzbar.decode(frame)
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    return parsed_data
                    
            # If that fails, try some preprocessing techniques
            # Convert to grayscale if it's not already
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Try decoding grayscale
            decoded_objects = pyzbar.decode(gray)
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    return parsed_data
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Try decoding blurred image
            decoded_objects = pyzbar.decode(blurred)
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    return parsed_data
            
            # Apply threshold to get binary image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Try decoding thresholded image
            decoded_objects = pyzbar.decode(thresh)
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    return parsed_data
            
            # Try morphological operations to enhance QR code features
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Try decoding morphologically enhanced image
            decoded_objects = pyzbar.decode(morph)
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                parsed_data = QRHandler._parse_wifi_qr_data(data)
                if parsed_data:
                    return parsed_data
            
            # Try resizing the frame to different scales
            for scale in [0.5, 1.5, 2.0]:
                width = int(frame.shape[1] * scale)
                height = int(frame.shape[0] * scale)
                dim = (width, height)
                
                # Resize frame
                resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
                
                # Try decoding resized frame
                decoded_objects = pyzbar.decode(resized)
                for obj in decoded_objects:
                    data = obj.data.decode("utf-8")
                    parsed_data = QRHandler._parse_wifi_qr_data(data)
                    if parsed_data:
                        return parsed_data
            
            return None # No valid QR code found after all attempts
        except Exception as e:
            # It's common for frames to not contain a decodable QR code, so logging every error might be noisy.
            # print(f"Error scanning QR code from frame: {e}") 
            return None

    @staticmethod
    def _parse_wifi_qr_data(data):
        """
        Parses the data string from a Wi-Fi QR code.

        Args:
            data (str): The raw data string from the QR code.

        Returns:
            dict or None: A dictionary with 'ssid', 'password', 'security' if the data
                          conforms to the Wi-Fi QR code format, otherwise None.
        """
        # Match the Wi-Fi QR code format
        # The standard format is: WIFI:S:<SSID>;T:<WPA|WEP|nopass>;P:<PASSWORD>;H:<true|false|blank>;;
        # But the fields can be in different orders, so we need to be flexible
        # Let's extract each field separately
        
        # Extract SSID (S:)
        ssid_match = re.search(r'S:([^;]*);', data)
        ssid = ssid_match.group(1) if ssid_match else None
        
        # Extract security type (T:)
        security_match = re.search(r'T:([^;]*);', data)
        security = security_match.group(1) if security_match else None
        
        # Extract password (P:)
        password_match = re.search(r'P:([^;]*);', data)
        password = password_match.group(1) if password_match else ""
        
        # Extract hidden flag (H:) if present
        hidden_match = re.search(r'H:([^;]*);', data)
        hidden = hidden_match.group(1) if hidden_match else "false"
        
        if ssid and security:
            # Normalize security type
            if security.upper() in ["WPA2", "WPA3"]:
                security = "WPA"  # Treat WPA2/WPA3 as WPA for simplicity in our app
            elif security.upper() == "NOPASS":
                password = ""  # No password for nopass
                
            return {
                'ssid': ssid,
                'password': password,
                'security': security
            }
        
        # Handle 'nopass' networks or other variations if needed
        # Example: WIFI:T:nopass;S:MyNetwork;;
        match_nopass = re.search(r'WIFI:T:(?P<security>nopass);S:(?P<ssid>[^;]*);', data)
        if match_nopass:
             return {
                'ssid': match_nopass.group('ssid'),
                'password': '', # No password for nopass
                'security': match_nopass.group('security')
            }
        
        # If it doesn't match the known Wi-Fi format, return None
        return None