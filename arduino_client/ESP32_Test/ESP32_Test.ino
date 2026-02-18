/*
 * ESP32 - IoT Manager 測試程式
 * 
 * 功能：
 * - 連接 WiFi
 * - 透過 HTTP 發送模擬感測器數據到 Blynk API
 * - 5 個虛擬腳位 (V5-V9)
 * 
 * 硬體：ESP32 DevKit
 * 板子設定：ESP32 Dev Module
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ==================== 設定區 ====================
// WiFi 設定
const char* ssid = "YOUR_WIFI_SSID";          // 修改為你的 WiFi 名稱
const char* password = "YOUR_WIFI_PASSWORD";  // 修改為你的 WiFi 密碼

// 伺服器設定
const char* serverUrl = "http://192.168.1.100:5000";  // 修改為你的伺服器 IP

// 發送間隔 (毫秒)
const unsigned long sendInterval = 5000;  // 每 5 秒發送一次
// ================================================

String deviceMAC = "";  // 將自動取得 MAC 地址

// 感測器定義（虛擬）- ESP32 使用不同的虛擬腳位
struct Sensor {
  String pin;
  String name;
  float minValue;
  float maxValue;
  String unit;
};

Sensor sensors[] = {
  {"V5", "CPU Temperature", 30.0, 80.0, "°C"},
  {"V6", "Pressure", 980.0, 1040.0, "hPa"},
  {"V7", "Altitude", 0.0, 500.0, "m"},
  {"V8", "CO2", 400.0, 2000.0, "ppm"},
  {"V9", "RSSI", -90.0, -30.0, "dBm"}
};

const int sensorCount = 5;
unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n");
  Serial.println("=====================================");
  Serial.println("  ESP32 IoT Manager 測試程式");
  Serial.println("  裝置類型: ESP32");
  Serial.println("=====================================");
  
  // 取得 MAC 地址
  deviceMAC = WiFi.macAddress();
  Serial.println("MAC 地址: " + deviceMAC);
  
  // 連接 WiFi
  connectWiFi();
  
  // 創建 DataStream 定義
  if (WiFi.status() == WL_CONNECTED) {
    createDataStreams();
    Serial.println("\n✅ 初始化完成！");
    Serial.println("開始發送模擬數據...\n");
  } else {
    Serial.println("\n❌ 初始化失敗：WiFi 未連接");
  }
}

void loop() {
  // 檢查 WiFi 連接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️  WiFi 斷線，重新連接...");
    connectWiFi();
    delay(5000);
    return;
  }
  
  // 定時發送數據
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    sendAllSensorData();
  }
  
  delay(100);
}

void connectWiFi() {
  Serial.println("\n📡 連接 WiFi: " + String(ssid));
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✅ WiFi 連接成功！");
    Serial.println("   IP 地址: " + WiFi.localIP().toString());
    Serial.println("   信號強度: " + String(WiFi.RSSI()) + " dBm");
  } else {
    Serial.println("❌ WiFi 連接失敗！");
    Serial.println("   請檢查 SSID 和密碼是否正確");
  }
}

void createDataStreams() {
  Serial.println("\n📝 創建 DataStream 定義...");
  
  HTTPClient http;
  String url = String(serverUrl) + "/blynk/admin/datastream";
  
  for (int i = 0; i < sensorCount; i++) {
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    String jsonData = "{";
    jsonData += "\"device_mac\":\"" + deviceMAC + "\",";
    jsonData += "\"pin\":\"" + sensors[i].pin + "\",";
    jsonData += "\"name\":\"ESP32-" + sensors[i].name + "\",";
    jsonData += "\"data_type\":\"double\",";
    jsonData += "\"min\":" + String(sensors[i].minValue, 1) + ",";
    jsonData += "\"max\":" + String(sensors[i].maxValue, 1) + ",";
    jsonData += "\"unit\":\"" + sensors[i].unit + "\"";
    jsonData += "}";
    
    int httpCode = http.POST(jsonData);
    
    if (httpCode > 0) {
      Serial.println("   ✅ " + sensors[i].name + " (" + sensors[i].pin + ")");
    } else {
      Serial.println("   ⚠️  " + sensors[i].name + " - HTTP " + String(httpCode));
    }
    
    http.end();
    delay(100);
  }
}

void sendAllSensorData() {
  unsigned long startTime = millis();
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.println("📊 [" + String(startTime / 1000) + "s] ESP32 發送數據：");
  
  int successCount = 0;
  
  for (int i = 0; i < sensorCount; i++) {
    float value;
    
    // 特殊處理：RSSI 使用實際 WiFi 信號強度
    if (sensors[i].pin == "V9") {
      value = WiFi.RSSI();
    } else {
      // 生成隨機數據（更真實的變化）
      value = sensors[i].minValue + 
              (random(0, 10000) / 10000.0) * 
              (sensors[i].maxValue - sensors[i].minValue);
    }
    
    // 發送到伺服器
    bool success = sendData(sensors[i].pin, value);
    
    if (success) {
      Serial.print("   ✅ ");
      successCount++;
    } else {
      Serial.print("   ❌ ");
    }
    
    Serial.print(sensors[i].name);
    Serial.print(": ");
    Serial.print(value, 2);
    Serial.println(" " + sensors[i].unit);
    
    delay(50);  // 避免請求過快
  }
  
  unsigned long elapsed = millis() - startTime;
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.println("✓ 成功: " + String(successCount) + "/" + String(sensorCount) + 
                 " | 耗時: " + String(elapsed) + "ms\n");
}

bool sendData(String pin, float value) {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }
  
  HTTPClient http;
  String url = String(serverUrl) + "/blynk/" + deviceMAC + "/update/" + pin + "?value=" + String(value, 2);
  
  http.begin(url);
  http.setTimeout(5000);  // 5 秒超時
  int httpCode = http.GET();
  http.end();
  
  return (httpCode == 200);
}
