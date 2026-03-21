from turtle import pos

from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from UAVcontrol.controller import Controller
import numpy as np

class Recorder(QObject):
    object_coor_signal = pyqtSignal(float, float, float)
    object_pix_signal = pyqtSignal(float, float, int, int)
    
    def __init__(self, controller: Controller):
        super().__init__()
        self.started = False
        self.controller = controller
        
        self.position = None # (x, y, z)
        self.orientation = None # (w, x, y, z)
        self.rgb = None
        self.depth = None
        
        self.starter = None # (x, y, z)
        self.object_coor = None # (x, y, z)
        
        self.R_convert1 = np.array([
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, -1]
        ])
        self.R_convert2 = np.array([
            [0,0,1],
            [1,0,0],
            [0,1,0]
        ])
        
    def start(self):
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.record_data)
        self.record_timer.start(5000)
        self.starter = np.array(self.starter)
        self.object_coor = np.array(self.object_coor)
        self.object_airsim_coor = (self.object_coor - self.starter) / 100
        self.object_coor_signal.emit(self.object_airsim_coor[0], self.object_airsim_coor[1], self.object_airsim_coor[2])
    
    def record_data(self):
        if self.started:
            self.controller.obtain_photos()
        
        position = self.position
        orientation = self.orientation
        rgb = self.rgb
        depth = self.depth
        R = quat_to_R(orientation[1], orientation[2], orientation[3], orientation[0])
        R = (self.R_convert1 @ R @ self.R_convert2).T
        position = np.array([position[1], position[0], -position[2]]).reshape(3, 1)
        object_coor = np.array([self.object_airsim_coor[1], self.object_airsim_coor[0], self.object_airsim_coor[2]]).reshape(3, 1)
        T = - R @ position
        fov_rad = np.deg2rad(self.controller.fov)
        width, height = self.controller.width, self.controller.height
        fx = width / (2 * np.tan(fov_rad / 2))
        fy = fx
        cx = width / 2
        cy = height / 2
        K = np.array([
            [fx, 0, cx],
            [0, fy, cy],
            [0, 0, 1]
        ])
        #print(R @ object_coor + T)
        pix = K @ (R @ object_coor + T)
        pix = pix / pix[2]
        self.object_pix_signal.emit(pix[0], pix[1], width, height)
        # pix: object position in pixel (pix0: x → ; pix1: y ↓ )
        
        self.rgb = None
        self.depth = None
        
    def stop(self):
        if self.started:
            self.started = False
            self.record_timer.stop()
            
def quat_to_R(qx, qy, qz, qw):
    R = np.array([
        [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qz*qw), 2*(qx*qz + qy*qw)],
        [2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qx*qw)],
        [2*(qx*qz - qy*qw), 2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy)]
    ])
    return R