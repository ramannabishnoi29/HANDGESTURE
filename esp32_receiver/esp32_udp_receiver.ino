#include <WiFi.h>
#include <WiFiUdp.h>

// Set Wi-Fi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// UDP Configuration
WiFiUDP udp;
const unsigned int localPort = 4210;
char packetBuffer[255];

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  Serial.printf("Connecting to %s ", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" CONNECTED!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

  // Begin UDP listening
  udp.begin(localPort);
  Serial.printf("Listening for UDP packets on port %d\n", localPort);
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(packetBuffer, 254);
    if (len > 0) {
      packetBuffer[len] = 0;
    }
    char cmd = packetBuffer[0];
    Serial.printf("Command Received: %c\n", cmd);

    // Motor driver control logic:
    switch (cmd) {
      case 'F':
        Serial.println("Action: MOVE FORWARD");
        break;
      case 'B':
        Serial.println("Action: MOVE BACKWARD");
        break;
      case 'L':
        Serial.println("Action: TURN LEFT");
        break;
      case 'R':
        Serial.println("Action: TURN RIGHT");
        break;
      case 'S':
      default:
        Serial.println("Action: STOP / HOLD");
        break;
    }
  }
}
