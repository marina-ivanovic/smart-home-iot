from simulators.gyro import run_gyro_simulator
import threading
import time
import json
import math
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT

batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = batch.copy()
            publish_data_counter = 0
            batch.clear()
        publish.multiple(local_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} GSG values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, batch,))
publisher_thread.daemon = True
publisher_thread.start()

def detect_significant_movement(accel, gyro, threshold_accel=2.0, threshold_gyro=50.0):
    """Detect if movement is significant enough to trigger alarm."""
    accel_magnitude = math.sqrt(accel[0]**2 + accel[1]**2 + accel[2]**2)
    gyro_magnitude = math.sqrt(gyro[0]**2 + gyro[1]**2 + gyro[2]**2)
    return accel_magnitude > threshold_accel or gyro_magnitude > threshold_gyro

def gsg_callback(accel_raw, gyro_raw, name, publish_event, settings):
    global publish_data_counter, publish_data_limit
    
    # Convert to g and deg/s
    accel = [a/16384.0 for a in accel_raw]
    gyro = [g/131.0 for g in gyro_raw]
    
    # Check for significant movement
    significant_movement = detect_significant_movement(accel, gyro)
    
    payload = {
        "measurement": "Gyroscope",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "accel_x": accel[0],
        "accel_y": accel[1],
        "accel_z": accel[2],
        "gyro_x": gyro[0],
        "gyro_y": gyro[1],
        "gyro_z": gyro[2],
        "significant_movement": significant_movement
    }
    
    with counter_lock:
        batch.append(('Gyroscope', json.dumps(payload), 0, True))
        publish_data_counter += 1
        if publish_data_counter >= publish_data_limit:
            publish_event.set()
    
    t = time.localtime()
    alert = " [ALARM!]" if significant_movement else ""
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} a/g: {accel[0]:.2f}g {gyro[0]:.2f}°/s{alert}")

def run_gsg(settings, threads, stop_event, name):
    if settings['simulated']:
        gsg_thread = threading.Thread(target=run_gyro_simulator, args=(1, gsg_callback, stop_event, name, publish_event, settings))
        gsg_thread.start()
        threads.append(gsg_thread)
    else:
        # Real MPU6050
        import MPU6050
        mpu = MPU6050.MPU6050()
        mpu.dmp_initialize()
        
        def read_gsg_real():
            while not stop_event.is_set():
                accel = mpu.get_acceleration()
                gyro = mpu.get_rotation()
                gsg_callback(accel, gyro, name, publish_event, settings)
                time.sleep(0.2)
        
        gsg_thread = threading.Thread(target=read_gsg_real)
        gsg_thread.start()
        threads.append(gsg_thread)
