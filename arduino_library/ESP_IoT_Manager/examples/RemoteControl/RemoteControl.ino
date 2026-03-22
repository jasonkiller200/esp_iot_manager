#include <ESP_IoT_Manager.h>

/*
 * RemoteControl (modular version)
 *
 * 與 RemoteControlMQTT 相同採用模組化方式：
 * - 手機配網
 * - mapControlPin 映射輸出
 * - system/reboot 指令
 */

const char* serverIP = "192.168.1.100";
const int serverPort = 5000;

const char* mqttHost = "192.168.1.100";
const uint16_t mqttPort = 1883;

ESP_IoT_Manager iot(serverIP, serverPort);

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

void onControl(String pin, String value) {
  Serial.printf("[CONTROL] %s = %s\n", pin.c_str(), value.c_str());
}

void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(PWM_PIN, OUTPUT);

  iot.enableProvisioning(true, "ESP-IoT-Setup", "", 180);

  if (!iot.begin("1.2.0")) {
    Serial.println("[INIT] failed");
    return;
  }

  iot.enableRemoteControl(true, mqttHost, mqttPort);

  iot.mapControlPin("V10", LED_PIN, OUTPUT_DIGITAL);      // 0/1 or ON/OFF
  iot.mapControlPin("V11", PWM_PIN, OUTPUT_PWM, 0, 1023); // PWM

  iot.onControlMessage(onControl);
  iot.onSystemCommand(onSystemCommand);

  iot.registerDatastream("V10", "LED Switch", 0, 1, "state", "integer");
  iot.registerDatastream("V11", "LED PWM", 0, 1023, "duty", "integer");

  Serial.println("Device ready for modular remote control");
}

void loop() {
  iot.loop();

  static unsigned long lastReport = 0;
  if (millis() - lastReport > 5000) {
    lastReport = millis();
    iot.sendData("V0", digitalRead(LED_PIN));
  }
}
