import time
import random

def run_gyro_simulator(interval, callback, stop_event, name, publish_event, settings):
    while not stop_event.is_set():
        # Simulate raw values (16384 = 1g, 131 = 1 deg/s)
        accel_raw = [
            random.randint(-16384, 16384),
            random.randint(-16384, 16384),
            random.randint(-16384, 16384)
        ]
        gyro_raw = [
            random.randint(-131*10, 131*10),
            random.randint(-131*10, 131*10),
            random.randint(-131*10, 131*10)
        ]
        callback(accel_raw, gyro_raw, name, publish_event, settings)
        time.sleep(interval)
