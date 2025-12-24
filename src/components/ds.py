from simulators.ds import run_door_sensor_simulator
import threading
import time

def ds_callback(value, name):
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Button Pressed")

def run_ds(settings, threads, stop_event, name):
    if settings['simulated']:
        ds_thread = threading.Thread(target=run_door_sensor_simulator, args=(2, ds_callback, stop_event, name))
        ds_thread.start()
        threads.append(ds_thread)
    else:
        # todo
        pass