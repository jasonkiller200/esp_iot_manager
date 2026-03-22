#include <ESP_IoT_Manager.h>

/**
 * ESP-IoT Manager - 測試客戶端程式碼 (ESP32)
 * 功能：
 * 1. 透過手機引導配網（Captive Portal）設定 WiFi
 * 2. 由 library 自動回報狀態與維持連線
 * 3. 監聽 Serial 輸入 'U' 觸發 OTA 更新
 */

// --- 伺服器設定 ---
const char* serverIP = "192.168.1.100";  // 你的電腦 IP
const int serverPort = 5000;               // Flask 預設 Port
const char* currentVersion = "1.1.0";
// -----------------

ESP_IoT_Manager iot(serverIP, serverPort);

unsigned long lastSend = 0;
const unsigned long sendInterval = 10000;

void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.println();
  Serial.println("=== ESP-IoT Manager Client Starting (ESP32) ===");

  // 啟用手機引導配網：首次上電會開 AP 讓手機填入 WiFi
  iot.enableProvisioning(true, "ESP-IoT-Setup", "", 180);

  if (!iot.begin(currentVersion)) {
    Serial.println("[INIT] Failed to start. Please reboot and run provisioning again.");
    return;
  }

  Serial.print("[INIT] MAC: ");
  Serial.println(iot.getMacAddress());
  Serial.print("[INIT] IP: ");
  Serial.println(iot.getLocalIP());

  // 建立一個簡單的 Datastream 供測試
  iot.registerDatastream("V0", "ESP32-RSSI", -100.0, 0.0, "dBm");

  Serial.println();
  Serial.println("指令提示:");
  Serial.println("- 輸入 'U' 觸發 OTA 更新流程");
  Serial.println("- 每 10 秒上傳一次 RSSI 到 V0");
}

void loop() {
  iot.loop();

  if (iot.isConnected() && millis() - lastSend >= sendInterval) {
    lastSend = millis();

    int rssi = WiFi.RSSI();
    bool ok = iot.sendData("V0", rssi);
    Serial.printf("[DATA] RSSI=%d dBm (%s)\n", rssi, ok ? "OK" : "FAIL");
  }

  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'U' || c == 'u') {
      Serial.println("[OTA] Manual trigger detected. Checking update...");
      iot.checkOTA();
    }
  }

  delay(30);
}
