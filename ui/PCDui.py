import pyqtgraph.opengl as gl
import numpy as np
from PyQt5.QtGui import QVector3D

class PointCloudWidget(gl.GLViewWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        # 相机与坐标轴
        self.setCameraPosition(distance=10)
        self.opts['center'] = QVector3D(0, 0, 0)

        # 初始化点云数据
        self.points = np.zeros((0, 3))
        self.colors = np.ones((0, 4))

        self.scatter = gl.GLScatterPlotItem(pos=self.points, color=self.colors, size=5)
        self.addItem(self.scatter)

    def get_pointcloud(self, points: np.ndarray, point: np.ndarray):
        if points is None or len(points) == 0:
            return
        self.points = np.asarray(points, dtype=float)
        self.colors = np.ones((len(points), 4))
        self.points = np.vstack([self.points, point])
        self.colors = np.vstack([self.colors, [1, 0, 0, 1]])
        self.scatter.setData(pos=self.points, color=self.colors)

        center = np.mean(self.points, axis=0)
        self.opts['center'] = QVector3D(*center)
        max_range = np.max(np.linalg.norm(self.points - center, axis=1))
        self.setCameraPosition(distance=max_range * 2.0)

    def change_pos(self, point: np.ndarray):
        point = np.asarray(point, dtype=float).reshape(1, 3)
        self.points[-1] = point
        self.scatter.setData(pos=self.points, color=self.colors)