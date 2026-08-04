// Include required libraries for hardware peripherals and network communications
#include <WiFi.h>          // Enables Wi-Fi connectivity for the ESP32 board[cite: 2]
#include <PubSubClient.h>  // Handles MQTT client protocol operations (publish/subscribe)[cite: 2]
#include <DHT.h>           // Interface library for reading DHT series environmental sensors[cite: 2]
#include <ArduinoJson.h>   // Constructs and serializes structured JSON payloads[cite: 2]

// Hardware Pin Definitions
#define DHTPIN 4           // Digital GPIO pin connected to the DHT11 data line[cite: 2]
#define DHTTYPE DHT11      // Specifies the model of the temperature/humidity sensor[cite: 2]
#define LDR_PIN 34         // Analog input pin connected to the LDR voltage divider circuit[cite: 2]
#define TRIG_PIN 5         // Digital output pin for the Ultrasonic sensor trigger pulse[cite: 2]
#define ECHO_PIN 18        // Digital input pin for reading the Ultrasonic echo response[cite: 2]

// Local Network Credentials & Broker Configuration
const char* ssid = "Cyril";               // Local Wi-Fi Access Point name
const char* password = "cta09004";          // Wi-Fi network password
const char* mqtt_server = "10.209.254.130"; // Host PC local IP address running Mosquitto MQTT broker[cite: 2]

// Communication Interface Instantiations
WiFiClient espClient;                     // Creates an unencrypted TCP client for network traffic[cite: 2]
PubSubClient client(espClient);           // Passes the network client into the MQTT protocol handler[cite: 2]
DHT dht(DHTPIN, DHTTYPE);                 // Initializes the DHT sensor instance with pin and sensor type[cite: 2]

// Function: Establishes connection to the local Wi-Fi Access Point
void setup_wifi() {
  WiFi.begin(ssid, password);             // Initiates Wi-Fi association using defined credentials[cite: 2]

  // Polls Wi-Fi connection status until successfully connected
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);                           // Non-blocking pause between connection attempts
    Serial.print(".");                    // Prints progress dots to the Serial Monitor
  }

  Serial.println("Connected to WiFi");    // Confirms successful network authentication
}

// System Initialization Execution
void setup() {
  Serial.begin(115200);                   // Starts serial communication at 115200 baud rate[cite: 2]

  dht.begin();                            // Activates internal timing for the DHT sensor[cite: 2]

  pinMode(TRIG_PIN, OUTPUT);              // Configures Ultrasonic Trig pin to send output pulses[cite: 2]
  pinMode(ECHO_PIN, INPUT);               // Configures Ultrasonic Echo pin to receive input timing[cite: 2]

  setup_wifi();                           // Calls function to establish Wi-Fi connection[cite: 2]

  client.setServer(mqtt_server, 1883);    // Configures MQTT client target server IP and port 1883[cite: 2]
}

// Function: Measures distance in centimeters using the Ultrasonic Sensor
float readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);            // Drives Trig pin LOW to clear existing signals[cite: 2]
  delayMicroseconds(2);                   // Brief pause for signal stabilization[cite: 2]

  digitalWrite(TRIG_PIN, HIGH);           // Drives Trig pin HIGH for 10 microseconds to send sonic pulse[cite: 2]
  delayMicroseconds(10);                  // Pulse duration[cite: 2]
  digitalWrite(TRIG_PIN, LOW);            // Returns Trig pin LOW[cite: 2]

  // Times how long the Echo pin stays HIGH (time-of-flight in microseconds)
  long duration = pulseIn(ECHO_PIN, HIGH); // Measures response time of returning echo[cite: 2]

  // Converts time duration into distance in cm: (duration * speed of sound 0.034 cm/us) / 2 (round trip)
  return duration * 0.034 / 2;            // Returns calculated distance[cite: 2]
}

// Main Program Loop
void loop() {

  // Reconnection Logic: Ensures the client remains connected to the MQTT broker
  if (!client.connected()) {
    while (!client.connected()) {
      // Connects with a unique client ID ("ESP32Client")
      if (client.connect("ESP32Client"))[cite: 2]
        break;                            // Breaks out of reconnect loop upon success[cite: 2]

      delay(2000);                        // Waits 2 seconds before retrying connection[cite: 2]
    }
  }

  // Acquisition of Real-Time Sensor Data
  float temp = dht.readTemperature();     // Reads ambient temperature in degrees Celsius[cite: 2]
  float hum = dht.readHumidity();         // Reads relative humidity percentage[cite: 2]
  int light = analogRead(LDR_PIN);        // Reads raw 12-bit ADC value (0-4095) from LDR sensor[cite: 2]
  float distance = readDistanceCM();      // Calls function to acquire ultrasonic distance reading[cite: 2]

  // JSON Payload Construction
  StaticJsonDocument<200> doc;            // Allocates a 200-byte memory buffer on the stack for JSON[cite: 2]

  // Assigns key-value pairs to the JSON document instance
  doc["temperature"] = temp;              // Map ambient temperature value[cite: 2]
  doc["humidity"] = hum;                  // Map relative humidity value[cite: 2]
  doc["light"] = light;                    // Map analog light intensity value[cite: 2]
  doc["distance"] = distance;              // Map calculated distance value[cite: 2]

  char buffer[256];                       // Character array buffer to hold serialized output string[cite: 2]
  serializeJson(doc, buffer);             // Serializes JSON object into a formatted string inside 'buffer'[cite: 2]

  // MQTT Publishing
  // Publishes serialized JSON data packet to topic 'esp32/21100434/data'
  client.publish("esp32/21100434/data", buffer); //[cite: 2]

  // Output Logging to Local Console
  Serial.print("Published: ");            // Logs confirmation prefix[cite: 2]
  Serial.println(buffer);                 // Displays actual formatted JSON string[cite: 2]

  delay(5000);                            // Pauses execution for 5 seconds before next transmission cycle[cite: 2]
}