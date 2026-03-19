from tracemalloc import start

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread
from PyQt6.QtWebEngineWidgets import QWebEngineView
from UAVcontrol.controller import Controller

class Datacollection(QMainWindow):
    def __init__(self, url):
        super().__init__()
        self.setWindowTitle("UAV Data Collector")
        self.resize(1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        self.UAV_view = QWebEngineView()
        self.UAV_view.load(QUrl(url))
        main_layout.addWidget(self.UAV_view, 2)
        
        information_widget = QWidget()
        information_layout = QVBoxLayout(information_widget)
        main_layout.addWidget(information_widget, 1)
        
        status_widget = QWidget()
        status_widget.setStyleSheet(
        """
        border: 1px solid black;
        """
        )
        self.img_label = QLabel()
        information_layout.addWidget(status_widget)
        information_layout.addWidget(self.img_label)
        
        status_layout = QVBoxLayout(status_widget)
        start_button = QPushButton("Start")
        self.UAV_position_label = QLabel("UAV Position:")
        self.object_position_label = QLabel("Object Position:")
        status_layout.addWidget(start_button)
        status_layout.addWidget(self.UAV_position_label)
        status_layout.addWidget(self.object_position_label)
        
        self.controller = None
        QTimer.singleShot(0, self.start_control)
        
    def start_control(self):
        self.UAV_thread = QThread()
        self.controller = Controller()
        self.controller.moveToThread(self.UAV_thread)
        self.UAV_thread.start()
        
    def closeEvent(self, event):
        if self.controller:
            self.controller.stop()
        if self.UAV_thread:
            self.UAV_thread.quit()
        
        event.accept()
        
    def keyPressEvent(self, event):
        if not self.controller:
            return
        key = event.key()
        
        if key == Qt.Key.Key_W:
            self.controller.forward = True
        elif key == Qt.Key.Key_S:
            self.controller.backward = True
        elif key == Qt.Key.Key_A:
            self.controller.left = True
        elif key == Qt.Key.Key_D:
            self.controller.right = True
        elif key == Qt.Key.Key_Space:
            self.controller.up = True
        elif key == Qt.Key.Key_Shift:
            self.controller.down = True
        elif key == Qt.Key.Key_Q:
            self.controller.turn_left = True
        elif key == Qt.Key.Key_E:
            self.controller.turn_right = True
            
    def keyReleaseEvent(self, event):
        if not self.controller:
            return
        self.controller.unlease()