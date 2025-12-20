import time
import random

def generate_values():
    keys = ["1", "2", "3", "A", "4", "5", "6", "B", "*", "0", "#", "D"]
    while True:
        yield random.choice(keys)

def run_dms_simulator(delay, callback, stop_event, name):
    for key in generate_values():
        time.sleep(delay)
        callback(key, name)
        if stop_event.is_set():
            break