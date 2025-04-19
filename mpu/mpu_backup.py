import RTIMU
import time
import os
import math

SETTINGS_FILE = "RTIMULib"

print("Using settings file:", SETTINGS_FILE + ".ini")
settings = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(settings)

print("IMU Name:", imu.IMUName())

if not imu.IMUInit():
    print("IMU Init Failed")
    exit(1)
else:
    print("IMU Init Succeeded")

imu.setSlerpPower(0.02)
imu.setGyroEnable(True)
imu.setAccelEnable(True)
imu.setCompassEnable(False)  # MPU6050 has no magnetometer

poll_interval = imu.IMUGetPollInterval()
print("Recommended Poll Interval:", poll_interval, "ms")


samples = []
while True: 
    if imu.IMURead(): 
        data = imu.getIMUData()
        accel = data["accel"]
        samples.append(accel)
        if len(samples) > 100:
            break
    time.sleep(poll_interval * 1.0 / 1000.0)
print("Samples collected:", len(samples))
ax = sum(s[0] for s in samples) / len(samples)
ay = sum(s[1] for s in samples) / len(samples)
az = sum(s[2] for s in samples) / len(samples)
roll0 = math.atan2(ay, az)
pitch0 = math.atan2(-ax, az)
print("Initial angles: Roll=%.2f, Pitch=%.2f" % (roll0 * 57.2958, pitch0 * 57.2958))

while True:
    if imu.IMURead():
        data = imu.getIMUData()
        fusionPose = data["fusionPose"]
        roll = fusionPose[0]
        pitch = fusionPose[1]
        yaw = fusionPose[2]
        # current_roll = roll - roll0
        # current_pitch = pitch - pitch0
        # current_yaw = yaw -  yaw0
        print("*" * 20)
        print("Roll: %.2f, Pitch: %.2f, Yaw: %.2f" % (roll * 57.2958, pitch * 57.2958, yaw * 57.2958))
        accel = data["accel"]
        g_x = -math.sin(pitch)
        g_y = math.sin(roll) * math.cos(pitch)
        g_z = math.cos(roll) * math.cos(pitch)

        print("Accel (G): X=%.3f, Y=%.3f, Z=%.3f" % (accel[0], accel[1], accel[2]))
        print("G: X=%.3f, Y=%.3f, Z=%.3f" % (g_x, g_y, g_z))
        lin_accel = [
            accel[0] - g_x,
            accel[1] - g_y,
            accel[2] - g_z,
        ]
        # Convert from Gs to m/s²
        
        # gravity = [g_x * 9.80665, g_y * 9.80665, g_z * 9.80665]
        # accel_ms2 = [x * 9.80665 for x in accel]
        # print("gravity m/s²: X=%.3f, Y=%.3f, Z=%.3f" % (gravity[0], gravity[1], gravity[2]))
        # print("accel m/s²: X=%.3f, Y=%.3f, Z=%.3f" % (accel_ms2[0], accel_ms2[1], accel_ms2[2]))
        # lin_accel = [
        #     accel_ms2[0] - gravity[0],
        #     accel_ms2[1] - gravity[1],
        #     accel_ms2[2] - gravity[2],
        # ]
        print("Accel : X=%.3f, Y=%.3f, Z=%.3f" % (lin_accel[0], lin_accel[1], lin_accel[2]))
        print("*" * 20 + "\n")
    time.sleep(poll_interval * 1.0 / 1000.0)
