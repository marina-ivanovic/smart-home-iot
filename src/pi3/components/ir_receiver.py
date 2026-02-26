#-----------------------------------------#
# Name - IR-Finalized.py
# Description - The finalized code to read data from an IR sensor and then reference it with stored values
# Author - Lime Parallelogram
# License - Completely Free
# Date - 12/09/2019
#------------------------------------------------------------#
# Imports modules

from datetime import datetime
import time
import threading
import json
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT
from simulators.ir import run_ir_simulator

batch = []
publish_data_counter = 0
publish_data_limit = 1
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
        print(f'published {publish_data_limit} DHT values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, batch,))
publisher_thread.daemon = True
publisher_thread.start()

def ir_callback(value, name, publish_event, settings):
    global publish_data_counter, publish_data_limit
    
    payload = {
        "measurement": "IrButtonPressed",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }
    
    with counter_lock:
        batch.append(('IrButtonPressed', json.dumps(payload), 0, True))
        publish_data_counter += 1
        if publish_data_counter >= publish_data_limit:
            publish_event.set()

    print(f"{name} | Pressed {value}" )


# Static program vars
def run_ir(settings, threads, stop_event, name):
    if settings['simulated']:
        ir_thread = threading.Thread(target=run_ir_simulator, args=(3, ir_callback, stop_event, name, publish_event, settings))
        ir_thread.start()
        threads.append(ir_thread)
    else:
        def run_code(stop_event, settings, publish_event):
            import RPi.GPIO as GPIO # type: ignore
            pin = settings['pin']
            Buttons = [0x300ff22dd, 0x300ffc23d, 0x300ff629d, 0x300ffa857, 0x300ff9867, 0x300ffb04f, 0x300ff6897, 0x300ff02fd, 0x300ff30cf, 0x300ff18e7, 0x300ff7a85, 0x300ff10ef, 0x300ff38c7, 0x300ff5aa5, 0x300ff42bd, 0x300ff4ab5, 0x300ff52ad]  # HEX code list
            ButtonsNames = ["LEFT",   "RIGHT",      "UP",       "DOWN",       "2",          "3",          "1",        "OK",        "4",         "5",         "6",         "7",         "8",          "9",        "*",         "0",        "#"]  # String list in same order as HEX list

            # Sets up GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN)

            # Gets binary value


            def getBinary():
                # Internal vars
                num1s = 0  # Number of consecutive 1s read
                binary = 1  # The binary value
                command = []  # The list to store pulse times in
                previousValue = 0  # The last value
                value = GPIO.input(pin)  # The current value

                # Waits for the sensor to pull pin low
                while value:
                    time.sleep(0.0001) # This sleep decreases CPU utilization immensely
                    value = GPIO.input(pin)
                    
                # Records start time
                startTime = datetime.now()
                
                while True:
                    # If change detected in value
                    if previousValue != value:
                        now = datetime.now()
                        pulseTime = now - startTime #Calculate the time of pulse
                        startTime = now #Reset start time
                        command.append((previousValue, pulseTime.microseconds)) #Store recorded data
                        
                    # Updates consecutive 1s variable
                    if value:
                        num1s += 1
                    else:
                        num1s = 0
                    
                    # Breaks program when the amount of 1s surpasses 10000
                    if num1s > 10000:
                        break
                        
                    # Re-reads pin
                    previousValue = value
                    value = GPIO.input(pin)
                    
                # Converts times to binary
                for (typ, tme) in command:
                    if typ == 1: #If looking at rest period
                        if tme > 1000: #If pulse greater than 1000us
                            binary = binary *10 +1 #Must be 1
                        else:
                            binary *= 10 #Must be 0
                        
                if len(str(binary)) > 34: #Sometimes, there is some stray characters
                    binary = int(str(binary)[:34])
                    
                return binary
                
            # Convert value to hex
            def convertHex(binaryValue):
                tmpB2 = int(str(binaryValue),2) #Temporarely propper base 2
                return hex(tmpB2)
                
            # TODO: add data sending to RGB
            while not stop_event.is_set():
                inData = convertHex(getBinary()) #Runs subs to get incoming hex value
                for button in range(len(Buttons)):#Runs through every value in list
                    if hex(Buttons[button]) == inData: #Checks this against incoming
                        print(ButtonsNames[button]) #Prints corresponding english name for button
                        ir_callback(ButtonsNames[button], settings['name'], publish_event, settings)
        ir_thread = threading.Thread(target=run_code, args=(stop_event, settings, publish_event,))
        ir_thread.start()
        threads.append(ir_thread)
