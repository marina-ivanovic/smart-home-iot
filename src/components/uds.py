from simulators.uds import run_uds_simulator
import threading
import time

def uds_callback(distance, name):
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Distance: {distance}cm")

def run_uds(settings, threads, stop_event, name):
    if settings['simulated']:
        uds_thread = threading.Thread(target=run_uds_simulator, args=(2, uds_callback, stop_event, name))
        uds_thread.start()
        threads.append(uds_thread)
    else:
        # todo
        pass