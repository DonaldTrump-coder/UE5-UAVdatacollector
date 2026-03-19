import airsim
from PyQt6.QtCore import pyqtSignal, QObject, QTimer

class Controller(QObject):
    def __init__(self):
        super().__init__()
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
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_control)
        self.timer.start(50)
        
        self.forward = False
        self.backward = False
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.turn_left = False
        self.turn_right = False
        
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
            yaw_mode = airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate)
            self.client.moveByVelocityBodyFrameAsync(
                vx,
                vy,
                vz,
                0.1,
                yaw_mode=yaw_mode
            )
            
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
        self.client.hoverAsync().join() # hover the drone before landing
        self.client.landAsync().join() # land the drone
        self.client.armDisarm(False)
        self.client.enableApiControl(False)
        self.landed = True