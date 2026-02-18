#include <ESP_IoT_Manager.h>

// 設定你的 WiFi 和伺服器資訊
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverIP = "192.168.1.100";  // 你的伺服器 IP
const int serverPort = 5000;

// 建立 IoT Manager 實例
ESP_IoT_Manager iot(ssid, password, serverIP, serverPort);

void setup() {
  // 初始化（會自動連接 WiFi）
  iot.begin("1.0.0");
  
  Serial.println("Device ready!");
  Serial.print("MAC: ");
  Serial.println(iot.getMacAddress());
}

void loop() {
  // 必須在 loop 中呼叫（處理心跳和 WebSocket）
  iot.loop();
  
  // 模擬讀取感測器
  float temperature = random(200, 300) / 10.0;  // 20.0 ~ 30.0
  int humidity = random(40, 80);                 // 40 ~ 80
  
  // 發送數據到 Virtual Pin（類似 Blynk）
  iot.sendData("V0", temperature);  // Temperature sensor
  iot.sendData("V1", humidity);     // Humidity sensor
  iot.sendData("V2", "Online");     // Status string
  
  Serial.printf("Sent: Temp=%.1f°C, Humidity=%d%%\n", temperature, humidity);
  
  // 每 10 秒發送一次
  delay(10000);
}
