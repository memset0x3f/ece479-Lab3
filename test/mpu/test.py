import numpy as np
import RTIMU
import time
import math
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import socket

class HighPassFilter:
    def __init__(self, alpha=0.9):
        self.alpha = alpha
        self.prev_input = np.zeros(3)
        self.prev_output = np.zeros(3)

    def apply(self, accel):
        output = self.alpha * (self.prev_output + accel - self.prev_input)
        self.prev_input = accel
        self.prev_output = output
        return output

class VelocityPositionTracker:
    """Velocity and position tracker with drift compensation."""
    def __init__(self):
        self.velocity = np.zeros(3)  # [vx, vy, vz] in m/s
        self.position = np.zeros(3)  # [x, y, z] in meters
        self.last_accel = np.zeros(3)

        # Compensation parameters
        self.velocity_decay = 0.8
        self.position_clip = 1
        self.zero_threshold = 0.5

    def accel_gain(self, a):
        # Piecewise gain function for acceleration
        gain = np.zeros_like(a)
        
        # for i in range(3):
            # gain[i] = np.sign(a[i]) * 0.01  # default gain
        # for i in range(3):
        #     abs_a = abs(a[i])
        #     if abs_a <= 1:
        #         gain[i] = a[i] * 0.02
        #     elif abs_a <= 3:
        #         gain[i] = np.sign(a[i]) * (0.02 + (abs_a - 1) * 0.01)
        #     else:
        #         gain[i] = np.sign(a[i]) * 0.04  # clamp maximum movement per axis
        return gain

    def update(self, accel, dt):
        if np.linalg.norm(accel) < self.zero_threshold:
            self.velocity *= 0.5
        else:
            avg_accel = 0.5 * (self.last_accel + accel)
            self.velocity += avg_accel * dt
            self.last_accel = accel.copy()

        self.position += self.accel_gain(accel)  # all x, y, z updated using gain
        self.velocity *= self.velocity_decay
        self.position = np.clip(self.position, -self.position_clip, self.position_clip)

class IMU:
    def __init__(self, slerp_power=0.02):
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
        self.rad2degree = 57.2958
        self.tracker = VelocityPositionTracker()
        self.last_ts = None
        self.hp_filter = HighPassFilter(alpha=0.9)

    def _get_lin_accel(self, data):
        fusionPose = data["fusionPose"]
        roll, pitch, yaw = fusionPose

        g_x = -math.sin(pitch)
        g_y = math.sin(roll) * math.cos(pitch)
        g_z = math.cos(roll) * math.cos(pitch)

        accel_mps2 = np.array(data["accel"]) * 9.8065
        lin_accel = accel_mps2 - np.array([g_x, g_y, g_z]) * 9.8065
        lin_accel_hp = self.hp_filter.apply(lin_accel)
        return lin_accel_hp, roll, pitch, yaw

    def get_data(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            ts = data["timestamp"]

            if self.last_ts is None:
                dt = self.poll_interval / 1000.0
            else:
                dt = (ts - self.last_ts) / 1e6
            self.last_ts = ts

            lin_accel, roll, pitch, yaw = self._get_lin_accel(data)
            self.tracker.update(lin_accel, dt)

            return {
                "timestamp": ts / 1e6,
                "roll": math.degrees(roll),
                "pitch": math.degrees(pitch),
                "yaw": math.degrees(yaw),
                "velocity": self.tracker.velocity.copy().tolist(),
                "position": self.tracker.position.copy().tolist(),
                "lin_accel": lin_accel.tolist()
            }
        return None

if __name__ == "__main__":
    try:
        imu = IMU()
        print("Tracking started. Press Ctrl+C to stop.")

        # Lists to store x, y positions and timestamps
        x_vals = []
        y_vals = []
        time_vals = []
        start_time = time.time()

        #creat a tcp here 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target = "10.186.9.83"
        port = 5005
        s.connect((target, port))
        while True:
            data = imu.get_data()
            if data:
                # Send data over TCP
                s.sendall(f"{data['position'][0]:.3f},{data['position'][1]:.3f}\n".encode())
                x_vals.append(data["position"][0])
                y_vals.append(data["position"][1])
                print("linear acceleration (m/s²): "
                      f"X={data['lin_accel'][0]:.3f}, "
                      f"Y={data['lin_accel'][1]:.3f}, Z={data['lin_accel'][2]:.3f}")
                time_vals.append(time.time() - start_time)
            time.sleep(imu.poll_interval / 1000.0)

    except KeyboardInterrupt:
        print("\nTracking stopped. Plotting trajectory and saving image...")
        plt.figure()
        cmap = get_cmap("viridis")
        norm_times = [(t % 10) / 10.0 for t in time_vals]  # normalize to [0,1] within 10s cycle

        for i in range(1, len(x_vals)):
            plt.plot(x_vals[i-1:i+1], y_vals[i-1:i+1], color=cmap(norm_times[i]))

        plt.xlim(-1, 1)
        plt.ylim(-1, 1)
        plt.xlabel('X Position (m)')
        plt.ylabel('Y Position (m)')
        plt.title('IMU Trajectory (X vs Y)')
        plt.grid(True)
        plt.savefig("imu_trajectory.png")
        plt.show()
