import json
import threading
import paho.mqtt.client as mqtt
from components.dms import run_dms
from components.ds import run_ds
from components.pir import run_pir
from components.uds import run_uds
from settings import load_settings
from components.dl import run_dl
from components.db import run_db
from time import sleep

lights_status, buzzer_status = False, False

def dl_turn_on():
    run_dl(pi1_settings['DL'], True)
    sleep(10)
    run_dl(pi1_settings['DL'], False)
    

def on_mqtt_message(client, userdata, msg):
    global lights_status, buzzer_status

    if msg.topic == "pi1/motionDl":
        dl_thread = threading.Thread(target=dl_turn_on)
        dl_thread.start()
        threads.append(dl_thread)
    elif msg.topic == "pi1/alarm":
        payload = json.loads(msg.payload.decode())
        alarm = payload["alarm"]
        
        if alarm:
            buzzer_status = True
        else:
            buzzer_status = False
        
        run_db(pi1_settings['DB'], buzzer_status)
    else:
        payload = json.loads(msg.payload.decode())
        device = payload["device"]

        if device == "DL":
            lights_status = not lights_status
            run_dl(pi1_settings['DL'], lights_status)

        elif device == "DB":
            buzzer_status = not buzzer_status
            run_db(pi1_settings['DB'], buzzer_status)


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass

def print_menu():
    print("\n" + "="*10 + " PI1 ACTUATORS " + "="*10)
    print("1. Door Light: Toggle light")
    print("2. Door Buzzer: Toggle buzzer")
    print("X. Exit")
    print("="*26)

if __name__ == "__main__":
    print('Starting PI1 app...')
    settings = load_settings()
    pi1_settings = settings['PI1']
    threads = []
    stop_event = threading.Event()

    try:
        if 'DS1' in pi1_settings: run_ds(pi1_settings['DS1'], threads, stop_event, "DS1")
        if 'DUS1' in pi1_settings: run_uds(pi1_settings['DUS1'], threads, stop_event, "DUS1")
        if 'DPIR1' in pi1_settings: run_pir(pi1_settings['DPIR1'], threads, stop_event, "DPIR1")
        if 'DMS' in pi1_settings: run_dms(pi1_settings['DMS'], threads, stop_event, "DMS")


        mqtt_client = mqtt.Client()
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.subscribe("pi1/actuator/cmd")
        mqtt_client.subscribe("pi1/motionDl")
        mqtt_client.loop_start()
        while True:
            print_menu()
            command = input("Enter a command: ")

            if command == '1':
                lights_status = not lights_status
                run_dl(pi1_settings['DL'], lights_status)
            elif command == '2':
                buzzer_status = not buzzer_status
                run_db(pi1_settings['DB'], buzzer_status)
            elif command.lower() == 'x':
                print("Exiting...")
                stop_event.set()
                break
            else:
                print("Unknown command.")

    except KeyboardInterrupt:
        print('\nStopping app')
        stop_event.set()
        for t in threads:
            t.join()