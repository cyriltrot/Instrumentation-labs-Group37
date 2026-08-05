from flask import Flask
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# Global variable to store the latest incoming sensor readings
sensor_data = {}

# Callback triggered when the client connects to Mosquitto
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with code: {rc}")
    # Subscribes to your specific student topic
    client.subscribe("esp32/21100434/data") #[cite: 2]

# Callback triggered every time a new MQTT message arrives
def on_message(client, userdata, msg):
    global sensor_data
    payload = msg.payload.decode()
    print(f"Message received: {payload}")
    try:
        # Parse incoming JSON string into a Python dictionary
        sensor_data = json.loads(payload) #[cite: 2]
    except json.JSONDecodeError:
        print("Invalid JSON received")

# Initialize MQTT Client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to local Mosquitto broker
mqtt_client.connect("localhost", 1883, 60) #[cite: 2]

# Start non-blocking background loop for incoming MQTT messages
mqtt_client.loop_start() #[cite: 2]

# Define root endpoint for Flask web server
@app.route('/')
def index():
    # Returns latest sensor readings as JSON to the browser
    return sensor_data #[cite: 2]

if __name__ == '__main__':
    # Runs local server on port 5000
    app.run(debug=True, port=5000) #[cite: 2]