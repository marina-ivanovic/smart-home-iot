import RPi.GPIO as GPIO # type: ignore
from time import sleep
import threading
import json
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT

#disable warnings (optional)
GPIO.setwarnings(False)

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

def rgb_callback(value, name, publish_event, settings):
    global publish_data_counter, publish_data_limit

    payload = {
        "measurement": "RgbLightValue",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    with counter_lock:
        batch.append(('RgbLightValue', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()



def actuate_rgb(value, settings, threads, stop_event, name):
    if settings['simulated']:
        pass # TODO: add simulator for rgb
    else:
        GPIO.setmode(GPIO.BCM)

        RED_PIN = settings['red_pin']
        GREEN_PIN = settings['green_pin']
        BLUE_PIN = settings['blue_pin']

        #set pins as outputs
        GPIO.setup(RED_PIN, GPIO.OUT)
        GPIO.setup(GREEN_PIN, GPIO.OUT)
        GPIO.setup(BLUE_PIN, GPIO.OUT)

        def turnOff():
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)
            
        def white():
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
            
        def red():
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)

        def green():
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.LOW)
            
        def blue():
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
            
        def yellow():
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.LOW)
            
        def purple():
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
            
        def lightBlue():
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
            
        if value == 1:
            white()
            color = "White"
        elif value == 2:
            red()
            color = "Red"
        elif value == 3:
            green()
            color = "Green"
        elif value == 4:
            blue()
            color = "Blue"
        elif value == 5:
            yellow()
            color = "Yellow"
        elif value == 6:
            purple()
            color = "Purple"
        elif value == 7:
            lightBlue()
            color = "Light Blue"
        elif value == 8:
            turnOff()
            color = "Off"
        
        rgb_callback(color, settings["name"], publish_event, settings)
