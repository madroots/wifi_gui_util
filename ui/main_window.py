from PyQt6.QtWidgets import QMainWindow, QToolBar, QStatusBar, QStackedWidget, QMessageBox
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt
import os

# Import UI components
from ui.network_list import NetworkListView
from ui.qr_scanner import QRScannerView

class MainWindow(QMainWindow):
    """
    The main application window.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wi-Fi QR Manager")
        self.setGeometry(100, 100, 800, 600) # Set a reasonable initial size

        # Create the central stacked widget to switch between views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create the main views
        self.network_list_view = NetworkListView()
        self.qr_scanner_view = QRScannerView()

        # Add views to the stacked widget
        self.stacked_widget.addWidget(self.network_list_view)
        self.stacked_widget.addWidget(self.qr_scanner_view)
        
        # Initially show the network list view
        self.stacked_widget.setCurrentWidget(self.network_list_view)

        # Create actions, menus, and toolbars
        self._create_actions()
        self._create_toolbars()
        self._create_status_bar()
        
        # Connect signals from views to main window slots for coordination
        self.network_list_view.qr_generated.connect(self.display_qr_code)
        self.qr_scanner_view.qr_scanned.connect(self.handle_scanned_qr)
        self.qr_scanner_view.scan_finished.connect(self.show_network_list_view)

    def _create_actions(self):
        """Create actions for menus and toolbars."""
        self.refresh_action = QAction(QIcon.fromTheme("view-refresh"), "&Refresh", self)
        self.refresh_action.setStatusTip("Refresh the list of saved networks")
        self.refresh_action.triggered.connect(self.network_list_view.refresh_connections)

        self.scan_qr_action = QAction(QIcon.fromTheme("camera-photo"), "&Scan QR Code", self)
        self.scan_qr_action.setStatusTip("Scan a QR code to import a Wi-Fi network")
        self.scan_qr_action.triggered.connect(self.show_qr_scanner_view)

        self.about_action = QAction(QIcon.fromTheme("help-about"), "&About", self)
        self.about_action.setStatusTip("Show information about this application")
        self.about_action.triggered.connect(self.show_about)

    def _create_toolbars(self):
        """Create toolbars."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False) # Make it fixed
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        toolbar.addAction(self.refresh_action)
        toolbar.addSeparator()
        toolbar.addAction(self.scan_qr_action)
        toolbar.addSeparator()
        # Spacer to push 'About' to the right (PyQt doesn't have a direct spacer, 
        # but we can add a stretchable widget or just leave space)
        # For simplicity, we'll add 'About' at the end.
        toolbar.addAction(self.about_action)

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready", 2000) # Show "Ready" for 2 seconds

    def show_qr_scanner_view(self):
        """Switch to the QR scanner view."""
        self.stacked_widget.setCurrentWidget(self.qr_scanner_view)
        self.qr_scanner_view.start_scan() # Start the camera scan when switching view

    def show_network_list_view(self):
        """Switch back to the network list view."""
        self.stacked_widget.setCurrentWidget(self.network_list_view)

    def display_qr_code(self, qr_image):
        """Display a generated QR code. This can be extended to show it in a dialog or the details panel."""
        # For now, just show a message. In a full implementation, 
        # this would update the NetworkListView's details panel or open a dialog.
        self.status_bar.showMessage("QR Code generated. Display logic goes here.", 5000)
        # Example of showing in a dialog (uncomment if needed)
        # from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout
        # dialog = QDialog(self)
        # dialog.setWindowTitle("Generated QR Code")
        # label = QLabel()
        # # Convert PIL Image to QPixmap (requires conversion)
        # # This is a placeholder for the actual conversion logic
        # # pixmap = self._pil_image_to_qpixmap(qr_image) 
        # # label.setPixmap(pixmap)
        # layout = QVBoxLayout()
        # layout.addWidget(label)
        # dialog.setLayout(layout)
        # dialog.exec()

    def handle_scanned_qr(self, ssid, password, security):
        """Handle a successfully scanned QR code."""
        self.status_bar.showMessage(f"Scanned QR Code: SSID='{ssid}', Security='{security}'", 5000)
        # In a full implementation, this would populate fields in the QRScannerView 
        # or open a dialog asking to connect/save.
        # For now, just show an info box.
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("QR Code Scanned")
        msg_box.setText(f"Wi-Fi Network Found:\nSSID: {ssid}\nPassword: {'*' * len(password) if password else '(None)'}\nSecurity: {security}")
        connect_button = msg_box.addButton("Connect Now", QMessageBox.ButtonRole.AcceptRole)
        save_button = msg_box.addButton("Save Profile", QMessageBox.ButtonRole.ActionRole)
        cancel_button = msg_box.addButton(QMessageBox.StandardButton.Cancel)
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == connect_button:
            self.attempt_connect(ssid, password)
        elif clicked_button == save_button:
            self.save_profile(ssid, password, security)

    def attempt_connect(self, ssid, password):
        """Attempt to connect to a network using WifiManager."""
        # Import here to avoid circular imports if needed
        from wifi_manager import WifiManager
        success, message = WifiManager.connect_to_network(ssid, password)
        if success:
            self.status_bar.showMessage(message, 5000)
            # Optionally, refresh the network list to show the new status
            self.network_list_view.refresh_connections()
        else:
            self.status_bar.showMessage(f"Connection failed: {message}", 5000)
            QMessageBox.critical(self, "Connection Error", message)

    def save_profile(self, ssid, password, security):
        """Save a new network profile using WifiManager."""
        from wifi_manager import WifiManager
        success, message = WifiManager.save_profile(ssid, password, security)
        if success:
            self.status_bar.showMessage(message, 5000)
            # Refresh the network list to show the new profile
            self.network_list_view.refresh_connections()
        else:
            self.status_bar.showMessage(f"Save profile failed: {message}", 5000)
            QMessageBox.critical(self, "Save Profile Error", message)

    def show_about(self):
        """Show an about dialog."""
        QMessageBox.about(self, "About Wi-Fi QR Manager",
                          "Wi-Fi QR Manager\n\n"
                          "A simple tool to manage saved Wi-Fi networks, "
                          "generate QR codes for sharing, and scan QR codes "
                          "to import networks.\n\n"
                          "Version 1.0")