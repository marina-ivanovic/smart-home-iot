import time
import random

def generate_values():
    while True:
        yield random.choice([True, False])

def run_door_sensor_simulator(delay, callback, stop_event, name, publish_event, settings, timer_callback=None):
    for value in generate_values():
        time.sleep(delay)
        if value:
             if timer_callback:
                 timer_callback()
             callback(value, name, publish_event, settings)
        if stop_event.is_set():
            break