#include <ESP_IoT_Manager.h>

/*
 * RemoteControlMQTT
 *
 * 目標：
 * - 不硬編碼 WiFi（使用 Captive Portal）
 * - 透過 mapControlPin 直接完成控制輸出，避免手寫 topic parser
 * - 支援 dashboard 發送重啟命令（system/reboot）
 */

const char* serverIP = "192.168.50.170";  // Flask server
const int serverPort = 5000;

const char* mqttHost = "192.168.50.170";  // MQTT broker
const uint16_t mqttPort = 1883;

ESP_IoT_Manager iot(serverIP, serverPort);

// 依你的板子調整 GPIO
const int LED_PIN = 2;
const int PWM_PIN = 5;

void onSystemCommand(String action, String payload) {
  Serial.printf("[SYSTEM] action=%s payload=%s\n", action.c_str(), payload.c_str());
  if (action == "reboot") {
    delay(100);
#ifdef ESP32
    ESP.restart();
#else
    ESP.reset();
#endif
  }
}

// 可選：如果你還想對某些 pin 做自訂邏輯，可保留此 callback
void onControl(String pin, String value) {
  Serial.printf("[CONTROL] %s = %s\n", pin.c_str(), value.c_str());
}

void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  pinMode(PWM_PIN, OUTPUT);

  // 啟用手機引導配網（首次上電）
  iot.enableProvisioning(true, "ESP-IoT-Setup", "", 180);

  if (!iot.begin("1.2.0")) {
    Serial.println("[INIT] failed");
    return;
  }

  // 啟用 MQTT 遠端控制
  iot.enableRemoteControl(true, mqttHost, mqttPort);

  // 以 Virtual Pin 映射硬體輸出，避免使用者手寫解析
  iot.mapControlPin("V10", LED_PIN, OUTPUT_DIGITAL);      // 0/1 或 ON/OFF
  iot.mapControlPin("V11", PWM_PIN, OUTPUT_PWM, 0, 1023); // PWM 範圍

  // 可選回調
  iot.onControlMessage(onControl);
  iot.onSystemCommand(onSystemCommand);

  // 註冊到 dashboard datastream
  iot.registerDatastream("V10", "LED Switch", 0, 1, "state", "integer");
  iot.registerDatastream("V11", "LED PWM", 0, 1023, "duty", "integer");

  Serial.println("[INIT] RemoteControlMQTT ready");
}

void loop() {
  iot.loop();

  // 範例：定期回報類比值
  static unsigned long lastReport = 0;
  if (millis() - lastReport > 5000) {
    lastReport = millis();

#ifdef ESP32
    int adc = analogRead(34);
#else
    int adc = analogRead(A0);
#endif
    iot.sendData("V0", adc);
  }
}
