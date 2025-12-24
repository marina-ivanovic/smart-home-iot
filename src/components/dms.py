from simulators.dms import run_dms_simulator
import threading
import time

def dms_callback(key, name):
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Key Pressed: {key}")

def run_dms(settings, threads, stop_event, name):
    if settings['simulated']:
        dms_thread = threading.Thread(target=run_dms_simulator, args=(4, dms_callback, stop_event, name))
        dms_thread.start()
        threads.append(dms_thread)
    else:
        # import RPi.GPIO as GPIO
        pass