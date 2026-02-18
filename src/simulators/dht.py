import time
import random

def run_dht_simulator(interval, callback, stop_event, name, publish_event, settings):
    while not stop_event.is_set():
        humidity = random.uniform(30, 70)
        temperature = random.uniform(18, 28)
        callback(humidity, temperature, name, publish_event, settings)
        time.sleep(interval)
