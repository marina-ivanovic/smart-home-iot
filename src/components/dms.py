import json
from simulators.dms import run_dms_simulator
import threading
import time
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT

typed_code = ""
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

def dms_callback(key, name, publish_event, settings):
    global publish_data_counter, publish_data_limit, typed_code

    if key == "#":
        payload = {
            "measurement": "Key",
            "simulated": settings['simulated'],
            "runs_on": settings["runs_on"],
            "name": settings["name"],
            "value": typed_code
        }

        with counter_lock:
            batch.append(('Key', json.dumps(payload), 0, True))
            publish_data_counter += 1

            if publish_data_counter >= publish_data_limit:
                publish_event.set()

        typed_code = ""
    else:
        typed_code += key

    

    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Key Pressed: {key}")

def run_dms(settings, threads, stop_event, name):
    if settings['simulated']:
        dms_thread = threading.Thread(target=run_dms_simulator, args=(4, dms_callback, stop_event, name, publish_event, settings))
        dms_thread.start()
        threads.append(dms_thread)
    else:
        import RPi.GPIO as GPIO # type: ignore
        import time

        R1 = settings["R1"]
        R2 = settings["R2"]
        R3 = settings["R3"]
        R4 = settings["R4"]

        C1 = settings["C1"]
        C2 = settings["C2"]
        C3 = settings["C3"]
        C4 = settings["C4"]

        # Initialize the GPIO pins

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(R1, GPIO.OUT)
        GPIO.setup(R2, GPIO.OUT)
        GPIO.setup(R3, GPIO.OUT)
        GPIO.setup(R4, GPIO.OUT)

        # Make sure to configure the input pins to use the internal pull-down resistors

        GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        def readLine(line, characters):
            GPIO.output(line, GPIO.HIGH)
            if(GPIO.input(C1) == 1):
                dms_callback(characters[0], name, publish_event, settings)
            if(GPIO.input(C2) == 1):
                dms_callback(characters[1], name, publish_event, settings)
            if(GPIO.input(C3) == 1):
                dms_callback(characters[2], name, publish_event, settings)
            if(GPIO.input(C4) == 1):
                dms_callback(characters[3], name, publish_event, settings)
            GPIO.output(line, GPIO.LOW)

        def detect_character():
            while not stop_event.is_set():
            # call the readLine function for each row of the keypad
                readLine(R1, ["1","2","3","A"])
                readLine(R2, ["4","5","6","B"])
                readLine(R3, ["7","8","9","C"])
                readLine(R4, ["*","0","#","D"])
                time.sleep(0.2)

        dms_thread = threading.Thread(target=detect_character)
        dms_thread.start()
        threads.append(dms_thread)