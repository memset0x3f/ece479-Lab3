import RTIMU
import time
import json

SETTINGS_FILE = "RTIMULib_backup"
CALIBRATION_FILE = "calibration.json"

def calibrate_gyro(settings):
    """Gyroscope calibration function"""
    print("\n=== Gyroscope Calibration ===")
    print("Place the sensor horizontally and keep it stationary.")
    input("Press Enter when ready to begin sampling...")
    
    # Initialize the IMU
    imu = RTIMU.RTIMU(settings)
    if not imu.IMUInit():
        print("IMU initialization failed")
        return None
    imu.setGyroEnable(True)
    imu.setAccelEnable(False)
    imu.setCompassEnable(False)
    
    # Data collection settings
    poll_interval = imu.IMUGetPollInterval()
    sample_count = 500  # number of samples to collect
    samples = []
    
    print(f"Collecting data (approximately {sample_count * poll_interval / 1000:.1f} seconds)...")
    for _ in range(sample_count):
        if imu.IMURead():
            data = imu.getIMUData()
            gyro = data["gyro"]
            samples.append(gyro)
        time.sleep(poll_interval / 1000.0)
    
    # Calculate average bias for each axis
    bias_x = sum(s[0] for s in samples) / len(samples)
    bias_y = sum(s[1] for s in samples) / len(samples)
    bias_z = sum(s[2] for s in samples) / len(samples)
    
    calibration = {
        "GyroBiasX": bias_x,
        "GyroBiasY": bias_y,
        "GyroBiasZ": bias_z
    }
    
    print("Gyroscope calibration completed. Bias parameters calculated.\n")
    return calibration

def calibrate_accel(settings):
    """Accelerometer calibration function"""
    print("\n=== Accelerometer Calibration ===")
    print("Please place the sensor on each of its six faces as prompted.")
    
    # Initialize the IMU
    imu = RTIMU.RTIMU(settings)
    if not imu.IMUInit():
        print("IMU initialization failed")
        return None
    imu.setGyroEnable(False)
    imu.setAccelEnable(True)
    imu.setCompassEnable(False)
    
    # Structure to hold min and max values for each axis
    min_max = {
        0: {"min": float("inf"), "max": -float("inf")},  # X-axis
        1: {"min": float("inf"), "max": -float("inf")},  # Y-axis
        2: {"min": float("inf"), "max": -float("inf")},  # Z-axis
    }
    
    # Calibration positions: (axis index, sign multiplier, description)
    positions = [
        (2,  1, "Z-axis up"),
        (2, -1, "Z-axis down"),
        (1,  1, "Y-axis up"),
        (1, -1, "Y-axis down"),
        (0,  1, "X-axis up"),
        (0, -1, "X-axis down"),
    ]
    
    # Iterate through each calibration position
    for axis, sign, desc in positions:
        input(f"\nPlace the sensor with {desc}, then press Enter to start sampling...")
        
        samples = []
        for _ in range(300):  # collect 300 samples for each position
            if imu.IMURead():
                data = imu.getIMUData()
                accel = data["accel"]
                samples.append(accel)
            time.sleep(0.01)
        
        # Calculate the average value for the specified axis (accounting for sign)
        avg = sum(s[axis] * sign for s in samples) / len(samples)
        
        # Update min and max values for the current axis
        if avg > min_max[axis]["max"]:
            min_max[axis]["max"] = avg
        if avg < min_max[axis]["min"]:
            min_max[axis]["min"] = avg
    
    calibration = {}
    axes = ['X', 'Y', 'Z']
    for i in range(3):
        calibration[f"AccelMin{axes[i]}"] = min_max[i]["min"]
        calibration[f"AccelMax{axes[i]}"] = min_max[i]["max"]
    
    print("\nAccelerometer calibration completed. Parameters calculated.\n")
    return calibration

def save_calibration(calibration_data, filename=CALIBRATION_FILE):
    """Save calibration parameters to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(calibration_data, f, indent=4)
        print(f"Calibration data saved to {filename}")
    except Exception as e:
        print(f"Failed to save calibration data: {e}")

if __name__ == "__main__":
    # Load the configuration settings
    settings = RTIMU.Settings(SETTINGS_FILE)
    
    # Perform calibration processes
    calibration_data = {}
    
    gyro_calibration = calibrate_gyro(settings)
    if gyro_calibration:
        calibration_data.update(gyro_calibration)
    
    accel_calibration = calibrate_accel(settings)
    if accel_calibration:
        calibration_data.update(accel_calibration)
    
    if calibration_data:
        save_calibration(calibration_data)
        print("All calibrations completed! Please restart the main program to apply the new parameters.")
    else:
        print("Calibration failed.")
