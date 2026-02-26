from simulators.ds import run_door_sensor_simulator
import threading
import time
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

def ds_callback(value, name, publish_event, settings):
    global publish_data_counter, publish_data_limit

    payload = {
        "measurement": "ButtonPress",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": bool(value)
    }

    with counter_lock:
        batch.append(('ButtonPress', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()
    
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Button Pressed: {bool(value)}")

def run_ds(settings, threads, stop_event, name):
    if settings['simulated']:
        ds_thread = threading.Thread(target=run_door_sensor_simulator, args=(2, ds_callback, stop_event, name, publish_event, settings))
        ds_thread.start()
        threads.append(ds_thread)
    else:
        import RPi.GPIO as GPIO  # type: ignore
        pin = settings['pin']
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        def real_callback(channel):
            state = 1 if GPIO.input(pin) == 0 else 0 # 1=Pressed/Closed, 0=Open
            ds_callback(state, name, publish_event, settings)

        GPIO.add_event_detect(pin, GPIO.BOTH, callback=real_callback, bouncetime=300)