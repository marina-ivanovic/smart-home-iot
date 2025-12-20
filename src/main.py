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
    print("1. DL: Light on")
    print("2. DL: Light off")
    print("3. DB: Buzzer on")
    print("4. DB: Buzzer off")
    print("X. Exit")
    print("="*26)

if __name__ == "__main__":
    print('Starting PI1 app...')
    settings = load_settings()
    pi1_settings = settings['PI1']
    threads = []
    stop_event = threading.Event()

    try:
        while True:
            print_menu()
            command = input("Enter a command: ")

            if command == '1':
                run_dl(pi1_settings['DL'], True)
            elif command == '2':
                run_dl(pi1_settings['DL'], False)
            elif command == '3':
                run_db(pi1_settings['DB'], True)
            elif command == '4':
                run_db(pi1_settings['DB'], False)
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