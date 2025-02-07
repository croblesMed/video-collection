import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QCheckBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from camera_streamer import CameraStreamer

class CameraGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.streamers = {}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(1000 // 30)  # Update at 30 FPS

    def initUI(self):
        self.setWindowTitle('Camera Collection')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.start_button = QPushButton('Start Stream', self)
        self.start_button.clicked.connect(self.start_stream)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Stream', self)
        self.stop_button.clicked.connect(self.stop_stream)
        layout.addWidget(self.stop_button)

        self.display_checkbox = QCheckBox('Display Live Feed', self)
        layout.addWidget(self.display_checkbox)

        self.camera_label = QLabel(self)
        self.camera_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camera_label)

        self.setLayout(layout)

    def start_stream(self):
        serial_number = "24750353"  # Example serial number
        output_file = "output.mp4"
        if serial_number not in self.streamers:
            streamer = CameraStreamer(serial_number, output_file)
            self.streamers[serial_number] = streamer
            streamer.start()

    def stop_stream(self):
        serial_number = "24750353"  # Example serial number
        if serial_number in self.streamers:
            self.streamers[serial_number].stop()
            self.streamers[serial_number].join()
            del self.streamers[serial_number]

    def update_frames(self):
        if self.display_checkbox.isChecked():
            serial_number = "24750353"  # Example serial number
            if serial_number in self.streamers:
                frame = self.streamers[serial_number].get_frame()
                if frame is not None:
                    image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
                    pixmap = QPixmap.fromImage(image)
                    self.camera_label.setPixmap(pixmap)
                else:
                    self.camera_label.clear()
        else:
            self.camera_label.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = CameraGUI()
    gui.show()
    sys.exit(app.exec_())