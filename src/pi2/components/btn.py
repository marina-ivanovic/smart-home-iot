from simulators.ds import run_door_sensor_simulator
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

def ds_callback(value, name, publish_event, settings):
    global publish_data_counter, publish_data_limit

    payload = {
        "measurement": "ButtonPress",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    with counter_lock:
        batch.append(('ButtonPress', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()
    
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Button Pressed")

def run_ds(settings, threads, stop_event, name, timer_callback=None):
    if settings['simulated']:
        ds_thread = threading.Thread(target=run_door_sensor_simulator, args=(2, ds_callback, stop_event, name, publish_event, settings, timer_callback))
        ds_thread.start()
        threads.append(ds_thread)
    else:
        import RPi.GPIO as GPIO
        pin = settings['pin']
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        def real_callback(channel):
            if GPIO.input(pin) == 0:
                ds_callback(1, name, publish_event, settings)
                
        # Add interrupt
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=real_callback, bouncetime=300)