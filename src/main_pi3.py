import json
import threading
import paho.mqtt.client as mqtt
from settings import load_settings
from pi3.sensors.dht1 import run_dht as run_dht1
from pi3.sensors.dht2 import run_dht as run_dht2
from pi3.sensors.pir3 import run_pir
from pi3.components.ir_receiver import run_ir
from pi3.actuators.rgb import actuate_rgb
from pi3.actuators.lcd import run_lcd
from env import HOSTNAME, PORT

dht1_humidity = 0.0
dht1_temperature = 0.0
dht2_humidity = 0.0
dht2_temperature = 0.0
dht3_humidity = 0.0
dht3_temperature = 0.0

def on_mqtt_message(client, userdata, msg):
    global dht1_humidity, dht1_temperature, dht2_humidity, dht2_temperature, dht3_humidity, dht3_temperature

    payload = json.loads(msg.payload.decode())
    
    if msg.topic == "pi3/dht":
        if "dht1_hum" in payload:
            dht1_humidity = payload["dht1_hum"]

        if "dht1_temp" in payload:
            dht1_temperature = payload["dht1_temp"]

        if "dht2_hum" in payload:
            dht2_humidity = payload["dht2_hum"]

        if "dht2_temp" in payload:
            dht2_temperature = payload["dht2_temp"]

        if "dht3_hum" in payload:
            dht3_humidity = payload["dht3_hum"]

        if "dht3_temp" in payload:
            dht3_temperature = payload["dht3_temp"]
        
def trigger_lcd_loop():
    run_lcd(pi3_settings["LCD"], threads, stop_event, "LCD", trigger_lcd_loop, dht1_humidity, dht1_temperature, dht2_humidity, dht2_temperature, dht3_humidity, dht3_temperature)

try:
    import RPi.GPIO as GPIO # type: ignore
    GPIO.setmode(GPIO.BCM)
except:
    pass

def print_menu():
    print("\n" + "="*10 + " PI3 ACTUATORS " + "="*10)
    print("1. Toggle RGB Light: White")
    print("2. Toggle RGB Light: Red")
    print("3. Toggle RGB Light: Green")
    print("4. Toggle RGB Light: Blue")
    print("5. Toggle RGB Light: Yellow")
    print("6. Toggle RGB Light: Purple")
    print("7. Toggle RGB Light: Light Blue")
    print("8. Toggle RGB Light: Off")
    print("X. Exit")
    print("="*26)

if __name__ == "__main__":
    print('Starting PI3 app...')
    settings = load_settings()
    pi3_settings = settings['PI3']
    threads = []
    stop_event = threading.Event()

    try:
        if 'DHT1' in pi3_settings: run_dht1(pi3_settings['DHT1'], threads, stop_event, "DHT1")
        if 'DHT2' in pi3_settings: run_dht2(pi3_settings['DHT2'], threads, stop_event, "DHT2")
        if 'DPIR3' in pi3_settings: run_pir(pi3_settings['DPIR3'], threads, stop_event, "DPIR3")
        if 'IR' in pi3_settings: run_ir(pi3_settings['IR'], threads, stop_event, "IR")
        trigger_lcd_loop()
        

        mqtt_client = mqtt.Client()
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect(HOSTNAME, PORT, 60)
        mqtt_client.subscribe("pi3/dht")
        mqtt_client.loop_start()
        while True:
            print_menu()
            command = input("Enter a command: ")

            if command == '1':
                actuate_rgb(1, pi3_settings["BRGB"], threads, stop_event, "BRGB")
            elif command == '2':
                actuate_rgb(2, pi3_settings["BRGB"], threads, stop_event, "BRGB")
            elif command == '3':
                actuate_rgb(3, pi3_settings["BRGB"], threads, stop_event, "BRGB")
            elif command == '4':
                actuate_rgb(4, pi3_settings["BRGB"], threads, stop_event, "BRGB")
            elif command == '5':
                actuate_rgb(5, pi3_settings["BRGB"], threads, stop_event, "BRGB")
            elif command == '6':
                actuate_rgb(6, pi3_settings["BRGB"], threads, stop_event, "BRGB")
            elif command == '7':
                actuate_rgb(7, pi3_settings["BRGB"], threads, stop_event, "BRGB")
            elif command == '8':
                actuate_rgb(8, pi3_settings["BRGB"], threads, stop_event, "BRGB")

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