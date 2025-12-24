from simulators.pir import run_pir_simulator
import threading
import time

def pir_callback(name):
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Motion Detected!")

def run_pir(settings, threads, stop_event, name):
    if settings['simulated']:
        pir_thread = threading.Thread(target=run_pir_simulator, args=(3, pir_callback, stop_event, name))
        pir_thread.start()
        threads.append(pir_thread)
    else:
        # todo
        pass