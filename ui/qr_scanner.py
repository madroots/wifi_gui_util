from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, QLabel, QPushButton, QFileDialog, QStackedWidget
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from qr_handler import QRHandler

class QRScannerView(QWidget):
    """
    Widget for scanning QR codes via camera or image file.
    Emits signals upon successful scan or when scan is finished/aborted.
    """
    # Signal emitted when a valid Wi-Fi QR code is scanned
    qr_scanned = pyqtSignal(str, str, str) # ssid, password, security
    # Signal emitted when the scan process is finished (e.g., user stops it)
    scan_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.cap = None # OpenCV VideoCapture object
        self.timer = QTimer() # Timer for camera feed updates
        self.timer.timeout.connect(self.update_camera_frame)
        self.is_camera_active = False
        self.is_image_loaded = False
        self.loaded_image = None
        self.last_qr_data = None # To avoid re-processing the same QR code repeatedly from video
        
        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI elements."""
        main_layout = QVBoxLayout(self)
        
        # --- Input Method Selector ---
        self.input_group_box = QGroupBox("Scan Method")
        input_layout = QHBoxLayout(self.input_group_box)
        
        self.use_camera_radio = QRadioButton("📷 Use Camera")
        self.load_image_radio = QRadioButton("📁 Load Image")
        
        # Check if a camera is available
        self.camera_available = self._check_camera()
        self.use_camera_radio.setChecked(self.camera_available)
        self.load_image_radio.setChecked(not self.camera_available)
        
        self.use_camera_radio.toggled.connect(self.on_input_method_changed)
        
        input_layout.addWidget(self.use_camera_radio)
        input_layout.addWidget(self.load_image_radio)
        input_layout.addStretch() # Push radio buttons to the left
        
        main_layout.addWidget(self.input_group_box)

        # --- Dynamic Input Area (Stacked) ---
        self.input_stacked_widget = QWidget() # A simple container for now
        self.input_stacked_layout = QVBoxLayout(self.input_stacked_widget)
        self.input_stacked_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack 1: Camera Feed
        self.camera_widget = QWidget()
        camera_layout = QVBoxLayout(self.camera_widget)
        
        self.camera_instructions_label = QLabel("Point your camera at a Wi-Fi QR Code")
        self.camera_instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(self.camera_instructions_label)
        
        self.camera_feed_label = QLabel()
        self.camera_feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_feed_label.setMinimumSize(400, 300) # Set a minimum size
        self.camera_feed_label.setStyleSheet("border: 1px solid gray;") # Add a border for visibility
        # Add a semi-transparent overlay guide (this is a placeholder, real overlay needs custom painting)
        # For now, just descriptive text
        self.camera_guide_label = QLabel("📷 Camera Feed")
        self.camera_guide_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_feed_label.setText("Starting camera...")
        camera_layout.addWidget(self.camera_feed_label)
        camera_layout.addWidget(self.camera_guide_label)
        
        # Stack 2: Load Image
        self.image_widget = QWidget()
        image_layout = QVBoxLayout(self.image_widget)
        
        self.image_instructions_label = QLabel("Select an image file containing a QR code.")
        self.image_instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.image_instructions_label)
        
        self.image_preview_label = QLabel()
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setMinimumSize(400, 300)
        self.image_preview_label.setStyleSheet("border: 1px dashed gray;")
        self.image_preview_label.setText("No image loaded.")
        image_layout.addWidget(self.image_preview_label)
        
        self.load_image_button = QPushButton("📂 Select Image File...")
        self.load_image_button.clicked.connect(self.load_image_file)
        image_layout.addWidget(self.load_image_button)
        
        # Add stacks to the container layout (simple show/hide for now)
        self.input_stacked_layout.addWidget(self.camera_widget)
        self.input_stacked_layout.addWidget(self.image_widget)
        
        main_layout.addWidget(self.input_stacked_widget)
        
        # --- Status/Result Display ---
        self.status_label = QLabel("Ready.")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # --- Scan/Decode Control (Bottom Section) ---
        # Use a stacked widget to switch between control sets
        self.control_stacked_widget = QStackedWidget()
        
        # Stack 0: Controls for Camera
        self.camera_control_widget = QWidget()
        camera_control_layout = QHBoxLayout(self.camera_control_widget)
        # Create the stop scan button here
        self.stop_scan_button = QPushButton("⏹ Stop Scan & Return")
        self.stop_scan_button.clicked.connect(self.stop_scan_and_return)
        camera_control_layout.addStretch()
        camera_control_layout.addWidget(self.stop_scan_button)
        
        # Stack 1: Controls for Image
        self.image_control_widget = QWidget()
        image_control_layout = QHBoxLayout(self.image_control_widget)
        # Create the image control buttons here
        self.scan_image_button = QPushButton("🔍 Scan Image")
        self.scan_image_button.clicked.connect(self.scan_loaded_image)
        self.scan_image_button.setEnabled(False) # Disabled until an image is loaded
        
        self.reset_image_button = QPushButton("🔄 Reset")
        self.reset_image_button.clicked.connect(self.reset_image_view)
        
        self.back_from_scanner_button = QPushButton("⬅ Back")
        self.back_from_scanner_button.clicked.connect(self.scan_finished.emit)
        
        image_control_layout.addWidget(self.scan_image_button)
        image_control_layout.addWidget(self.reset_image_button)
        image_control_layout.addStretch()
        image_control_layout.addWidget(self.back_from_scanner_button)
        
        self.control_stacked_widget.addWidget(self.camera_control_widget)
        self.control_stacked_widget.addWidget(self.image_control_widget)
        
        main_layout.addWidget(self.control_stacked_widget)
        
        # --- Action Buttons (for scanned QR) ---
        # These will be shown/hidden as needed, placed below the controls
        self.connect_button = QPushButton("🔗 Connect Now")
        self.connect_button.clicked.connect(self.on_connect_clicked)
        self.connect_button.hide() # Initially hidden
        
        self.save_profile_button = QPushButton("💾 Save Profile")
        self.save_profile_button.clicked.connect(self.on_save_profile_clicked)
        self.save_profile_button.hide() # Initially hidden
        
        self.scanned_qr_actions_layout = QHBoxLayout()
        self.scanned_qr_actions_layout.addStretch()
        self.scanned_qr_actions_layout.addWidget(self.connect_button)
        self.scanned_qr_actions_layout.addWidget(self.save_profile_button)
        main_layout.addLayout(self.scanned_qr_actions_layout)
        
        # Initialize UI state
        self.on_input_method_changed(self.use_camera_radio.isChecked())

    def _check_camera(self):
        """Check if a camera is available."""
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.release()
                return True
            else:
                return False
        except:
            return False

    def on_input_method_changed(self, is_camera_selected):
        """Handle switching between camera and image input methods."""
        if is_camera_selected:
            self.camera_widget.show()
            self.image_widget.hide()
            self.control_stacked_widget.setCurrentWidget(self.camera_control_widget)
            self.status_label.setText("Camera selected. Click 'Stop Scan & Return' when done.")
            self.hide_scanned_actions()
        else:
            self.camera_widget.hide()
            self.image_widget.show()
            self.control_stacked_widget.setCurrentWidget(self.image_control_widget)
            self.status_label.setText("Image loading selected.")
            self.hide_scanned_actions()

    def start_scan(self):
        """Start the camera scanning process."""
        if not self.use_camera_radio.isChecked():
            return # Only start if camera is the selected method

        if not self.camera_available:
            self.status_label.setText("No camera available.")
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_label.setText("Error: Could not open camera.")
            return

        self.is_camera_active = True
        self.last_qr_data = None # Reset last scanned data
        self.timer.start(30) # Update frame every 30 ms (approx. 33 FPS)
        self.status_label.setText("Scanning... Please wait.")
        self.hide_scanned_actions()

    def update_camera_frame(self):
        """Capture and display a frame from the camera, and scan for QR codes."""
        if not self.is_camera_active or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.status_label.setText("Error: Failed to grab frame from camera.")
            self.stop_camera()
            return

        # Display the frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        # Scale pixmap to fit the label, keeping aspect ratio
        scaled_pixmap = pixmap.scaled(self.camera_feed_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        self.camera_feed_label.setPixmap(scaled_pixmap)

        # Scan for QR codes in the frame
        qr_data = QRHandler.scan_qr_from_frame(frame)
        if qr_data and qr_data != self.last_qr_data: # Avoid re-processing the same code immediately
            self.last_qr_data = qr_data
            self.display_scanned_qr(qr_data)
            self.timer.stop() # Stop continuous scanning once found

    def stop_camera(self):
        """Stop the camera capture and timer."""
        self.is_camera_active = False
        if self.timer.isActive():
            self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        # Clear the feed label
        self.camera_feed_label.clear()
        self.camera_feed_label.setText("Camera stopped.")

    def load_image_file(self):
        """Open a file dialog to load an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        """Load an image from a file path."""
        try:
            # Use OpenCV to load the image
            image = cv2.imread(file_path)
            if image is None:
                self.status_label.setText(f"Error: Could not load image from {file_path}")
                return
                
            self.loaded_image = image
            self.is_image_loaded = True
            self.scan_image_button.setEnabled(True)
            self.status_label.setText(f"Image loaded: {file_path}")
            
            # Display a thumbnail/preview
            self.display_image_preview(image)
            
        except Exception as e:
            self.status_label.setText(f"Error loading image: {e}")

    def display_image_preview(self, image):
        """Display a preview of the loaded image."""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            # Scale pixmap to fit the label, keeping aspect ratio
            scaled_pixmap = pixmap.scaled(self.image_preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            self.image_preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            self.status_label.setText(f"Error displaying image preview: {e}")

    def scan_loaded_image(self):
        """Scan the loaded image for a QR code."""
        if not self.is_image_loaded or self.loaded_image is None:
            self.status_label.setText("No image loaded to scan.")
            return
            
        self.status_label.setText("Scanning loaded image...")
        qr_data = QRHandler.scan_qr_from_frame(self.loaded_image) # Reuse the frame scanning logic
        if qr_data:
            self.display_scanned_qr(qr_data)
        else:
            self.status_label.setText("No valid QR code found in the image.")
            self.hide_scanned_actions()

    def reset_image_view(self):
        """Reset the image loading view."""
        self.loaded_image = None
        self.is_image_loaded = False
        self.scan_image_button.setEnabled(False)
        self.image_preview_label.clear()
        self.image_preview_label.setText("No image loaded.")
        self.status_label.setText("Image loading selected. Click 'Select Image File...' to load an image.")
        self.hide_scanned_actions()

    def display_scanned_qr(self, qr_data):
        """Display the details of the scanned QR code and show action buttons."""
        ssid = qr_data.get('ssid', 'Unknown')
        password = qr_data.get('password', '')
        security = qr_data.get('security', 'Unknown')
        
        masked_password = '*' * len(password) if password else '(None)'
        details_text = f"<b>Scanned QR Code:</b><br>SSID: {ssid}<br>Password: {masked_password}<br>Security: {security}"
        self.status_label.setText(details_text)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Store scanned data for button actions
        self.scanned_ssid = ssid
        self.scanned_password = password
        self.scanned_security = security
        
        # Show action buttons
        self.connect_button.show()
        self.save_profile_button.show()
        
        # Hide other controls that are not relevant now
        # (They are still part of the layout but can be managed by hiding if needed)

    def hide_scanned_actions(self):
        """Hide the action buttons for scanned QR codes."""
        self.connect_button.hide()
        self.save_profile_button.hide()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def on_connect_clicked(self):
        """Handle the 'Connect Now' button click."""
        # Emit the signal to let the main window handle the connection logic
        self.qr_scanned.emit(self.scanned_ssid, self.scanned_password, self.scanned_security)

    def on_save_profile_clicked(self):
        """Handle the 'Save Profile' button click."""
        # Emit the signal to let the main window handle the save profile logic
        self.qr_scanned.emit(self.scanned_ssid, self.scanned_password, self.scanned_security)

    def stop_scan_and_return(self):
        """Stop any active scan and signal to return to the main view."""
        self.stop_camera()
        self.reset_image_view() # Also reset image state
        self.scan_finished.emit()