#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* server = "http://YOUR_COMPUTER_IP:5000/add_data";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  dht.begin();
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Connected");
}

void sendData(String id, String loc, String type, float val, float threshold) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(server);
    http.addHeader("Content-Type", "application/json");

    String status = (val > threshold) ? "Alert" : "Normal";
    String json = "{\"sensor_id\":\"" + id + "\",\"location\":\"" + loc + "\",\"type\":\"" + type + "\",\"value\":" + String(val) + ",\"status\":\"" + status + "\"}";

    int httpResponseCode = http.POST(json);
    Serial.println("Response Code: " + String(httpResponseCode));
    http.end();
  }
}

void loop() {
  float temp = dht.readTemperature();
  if (!isnan(temp)) {
    sendData("S001", "Block A", "temperature", temp, 30.0);
  }
  delay(2000);
  
  sendData("S002", "Block B", "light", random(200, 800), 700.0);
  delay(2000);
  
  sendData("S003", "Block C", "energy", random(10, 50), 45.0);
  delay(10000); // 10-second intervals
}
