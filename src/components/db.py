from actuators.db import actuate_db
import time

def run_db(settings, on):
    if settings['simulated']:
        actuate_db(on)
    else:
        import RPi.GPIO as GPIO
        GPIO.output(settings['pin'], GPIO.HIGH if on else GPIO.LOW)
        print(f"Real DB toggled: {on}")