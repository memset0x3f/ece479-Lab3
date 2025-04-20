
import numpy as np
import RTIMU
import time
class EKF:
    def __init__(self):
        # 状态向量：四元数 [q0, q1, q2, q3]
        self.x = np.array([1, 0, 0, 0], dtype=float)  # 初始姿态：无旋转
        # 状态协方差矩阵
        self.P = np.eye(4) * 0.1
        # 过程噪声协方差
        self.Q = np.eye(4) * 0.001
        # 测量噪声协方差
        self.R = np.eye(3) * 0.01
        # 重力向量（世界坐标系）
        self.g_world = np.array([0, 0, -1], dtype=float)  # 重力沿z轴负方向

    def predict(self, omega, dt):
        """预测步骤：使用陀螺仪数据更新姿态"""
        # omega: 陀螺仪测量值 [wx, wy, wz] (rad/s)
        # dt: 时间间隔 (s)
        Omega = np.array([
            [0, -omega[0], -omega[1], -omega[2]],
            [omega[0], 0, omega[2], -omega[1]],
            [omega[1], -omega[2], 0, omega[0]],
            [omega[2], omega[1], -omega[0], 0]
        ])
        # 状态转移矩阵（线性近似）
        F = np.eye(4) + 0.5 * Omega * dt
        # 预测状态
        self.x = F @ self.x
        self.x /= np.linalg.norm(self.x)  # 归一化四元数
        # 更新协方差
        self.P = F @ self.P @ F.T + self.Q

    def update(self, accel):
        """更新步骤：使用加速度计数据校正姿态"""
        # accel: 加速度计测量值 [ax, ay, az] (g)
        q = self.x
        # 四元数转旋转矩阵
        R = self.quat_to_rot(q)
        # 预测的重力向量（设备坐标系）
        h = R @ self.g_world
        # 测量残差
        y = accel - h
        # 计算测量雅可比矩阵
        H = self.compute_H(q)
        # 卡尔曼增益
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)
        # 更新状态
        self.x += K @ y
        self.x /= np.linalg.norm(self.x)  # 归一化四元数
        # 更新协方差
        self.P = (np.eye(4) - K @ H) @ self.P

    def compute_H(self, q):
        """计算测量雅可比矩阵 H"""
        eps = 1e-6
        H = np.zeros((3, 4))
        for i in range(4):
            q_eps = q.copy()
            q_eps[i] += eps
            R_eps = self.quat_to_rot(q_eps)
            h_eps = R_eps @ self.g_world
            H[:, i] = (h_eps - self.quat_to_rot(q) @ self.g_world) / eps
        return H

    def quat_to_rot(self, q):
        """四元数转换为旋转矩阵"""
        return np.array([
            [1 - 2*(q[2]**2 + q[3]**2), 2*(q[1]*q[2] - q[0]*q[3]), 2*(q[1]*q[3] + q[0]*q[2])],
            [2*(q[1]*q[2] + q[0]*q[3]), 1 - 2*(q[1]**2 + q[3]**2), 2*(q[2]*q[3] - q[0]*q[1])],
            [2*(q[1]*q[3] - q[0]*q[2]), 2*(q[2]*q[3] + q[0]*q[1]), 1 - 2*(q[1]**2 + q[2]**2)]
        ])

    def get_gravity(self):
        """获取设备坐标系中的重力分量"""
        R = self.quat_to_rot(self.x)
        return R @ self.g_world

    def get_linear_accel(self, accel):
        """计算线性加速度"""
        gravity = self.get_gravity()
        return accel - gravity

# IMU配置和初始化
SETTINGS_FILE = "RTIMULib"
settings = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(settings)

if not imu.IMUInit():
    print("IMU初始化失败")
    exit(1)

imu.setSlerpPower(0.02)
imu.setGyroEnable(True)
imu.setAccelEnable(True)
imu.setCompassEnable(False)

poll_interval = imu.IMUGetPollInterval()

# 初始化EKF
ekf = EKF()

# 主循环
while True:
    if imu.IMURead():
        data = imu.getIMUData()
        accel = np.array(data["accel"])  # 加速度 (g)
        gyro = np.array(data["gyro"])    # 角速度 (rad/s)
        timestamp = data["timestamp"]

        # 计算时间间隔
        if 'last_timestamp' in locals():
            dt = (timestamp - last_timestamp) / 1e6  # 微秒转秒
        else:
            dt = poll_interval / 1000.0
        last_timestamp = timestamp

        # EKF预测和更新
        ekf.predict(gyro, dt)
        ekf.update(accel)
        # 获取线性加速度
        lin_accel = ekf.get_linear_accel(accel)

        print("线性加速度 (g): X=%.3f, Y=%.3f, Z=%.3f" % tuple(lin_accel))

    time.sleep(poll_interval * 1.0 / 1000.0)