import json
import threading
import paho.mqtt.client as mqtt
from settings import load_settings
from pi3.sensors.dht1 import run_dht as run_dht1
from pi3.sensors.dht2 import run_dht as run_dht2
from pi3.sensors.pir3 import run_pir
from pi3.components.ir_receiver import run_ir
from pi3.actuators.rgb import actuate_rgb

lights_status, buzzer_status = False, False

def on_mqtt_message(client, userdata, msg):
    global lights_status, buzzer_status

    payload = json.loads(msg.payload.decode())
    device = payload["device"]

    print(device)

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

        # mqtt_client = mqtt.Client()
        # mqtt_client.on_message = on_mqtt_message
        # mqtt_client.connect("localhost", 1883, 60)
        # mqtt_client.subscribe("pi3/actuator/cmd")
        # mqtt_client.loop_start()
        while True:
            print_menu()
            command = input("Enter a command: ")

            if command == '1':
                actuate_rgb(1, settings, threads, stop_event, "BRGB")
            elif command == '2':
                actuate_rgb(2, settings, threads, stop_event, "BRGB")
            elif command == '3':
                actuate_rgb(3, settings, threads, stop_event, "BRGB")
            elif command == '4':
                actuate_rgb(4, settings, threads, stop_event, "BRGB")
            elif command == '5':
                actuate_rgb(5, settings, threads, stop_event, "BRGB")
            elif command == '6':
                actuate_rgb(6, settings, threads, stop_event, "BRGB")
            elif command == '7':
                actuate_rgb(7, settings, threads, stop_event, "BRGB")
            elif command == '8':
                actuate_rgb(8, settings, threads, stop_event, "BRGB")

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