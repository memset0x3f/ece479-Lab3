import numpy as np
import RTIMU
import time
import math
import json
import socket
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap

class VelocityPositionTracker:
    """Velocity and position tracker with drift compensation, 用度数阈值。"""
    def __init__(self):
        self.position = np.zeros(3)  # [x, y, z] in meters
        self.position_clip = 1

    def update(self, roll_deg, pitch_deg):
        delta_position = np.zeros(3)

        # degree
        roll_thresh_deg = 30
        pitch_thresh_deg = 30

        if abs(roll_deg) > roll_thresh_deg:
            delta_position[0] += math.copysign(
                1,
                roll_deg
            ) * (0.02 + (abs(roll_deg) - roll_thresh_deg) * 0.01)
        if abs(pitch_deg) > pitch_thresh_deg:
            delta_position[1] += math.copysign(
                1,
                pitch_deg
            ) * (0.02 + (abs(pitch_deg) - pitch_thresh_deg) * 0.01)

        self.position += delta_position
        self.position = np.clip(self.position, -self.position_clip, self.position_clip)

class IMU:
    def __init__(self, slerp_power=0.2):
        self.SETTINGS_FILE = "RTIMULib"
        self.settings = RTIMU.Settings(self.SETTINGS_FILE)
        self.imu = RTIMU.RTIMU(self.settings)

        if not self.imu.IMUInit():
            raise RuntimeError("Failed to initialize IMU")

        self.imu.setSlerpPower(slerp_power)
        self.imu.setGyroEnable(True)
        self.imu.setAccelEnable(True)
        self.imu.setCompassEnable(False)

        self.poll_interval = self.imu.IMUGetPollInterval()
        self.tracker = VelocityPositionTracker()
        self.last_ts = None

    def get_data(self):
        if not self.imu.IMURead():
            return None

        data = self.imu.getIMUData()
        ts = data["timestamp"]
        # 计算时间差（秒）
        if self.last_ts is None:
            dt = self.poll_interval / 1000.0
        else:
            dt = (ts - self.last_ts) / 1e6
        self.last_ts = ts

        fusionPose = data["fusionPose"]
    
        roll_deg  = math.degrees(fusionPose[0])
        pitch_deg = math.degrees(fusionPose[1])
        yaw_deg   = math.degrees(fusionPose[2])

        self.tracker.update(roll_deg, pitch_deg)

        return {
            "timestamp": ts / 1e6,
            "roll": roll_deg,
            "pitch": pitch_deg,
            "yaw": yaw_deg,
            "position": self.tracker.position.copy().tolist()
        }

# if __name__ == "__main__":
#     # 初始化 UDP socket
#     udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     udp_addr = ("10.186.9.83", 5005)

#     try:
#         imu = IMU()
#         print("Tracking started. Press Ctrl+C to stop.")

#         x_vals = []
#         y_vals = []
#         time_vals = []
#         start_time = time.time()

#         while True:
#             data = imu.get_data()
#             if data:
#                 print(f"\nPosition (m): X={data['position'][0]:.3f}, "
#                       f"Y={data['position'][1]:.3f}, Z={data['position'][2]:.3f}")
#                 print(f"Roll (deg): {data['roll']:.3f}, "
#                       f"Pitch (deg): {data['pitch']:.3f}, "
#                       f"Yaw (deg): {data['yaw']:.3f}")
#                 x_vals.append(data["position"][0])
#                 y_vals.append(data["position"][1])
#                 time_vals.append(time.time() - start_time) 
#                 msg = json.dumps(data)
#                 udp_sock.sendto(msg.encode("utf-8"), udp_addr)

#             time.sleep(imu.poll_interval / 1000.0)

#     except KeyboardInterrupt:
#         print("\nTracking stopped. Plotting trajectory and saving image...")
#         plt.figure()
#         cmap = get_cmap("viridis")
#         norm_times = [(t % 10) / 10.0 for t in time_vals]  # normalize to [0,1] within 10s cycle

#         for i in range(1, len(x_vals)):
#             plt.plot(
#                 x_vals[i-1:i+1],
#                 y_vals[i-1:i+1],
#                 color=cmap(norm_times[i])
#             )

#         plt.xlim(-1, 1)
#         plt.ylim(-1, 1)
#         plt.xlabel('X Position (m)')
#         plt.ylabel('Y Position (m)')
#         plt.title('IMU Trajectory (X vs Y)')
#         plt.grid(True)
#         plt.savefig("imu_trajectory.png")
#         plt.show()

if __name__ == "__main__":
    import socket, json, time
    import matplotlib.pyplot as plt
    from matplotlib.cm import get_cmap

    # ---- 配置 ----
    UDP_IP   = "100.127.82.27"
    UDP_PORT = 3000
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        imu = IMU()
        print("Tracking started. Press Ctrl+C to stop.")
        x_vals, y_vals, time_vals = [], [], []
        start_time = time.time()
        next_ts = start_time

        while True:
            # 精准节拍
            now = time.time()
            if now < next_ts:
                time.sleep(next_ts - now)
            next_ts += imu.poll_interval / 1000.0

            data = imu.get_data()
            if not data:
                continue

            # 打印
            print(f"\nPosition: X={data['position'][0]:.3f}, "
                  f"Y={data['position'][1]:.3f}, Z={data['position'][2]:.3f}")
            print(f"Roll={data['roll']:.3f}°, "
                  f"Pitch={data['pitch']:.3f}°, "
                  f"Yaw={data['yaw']:.3f}°")

            # 保存用于绘图
            x_vals.append(data["position"][0])
            y_vals.append(data["position"][1])
            time_vals.append(now - start_time)

            # 发送（加换行）
            msg = json.dumps(data) + "\n"
            try:
                sent = udp_sock.sendto(msg.encode("utf-8"), (UDP_IP, UDP_PORT))
                print(sent) 
            except Exception as e:
                print(f"UDP send error: {e}")

    except KeyboardInterrupt:
        print("\nTracking stopped. Plotting trajectory...")
    finally:
        udp_sock.close()

        # 绘图
        plt.figure()
        cmap = get_cmap("viridis")
        norm_times = [(t % 10) / 10.0 for t in time_vals]
        for i in range(1, len(x_vals)):
            plt.plot(
                x_vals[i-1:i+1],
                y_vals[i-1:i+1],
                color=cmap(norm_times[i])
            )
        plt.xlim(-1, 1)
        plt.ylim(-1, 1)
        plt.xlabel('X Position (m)')
        plt.ylabel('Y Position (m)')
        plt.title('IMU Trajectory (X vs Y)')
        plt.grid(True)
        plt.savefig("imu_trajectory.png")
        plt.show()
