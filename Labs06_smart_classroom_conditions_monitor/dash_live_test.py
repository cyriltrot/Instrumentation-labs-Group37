from collections import deque
import json
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import paho.mqtt.client as mqtt
import plotly.graph_objs as go

MQTT_BROKER = "10.95.243.130"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/dht11"

MAX_POINTS = 20
time_stamps = deque(maxlen=MAX_POINTS)
temp_buffer = deque(maxlen=MAX_POINTS)
counter = 0

def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected successfully!")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global counter
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        if "temperature" in data:
            counter += 1
            time_stamps.append(counter)
            temp_buffer.append(float(data["temperature"]))
            print(f"[MQTT Update] Temp: {data['temperature']}°C")
    except Exception as e:
        print(f"[MQTT Error] {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

app = dash.Dash(__name__)

# Full-page dark container wrapper
app.layout = html.Div(
    style={
        "backgroundColor": "#0d1117",
        "color": "#c9d1d9",
        "padding": "30px",
        "minHeight": "100vh",
        "fontFamily": "system-ui, -apple-system, sans-serif"
    },
    children=[
        html.H2("Live MQTT Temperature Stream", style={"color": "#58a6ff", "marginBottom": "20px"}),
        html.Div(
            style={
                "backgroundColor": "#161b22",
                "border": "1px solid #30363d",
                "borderRadius": "8px",
                "padding": "15px"
            },
            children=[dcc.Graph(id="live-temp-graph")]
        ),
        dcc.Interval(id="interval-trigger", interval=1000, n_intervals=0)
    ]
)

@app.callback(
    Output("live-temp-graph", "figure"),
    [Input("interval-trigger", "n_intervals")]
)
def update_graph(n):
    trace = go.Scatter(
        x=list(time_stamps),
        y=list(temp_buffer),
        mode="lines+markers",
        line=dict(color="#ff7b72", width=3),
        marker=dict(size=6, color="#ff7b72")
    )
    
    figure = go.Figure(
        data=[trace],
        layout=go.Layout(
            title=dict(text="<b>Temperature Stream (°C)</b>", font=dict(color="#c9d1d9", size=16)),
            paper_bgcolor="#161b22",  # Fixed dark card background
            plot_bgcolor="#161b22",   # Fixed dark plot canvas background
            margin=dict(l=50, r=30, t=50, b=50),
            xaxis=dict(
                title=dict(text="Sample", font=dict(color="#8b949e")),
                showgrid=True,
                gridcolor="#21262d",
                tickfont=dict(color="#8b949e"),
                zeroline=False
            ),
            yaxis=dict(
                title=dict(text="°C", font=dict(color="#8b949e")),
                showgrid=True,
                gridcolor="#21262d",
                tickfont=dict(color="#8b949e"),
                zeroline=False
            )
        )
    )
    return figure

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=8050)