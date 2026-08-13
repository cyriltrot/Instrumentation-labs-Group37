import json
from collections import deque
import datetime
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---
MQTT_BROKER = "10.136.230.130"  # or "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/smart_classroom/data"

MAX_POINTS = 30

times = deque(maxlen=MAX_POINTS)
temps = deque(maxlen=MAX_POINTS)
humi = deque(maxlen=MAX_POINTS)
light = deque(maxlen=MAX_POINTS)
dist = deque(maxlen=MAX_POINTS)

latest_data = {
    "temperature": 0.0,
    "humidity": 0.0,
    "light": 0,
    "distance": 0.0
}
last_msg_timestamp = None

# --- MQTT CALLBACKS ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"\n[MQTT SUCCESS] Subscribed to '{MQTT_TOPIC}'")
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global last_msg_timestamp
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        last_msg_timestamp = datetime.datetime.now()

        t = float(payload.get("temperature", 0.0))
        h = float(payload.get("humidity", 0.0))
        l = int(float(payload.get("light", 0)))
        d = float(payload.get("distance", 0.0))

        times.append(now_str)
        temps.append(t)
        humi.append(h)
        light.append(l)
        dist.append(d)

        latest_data["temperature"] = t
        latest_data["humidity"] = h
        latest_data["light"] = l
        latest_data["distance"] = d
    except Exception as e:
        print(f"[PARSING ERROR] {e}")

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"[MQTT ERROR] {e}")

# --- DASH APP & STYLING ---
app = dash.Dash(__name__)
app.title = "Lab 6 Advanced Telemetry"

CARD_STYLE = {
    "backgroundColor": "#161b22",
    "borderRadius": "12px",
    "padding": "16px",
    "boxShadow": "0 8px 24px rgba(0,0,0,0.4)",
    "border": "1px solid #30363d",
    "textAlign": "center"
}

def build_gauge(val, title, min_v, max_v, unit, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'suffix': f" {unit}", 'font': {'color': '#ffffff', 'size': 20}},
        title={'text': title, 'font': {'color': '#8b949e', 'size': 13}},
        gauge={
            'axis': {'range': [min_v, max_v], 'tickwidth': 1, 'tickcolor': "#30363d"},
            'bar': {'color': color},
            'bgcolor': "#0d1117",
            'borderwidth': 1,
            'bordercolor': "#30363d",
        }
    ))
    fig.update_layout(
        paper_bgcolor="#161b22",
        plot_bgcolor="#161b22",
        margin=dict(l=20, r=20, t=30, b=10),
        height=140
    )
    return fig

def build_line_chart(x_vals, y_vals, title, color, fill_color, unit):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(x_vals),
        y=list(y_vals),
        mode="lines+markers",
        fill="tozeroy",
        fillcolor=fill_color,
        line=dict(color=color, width=2, shape="spline"),
        marker=dict(size=4, color=color)
    ))
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(color="#c9d1d9", size=13)),
        paper_bgcolor="#161b22",
        plot_bgcolor="#161b22",
        margin=dict(l=40, r=15, t=35, b=35),
        xaxis=dict(showgrid=True, gridcolor="#21262d", tickfont=dict(color="#8b949e"), zeroline=False),
        yaxis=dict(title=dict(text=unit, font=dict(color="#8b949e")), showgrid=True, gridcolor="#21262d", tickfont=dict(color="#8b949e"), zeroline=False),
        height=220
    )
    return fig

app.layout = html.Div(
    style={"backgroundColor": "#0d1117", "color": "#c9d1d9", "padding": "24px", "minHeight": "100vh", "fontFamily": "Segoe UI, sans-serif"},
    children=[
        # Header + Connection Status Indicator
        html.Div([
            html.Div([
                html.H2("SMART CLASSROOM TELEMETRY CENTER", style={"margin": "0", "fontWeight": "700", "color": "#58a6ff"}),
                html.P("Lab 6 Real-time MQTT Environment Dashboard", style={"color": "#8b949e", "margin": "4px 0 0 0"}),
            ]),
            html.Div(id="status-badge", style={"padding": "8px 16px", "borderRadius": "20px", "fontWeight": "bold", "fontSize": "12px"})
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"}),

        # Dynamic Alert Banner
        html.Div(id="alert-banner", style={"marginBottom": "20px"}),

        # Circular Gauge Meters
        html.Div([
            html.Div([dcc.Graph(id="gauge-temp", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "23%"}),
            html.Div([dcc.Graph(id="gauge-hum", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "23%"}),
            html.Div([dcc.Graph(id="gauge-light", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "23%"}),
            html.Div([dcc.Graph(id="gauge-dist", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "23%"}),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "20px"}),

        # Time-series Line Graphs
        html.Div([
            html.Div([dcc.Graph(id="graph-temp", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "48%", "marginBottom": "16px"}),
            html.Div([dcc.Graph(id="graph-hum", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "48%", "marginBottom": "16px"}),
            html.Div([dcc.Graph(id="graph-light", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "48%"}),
            html.Div([dcc.Graph(id="graph-dist", config={'displayModeBar': False})], style={**CARD_STYLE, "width": "48%"}),
        ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-between"}),

        dcc.Interval(id="interval-update", interval=1000, n_intervals=0)
    ]
)

@app.callback(
    [
        Output("status-badge", "children"),
        Output("status-badge", "style"),
        Output("alert-banner", "children"),
        Output("gauge-temp", "figure"),
        Output("gauge-hum", "figure"),
        Output("gauge-light", "figure"),
        Output("gauge-dist", "figure"),
        Output("graph-temp", "figure"),
        Output("graph-hum", "figure"),
        Output("graph-light", "figure"),
        Output("graph-dist", "figure"),
    ],
    [Input("interval-update", "n_intervals")]
)
def update_dashboard(n):
    # Check MQTT Stream Status
    is_online = False
    if last_msg_timestamp:
        seconds_since_last = (datetime.datetime.now() - last_msg_timestamp).total_seconds()
        if seconds_since_last < 5:
            is_online = True

    if is_online:
        badge_text = "● CONNECTED"
        badge_style = {"backgroundColor": "rgba(63, 185, 80, 0.15)", "color": "#3fb950", "border": "1px solid #3fb950"}
    else:
        badge_text = "● OFFLINE"
        badge_style = {"backgroundColor": "rgba(248, 81, 73, 0.15)", "color": "#f85149", "border": "1px solid #f85149"}

    # Evaluate Threshold Alerts
    alerts = []
    if latest_data["temperature"] > 30.0:
        alerts.append("HIGH TEMPERATURE ALERT (>30°C)")
    if latest_data["distance"] > 0 and latest_data["distance"] < 10.0:
        alerts.append("PROXIMITY WARNING (<10cm)")

    if alerts:
        alert_element = html.Div(
            f"⚠️ {' | '.join(alerts)}",
            style={
                "backgroundColor": "rgba(248, 81, 73, 0.2)",
                "color": "#ff7b72",
                "border": "1px solid #f85149",
                "padding": "10px",
                "borderRadius": "8px",
                "textAlign": "center",
                "fontWeight": "bold"
            }
        )
    else:
        alert_element = html.Div()

    # Gauges
    g_temp = build_gauge(latest_data["temperature"], "TEMPERATURE", 0, 50, "°C", "#ff7b72")
    g_hum = build_gauge(latest_data["humidity"], "HUMIDITY", 0, 100, "%", "#3fb950")
    g_light = build_gauge(latest_data["light"], "LIGHT", 0, 4095, "RAW", "#d29922")
    g_dist = build_gauge(latest_data["distance"], "PROXIMITY", 0, 200, "cm", "#a371f7")

    # Line Graphs
    f_temp = build_line_chart(times, temps, "Temperature Stream", "#ff7b72", "rgba(255, 123, 114, 0.12)", "°C")
    f_hum = build_line_chart(times, humi, "Relative Humidity", "#3fb950", "rgba(63, 185, 80, 0.12)", "%")
    f_light = build_line_chart(times, light, "Ambient Light Level", "#d29922", "rgba(210, 153, 34, 0.12)", "RAW")
    f_dist = build_line_chart(times, dist, "Ultrasonic Distance", "#a371f7", "rgba(163, 113, 247, 0.12)", "cm")

    return badge_text, badge_style, alert_element, g_temp, g_hum, g_light, g_dist, f_temp, f_hum, f_light, f_dist

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=8050)