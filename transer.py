import numpy as np
import open3d as o3d
import math

X = 3440.0/100
Y = -740.0/100
Z = 11870.0/100
Pitch = 180.0
Yaw = 90.0
Roll = 180.0 # degrees

def inverse_UE_transform(x_world, y_world, z_world):
    # rotations and translation in of GS in UE
    pitch, yaw, roll = np.radians([Pitch, Yaw, Roll])

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll),  np.cos(roll)]
    ])
    
    Ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])
    
    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw),  np.cos(yaw), 0],
        [0, 0, 1]
    ])

    R = Rz @ Ry @ Rx
    T = np.array([X, Y, Z])
    
    P_world = np.array([y_world, -x_world, z_world])
    P_local = R.T @ (P_world - T)
    return float(P_local[0]), float(P_local[1]), float(P_local[2]) # left-handed to right-handed

def get_lla(x, y, z):
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2*f - f*f

    # 经度
    lon = math.atan2(y, x)

    # 中间量
    p = math.sqrt(x*x + y*y)

    # 初始纬度
    lat = math.atan2(z, p * (1 - e2))

    # 迭代求纬度（Bowring method）
    while True:
        N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
        lat_new = math.atan2(z + e2 * N * math.sin(lat), p)
        if abs(lat_new - lat) < 1e-12:  # 收敛标准
            break
        lat = lat_new

    # 高程
    N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
    h = p / math.cos(lat) - N

    # 转为角度
    lat_deg = math.degrees(lat)
    lon_deg = math.degrees(lon)

    return lat_deg, lon_deg, h

def get_GS_points(filename):
    pcd = o3d.io.read_point_cloud(filename)
    points = np.asarray(pcd.points)

    num_points = points.shape[0]
    sample_ratio = 0.005
    sample_num = int(num_points * sample_ratio)

    # 随机抽样索引
    indices = np.random.choice(num_points, sample_num, replace=False)
    points = points[indices]

    return points