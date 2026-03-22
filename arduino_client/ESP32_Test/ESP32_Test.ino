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

#include <ESP_IoT_Manager.h>

// ==================== 設定區 ====================
// 伺服器設定
const char* serverIP = "192.168.1.100";  // 修改為你的伺服器 IP
const int serverPort = 5000;

// 發送間隔 (毫秒)
const unsigned long sendInterval = 5000;  // 每 5 秒發送一次
// ================================================

String deviceMAC = "";  // 將自動取得 MAC 地址

// 由函式庫處理連線與 API 傳輸
ESP_IoT_Manager iot(serverIP, serverPort);

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

const char* pins[sensorCount] = {"V5", "V6", "V7", "V8", "V9"};
String values[sensorCount];
const char* valuePtrs[sensorCount];

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n");
  Serial.println("=====================================");
  Serial.println("  ESP32 IoT Manager 測試程式");
  Serial.println("  裝置類型: ESP32");
  Serial.println("=====================================");
  
  // 啟用手機引導配網（Captive Portal）
  // 第一次使用時，請用手機連接 ESP-IoT-Setup-XXXX，開啟彈出頁設定 WiFi
  iot.enableProvisioning(true, "ESP-IoT-Setup", "", 180);

  // 初始化（含 WiFi 連線、心跳、WebSocket）
  if (iot.begin("1.1.0")) {
    deviceMAC = iot.getMacAddress();
    Serial.println("MAC 地址: " + deviceMAC);
    createDataStreams();
    Serial.println("\n✅ 初始化完成！");
    Serial.println("開始發送模擬數據...\n");
  } else {
    Serial.println("\n❌ 初始化失敗：WiFi 未連接");
  }
}

void loop() {
  iot.loop();

  if (!iot.isConnected()) {
    delay(500);
    return;
  }
  
  // 定時發送數據
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    sendAllSensorData();
  }
  
  delay(100);
}

void createDataStreams() {
  Serial.println("\n📝 創建 DataStream 定義...");

  for (int i = 0; i < sensorCount; i++) {
    bool success = iot.registerDatastream(
      sensors[i].pin.c_str(),
      ("ESP32-" + sensors[i].name).c_str(),
      sensors[i].minValue,
      sensors[i].maxValue,
      sensors[i].unit.c_str()
    );

    if (success) {
      Serial.println("   ✅ " + sensors[i].name + " (" + sensors[i].pin + ")");
    } else {
      Serial.println("   ⚠️  " + sensors[i].name + " - 註冊失敗");
    }

    delay(100);
  }
}

void sendAllSensorData() {
  unsigned long startTime = millis();
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.println("📊 [" + String(startTime / 1000) + "s] ESP32 發送數據：");
  
  int valueCount = 0;
  
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
    
    // 暫存數值，稍後批次發送
    values[i] = String(value, 2);
    valuePtrs[i] = values[i].c_str();
    valueCount++;
    Serial.print("   • ");
    
    Serial.print(sensors[i].name);
    Serial.print(": ");
    Serial.print(value, 2);
    Serial.println(" " + sensors[i].unit);
    
    delay(20);
  }

  // 批次送出，降低 HTTP request 次數
  bool batchSuccess = iot.sendMultiple(pins, valuePtrs, sensorCount);
  if (!batchSuccess) {
    Serial.println("⚠️  批次發送失敗");
  }
  
  unsigned long elapsed = millis() - startTime;
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  int uploadCount = batchSuccess ? sensorCount : 0;
  Serial.println("✓ 生成: " + String(valueCount) + "/" + String(sensorCount) +
                 " | 上傳: " + String(uploadCount) + "/" + String(sensorCount) +
                 " | 耗時: " + String(elapsed) + "ms\n");
}
