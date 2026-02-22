from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# InfluxDB Configuration
token = "token" # TODO: change token
org = "org" # TODO: change organization
url = "http://localhost:8086"
bucket = "bucket" # TODO: change bucket
influxdb_client = InfluxDBClient(url=url, token=token, org=org)


# MQTT Configuration
mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

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

    # TODO: subscribe to other channels here

mqtt_client.on_connect = on_connect
mqtt_client.on_message = lambda client, userdata, msg: save_to_db(json.loads(msg.payload.decode('utf-8')))


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
    try:
        query_api = influxdb_client.query_api()
        tables = query_api.query(query, org=org)

        container = []
        for table in tables:
            for record in table.records:
                container.append(record.values)

        return jsonify({"status": "success", "data": container})
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

@app.route('/api/state', methods=['GET'])
def get_current_state():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "Temperature" or r["_measurement"] == "Humidity")
    |> last()"""
    return handle_influx_query(query)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
