import json
from simulators.dms import run_dms_simulator
import threading
import time
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT

batch = []
publish_data_counter = 0
publish_data_limit = 5 # Change the batch size as needed
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
        print(f'published {publish_data_limit} DMS values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, batch,))
publisher_thread.daemon = True
publisher_thread.start()

def dms_callback(key, name, publish_event, settings):
    global publish_data_counter, publish_data_limit

    payload = {
        "measurement": "Key",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": key
    }

    with counter_lock:
        batch.append(('Key', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()

    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Key Pressed: {key}")

def run_dms(settings, threads, stop_event, name):
    if settings['simulated']:
        dms_thread = threading.Thread(target=run_dms_simulator, args=(4, dms_callback, stop_event, name, publish_event, settings))
        dms_thread.start()
        threads.append(dms_thread)
    else:
        # import RPi.GPIO as GPIO
        pass