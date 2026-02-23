from simulators.pir import run_pir_simulator
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

def pir_callback(name, publish_event, settings):
    global publish_data_counter, publish_data_limit

    payload = {
        "measurement": "MotionDetected",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": True
    }

    with counter_lock:
        batch.append(('MotionDetected', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Motion Detected!")

def run_pir(settings, threads, stop_event, name):
    if settings['simulated']:
        pir_thread = threading.Thread(target=run_pir_simulator, args=(3, pir_callback, stop_event, name, publish_event, settings))
        pir_thread.start()
        threads.append(pir_thread)
    else:
        import RPi.GPIO as GPIO # type: ignore
        PIR_PIN = settings['pin']
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)

        def motion_detected(channel):
            print("You moved")
            pir_callback(name, publish_event, settings)

        #def no_motion(channel):
            # print("You stopped moving")
            #pir_callback(False, name, publish_event, settings)
            
        GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=motion_detected)
        #GPIO.add_event_detect(PIR_PIN, GPIO.FALLING, callback=no_motion)