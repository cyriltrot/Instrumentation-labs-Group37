#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ==========================================================
// CONFIGURATION & PIN DEFINITIONS
// ==========================================================
const char* ssid         = "Cyril";
const char* password     = "cta09004";
const char* mqtt_server  = "10.136.230.130"; 
const int   mqtt_port    = 1883;
const char* mqtt_topic   = "esp32/smart_classroom/data";

#define DHTPIN      4
#define DHTTYPE     DHT11   // Change to DHT22 if using DHT22
#define LDR_PIN     34
#define TRIG_PIN    5
#define ECHO_PIN    18

// Initialize Sensor Objects
DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient client(espClient);

// Timing variables for non-blocking loop
unsigned long lastMsg = 0;
const long interval = 2000; // Publish every 2000ms (2 seconds)

// ==========================================================
// HELPER FUNCTIONS
// ==========================================================
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32ClassroomClient-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
  if (duration == 0) return -1.0; // Out of range or error
  return (duration * 0.0343) / 2.0; // Distance in cm
}

// ==========================================================
// SETUP & MAIN LOOP
// ==========================================================
void setup() {
  Serial.begin(115200);
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  dht.begin();
  setup_wifi();
  
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;

    // 1. Read Sensors
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    int lightRaw = analogRead(LDR_PIN);
    float distance = readDistance();

    // Check for DHT read errors
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor!");
      humidity = 0.0;
      temperature = 0.0;
    }

    // 2. Build JSON Payload
    StaticJsonDocument<200> doc;
    doc["temperature"] = temperature;
    doc["humidity"]    = humidity;
    doc["light"]       = lightRaw;
    doc["distance"]    = distance;

    char buffer[250];
    serializeJson(doc, buffer);

    // 3. Publish to MQTT Broker
    Serial.print("Publishing payload: ");
    Serial.println(buffer);
    client.publish(mqtt_topic, buffer);
  }
}