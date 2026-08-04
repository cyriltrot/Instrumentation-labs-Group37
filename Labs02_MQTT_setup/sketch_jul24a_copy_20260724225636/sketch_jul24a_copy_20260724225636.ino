
#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

// --- Hardware Configuration ---
#define DHTPIN 4          // GPIO pin connected to DHT11 DATA line
#define DHTTYPE DHT11     // Sensor type

DHT dht(DHTPIN, DHTTYPE);

// --- Network & Broker Configuration ---
const char* ssid        = "Cyril";      // Replace with your Wi-Fi Name
const char* password    = "cta09004";  // Replace with your Wi-Fi Password
const char* mqtt_server = "10.217.38.130";      // Your PC's Local IPv4 Address
const int   mqtt_port   = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

void setup_wifi() {
  delay(10);
  Serial.begin(115200);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Wi-Fi connected!");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connected to MQTT broker!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  dht.begin();
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Read sensor data every 2 seconds
  unsigned long now = millis();
  if (now - lastMsg > 2000) {
    lastMsg = now;

    float humidity = dht.readHumidity();
    float tempC = dht.readTemperature();

    // Check if readings failed
    if (isnan(humidity) || isnan(tempC)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    // Build JSON payload
    String payload = "{\"temperature\": " + String(tempC, 1) + 
                     ", \"humidity\": " + String(humidity, 1) + "}";
    
    Serial.print("Publishing message: ");
    Serial.println(payload);

    // Publish payload to topic: esp32/dht11
    client.publish("esp32/dht11", payload.c_str());
  }
}