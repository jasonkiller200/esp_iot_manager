#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP8266httpUpdate.h>

/**
 * ESP-IoT Manager MVP - 測試客戶端程式碼 (ESP8266 / NodeMCU)
 * 功能：
 * 1. 連接 Wi-Fi 並回報狀態給 Flask 伺服器
 * 2. 每 30 秒發送心跳包
 * 3. 自動檢查並執行 OTA 更新
 */

// --- 請根據你的網路環境修改以下資訊 ---
const char* ssid = "ASUS_A8_2G";         // 你的 WiFi 名稱
const char* password = "iti422utt";      // 你的 WiFi 密碼
const char* server_ip = "192.168.50.170"; // 你的電腦 IP
const int server_port = 5000;             // Flask 預設 Port
const char* current_version = "1.0.0";    // 當前設備版本
// -------------------------------------

const char* chip_type = "ESP8266";
String mac_addr;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=== ESP-IoT Manager Client Starting (ESP8266) ===");

  // 連接 Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  
  mac_addr = WiFi.macAddress();
  Serial.print("Local IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("MAC Address: ");
  Serial.println(mac_addr);
  Serial.print("Current Version: ");
  Serial.println(current_version);

  // 初始化時回報一次狀態
  reportStatus();
}

void loop() {
  static unsigned long last_report = 0;
  
  // 每 30 秒回報一次心跳
  if (millis() - last_report > 30000) {
    reportStatus();
    last_report = millis();
  }
}

// 向 Flask 伺服器回報目前設備狀態
void reportStatus() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    String url = "http://" + String(server_ip) + ":" + String(server_port) + "/api/update_status";
    
    Serial.print("\n[HTTP] Reporting status to ");
    Serial.println(url);

    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<300> doc;
    doc["mac"] = mac_addr;
    doc["ip"] = WiFi.localIP().toString();
    doc["version"] = current_version;
    doc["chip_type"] = chip_type;

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    int httpResponseCode = http.POST(jsonPayload);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.printf("[HTTP] Success (Code: %d): %s\n", httpResponseCode, response.c_str());
      
      // 解析伺服器回應，檢查是否有韌體更新
      parseServerResponse(response);
    } else {
      Serial.printf("[HTTP] Error (Code: %d)\n", httpResponseCode);
    }
    http.end();
  }
}

// 解析伺服器回應，檢查是否有強制更新
void parseServerResponse(String response) {
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, response);
  
  if (error) {
    Serial.println("[JSON] Parse error");
    return;
  }
  
  // 檢查 firmware 是否有更新
  if (doc.containsKey("firmware")) {
    JsonObject firmware = doc["firmware"];
    
    // 檢查是否有 update_available 且為 true
    if (firmware.containsKey("update_available")) {
      bool updateAvail = firmware["update_available"].as<bool>();
      
      if (updateAvail) {
        const char* fwUrl = firmware["url"].as<const char*>();
        const char* fwVersion = firmware["version"].as<const char*>();
        
        Serial.println("[OTA] New firmware available!");
        Serial.print("[OTA] Version: ");
        Serial.println(fwVersion);
        Serial.print("[OTA] URL: ");
        Serial.println(fwUrl);
        
        // 執行 OTA 更新
        startOTA(fwUrl);
        return;
      }
    }
    Serial.println("[OTA] Firmware is up to date");
  } else {
    Serial.println("[INFO] No firmware data in response");
  }
}

// 執行 OTA 更新
void startOTA(const char* filename) {
  // 確保 URL 包含完整路徑
  String url;
  if (String(filename).startsWith("http")) {
    url = String(filename);
  } else {
    url = "http://" + String(server_ip) + ":" + String(server_port) + String(filename);
  }
  
  Serial.printf("[OTA] Connecting to %s\n", url.c_str());

  WiFiClient client;
  t_httpUpdate_return ret = ESPhttpUpdate.update(client, url);

  switch (ret) {
    case HTTP_UPDATE_FAILED:
      Serial.printf("[OTA] FAILED. Error (%d): %s\n", ESPhttpUpdate.getLastError(), ESPhttpUpdate.getLastErrorString().c_str());
      break;
    case HTTP_UPDATE_NO_UPDATES:
      Serial.println("[OTA] No updates available.");
      break;
    case HTTP_UPDATE_OK:
      Serial.println("[OTA] SUCCESS. Device will reboot now.");
      break;
  }
}
