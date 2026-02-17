/*
 * NodeMCU (ESP8266) LED Blink Example
 * 此程式適用於 ESP8266 (NodeMCU V3/V2/V1)
 * 
 * 【標準程式碼】- 不需要修改的部分
 * 【可修改功能】- 可以根據需求調整的部分
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <stdlib.h>

// ============================================================================
// 【標準程式碼】WiFi 連線設定 - 基礎配置
// ============================================================================
const char* ssid     = "ASUS_A8_2G";           // 【可修改功能】WiFi 名稱
const char* password = "iti422utt";           // 【可修改功能】WiFi 密碼

// ============================================================================
// 【標準程式碼】OTA 更新伺服器設定
// ============================================================================
const char* otaServer = "http://192.168.50.170:5000";  // 【可修改功能】OTA 伺服器位址
String deviceMac;    // 【可修改功能】裝置 MAC 位址 (會自動取得)

// ============================================================================
// 【可修改功能】韌體版本 - 每次上傳新韌體請修改版本號
// ============================================================================
const char* FIRMWARE_VERSION = "1.0.2";  // 【可修改功能】目前韌體版本

// ============================================================================
// 【可修改功能】LED 閃爍參數設定
// ============================================================================
const int LED_PIN = D4;           // NodeMCU 內建 LED (D4 = GPIO2)
const int BLINK_ON_TIME = 500;    // 【可修改功能】LED 亮起時間 (毫秒)
const int BLINK_OFF_TIME = 500;   // 【可修改功能】LED 熄滅時間 (毫秒)

// ============================================================================
// 【可修改功能】OTA 更新檢查間隔 (毫秒)
// ============================================================================
const unsigned long OTA_CHECK_INTERVAL = 60000;   // 每 60 秒檢查一次更新
const unsigned long STATUS_REPORT_INTERVAL = 30000;  // 每 30 秒回報狀態

// ============================================================================
// 【標準程式碼】全域變數
// ============================================================================
unsigned long lastOtaCheck = 0;
unsigned long lastStatusReport = 0;
bool ledState = false;
bool updateInProgress = false;
String latestFirmwareUrl = "";

// ============================================================================
// 【標準程式碼】setup() - 初始化
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(10);
  
  Serial.println("");
  Serial.println("========================================");
  Serial.println("ESP8266 OTA LED Blink");
  Serial.println("Firmware Version: " + String(FIRMWARE_VERSION));
  Serial.println("========================================");
  
  // 初始化 LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);  // 預設熄滅 (ESP8266 低電位驅動)
  
  // 取得 MAC 位址
  deviceMac = WiFi.macAddress();
  Serial.println("Device MAC: " + deviceMac);
  
  // 連接 WiFi
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  
  // 初始狀態回報 (會檢查是否有新韌體)
  reportStatus();
}

// ============================================================================
// 【標準程式碼】loop() - 主迴圈
// ============================================================================
void loop() {
  unsigned long currentMillis = millis();
  
  // 如果正在更新韌體，跳過 LED 閃爍
  if (!updateInProgress) {
    blinkLED(currentMillis);
  }
  
  // 定時回報狀態
  if (currentMillis - lastStatusReport >= STATUS_REPORT_INTERVAL) {
    reportStatus();
    lastStatusReport = currentMillis;
  }
  
  // 定時檢查 OTA 更新
  if (currentMillis - lastOtaCheck >= OTA_CHECK_INTERVAL) {
    checkForOTA();
    lastOtaCheck = currentMillis;
  }
}

// ============================================================================
// 【可修改功能】LED 閃爍函式
// ============================================================================
/*
void blinkLED(unsigned long currentMillis) {
  static unsigned long previousMillis = 0;
  
  if (ledState == false && currentMillis - previousMillis >= BLINK_OFF_TIME) {
    ledState = true;
    digitalWrite(LED_PIN, LOW);   // 點亮 LED
    previousMillis = currentMillis;
    Serial.println("LED ON");
  }
  else if (ledState == true && currentMillis - previousMillis >= BLINK_ON_TIME) {
    ledState = false;
    digitalWrite(LED_PIN, HIGH);  // 熄滅 LED
    previousMillis = currentMillis;
    Serial.println("LED OFF");
  }
}
*/
// ============================================================================
// 【可修改功能】自訂閃爍模式 - 可替換 blinkLED()
// ============================================================================

void blinkLED(unsigned long currentMillis) {
  static unsigned long previousMillis = 0;
  
  // SOS 閃爍模式
  if (currentMillis - previousMillis >= 200) {
    static int patternIndex = 0;
    static bool ledState = false;
    
    // 短閃:200ms, 長閃:600ms, 間隔:200ms
    // 圖案: ...---... (S O S)
    int pattern[] = {200, 200, 200, 600, 200, 200, 600, 200, 200, 600, 200};
    
    digitalWrite(LED_PIN, ledState ? LOW : HIGH);
    ledState = !ledState;
    previousMillis = currentMillis;
  }
}


// ============================================================================
// 【標準程式碼】回報裝置狀態到伺服器
// ============================================================================
void reportStatus() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    
    String serverPath = String(otaServer) + "/api/update_status";
    
    http.begin(client, serverPath);
    http.addHeader("Content-Type", "application/json");
    
    String jsonPayload = "{";
    jsonPayload += "\"mac\":\"" + deviceMac + "\",";
    jsonPayload += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
    jsonPayload += "\"version\":\"" + String(FIRMWARE_VERSION) + "\",";
    jsonPayload += "\"chip_type\":\"ESP8266\"";
    jsonPayload += "}";
    
    int httpResponseCode = http.POST(jsonPayload);
    
    Serial.print("Status Report - HTTP Response: ");
    Serial.println(httpResponseCode);
    
    if (httpResponseCode == 200) {
      String response = http.getString();
      Serial.println("Server Response: " + response);
      
      // 解析回應中的韌體資訊
      // 檢查是否有 firmware.update_available == true
      if (response.indexOf("\"update_available\":true") > 0) {
        // 提取 firmware URL
        int urlStart = response.indexOf("\"url\":\"") + 7;
        int urlEnd = response.indexOf("\"", urlStart);
        if (urlStart > 6 && urlEnd > urlStart) {
          latestFirmwareUrl = String(otaServer) + response.substring(urlStart, urlEnd);
          Serial.println("New firmware available!");
          Serial.println("URL: " + latestFirmwareUrl);
          
          // 自動執行 OTA 更新
          performOTA(latestFirmwareUrl);
        }
      }
    }
    
    http.end();
  }
}

// ============================================================================
// 【標準程式碼】檢查 OTA 更新 (可選擇使用)
// ============================================================================
void checkForOTA() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    
    String checkUrl = String(otaServer) + "/api/firmware/check?chip_type=ESP8266&version=" + String(FIRMWARE_VERSION);
    
    http.begin(client, checkUrl);
    int httpCode = http.GET();
    
    if (httpCode == 200) {
      String response = http.getString();
      Serial.println("OTA Check Response: " + response);
      
      if (response.indexOf("\"update_available\":true") > 0) {
        int urlStart = response.indexOf("\"url\":\"") + 7;
        int urlEnd = response.indexOf("\"", urlStart);
        if (urlStart > 6 && urlEnd > urlStart) {
          latestFirmwareUrl = String(otaServer) + response.substring(urlStart, urlEnd);
          Serial.println("New firmware found! URL: " + latestFirmwareUrl);
          performOTA(latestFirmwareUrl);
        }
      } else {
        Serial.println("Firmware is up to date");
      }
    }
    
    http.end();
  }
}

// ============================================================================
// 【標準程式碼】執行 OTA 更新 (使用內建 Update 類別)
// ============================================================================
void performOTA(String firmwareUrl) {
  if (updateInProgress) {
    Serial.println("Update already in progress");
    return;
  }
  
  Serial.println("========================================");
  Serial.println("Starting OTA Update...");
  Serial.println("URL: " + firmwareUrl);
  Serial.println("========================================");
  
  updateInProgress = true;
  
  Serial.println("Connecting to firmware server...");
  
  WiFiClient client;
  HTTPClient http;
  http.begin(client, firmwareUrl);
  
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    int contentLength = http.getSize();
    Serial.println("Firmware size: " + String(contentLength));
    
    if (contentLength > 0) {
      bool canBegin = Update.begin(contentLength);
      
      if (canBegin) {
        Serial.println("Starting update...");
        
        size_t written = Update.writeStream(http.getStream());
        
        if (written == contentLength) {
          Serial.println("Written : " + String(written) + " successfully");
        } else {
          Serial.println("Written only : " + String(written) + "/" + String(contentLength));
        }
        
        if (Update.end(true)) {
          Serial.println("========================================");
          Serial.println("OTA Update successful! Rebooting...");
          Serial.println("========================================");
          delay(1000);
          ESP.restart();
        } else {
          Update.printError(Serial);
          Serial.println("OTA Update failed!");
          updateInProgress = false;
        }
      } else {
        Serial.println("Not enough space for OTA");
        updateInProgress = false;
      }
    }
  } else {
    Serial.println("HTTP error: " + String(httpCode));
    updateInProgress = false;
  }
  
  http.end();
}

/*
 * ============================================================================
 * 其他可修改功能範例
 * ============================================================================
 * 
 * 1. 呼吸燈效果:
 *    void breatheLED() {
 *      for (int brightness = 0; brightness <= 255; brightness++) {
 *        analogWrite(LED_PIN, brightness);
 *        delay(10);
 *      }
 *      for (int brightness = 255; brightness >= 0; brightness--) {
 *        analogWrite(LED_PIN, brightness);
 *        delay(10);
 *      }
 *    }
 * 
 * 2. 根據溫度閃爍:
 *    void tempBlink(int temperature) {
 *      int blinkCount = map(temperature, 0, 50, 1, 10);
 *      for (int i = 0; i < blinkCount; i++) {
 *        digitalWrite(LED_PIN, LOW);
 *        delay(100);
 *        digitalWrite(LED_PIN, HIGH);
 *        delay(100);
 *      }
 *    }
 * 
 * 3. WiFi 信號強度指示:
 *    void wifiStrengthIndicator() {
 *      int rssi = WiFi.RSSI();
 *      int blinkCount = map(rssi, -100, -30, 1, 5);
 *      // 閃爍次數代表信號強度
 *    }
 */
