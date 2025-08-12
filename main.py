#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow

def main():
    # Check if the application is running as root
    if os.geteuid() != 0:
        app = QApplication(sys.argv)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Insufficient Privileges")
        msg_box.setText("This application requires root privileges to manage Wi-Fi connections.")
        msg_box.setInformativeText("Please run the application with 'sudo python3 main.py'")
        msg_box.exec()
        sys.exit(1)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()