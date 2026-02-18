#include <ESP_IoT_Manager.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverIP = "192.168.1.100";

ESP_IoT_Manager iot(ssid, password, serverIP, 5000);

// 定義 LED 腳位
const int LED_PIN = 2;  // ESP32/ESP8266 內建 LED
int ledState = LOW;

// 當收到控制指令時的回調函式
void handleControl(String pin, String value) {
  Serial.printf("Received command: %s = %s\n", pin.c_str(), value.c_str());
  
  if (pin == "V10") {
    // V10 控制 LED 開關
    ledState = (value == "1") ? HIGH : LOW;
    digitalWrite(LED_PIN, ledState);
    Serial.printf("LED turned %s\n", ledState ? "ON" : "OFF");
    
    // 回報 LED 狀態
    iot.sendData("V10", ledState);
  }
  else if (pin == "V11") {
    // V11 控制 LED 亮度（PWM）
    int brightness = value.toInt();
    analogWrite(LED_PIN, brightness);
    Serial.printf("LED brightness: %d\n", brightness);
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  iot.begin("1.0.0");
  
  // 註冊控制指令回調函式
  iot.onControlMessage(handleControl);
  
  Serial.println("Device ready for remote control!");
  Serial.println("Use Web interface to control V10 (LED On/Off)");
}

void loop() {
  iot.loop();
  
  // 定期回報設備狀態
  static unsigned long lastReport = 0;
  if (millis() - lastReport > 5000) {
    iot.sendData("V0", ledState ? "ON" : "OFF");  // LED status
    iot.sendData("V1", analogRead(A0));           // Analog input
    lastReport = millis();
  }
}
