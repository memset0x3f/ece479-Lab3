import numpy as np
import RTIMU
import time
import math
try:
    import config
except ImportError:
    print("In testing mpu mode, don't need config.py")
    
import smbus 
from collections import deque
from scipy.signal import butter, filtfilt, windows
from scipy.fft import rfft, rfftfreq
try: 
    from button import ButtonDetector
except ImportError:
    print("In testing mpu mode, don't need button.py")
    pass

bus = smbus.SMBus(1)
MUX_ADDR = 0x70
NUM_SENSORS = 3
SETTINGS_FILE_0 = "RTIMULib_0"
SETTINGS_FILE_1 = "RTIMULib_1"
SETTINGS_FILE_2 = "RTIMULib_2"

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
        # print(self.position)
    
    def update_position_by_tilt(self, tilt, dt, sensitivity=0.01):
        """
        Update the position based on the tilt (roll, pitch).
        The more tilt, the faster the position moves.
        """
        #the roll, pitch are in degrees
        roll, pitch, yaw = tilt  # Only consider roll and pitch
        tilt_magnitude = math.sqrt(roll**2 + pitch**2)  # Calculate tilt magnitude
        threshold = 30  # degrees
        if tilt_magnitude < threshold:
            return  # Ignore small tilts

        self.position[0] += pitch * sensitivity * dt
        self.position[1] += -yaw * sensitivity * dt
        # Clip the position to avoid excessive drift
        self.position = np.clip(self.position, -self.position_clip, self.position_clip)


    def update_attitude(self, gyro, dt):
        
        self.attitude += gyro * dt
        self.attitude = np.clip(self.attitude, -np.pi/3, np.pi/3)


class TapDetector:
    def __init__(self,
                 fs=250,
                 window_size=64,
                 overlap=0.9,
                 lowcut=5,
                 highcut=40,
                 energy_band=(10, 40),
                 energy_threshold=1,
                 peak_threshold=0.2,
                 double_window_ms=200):
        self.fs = fs
        self.window_size = window_size
        self.step = int(window_size * (1 - overlap))
        self.energy_band = energy_band
        self.energy_threshold = energy_threshold
        self.peak_threshold = peak_threshold
        self.double_window_samples = int(double_window_ms * fs / 1000)
        self.refractory = window_size

        nyq = 0.5 * fs
        b, a = butter(4, [lowcut/nyq, highcut/nyq], btype='band')
        
        self.b, self.a = b, a

    
        self.win = windows.hamming(window_size)

        self.buf = deque(maxlen=window_size)
        self.sample_idx = 0
        self.last_tap_idx = -self.refractory
        self.prev_tap_idx = None

    def feed(self, accel_sample):
        startT = time.time()
        mag = np.linalg.norm(accel_sample)
        
        self.buf.append(mag)

        event = None
        if len(self.buf) == self.window_size and \
           (self.sample_idx + 1 - self.window_size) % self.step == 0:
            # exit()
            print("entered")
            seg = np.array(self.buf)
            seg_filt = filtfilt(self.b, self.a, seg)
            seg_win = seg_filt * self.win
            fft_vals = np.abs(rfft(seg_win))
            freqs = rfftfreq(self.window_size, 1/self.fs)

            mask = (freqs >= self.energy_band[0]) & (freqs <= self.energy_band[1])
            energy = np.sum(fft_vals[mask]**2)
            peak = seg_win.max()
            print("peak", peak)
            print("energy", energy)
            if (energy > self.energy_threshold * np.mean(fft_vals) and
                peak > self.peak_threshold and
                self.sample_idx - self.last_tap_idx > self.refractory):
                tap_idx = self.sample_idx - self.window_size + 1

                if (self.prev_tap_idx is not None and
                    tap_idx - self.prev_tap_idx <= self.double_window_samples):
                    event = ("double", tap_idx)
                    self.prev_tap_idx = None
                else:
                    event = ("single", tap_idx)
                    self.prev_tap_idx = tap_idx
                    # print(self.buf)
                self.last_tap_idx = self.sample_idx
        self.sample_idx += 1
        endT = time.time()
        # print("Time taken: ", endT - startT)
        return event

class IMU:
    def __init__(self, channel, setting_file ,slerp_power=0.02, tap_params=None, enable_tap_detector = True, enable_tracker=True):
        # print("IMU init")
        # print("Channel: ", channel)
        if self._select_channel(channel):
            # print("Channel selected: ", channel)
            self.channel = channel
            self.SETTINGS_FILE = setting_file
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
            self.tap_detector = TapDetector(**(tap_params or {}))
            self.name = f"IMU_{channel}"
            self.enable_tap_detector = enable_tap_detector
            self.enable_tracker = enable_tracker
        else: 
            print("Failed to select channel", self.channel)
        
    
    def _select_channel(self, channel):
        try: 
            bus.write_byte(MUX_ADDR, 1 << channel)
            return True
        except IOError:
            print(f"Failed to select channel {channel}")
            return False

    # def _get_lin_accel(self, data):
    #     fusionPose = data["fusionPose"]
    #     roll, pitch, _ = fusionPose

    #     g_x = -math.sin(pitch)
    #     g_y = math.sin(roll) * math.cos(pitch)
    #     g_z = math.cos(roll) * math.cos(pitch)

    #     accel_mps2 = np.array(data["accel"]) * 9.8065
    #     return accel_mps2 - np.array([g_x, g_y, g_z]) * 9.8065

    def get_data(self):
        
        startT = time.time()
        if self._select_channel(self.channel):
            # start_imu_readT = time.time()
            # temp = self.imu.IMURead()
            # end_imu_readT = time.time()
            # print("IMU read time: ", end_imu_readT - start_imu_readT)
            tmp = self.imu.IMURead()
            endT = time.time()
            # print(f"{self.name} Time take for event: ", endT - startT)
            if tmp:
                data = self.imu.getIMUData()
                ts = data["timestamp"]

                if self.last_ts is None:
                    dt = self.poll_interval / 1000.0
                else:
                    dt = (ts - self.last_ts) / 1e6
                self.last_ts = ts

                # lin_accel = self._get_lin_accel(data)
                lin_accel = np.array(data["accel"])
                
                # startT = time.time()
                if self.enable_tap_detector:
                    # start_solve_t = time.time()
                    event = self.tap_detector.feed(np.array(lin_accel))
                    # end_solve_t = time.time()
                    # print(f"{self.name}: Tap detection time: ", end_solve_t - start_solve_t)
                else: 
                    event = None
                # self.tracker.update(lin_accel, dt)
                # print(f"{self.name}: rate:", dt)
                if self.name == "IMU_2":
                    print(f"{self.name}: attitude: ", self.tracker.get_attitude_in_degrees())


                if not self.enable_tracker:
                    return {
                        "timestamp": ts,
                        "lin_accel": lin_accel.tolist(),
                        "velocity": self.tracker.velocity.copy().tolist(),
                        "position": self.tracker.position.copy().tolist(),
                        "attitude": self.tracker.get_attitude_in_degrees().copy().tolist(),
                        "gyro": np.array(data["gyro"]).tolist(),
                        "event": event, 
                    }

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
                    "gyro": gyro.tolist(),
                    "event": event, 
                }
            else: 
                print("IMU read failed")
                return None
        else: 
            print("Failed to select channel", self.channel)
            return None
        
        
    # def read_data(self):
    #     if self._select_channel(self.channel):
    #         if self.imu.IMURead():
    #             data = self.imu.getIMUData()
    #             ts = data["timestamp"]
    #             if self.last_ts is None:
    #                 dt = self.poll_interval / 1000.0
    #             else:
    #                 dt = (ts - self.last_ts) / 1e6
    #             self.last_ts = ts 
                
                
    #         else: 
    #             print("IMU read failed")
    #             return None
    #     else: 
    #         print("Failed to select channel", self.channel)
    #         return None
        
        

class ControllerData:
    def __init__(self):
        self.indexFinger = IMU(channel=0, setting_file=SETTINGS_FILE_0, enable_tracker=False) 
        self.middleFinger = IMU(channel=1, setting_file=SETTINGS_FILE_1, enable_tracker=False)
        self.hand = IMU(channel=2, setting_file=SETTINGS_FILE_2, enable_tap_detector=False)
        # print(self.indexFinger.tap_detector)
        self.poll_interval = self.indexFinger.poll_interval
        try:
            self.button_detector = ButtonDetector(config.BUTTONS_ADDR)
        except:
            print("In testing mpu mode, don't need button.py")
            self.button_detector = None
        print(self.indexFinger.get_data())
        print("init done")
        
    def get_data(self):
        # print(self.indexFinger.name)
        left_data = self.indexFinger.get_data()
        right_data = self.middleFinger.get_data()
        hand_data = self.hand.get_data()
        try:
            button_data = self.button_detector.detectAll()
        except:
            # print("In testing mpu mode, don't need button.py")
            button_data = None
        data = {
            "leftEvent": None, 
            "rightEvent": None, 
            "position": None, 
            "buttons": None,
            "attitude": None
        }
        if left_data != None: 
            data["leftEvent"] = left_data["event"]
        if right_data != None: 
            data["rightEvent"] = right_data["event"]
        if hand_data != None:
            data["position"] = hand_data["position"]
            data["attitude"] = hand_data["attitude"]
        if button_data != None:
            data["buttons"] = button_data
        return data
        


if __name__ == "__main__":
    data_stream = ControllerData()
    while True: 
        data = data_stream.get_data()
        if data:
            pass
            # print("Data: ", data)
        else:
            pass
            # print("No data")
        if data["leftEvent"] != None:
            # print("Left event: ", data["leftEvent"])
            exit()
        if data["rightEvent"] != None:
            # print("Right event: ", data["rightEvent"])
            exit()
        # print(data_stream.poll_interval / 1000)
        # print("Time interval: ", data_stream.poll_interval / 1000.0)
        time.sleep(1 / 1000.0)
    
    # imu0 = IMU(channel=0, setting_file=SETTINGS_FILE_0)
    # while True:
    #     print(imu0.get_data())
    #     print(imu0.get_data())
    # imu1 = IMU(channel=1, setting_file=SETTINGS_FILE_1)
    # while True:
    #     print(imu1.get_data())
    #     print(imu1.get_data())
    # imu2 = IMU(channel=2, setting_file=SETTINGS_FILE_2)
    # while True:
    #     print(imu2.get_data())
    #     print(imu2.get_data())
    
    # try:
    #     imu0 = IMU(channel=0, setting_file=SETTINGS_FILE_0)
    #     imu1 = IMU(channel=1, setting_file=SETTINGS_FILE_1)
    #     imu2 = IMU(channel=2, setting_file=SETTINGS_FILE_2)
    #     print("Tracking started. Press Ctrl+C to stop.")
    #     imus = [imu0, imu1, imu2]
    #     ccnt = 0
    #     while True:
    #         cnt = 0
    #         for imu in imus:
                
    #             if cnt != 0:
                    
    #                 cnt+= 1
    #                 continue
    #             else: 
    #                 print(f"CHANNEL_{cnt}_" )
    #                 cnt += 1
    #             data = imu.get_data()
    #             if data:
    #                 print(f"\nPosition (m): X={data['position'][0]:.3f}, "
    #                     f"Y={data['position'][1]:.3f}, Z={data['position'][2]:.3f}")
    #                 print(f"Velocity (m/s): X={data['velocity'][0]:.3f}, "
    #                     f"Y={data['velocity'][1]:.3f}, Z={data['velocity'][2]:.3f}")
    #                 print("Linear Acceleration (m/s²): "
    #                     f"X={data['lin_accel'][0]:.3f}, "
    #                     f"Y={data['lin_accel'][1]:.3f}, Z={data['lin_accel'][2]:.3f}")
    #                 print(f"Attitude (rad): Roll={data['attitude'][0]:.3f}, "
    #                         f"Pitch={data['attitude'][1]:.3f}, Yaw={data['attitude'][2]:.3f}")
    #                 print(f"event:", {data["event"]})
    #                 if data["event"]:
    #                     ccnt += 1
    #                     if ccnt > 1:
    #                         print("ccnt", ccnt)
    #                         exit()
    #                     # exit()
    #                 print("time interval: ", imu.poll_interval / 1000.0)
    #                 time.sleep(imu.poll_interval / 1000.0)
    #             else: 
    #                 print("Channel ", cnt, "NO data")

    # except KeyboardInterrupt:
    #     print("\nTracking stopped.")
