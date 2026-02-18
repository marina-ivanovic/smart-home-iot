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
        import RPi.GPIO as GPIO
        trig = settings['pin_trig']
        echo = settings['pin_echo']
        
        GPIO.setup(trig, GPIO.OUT)
        GPIO.setup(echo, GPIO.IN)
        
        def measure_distance():
            while not stop_event.is_set():
                GPIO.output(trig, False)
                time.sleep(0.2)
                
                GPIO.output(trig, True)
                time.sleep(0.00001)
                GPIO.output(trig, False)
                
                pulse_start = time.time()
                pulse_end = time.time()
                
                timeout = time.time() + 0.1
                while GPIO.input(echo) == 0:
                    pulse_start = time.time()
                    if time.time() > timeout: break

                while GPIO.input(echo) == 1:
                    pulse_end = time.time()
                    if time.time() > timeout: break

                pulse_duration = pulse_end - pulse_start
                distance = pulse_duration * 17150
                distance = round(distance, 2)
                
                if distance > 0 and distance < 400:
                    uds_callback(distance, name, publish_event, settings)
                    
                time.sleep(1)

        uds_thread = threading.Thread(target=measure_distance)
        uds_thread.start()
        threads.append(uds_thread)