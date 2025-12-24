import time
import random

def generate_values():
    while True:
        yield random.choice([True, False, False, False])

def run_pir_simulator(delay, callback, stop_event, name):
    for motion in generate_values():
        time.sleep(delay)
        if motion:
            callback(name)
        if stop_event.is_set():
            break