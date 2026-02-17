#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <HTTPUpdate.h>

/**
 * ESP-IoT Manager MVP - 測試客戶端程式碼 (ESP32)
 * 功能：
 * 1. 連接 Wi-Fi 並回報狀態給 Flask 伺服器
 * 2. 每 30 秒發送心跳包
 * 3. 監聽 Serial 輸入 'U' 觸發 OTA 更新 (手動模式)
 */

// --- 請根據你的網路環境修改以下資訊 ---
const char* ssid = "YOUR_WIFI_SSID";         // 你的 WiFi 名稱
const char* password = "YOUR_WIFI_PASSWORD"; // 你的 WiFi 密碼
const char* server_ip = "192.168.1.100";     // 你的電腦 IP (請在終端機輸入 ipconfig 查看 IPv4 位址)
const int server_port = 5000;                // Flask 預設 Port
const char* current_version = "1.0.0";       // 當前設備版本
// -------------------------------------

const char* chip_type = "esp32";
String mac_addr;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("
--- ESP-IoT Manager Client Starting ---");

  // 連接 Wi-Fi
  Serial.printf("Connecting to %s...", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("
WiFi Connected!");
  
  mac_addr = WiFi.macAddress();
  Serial.print("Local IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("MAC Address: ");
  Serial.println(mac_addr);

  // 初始化時回報一次狀態
  reportStatus();
  
  Serial.println("
指令提示：");
  Serial.println("- 輸入 'U' 觸發 OTA 更新流程");
  Serial.println("- 每 30 秒自動發送心跳更新狀態");
}

void loop() {
  static unsigned long last_report = 0;
  
  // 每 30 秒回報一次心跳 (避免 Web 介面顯示設備離線)
  if (millis() - last_report > 30000) {
    reportStatus();
    last_report = millis();
  }

  // 監聽 Serial 視窗輸入
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'U' || c == 'u') {
      Serial.println("
[OTA] Manual Trigger Detected. Checking update...");
      // 在 MVP 階段，我們假設伺服器上有一個名為 firmware.bin 的檔案
      startOTA("firmware.bin"); 
    }
  }
}

// 向 Flask 伺服器回報目前設備狀態 (API: /api/update_status)
void reportStatus() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    // 注意：這裡的路徑包含了 Blueprints 中定義的 /api 前綴
    String url = "http://" + String(server_ip) + ":" + String(server_port) + "/api/update_status";
    
    Serial.print("[HTTP] Reporting status to ");
    Serial.println(url);

    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    // 建立 JSON 物件 (需要安裝 ArduinoJson 函式庫)
    StaticJsonDocument<200> doc;
    doc["mac"] = mac_addr;
    doc["ip"] = WiFi.localIP().toString();
    doc["version"] = current_version;
    doc["chip_type"] = chip_type;

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    int httpResponseCode = http.POST(jsonPayload);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.printf("[HTTP] Success (Code: %d): %s
", httpResponseCode, response.c_str());
    } else {
      Serial.printf("[HTTP] Error (Code: %d)
", httpResponseCode);
    }
    http.end();
  }
}

// 執行 OTA 更新 (API: /api/ota/<filename>)
void startOTA(String filename) {
  String url = "http://" + String(server_ip) + ":" + String(server_port) + "/api/ota/" + filename;
  Serial.printf("[OTA] Connecting to %s
", url.c_str());

  // httpUpdate 會處理下載、驗證與自動重啟
  // 記得將 ESP32 開發板設定中的 Flash Size 設定正確
  t_httpUpdate_return ret = httpUpdate.update(url);

  switch (ret) {
    case HTTP_UPDATE_FAILED:
      Serial.printf("[OTA] FAILED. Error (%d): %s
", httpUpdate.getLastError(), httpUpdate.getLastErrorString().c_str());
      break;
    case HTTP_UPDATE_NO_UPDATES:
      Serial.println("[OTA] No updates available (Same version or server error).");
      break;
    case HTTP_UPDATE_OK:
      Serial.println("[OTA] SUCCESS. Device will reboot now.");
      break;
  }
}
