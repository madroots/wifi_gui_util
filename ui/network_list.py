from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QAbstractItemView, QHeaderView
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage
import io
from wifi_manager import WifiManager
from qr_handler import QRHandler

class NetworkListView(QWidget):
    """
    Widget to display the list of saved networks and their details/QR codes.
    Emits a signal when a QR code is generated.
    """
    qr_generated = pyqtSignal(object) # Signal carrying the PIL Image object

    def __init__(self):
        super().__init__()
        self.connections = []
        self.current_qr_image = None
        self._setup_ui()
        self.refresh_connections() # Load connections on init

    def _setup_ui(self):
        """Setup the UI elements."""
        layout = QVBoxLayout(self)

        # --- Top Panel: Network List ---
        self.network_table = QTableWidget(0, 4) # 0 rows, 4 columns
        self.network_table.setHorizontalHeaderLabels(["SSID", "Security", "Status", "Actions"])
        self.network_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.network_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.network_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Make the table headers interactive
        header = self.network_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # SSID stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Security
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Actions
        
        # Connect selection change
        self.network_table.currentCellChanged.connect(self.on_network_selected)
        
        layout.addWidget(self.network_table)

        # --- Bottom Panel: Details / QR Display ---
        self.details_qr_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_qr_widget)
        
        # Placeholder for details or QR
        self.info_label = QLabel("Select a network to view details.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        self.details_layout.addWidget(self.info_label)
        
        # Action buttons for details (initially hidden)
        self.details_button_layout = QHBoxLayout()
        self.details_button_layout.addStretch()
        self.copy_password_button = QPushButton("Copy Password")
        self.copy_password_button.clicked.connect(self.copy_selected_password)
        self.copy_password_button.hide()
        self.generate_qr_button = QPushButton("Generate QR Code")
        self.generate_qr_button.clicked.connect(self.generate_qr_for_selected)
        self.generate_qr_button.hide()
        self.details_button_layout.addWidget(self.copy_password_button)
        self.details_button_layout.addWidget(self.generate_qr_button)
        self.details_layout.addLayout(self.details_button_layout)
        
        # Placeholder for QR Code display (initially hidden)
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.hide()
        self.details_layout.addWidget(self.qr_label)
        
        # Action buttons for QR (initially hidden)
        self.qr_button_layout = QHBoxLayout()
        self.qr_button_layout.addStretch()
        self.save_qr_button = QPushButton("Save QR Code...")
        self.save_qr_button.clicked.connect(self.save_current_qr_code)
        self.save_qr_button.hide()
        
        # Button to save the QR string to a text file
        self.save_qr_string_button = QPushButton("Save QR String...")
        self.save_qr_string_button.clicked.connect(self.save_qr_string_to_file)
        self.save_qr_string_button.hide()
        
        self.back_to_details_button = QPushButton("Back to Details")
        self.back_to_details_button.clicked.connect(self.show_network_details)
        self.back_to_details_button.hide()
        self.qr_button_layout.addWidget(self.save_qr_button)
        self.qr_button_layout.addWidget(self.save_qr_string_button)
        self.qr_button_layout.addWidget(self.back_to_details_button)
        self.details_layout.addLayout(self.qr_button_layout)
        
        layout.addWidget(self.details_qr_widget)

    def refresh_connections(self):
        """Refresh the list of saved connections."""
        self.connections = WifiManager.get_saved_connections()
        self._populate_network_table()
        self.info_label.setText("Network list refreshed. Select a network.")
        # Clear details/QR display
        self.show_network_details() # This will reset the bottom panel

    def _populate_network_table(self):
        """Populate the network table with data."""
        self.network_table.setRowCount(len(self.connections))
        for row, conn in enumerate(self.connections):
            ssid_item = QTableWidgetItem(conn['ssid'])
            ssid_item.setData(Qt.ItemDataRole.UserRole, conn) # Store full data in UserRole
            self.network_table.setItem(row, 0, ssid_item)
            
            security_item = QTableWidgetItem("WPA/WPA2" if conn['password'] else "Open")
            self.network_table.setItem(row, 1, security_item)
            
            # Status is tricky to get dynamically without more nmcli calls
            # For simplicity, we'll leave it blank or assume disconnected
            # A more advanced version could check `nmcli connection show --active`
            status_item = QTableWidgetItem("Unknown") 
            self.network_table.setItem(row, 2, status_item)
            
            # Actions column with buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(30, 30)
            copy_btn.setToolTip("Copy Password")
            # Using lambda with default argument to capture 'conn' at definition time
            copy_btn.clicked.connect(lambda checked, c=conn: self.copy_password(c))
            actions_layout.addWidget(copy_btn)
            
            qr_btn = QPushButton("🧾")
            qr_btn.setFixedSize(30, 30)
            qr_btn.setToolTip("Generate QR Code")
            qr_btn.clicked.connect(lambda checked, c=conn: self.generate_qr_code(c))
            actions_layout.addWidget(qr_btn)
            
            actions_widget.setLayout(actions_layout)
            self.network_table.setCellWidget(row, 3, actions_widget)

    def on_network_selected(self, current_row, current_column, previous_row, previous_column):
        """Handle selection change in the network table."""
        if current_row >= 0:
            item = self.network_table.item(current_row, 0)
            if item:
                conn_data = item.data(Qt.ItemDataRole.UserRole)
                if conn_data:
                    self.display_network_details(conn_data)

    def display_network_details(self, connection_data):
        """Display details of the selected network."""
        self.current_connection = connection_data
        ssid = connection_data['ssid']
        password = connection_data['password']
        
        details_text = f"<b>SSID:</b> {ssid}<br>"
        # Mask password for display
        masked_password = '*' * len(password) if password else "(None)"
        details_text += f"<b>Password:</b> {masked_password}<br>"
        details_text += f"<b>Security:</b> {'WPA/WPA2' if password else 'Open'}<br>"
        
        self.info_label.setText(details_text)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Show detail action buttons
        self.copy_password_button.show()
        self.generate_qr_button.show()
        
        # Hide QR elements
        self.qr_label.hide()
        self.save_qr_button.hide()
        self.back_to_details_button.hide()

    def show_network_details(self):
        """Explicitly show the network details panel (e.g., after generating QR)."""
        # Reset selection if needed, or just clear if no selection
        selected_rows = self.network_table.selectionModel().selectedRows()
        if selected_rows:
            # Re-display details for the currently selected network
            current_row = selected_rows[0].row()
            item = self.network_table.item(current_row, 0)
            if item:
                conn_data = item.data(Qt.ItemDataRole.UserRole)
                if conn_data:
                    self.display_network_details(conn_data)
        else:
            # No selection, show default message
            self.info_label.setText("Select a network to view details.")
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.copy_password_button.hide()
            self.generate_qr_button.hide()
            
        # Ensure QR elements are hidden
        self.qr_label.hide()
        self.save_qr_button.hide()
        self.save_qr_string_button.hide()
        self.back_to_details_button.hide()
        self.info_label.show() # Make sure the info label is visible

    def copy_selected_password(self):
        """Copy the password of the currently selected network."""
        selected_rows = self.network_table.selectionModel().selectedRows()
        if selected_rows:
            current_row = selected_rows[0].row()
            item = self.network_table.item(current_row, 0)
            if item:
                conn_data = item.data(Qt.ItemDataRole.UserRole)
                if conn_data:
                    self.copy_password(conn_data)

    def copy_password(self, connection_data):
        """Copy a password to the clipboard."""
        from PyQt6.QtWidgets import QApplication
        password = connection_data.get('password', '')
        if password:
            clipboard = QApplication.clipboard()
            clipboard.setText(password)
            # Find the main window to access its status bar
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showMessage("Password copied to clipboard.", 3000)
        else:
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showMessage("No password to copy for this network.", 3000)

    def generate_qr_for_selected(self):
        """Generate QR code for the currently selected network."""
        selected_rows = self.network_table.selectionModel().selectedRows()
        if selected_rows:
            current_row = selected_rows[0].row()
            item = self.network_table.item(current_row, 0)
            if item:
                conn_data = item.data(Qt.ItemDataRole.UserRole)
                if conn_data:
                    self.generate_qr_code(conn_data)

    def generate_qr_code(self, connection_data):
        """Generate a QR code for a given network and display it."""
        ssid = connection_data['ssid']
        password = connection_data['password']
        # Assume WPA/WPA2 if there's a password, otherwise open
        security = "WPA" if password else "nopass" 
        
        qr_image = QRHandler.generate_wifi_qr_code(ssid, password, security)
        if qr_image:
            self.current_qr_image = qr_image # Store for saving
            self.display_qr(qr_image, ssid)
            # Emit signal
            self.qr_generated.emit(qr_image)
        else:
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showMessage("Failed to generate QR code.", 5000)

    def display_qr(self, qr_image, ssid):
        """Display the QR code image in the QLabel."""
        try:
            # Convert PIL Image to QPixmap
            qimage = self._pil_image_to_qimage(qr_image)
            if qimage:
                pixmap = QPixmap.fromImage(qimage)
                # Scale pixmap to fit the label, keeping aspect ratio
                scaled_pixmap = pixmap.scaled(self.qr_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.qr_label.setPixmap(scaled_pixmap)
                
                self.qr_label.show()
                self.info_label.hide() # Hide details text
                self.copy_password_button.hide()
                self.generate_qr_button.hide()
                self.save_qr_button.show()
                self.save_qr_string_button.show()
                self.back_to_details_button.show()
                
                self.info_label.setText(f"QR Code for <b>{ssid}</b>")
            else:
                raise Exception("Failed to convert PIL image to QImage.")
        except Exception as e:
            print(f"Error displaying QR code: {e}")
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showMessage("Error displaying QR code.", 5000)

    def _pil_image_to_qimage(self, pil_image):
        """Convert a PIL Image to a QImage."""
        try:
            # Ensure image is in RGB mode
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            
            # Save PIL image to a bytes buffer
            buf = io.BytesIO()
            pil_image.save(buf, format='PNG') # Use PNG for lossless
            img_data = buf.getvalue()
            buf.close()
            
            # Create QImage from bytes
            qimage = QImage()
            qimage.loadFromData(img_data)
            return qimage
        except Exception as e:
            print(f"Error converting PIL image to QImage: {e}")
            return None

    def save_current_qr_code(self):
        """Save the currently displayed QR code to a file."""
        if not self.current_qr_image:
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showMessage("No QR code to save.", 3000)
            return

        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save QR Code", f"wifi_{self.current_connection['ssid']}.png", "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            try:
                # Save the PIL image directly
                self.current_qr_image.save(file_path, 'PNG')
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"QR code saved to {file_path}", 5000)
            except Exception as e:
                print(f"Error saving QR code: {e}")
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"Failed to save QR code: {e}", 5000)

    def save_qr_string_to_file(self):
        """Save the QR code string to a text file."""
        if not self.current_connection:
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showMessage("No network selected.", 3000)
            return

        ssid = self.current_connection['ssid']
        password = self.current_connection['password']
        security = "WPA" if password else "nopass"

        # Construct the WiFi string
        if security.upper() == "NOPASS":
            wifi_string = f"WIFI:T:nopass;S:{ssid};;"
        else:
            wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};;"

        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save QR String", f"wifi_{ssid}.txt", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(wifi_string)
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"QR string saved to {file_path}", 5000)
            except Exception as e:
                print(f"Error saving QR string: {e}")
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"Failed to save QR string: {e}", 5000)