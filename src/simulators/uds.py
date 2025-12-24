import time
import random

def generate_values(initial_distance=100):
    distance = initial_distance
    while True:
        distance = distance + random.randint(-10, 10)
        if distance < 0: distance = 0
        yield distance

def run_uds_simulator(delay, callback, stop_event, name):
    for dist in generate_values():
        time.sleep(delay)
        callback(dist, name)
        if stop_event.is_set():
            break