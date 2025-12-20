from actuators.dl import actuate_dl
import time

def run_dl(settings, on):
    if settings['simulated']:
        actuate_dl(on)
    else:
        import RPi.GPIO as GPIO
        GPIO.output(settings['pin'], GPIO.HIGH if on else GPIO.LOW)
        print(f"Real DL toggled: {on}")