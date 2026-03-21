from tracemalloc import start

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QLineEdit
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread
from PyQt6.QtWebEngineWidgets import QWebEngineView
from UAVcontrol.controller import Controller
from UAVcontrol.recorder import Recorder
import numpy as np
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen

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
        self.img_widget = QWidget()
        information_layout.addWidget(status_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        information_layout.addWidget(self.img_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        status_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        
        imgs_layout = QVBoxLayout(self.img_widget)
        self.rgb_label = QLabel()
        self.depth_label = QLabel()
        imgs_layout.addWidget(self.rgb_label)
        imgs_layout.addWidget(self.depth_label)
        
        status_layout = QVBoxLayout(status_widget)
        start_button = QPushButton("Start")
        self.UAV_position_label = QLabel("UAV Position:")
        self.object_position_label = QLabel("Object Position:")
        scene_transformation_widget = QWidget()
        object_coor_widget = QWidget()
        status_layout.addWidget(start_button)
        status_layout.addWidget(self.UAV_position_label)
        status_layout.addWidget(self.object_position_label)
        status_layout.addWidget(scene_transformation_widget)
        status_layout.addWidget(object_coor_widget)
        start_button.clicked.connect(self.start_recording)
        
        scene_transformation_layout = QHBoxLayout(scene_transformation_widget)
        scene_transformation_label = QLabel("Starter Coordinate:")
        scene_transformation_x_label = QLabel("x=")
        self.scene_transformation_x_edit = QLineEdit()
        scene_transformation_y_label = QLabel("y=")
        self.scene_transformation_y_edit = QLineEdit()
        scene_transformation_z_label = QLabel("z=")
        self.scene_transformation_z_edit = QLineEdit()
        self.scene_transformation_pushbutton = QPushButton("Input")
        
        scene_transformation_layout.addWidget(scene_transformation_label)
        scene_transformation_layout.addWidget(scene_transformation_x_label)
        scene_transformation_layout.addWidget(self.scene_transformation_x_edit)
        scene_transformation_layout.addWidget(scene_transformation_y_label)
        scene_transformation_layout.addWidget(self.scene_transformation_y_edit)
        scene_transformation_layout.addWidget(scene_transformation_z_label)
        scene_transformation_layout.addWidget(self.scene_transformation_z_edit)
        scene_transformation_layout.addWidget(self.scene_transformation_pushbutton)
        
        object_coor_layout = QHBoxLayout(object_coor_widget)
        object_coor_label = QLabel("Object Coordinate:")
        object_coor_x_label = QLabel("x=")
        self.object_coor_x_edit = QLineEdit()
        object_coor_y_label = QLabel("y=")
        self.object_coor_y_edit = QLineEdit()
        object_coor_z_label = QLabel("z=")
        self.object_coor_z_edit = QLineEdit()
        self.object_coor_pushbutton = QPushButton("Input")
        
        object_coor_layout.addWidget(object_coor_label)
        object_coor_layout.addWidget(object_coor_x_label)
        object_coor_layout.addWidget(self.object_coor_x_edit)
        object_coor_layout.addWidget(object_coor_y_label)
        object_coor_layout.addWidget(self.object_coor_y_edit)
        object_coor_layout.addWidget(object_coor_z_label)
        object_coor_layout.addWidget(self.object_coor_z_edit)
        object_coor_layout.addWidget(self.object_coor_pushbutton)
        
        self.starter = (219460.015625, -290750.03125, 162.000488) # (x, y, z)
        self.object_coor = (209905.375, -289765.21875, 721.391479) # (x, y, z)
        
        self.controller = None
        QTimer.singleShot(0, self.start_control)
        
    def start_control(self):
        self.UAV_thread = QThread()
        self.controller = Controller()
        self.controller.moveToThread(self.UAV_thread)
        self.UAV_thread.start()
        self.controller.position_signal.connect(self.position_got)
        self.controller.orientation_signal.connect(self.orientation_got)
        self.controller.rgb_signal.connect(self.rgb_got)
        self.controller.depth_signal.connect(self.depth_got)
        
        self.recorder = Recorder(self.controller)
        self.recordthread = QThread()
        self.recorder.object_coor_signal.connect(self.display_object_coor)
        self.recorder.object_pix_signal.connect(self.display_object_pix)
        self.recorder.moveToThread(self.recordthread)
        self.recordthread.start()
        
    def display_object_coor(self, x: float, y: float, z: float):
        self.object_position_label.setText(f"Object Position: ({x:.2f}, {y:.2f}, {z:.2f})")
    
    def display_object_pix(self, x: float, y: float, width: int, height: int):
        pixmap = self.rgb_label.pixmap()
        if pixmap is None:
            return
        painter = QPainter(pixmap)
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(QPen())
        r = 5
        
        pixmap_w = pixmap.width()
        pixmap_h = pixmap.height()
        scale_x = pixmap_w / width
        scale_y = pixmap_h / height
        x = x * scale_x
        y = y * scale_y
        
        painter.drawEllipse(int(x - r), int(y - r), 2*r, 2*r)

        painter.end()
        self.rgb_label.setPixmap(pixmap)
        
    def start_recording(self):
        if self.starter is not None and self.object_coor is not None:
            if self.recorder:
                self.recorder.starter = self.starter
                self.recorder.object_coor = self.object_coor
                self.recorder.started = True
                self.recorder.start()
        
    def position_got(self, x: float, y: float, z: float):
        self.UAV_position_label.setText(f"UAV Position: ({x:.2f}, {y:.2f}, {z:.2f})")
        if self.recorder.started:
            self.recorder.position = (x, y, z)
        
    def orientation_got(self, w: float, x: float, y: float, z: float):
        if self.recorder.started:
            self.recorder.orientation = (w, x, y, z)
    
    def rgb_got(self, img: np.ndarray):
        if img is None:
            return
        if self.recorder.started:
            self.recorder.rgb = img
        img = img[:, :, ::-1] # convert BGR to RGB
        h, w, ch = img.shape
        bytes_per_line = ch * w
        qimg = QImage(img.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.rgb_label.setPixmap(QPixmap.fromImage(qimg))
        
    def depth_got(self, img: np.ndarray):
        if img is None:
            return
        if self.recorder.started:
            self.recorder.depth = img
        h, w = img.shape
        img_norm = (img - img.min()) / (img.max() - img.min() + 1e-8)
        img_uint8 = (img_norm * 255).astype('uint8')
        bytes_per_line = w
        qimg = QImage(img_uint8.tobytes(), w, h, bytes_per_line, QImage.Format.Format_Grayscale8).copy()
        self.depth_label.setPixmap(QPixmap.fromImage(qimg))
        
    def closeEvent(self, event):
        if self.recorder:
            self.recorder.stop()
        if self.recordthread:
            self.recordthread.quit()
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