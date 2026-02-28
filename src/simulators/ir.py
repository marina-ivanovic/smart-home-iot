import time
import random

def generate_values():
    keys = ["LEFT", "RIGHT", "UP", "DOWN", "2", "3", "1", "OK", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    while True:
        yield random.choice(keys)

def run_ir_simulator(delay, callback, stop_event, name, publish_event, settings):
    for key in generate_values():
        time.sleep(delay)
        callback(key, name, publish_event, settings)
        if stop_event.is_set():
            break