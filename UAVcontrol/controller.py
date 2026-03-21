import airsim
from PyQt6.QtCore import pyqtSignal, QObject, QTimer
import numpy as np
import time

class Controller(QObject):
    position_signal = pyqtSignal(float, float, float)
    orientation_signal = pyqtSignal(float, float, float, float)
    rgb_signal = pyqtSignal(object)
    depth_signal = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        QTimer.singleShot(0, self.initialize_UAV)
        self.lock = False
        
    def initialize_UAV(self):
        try:
            self.client = airsim.MultirotorClient()
            self.client.confirmConnection()
        except:
            self.running = False
            return
        self.client.enableApiControl(True)
        self.client.armDisarm(True)
        self.client.takeoffAsync().join() # takeoff the drone before controlling
        self.running=True
        self.landed=False
        
        self.forward = False
        self.backward = False
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.turn_left = False
        self.turn_right = False
        
        camera_info = self.client.simGetCameraInfo("0")
        self.fov = camera_info.fov
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_control)
        self.timer.start(50)
        
    def get_state(self):
        state = self.client.getMultirotorState()
        pos = state.kinematics_estimated.position
        ori = state.kinematics_estimated.orientation
        x = pos.x_val
        y = pos.y_val
        z = pos.z_val
        self.position_signal.emit(x, y, z)
        self.orientation_signal.emit(ori.w_val, ori.x_val, ori.y_val, ori.z_val)
        
    def update_control(self):
        if self.running:
            vx, vy, vz = 0, 0, 0
            yaw_rate = 0
            if self.forward:
                vx = 2
            if self.backward:
                vx = -2
            if self.left:
                vy = -2
            if self.right:
                vy = 2
            if self.up:
                vz = -2
            if self.down:
                vz = 2
            if self.turn_left:
                yaw_rate = -30
            if self.turn_right:
                yaw_rate = 30
            while self.lock is True:
                continue
            self.lock = True
            yaw_mode = airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate)
            self.client.moveByVelocityBodyFrameAsync(
                vx,
                vy,
                vz,
                0.1,
                yaw_mode=yaw_mode
            )
            self.get_state()
            self.lock = False
            
    def obtain_photos(self):
        if self.running:
            while self.lock is True:
                continue
            self.lock = True
            responses = self.client.simGetImages([
                airsim.ImageRequest("0", airsim.ImageType.Scene, False, False),
                airsim.ImageRequest("0", airsim.ImageType.DepthPerspective, True)
            ])
            self.width = responses[0].width
            self.height = responses[0].height
            rgb = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
            rgb = rgb.reshape(responses[0].height, responses[0].width, 3)
            
            depth = np.array(responses[1].image_data_float, dtype=np.float32)
            depth = depth.reshape(responses[1].height, responses[1].width)
            
            self.rgb_signal.emit(rgb)
            self.depth_signal.emit(depth)
            self.lock = False
            
    def unlease(self):
        self.forward = False
        self.backward = False
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.turn_left = False
        self.turn_right = False
            
    def stop(self):
        if self.running is False:
            return
        self.running = False
        self.timer.stop()
        time.sleep(0.1)
        self.client.hoverAsync().join() # hover the drone before landing
        self.client.landAsync().join() # land the drone
        self.client.armDisarm(False)
        self.client.enableApiControl(False)
        self.landed = True