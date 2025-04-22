import numpy as np
import RTIMU
import time
import math
import config

class VelocityPositionTracker:
    """Velocity and position tracker with drift compensation."""
    def __init__(self):
        self.velocity = np.zeros(3)  # [vx, vy, vz] in m/s
        self.position = np.zeros(3)  # [x, y, z] in meters
        self.last_accel = np.zeros(3)
        self.attitude = np.zeros(3)  # [roll, pitch, yaw] in radians

        # Compensation parameters
        self.velocity_decay = 0.8
        self.position_clip = 1
        self.zero_threshold = 0.05
        self.rad2degree = 57.2958
    
    def get_attitude_in_degrees(self):
        return self.attitude * self.rad2degree
    

    def update(self, accel, dt):
        if np.linalg.norm(accel) < self.zero_threshold:
            self.velocity *= 0.5
        else:
            avg_accel = 0.5 * (self.last_accel + accel)
            self.velocity += avg_accel * dt
            self.last_accel = accel.copy()

        self.position += self.velocity * dt
        self.velocity *= self.velocity_decay
        self.position = np.clip(self.position, -self.position_clip, self.position_clip)
    
    def update_position_by_tilt(self, tilt, dt, sensitivity=0.01):
        """
        Update the position based on the tilt (roll, pitch).
        The more tilt, the faster the position moves.
        """
        #the roll, pitch are in degrees
        roll, pitch = tilt[:2]  # Only consider roll and pitch
        tilt_magnitude = math.sqrt(roll**2 + pitch**2)  # Calculate tilt magnitude
        threshold = 30  # degrees
        if tilt_magnitude < threshold:
            return  # Ignore small tilts

        self.position[0] += roll * sensitivity * dt
        self.position[1] += pitch * sensitivity * dt
        # Clip the position to avoid excessive drift
        self.position = np.clip(self.position, -self.position_clip, self.position_clip)


    def update_attitude(self, gyro, dt):
        self.attitude += gyro * dt
        self.attitude = np.clip(self.attitude, -np.pi, np.pi)
        

class IMU:
    def __init__(self, slerp_power=0.02):
        self.SETTINGS_FILE = config.SETTINGS_FILE
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

    def _get_lin_accel(self, data):
        fusionPose = data["fusionPose"]
        roll, pitch, _ = fusionPose

        g_x = -math.sin(pitch)
        g_y = math.sin(roll) * math.cos(pitch)
        g_z = math.cos(roll) * math.cos(pitch)

        accel_mps2 = np.array(data["accel"]) * 9.8065
        return accel_mps2 - np.array([g_x, g_y, g_z]) * 9.8065

    def get_data(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            ts = data["timestamp"]

            if self.last_ts is None:
                dt = self.poll_interval / 1000.0
            else:
                dt = (ts - self.last_ts) / 1e6
            self.last_ts = ts

            lin_accel = self._get_lin_accel(data)
            # self.tracker.update(lin_accel, dt)

            gyro = np.array(data["gyro"]) # in rad/s 
            self.tracker.update_attitude(gyro, dt)
            tilt = self.tracker.get_attitude_in_degrees()
            self.tracker.update_position_by_tilt(tilt, dt)


            return {
                "timestamp": ts,
                "lin_accel": lin_accel.tolist(),
                "velocity": self.tracker.velocity.copy().tolist(),
                "position": self.tracker.position.copy().tolist(),
                "attitude": self.tracker.get_attitude_in_degrees().copy().tolist(),
            }
        return None

if __name__ == "__main__":
    try:
        imu = IMU()
        print("Tracking started. Press Ctrl+C to stop.")

        while True:
            data = imu.get_data()
            if data:
                print(f"\nPosition (m): X={data['position'][0]:.3f}, "
                      f"Y={data['position'][1]:.3f}, Z={data['position'][2]:.3f}")
                print(f"Velocity (m/s): X={data['velocity'][0]:.3f}, "
                      f"Y={data['velocity'][1]:.3f}, Z={data['velocity'][2]:.3f}")
                print("Linear Acceleration (m/s²): "
                      f"X={data['lin_accel'][0]:.3f}, "
                      f"Y={data['lin_accel'][1]:.3f}, Z={data['lin_accel'][2]:.3f}")
                print(f"Attitude (rad): Roll={data['attitude'][0]:.3f}, "
                        f"Pitch={data['attitude'][1]:.3f}, Yaw={data['attitude'][2]:.3f}")
                time.sleep(imu.poll_interval / 1000.0)

    except KeyboardInterrupt:
        print("\nTracking stopped.")
