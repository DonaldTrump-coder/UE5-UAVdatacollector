from tracemalloc import start

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

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