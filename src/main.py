import threading
from settings import load_settings
from components.dl import run_dl
from components.db import run_db

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

    lights_status, buzzer_status = False, False

    try:
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