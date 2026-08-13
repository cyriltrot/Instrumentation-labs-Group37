import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import paho.mqtt.client as mqtt
import json
import collections

# Maintain maximum 20 historical data points per sensor
MAX_POINTS = 20
data_store = {
    'time': collections.deque(maxlen=MAX_POINTS),
    'temperature': collections.deque(maxlen=MAX_POINTS),
    'humidity': collections.deque(maxlen=MAX_POINTS),
    'light': collections.deque(maxlen=MAX_POINTS),
    'distance': collections.deque(maxlen=MAX_POINTS)
}

reading_counter = 0

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with code: {rc}")
    client.subscribe("esp32/21100434/data")

def on_message(client, userdata, msg):
    global reading_counter
    payload = msg.payload.decode()
    try:
        data = json.loads(payload)
        reading_counter += 1
        
        data_store['time'].append(f"#{reading_counter}")
        data_store['temperature'].append(data.get('temperature', 0))
        data_store['humidity'].append(data.get('humidity', 0))
        data_store['light'].append(data.get('light', 0))
        data_store['distance'].append(data.get('distance', 0))
    except json.JSONDecodeError:
        print("Invalid JSON received")

# Start MQTT Client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

# Initialize Dash application with DARKLY Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = dbc.Container([
    # Title Header
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H1("Real-Time IoT Sensor Dashboard", className="text-center text-primary fw-bold mt-3 mb-1"),
                    html.P("Live Telemetry via MQTT & Mosquitto Broker", className="text-center text-muted mb-3"),
                    html.P("Monitor your ESP32 sensor readings with a responsive dashboard layout.", className="text-center text-light")
                ])
            ], color="dark", className="mb-4 shadow-sm")
        , width=12)
    ]),

    # KPI Metric Cards Row
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Temperature", className="card-title text-danger mb-2"),
                html.H3(id="val-temp", className="card-text fw-bold", children="-- °C")
            ])
        ], color="secondary", outline=True), lg=3, md=6, sm=12),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Humidity", className="card-title text-info mb-2"),
                html.H3(id="val-hum", className="card-text fw-bold", children="-- %")
            ])
        ], color="secondary", outline=True), lg=3, md=6, sm=12),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Light Intensity", className="card-title text-warning mb-2"),
                html.H3(id="val-light", className="card-text fw-bold", children="-- ADC")
            ])
        ], color="secondary", outline=True), lg=3, md=6, sm=12),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Distance", className="card-title text-success mb-2"),
                html.H3(id="val-dist", className="card-text fw-bold", children="-- cm")
            ])
        ], color="secondary", outline=True), lg=3, md=6, sm=12),
    ], className="g-3 mb-4"),

    # Graph Grid Layout
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H5("Temperature")),
            dbc.CardBody(dcc.Graph(id='graph-temperature', config={'displayModeBar': False}))
        ], className="shadow-sm h-100"), lg=6, md=12),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H5("Humidity")),
            dbc.CardBody(dcc.Graph(id='graph-humidity', config={'displayModeBar': False}))
        ], className="shadow-sm h-100"), lg=6, md=12),
    ], className="g-4 mb-4"),
    
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H5("Light Intensity")),
            dbc.CardBody(dcc.Graph(id='graph-light', config={'displayModeBar': False}))
        ], className="shadow-sm h-100"), lg=6, md=12),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H5("Distance")),
            dbc.CardBody(dcc.Graph(id='graph-distance', config={'displayModeBar': False}))
        ], className="shadow-sm h-100"), lg=6, md=12),
    ], className="g-4 mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody(html.P("Live dashboard updates every 2 seconds. Adjust your MQTT source or Mosquitto broker settings as needed.", className="mb-0 text-muted"))
        ], color="dark", className="shadow-sm"), width=12)
    ], className="mb-4"),

    dcc.Interval(id='interval-component', interval=2000, n_intervals=0)
], fluid=True, className="px-4 py-4")

# Reusable function for consistent graph styling
def make_figure(x, y, title, y_title, color):
    return {
        'data': [{
            'x': x,
            'y': y,
            'type': 'scatter',
            'mode': 'lines+markers',
            'name': title,
            'line': {'color': color, 'width': 3, 'shape': 'spline'},
            'marker': {'size': 6, 'color': color}
        }],
        'layout': {
            'title': {'text': title, 'font': {'size': 18, 'color': '#ffffff'}},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'xaxis': {'title': 'Sample Index', 'gridcolor': '#333333', 'color': '#aaaaaa'},
            'yaxis': {'title': y_title, 'gridcolor': '#333333', 'color': '#aaaaaa'},
            'margin': {'l': 50, 'r': 30, 't': 40, 'b': 40}
        }
    }

@app.callback(
    [Output('val-temp', 'children'),
     Output('val-hum', 'children'),
     Output('val-light', 'children'),
     Output('val-dist', 'children'),
     Output('graph-temperature', 'figure'),
     Output('graph-humidity', 'figure'),
     Output('graph-light', 'figure'),
     Output('graph-distance', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    x_axis = list(data_store['time'])
    temp_data = list(data_store['temperature'])
    hum_data = list(data_store['humidity'])
    light_data = list(data_store['light'])
    dist_data = list(data_store['distance'])

    # Format KPI metric text
    latest_temp = f"{temp_data[-1]:.1f} °C" if temp_data else "-- °C"
    latest_hum = f"{hum_data[-1]:.1f} %" if hum_data else "-- %"
    latest_light = f"{light_data[-1]}" if light_data else "-- ADC"
    latest_dist = f"{dist_data[-1]:.1f} cm" if dist_data else "-- cm"

    # Generate styled figures
    fig_temp = make_figure(x_axis, temp_data, 'Temperature Stream', '°C', '#ff4d4d')
    fig_hum = make_figure(x_axis, hum_data, 'Humidity Stream', '%', '#3399ff')
    fig_light = make_figure(x_axis, light_data, 'Light Intensity', 'ADC Value', '#ffcc00')
    fig_dist = make_figure(x_axis, dist_data, 'Distance Stream', 'cm', '#00cc66')
    
    return latest_temp, latest_hum, latest_light, latest_dist, fig_temp, fig_hum, fig_light, fig_dist

if __name__ == '__main__':
    app.run(debug=True, port=8050)