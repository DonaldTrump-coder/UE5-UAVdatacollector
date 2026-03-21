from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from UAVcontrol.controller import Controller
import numpy as np
from dataclasses import dataclass
import time
import math
import os
import cv2

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
        self.folder = None
        
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
        
        self.last_x = None
        self.last_y = None
        self.forward = None
        self.right = None
        
        self.time = None
        
    def start(self):
        self.starter = np.array(self.starter)
        self.object_coor = np.array(self.object_coor)
        self.object_airsim_coor = (self.object_coor - self.starter) / 100
        self.object_coor_signal.emit(self.object_airsim_coor[0], self.object_airsim_coor[1], self.object_airsim_coor[2])
        
        self.pos_folder = os.path.join(self.folder, "pos")
        self.rgb_folder = os.path.join(self.folder, "rgb")
        self.depth_folder = os.path.join(self.folder, "depth")
        self.pix_folder = os.path.join(self.folder, "pix")
        os.makedirs(self.pos_folder, exist_ok=True)
        os.makedirs(self.rgb_folder, exist_ok=True)
        os.makedirs(self.depth_folder, exist_ok=True)
        os.makedirs(self.pix_folder, exist_ok=True)
        self.time = 0
        
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.record_data)
        self.record_timer.start(5000)
    
    def record_data(self):
        if self.started:
            self.controller.obtain_photos()
        
        position = self.position
        orientation = self.orientation
        while self.rgb is None or self.depth is None:
            time.sleep(0.01)
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
        if (R @ object_coor + T)[2] <= 0:
            pix = "back"
        else:
            pix = K @ (R @ object_coor + T)
            pix = (pix / pix[2])[:2]
            if pix[0] < 0:
                pix = "left"
            elif pix[0] > width:
                pix = "right"
            elif pix[1] < 0:
                pix = "top"
            elif pix[1] > height:
                pix = "bottom"
            else:
                self.object_pix_signal.emit(pix[0], pix[1], width, height)
                # pix: object position in pixel (pix0: x → ; pix1: y ↓ )
        
        position = (position[1], position[0], position[2]) # (x, y, -z) in Airsim
        orientation = quaternion_to_euler(orientation[1], orientation[2], orientation[3], orientation[0]) # (roll, pitch, yaw) in Airsim
        yaw = orientation[2]
        if self.last_x is not None and self.last_y is not None:
            dx = position[0] - self.last_x
            dy = position[1] - self.last_y
            self.forward = math.cos(yaw) * dx + math.sin(yaw) * dy
            self.right = -math.sin(yaw) * dx + math.cos(yaw) * dy
            
        self.last_x = position[0]
        self.last_y = position[1]
        orientation = (orientation[0], orientation[1], orientation[2])
        record = Record(position=position, orientation=orientation, rgb=rgb, depth=depth, pix=pix, forward=self.forward, right=self.right)
        self.save_record(record)
        self.time += 1
        
        self.rgb = None
        self.depth = None
        
    def save_record(self, record):
        # record pos
        filename = f"{self.time}.txt"
        filepath = os.path.join(self.pos_folder, filename)
        with open(filepath, "w") as f:
            f.write("x, y, z, yaw, forward, right\n")
            values = [record.position[0], record.position[1], record.position[2], record.orientation[2], record.forward, record.right]
            line = ", ".join("None" if v is None else str(v) for v in values)
            f.write(line + "\n")
        
        # record pix
        filename = f"{self.time}.txt"
        filepath = os.path.join(self.pix_folder, filename)
        pix = record.pix
        with open(filepath, "w") as f:
            if isinstance(pix, str):
                line = pix
            else:
                line = f"{pix[0]}, {pix[1]}"
            f.write(line + "\n")
        
        # record rgb
        filename = f"{self.time}.png"
        filepath = os.path.join(self.rgb_folder, filename)
        cv2.imwrite(filepath, record.rgb)
        
        #record depth
        filename = f"{self.time}.npy"
        filepath = os.path.join(self.depth_folder, filename)
        np.save(filepath, record.depth)
        
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

def quaternion_to_euler(x, y, z, w):
    # roll (x-axis rotation)
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 * (1.0 - 2.0 * (x * x + y * y))
    roll = math.atan2(t0, t1)

    # pitch (y-axis rotation)
    t2 = +2.0 * (w * y - z * x)
    t2 = max(min(t2, 1.0), -1.0)
    pitch = math.asin(t2)

    # yaw (z-axis rotation)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 * (1.0 - 2.0 * (y * y + z * z))
    yaw = math.atan2(t3, t4)

    return roll, pitch, yaw

@dataclass
class Record:
    position: tuple[float, float, float] # (x, y, -z)
    orientation: tuple[float, float, float] # (roll, pitch, yaw)
    rgb: np.ndarray
    depth: np.ndarray
    pix: tuple[float, float] # (x, y)
    forward: float
    right: float