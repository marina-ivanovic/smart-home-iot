from simulators.uds import run_uds_simulator
import threading
import time
import json
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

def uds_callback(distance, name, publish_event, settings):
    global publish_data_counter, publish_data_limit

    payload = {
        "measurement": "Distance",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": distance
    }

    with counter_lock:
        batch.append(('Distance', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()

    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Distance: {distance}cm")

def run_uds(settings, threads, stop_event, name):
    if settings['simulated']:
        uds_thread = threading.Thread(target=run_uds_simulator, args=(2, uds_callback, stop_event, name, publish_event, settings))
        uds_thread.start()
        threads.append(uds_thread)
    else:
        # todo
        pass