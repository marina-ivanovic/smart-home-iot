from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import threading
from flask_cors import CORS
from time import sleep
import time


app = Flask(__name__)
CORS(app)

# Alarm stuff
system_on = False
alarm_on = False
people_inside = 0
dus_queue_size = 7
dus1_queue = []
dus2_queue = []
ds1_last_signal = None
ds2_last_signal = None
super_secret_pin = "1111"

# InfluxDB Configuration
token = "token" # TODO: change token
org = "org" # TODO: change organization
url = "http://localhost:8086"
bucket = "bucket" # TODO: change bucket
influxdb_client = InfluxDBClient(url=url, token=token, org=org)

def delayed_system_boot():
    global system_on

    sleep(10)
    system_on = True

def check_door_locked(is_triggered_by_ds1):
    global ds1_last_signal, ds2_last_signal, alarm_on, system_on
    
    sleep(5)

    if is_triggered_by_ds1:
        if ds1_last_signal is not None and ds1_last_signal + 5 <= time.time() and system_on:
            alarm_on = True
            notify_pi1_alarm()
    else:
        if ds2_last_signal is not None and ds2_last_signal + 5 <= time.time() and system_on:
            alarm_on = True
            notify_pi1_alarm()

def on_connect(client, userdata, flags, rc):
    client.subscribe("ButtonPress")
    client.subscribe("Key")
    client.subscribe("MotionDetected")
    client.subscribe("Distance")
    client.subscribe("LightOn")
    client.subscribe("BuzzerOn")
    client.subscribe("Humidity")
    client.subscribe("Temperature")
    client.subscribe("Gyroscope")
    client.subscribe("IrButtonPressed")
    client.subscribe("RgbLightValue")
    client.subscribe("LcdText")

    # channel where dht values will be sent for lcd to be updated
    client.subscribe("DhtValuesChanged")

def on_message(client, userdata, msg):
    global system_on, alarm_on, people_inside, dus1_queue, dus2_queue, dus_queue_size, ds1_last_signal, ds2_last_signal
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        topic = msg.topic
        if topic == "DhtValuesChanged":
            
            fields = [
                "dht1_temp", "dht1_hum",
                "dht2_temp", "dht2_hum",
                "dht3_temp", "dht3_hum"
            ]
            outgoing_payload = {k: payload[k] for k in fields if k in payload}

            # Publish to different topic
            client.publish(
                "pi3/dht",
                json.dumps(outgoing_payload)
            )
        else:
            save_to_db(payload)
            if topic == "IrButtonPressed":
                color = payload["value"]
                if color in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                    outgoing_payload = { "color": int(color) }
                    client.publish(
                        "pi3/rgb",
                        json.dumps(outgoing_payload)
                    )
            
            if topic == "Distance":
                if payload["name"] == "DUS1":
                    if len(dus1_queue) >= dus_queue_size:
                        dus1_queue = dus1_queue[1:]
                        dus1_queue.append(payload["value"])

                if payload["name"] == "DUS2":
                    if len(dus2_queue) >= dus_queue_size:
                        dus2_queue = dus2_queue[1:]
                        dus2_queue.append(payload["value"])

            if topic == "MotionDetected":
                if system_on and people_inside <= 0:
                    alarm_on = True
                    notify_pi1_alarm()

                if payload["name"] == "DPIR1":
                    outgoing_payload = { "light": True }
                    client.publish(
                        "pi1/motionDl",
                        json.dumps(outgoing_payload)
                    )

                    distance = 0
                    someone_entering = None
                    for entry in dus1_queue:
                        if distance < entry:
                            someone_entering = False
                        else:
                            someone_entering = True
                        distance = entry

                    if someone_entering is not None:
                        if someone_entering:
                            people_inside += 1
                        else:
                            people_inside -= 1
                        if people_inside < 0:
                            people_inside = 0

                if payload["name"] == "DPIR2":
                    distance = 0
                    someone_entering = None
                    for entry in dus2_queue:
                        if distance < entry:
                            someone_entering = False
                        else:
                            someone_entering = True
                        distance = entry

                    if someone_entering is not None:
                        if someone_entering:
                            people_inside += 1
                        else:
                            people_inside -= 1
                        if people_inside < 0:
                            people_inside = 0
                            
            if topic == "ButtonPress":
                if payload["name"] == "DS1":
                    if payload["value"]:
                        ds1_last_signal = time.time()
                        doorlock_thread = threading.Thread(target=check_door_locked, args=(True,))
                        doorlock_thread.start()
                    else:
                        ds1_last_signal = None
                        alarm_on = False
                        notify_pi1_alarm()
                if payload["name"] == "DS2":
                    if payload["value"]:
                        ds2_last_signal = time.time()
                        doorlock_thread = threading.Thread(target=check_door_locked, args=(False,))
                        doorlock_thread.start()
                    else:
                        ds2_last_signal = None
                        alarm_on = False
                        notify_pi1_alarm()


            if topic == "Key":
                if payload["value"] == super_secret_pin:
                    if system_on:
                        system_on = False
                        alarm_on = False
                        notify_pi1_alarm()
                    else:
                        system_thread = threading.Thread(target=delayed_system_boot)
                        system_thread.start()
                else:
                    if system_on:
                        alarm_on = True
                        notify_pi1_alarm()

            if topic == "Gyroscope":
                if payload["significant_movement"]:
                    if system_on:
                        alarm_on = True
                        notify_pi1_alarm()

    except Exception as e:
        print("Error processing message:", e)

# MQTT Configuration
mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_start()

PI1_IP = "localhost"
PI2_IP = "localhost"
PI3_IP = "localhost"
PI1_PORT = 1883
PI2_PORT = 1883
PI3_PORT = 1883

def notify_pi1_alarm():
    if system_on:
        mqtt_client.publish(
            "pi1/alarm",
            json.dumps({"alarm": alarm_on})
        )
    if not system_on and not alarm_on:
        mqtt_client.publish(
            "pi1/alarm",
            json.dumps({"alarm": alarm_on})
        )

def save_to_db(data):
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    point = (
        Point(data["measurement"])
        .tag("simulated", data["simulated"])
        .tag("runs_on", data["runs_on"])
        .tag("name", data["name"])
    )
    
    if data["measurement"] == "Gyroscope":
        point = (point
            .field("accel_x", data["accel_x"])
            .field("accel_y", data["accel_y"])
            .field("accel_z", data["accel_z"])
            .field("gyro_x", data["gyro_x"])
            .field("gyro_y", data["gyro_y"])
            .field("gyro_z", data["gyro_z"])
            .field("significant_movement", data["significant_movement"])
        )
    else:
        point = point.field("measurement", data["value"])
    
    write_api.write(bucket=bucket, org=org, record=point)

# Route to store dummy data
@app.route('/store_data', methods=['POST'])
def store_data():
    try:
        data = request.get_json()
        store_data(data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def handle_influx_query(query):
    global alarm_on, system_on
    try:
        query_api = influxdb_client.query_api()
        tables = query_api.query(query, org=org)

        container = []
        for table in tables:
            for record in table.records:
                container.append(record.values)

        return jsonify({"status": "success", "data": container, "alarm": alarm_on, "system": system_on})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/simple_query', methods=['GET'])
def retrieve_simple_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Humidity")"""
    return handle_influx_query(query)


@app.route('/aggregate_query', methods=['GET'])
def retrieve_aggregate_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Humidity")
    |> mean()"""
    return handle_influx_query(query)

@app.route("/actuator/<device>/toggle", methods=["GET"])
def actuator_toggle(device):
    mqtt_client.publish(
        "pi1/actuator/cmd",
        json.dumps({"device": device})
    )
    return "OK"

@app.route("/pi2/timer/set", methods=["POST"])
def set_timer():
    data = request.get_json()
    seconds = int(data.get("seconds", 0))
    mqtt_client.publish("pi2/timer/set", json.dumps({"value": str(seconds)}))
    return jsonify({"status": "success", "message": f"Timer set to {seconds}s"})

@app.route("/pi2/timer/config", methods=["POST"])
def set_timer_add_config():
    data = request.get_json()
    amount = int(data.get("amount", 10))
    mqtt_client.publish("pi2/timer/add", json.dumps({"amount": amount}))
    return jsonify({"status": "success", "message": f"Add amount set to {amount}s"})

@app.route("/pi3/rgb", methods=['POST'])
def change_rgb_color():
    data = request.get_json()
    color = int(data.get("color", 8))
    outgoing_payload = { "color": int(color) }
    mqtt_client.publish(
        "pi3/rgb",
        json.dumps(outgoing_payload)
    )
    return jsonify({"status": "success", "message": f"Color RGB set to option {color}"})

@app.route("/api/alarm", methods=['POST'])
def toggle_alarm():
    global alarm_on
    data = request.get_json()
    is_alarm_on = data.get("alarm_on", alarm_on)
    alarm_on = is_alarm_on
    notify_pi1_alarm()
    return jsonify({"status": "success", "message": f"Set alarm to {alarm_on}"})

@app.route("/api/system", methods=['POST'])
def toggle_system():
    global system_on
    data = request.get_json()
    is_system_on = data.get("system_on", system_on)
    system_on = is_system_on
    return jsonify({"status": "success", "message": f"Set system to {system_on}"})

@app.route('/api/state', methods=['GET'])
def get_current_state():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "Temperature" or r["_measurement"] == "Humidity")
    |> last()"""
    return handle_influx_query(query)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
