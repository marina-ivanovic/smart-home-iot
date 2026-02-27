import json
import threading
import time
import paho.mqtt.client as mqtt
from pi2.components.ds2 import run_ds as run_ds2
from pi2.components.dus2 import run_uds as run_dus2
from pi2.components.pir2 import run_pir as run_pir2
from pi2.components.btn import run_ds as run_btn
from pi2.sensors.dht3 import run_dht
from pi2.sensors.gsg import run_gsg
from pi2.actuators.sd4 import actuate_4sd, blink_4sd
from settings import load_settings
from env import HOSTNAME, PORT

# Global state for timer
timer_seconds = 0
timer_running = False
add_seconds_amount = 10  # Default, can be set via Web app

def on_mqtt_message(client, userdata, msg):
    global timer_seconds, timer_running, add_seconds_amount
    
    payload = json.loads(msg.payload.decode())
    
    if msg.topic == "pi2/timer/set":
        timer_seconds = int(payload.get("value", 0)) 
        timer_running = True
        print(f"Timer set to {timer_seconds} seconds")
    
    elif msg.topic == "pi2/timer/add":
        add_seconds_amount = int(payload.get("amount", 10))
        print(f"Add seconds amount updated to {add_seconds_amount}")
    
    elif msg.topic == "pi2/display/cmd":
        # Direct display control
        display_value = payload["value"]
        actuate_4sd(pi2_settings['4SD'], display_value)

def timer_thread_func():
    global timer_seconds, timer_running
    while True:
        if timer_running and timer_seconds > 0:
            mins = timer_seconds // 60
            secs = timer_seconds % 60
            display_value = f"{mins:02d}:{secs:02d}"
            actuate_4sd(pi2_settings['4SD'], display_value)
            time.sleep(1)
            timer_seconds -= 1
        elif timer_running and timer_seconds == 0:
            # Timer expired - blink
            print("Timer expired! Blinking...")
            blink_4sd(pi2_settings['4SD'])
            timer_running = False
        else:
            time.sleep(0.5)

def btn_pressed_handler():
    """BTN adds N seconds when pressed (tacka 8b)"""
    global timer_seconds, add_seconds_amount
    if timer_running:
        timer_seconds += add_seconds_amount
        print(f"Added {add_seconds_amount} seconds. New time: {timer_seconds}s")
    else:
        # Stop blinking if timer was blinking (tacka 8c)
        print("BTN pressed - stopping blink")

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass

def print_menu():
    print("\n" + "="*10 + " PI2 CONTROLS " + "="*10)
    print("1. Test 4SD Display")
    print("2. Trigger BTN (add seconds)")
    print("X. Exit")
    print("="*26)

if __name__ == "__main__":
    print('Starting PI2 app...')
    
    settings = load_settings()
    pi2_settings = settings['PI2']
    
    threads = []
    stop_event = threading.Event()
    
    try:
        # Start all sensors
        if 'DS2' in pi2_settings: run_ds2(pi2_settings['DS2'], threads, stop_event, "DS2")
        if 'DUS2' in pi2_settings: run_dus2(pi2_settings['DUS2'], threads, stop_event, "DUS2")
        if 'DPIR2' in pi2_settings: run_pir2(pi2_settings['DPIR2'], threads, stop_event, "DPIR2")
        if 'BTN' in pi2_settings: run_btn(pi2_settings['BTN'], threads, stop_event, "BTN")
        if 'DHT3' in pi2_settings: run_dht(pi2_settings['DHT3'], threads, stop_event, "DHT3")
        if 'GSG' in pi2_settings: run_gsg(pi2_settings['GSG'], threads, stop_event, "GSG")
        
        # Start timer display thread
        timer_thread = threading.Thread(target=timer_thread_func, daemon=True)
        timer_thread.start()
        
        # MQTT client for Web app commands
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect(HOSTNAME, PORT, 60)
        mqtt_client.subscribe("pi2/timer/set")
        mqtt_client.subscribe("pi2/timer/add")
        mqtt_client.subscribe("pi2/display/cmd")
        mqtt_client.loop_start()
        
        # Console menu (optional, like PI1)
        while True:
            print_menu()
            command = input("Enter a command: ")
            
            if command == '1':
                actuate_4sd(pi2_settings['4SD'], "12:34")
            elif command == '2':
                btn_pressed_handler()
            elif command.lower() == 'x':
                print("Exiting...")
                stop_event.set()
                break
            else:
                print("Unknown command.")
    
    except KeyboardInterrupt:
        print('\nStopping PI2 app')
        stop_event.set()
        for t in threads:
            t.join()
