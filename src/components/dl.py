from actuators.dl import actuate_dl
import time
import threading
import json
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT

batch = []
publish_data_counter = 0
publish_data_limit = 1 # Change the batch size as needed
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

def run_dl(settings, on):
    global publish_data_counter, publish_data_limit
    if settings['simulated']:
        actuate_dl(on)
    else:
        import RPi.GPIO as GPIO
        GPIO.output(settings['pin'], GPIO.HIGH if on else GPIO.LOW)
        print(f"Real DL toggled: {on}")

    payload = {
        "measurement": "LightOn",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": on
    }

    with counter_lock:
        batch.append(('LightOn', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()