# Wi-Fi QR Manager

A simple GUI tool to manage saved Wi-Fi networks, generate QR codes for easy sharing, and scan QR codes to quickly import new networks. Built with Python, PyQt6, and `nmcli` for NetworkManager interaction.

## Features

- **List Saved Networks**: View your saved Wi-Fi connections and their details.
- **Generate QR Codes**: Create a scannable QR code for any of your saved networks to easily share the connection details (SSID and password) with others.
- **Scan QR Codes**:
  - Use your device's camera to scan a QR code in real-time.
  - Load and scan a QR code from an image file.
- **Import Networks**: After scanning a QR code, you can choose to connect to the network immediately or save its profile for later.
- **Security**: Requires root privileges to interact with NetworkManager, ensuring safe management of your network profiles.

## Prerequisites

- **Linux** with [NetworkManager](https://networkmanager.dev/) installed (most modern Linux distributions include it).
- **Python 3.13** or later.
- The following Python packages:
  - `PyQt6`
  - `qrcode[pil]`
  - `opencv-python`
  - `pyzbar`
  - `zxing-cpp` (Python bindings)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:madroots/wifi_gui_util.git
   cd wifi_gui_util
   ```

2. **Install Python Dependencies**:
   It's recommended to use a virtual environment.
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install PyQt6 qrcode[pil] opencv-python pyzbar zxing-cpp
   ```
   > **Note**: `zxing-cpp` requires the C++ library `zxing-cpp` to be installed on your system. Please refer to the [zxing-cpp-py documentation](https://github.com/ahnitz/zxing-cpp) for specific installation instructions for your Linux distribution.

3. **Make the Launcher Executable** (Recommended):
   The provided `launch.sh` script handles running the application with the necessary privileges.
   ```bash
   chmod +x launch.sh
   ```

## Usage

### Running the Application

Due to the need to interact with system network settings, the application requires elevated privileges.

**Recommended Way (using the launcher script)**:
```bash
./launch.sh
```
This script uses `pkexec` to securely prompt for your password and run the application with the necessary permissions.

**Direct Method (requires `sudo`)**:
```bash
sudo python3 main.py
```

### How to Use

1. **Main Window**:
   - The main window displays a list of your saved Wi-Fi networks.
   - Use the "Refresh" button in the toolbar to update the list.
   - Select a network from the list to see its details in the panel below.

2. **Generating a QR Code**:
   - Select a network from the list.
   - Click the "Generate QR Code" button in the details panel, or click the "🧾" button in the Actions column of the table.
   - The QR code will be displayed. You can then:
     - Click "Save QR Code..." to save the image as a `.png` file.
     - Click "Save QR String..." to save the raw QR code text data as a `.txt` file.
   - Click "Back to Details" to return to the network information.

3. **Scanning a QR Code**:
   - Click the "Scan QR Code" button in the toolbar to switch to the scanner view.
   - **Camera Scan**:
     - Ensure the "📷 Use Camera" option is selected (default if a camera is detected).
     - Point your camera at a Wi-Fi QR code. The application will automatically scan and process it.
   - **Image Scan**:
     - Select the "📁 Load Image" option.
     - Click "📂 Select Image File..." and choose an image file containing a QR code.
     - Click the "🔍 Scan Image" button.
   - Once a valid QR code is found, its details will be displayed, and you will be prompted to "Connect Now" or "Save Profile".

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.