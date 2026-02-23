from simulators.dht import run_dht_simulator
import threading
import time
import json
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT

batch = []
publish_data_counter = 0
publish_data_limit = 10
counter_lock = threading.Lock()

def publisher_task(event, batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = batch.copy()
            publish_data_counter = 0
            batch.clear()
        publish.multiple(local_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} DHT values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, batch,))
publisher_thread.daemon = True
publisher_thread.start()

def dht_callback(humidity, temperature, name, publish_event, settings):
    global publish_data_counter, publish_data_limit
    
    payload_humidity = {
        "measurement": "Humidity",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": humidity
    }
    
    payload_temperature = {
        "measurement": "Temperature",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": temperature
    }
    
    with counter_lock:
        batch.append(('Humidity', json.dumps(payload_humidity), 0, True))
        batch.append(('Temperature', json.dumps(payload_temperature), 0, True))
        publish_data_counter += 2
        if publish_data_counter >= publish_data_limit:
            publish_event.set()
    
    t = time.localtime()
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)} | {name} Humidity: {humidity:.2f}%, Temperature: {temperature:.2f}°C")

def run_dht(settings, threads, stop_event, name):
    if settings['simulated']:
        dht_thread = threading.Thread(target=run_dht_simulator, args=(3, dht_callback, stop_event, name, publish_event, settings))
        dht_thread.start()
        threads.append(dht_thread)
    else:
        # Real DHT11 sensor
        import LA_DHT as DHT
        dht = DHT.DHT(settings['pin'])
        
        def read_dht_real():
            while not stop_event.is_set():
                chk = dht.readDHT11()
                if chk == dht.DHTLIB_OK:
                    dht_callback(dht.humidity, dht.temperature, name, publish_event, settings)
                else:
                    print(f"{name} DHT read error: {chk}")
                time.sleep(2)
        
        dht_thread = threading.Thread(target=read_dht_real)
        dht_thread.start()
        threads.append(dht_thread)
