#include "ESP_IoT_Manager.h"

ESP_IoT_Manager* ESP_IoT_Manager::_instance = nullptr;

ESP_IoT_Manager::ESP_IoT_Manager(const char* ssid, const char* password, const char* serverIP, int serverPort)
    : _mqttClient(_mqttWiFiClient) {
    _ssid = ssid;
    _password = password;
    _serverIP = serverIP;
    _serverPort = serverPort;
    _lastHeartbeat = 0;
    _heartbeatInterval = 30000;  // 30 秒
    _lastWiFiRetry = 0;
    _wifiRetryInterval = 10000;  // 10 秒
    _controlCallback = nullptr;
    _wsConnected = false;
    _useProvisioning = false;
    _apNamePrefix = "ESP-IoT-Setup";
    _apPassword = "";
    _portalTimeoutSec = 180;
    _instance = this;
    _remoteControlEnabled = false;
    _mqttHost = serverIP ? String(serverIP) : String("127.0.0.1");
    _mqttPort = 1883;
    _lastMqttRetry = 0;
    _mqttRetryInterval = 5000;
    _controlMappingCount = 0;
    _systemCallback = nullptr;
    
#ifdef ESP32
    _chipType = "ESP32";
#else
    _chipType = "ESP8266";
#endif
}

ESP_IoT_Manager::ESP_IoT_Manager(const char* serverIP, int serverPort)
    : ESP_IoT_Manager(nullptr, nullptr, serverIP, serverPort) {}

bool ESP_IoT_Manager::begin(const char* deviceVersion) {
    Serial.begin(115200);
    delay(1000);
    
    _deviceVersion = deviceVersion;
    
    Serial.println("\n=== ESP-IoT Manager Starting ===");
    Serial.printf("Version: %s\n", _deviceVersion.c_str());
    Serial.printf("Chip: %s\n", _chipType.c_str());
    
    // 連接 WiFi
    if (!connectWiFi()) {
        return false;
    }
    
    _macAddress = WiFi.macAddress();
    Serial.printf("MAC: %s\n", _macAddress.c_str());
    Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
    
    // 初次回報狀態
    if (!reportStatus()) {
        Serial.println("[WARNING] Failed to report initial status");
    }
    
    // 初始化 WebSocket（Phase 3 即時控制用）
    _webSocket.begin(_serverIP, _serverPort, "/ws");
    _webSocket.onEvent([](WStype_t type, uint8_t* payload, size_t length) {
        if (_instance) {
            _instance->handleWebSocketEvent(type, payload, length);
        }
    });
    _webSocket.setReconnectInterval(5000);

    // 初始化 MQTT 控制
    _mqttClient.setServer(_mqttHost.c_str(), _mqttPort);
    _mqttClient.setCallback([](char* topic, byte* payload, unsigned int length) {
        if (_instance) {
            _instance->handleMqttMessage(topic, payload, length);
        }
    });
    
    Serial.println("=== Initialization Complete ===\n");
    return true;
}

void ESP_IoT_Manager::loop() {
    // 維持 WiFi 連線（非阻塞）
    if (WiFi.status() != WL_CONNECTED) {
        if (millis() - _lastWiFiRetry > _wifiRetryInterval) {
            _lastWiFiRetry = millis();
            Serial.println("[WiFi] Disconnected, retrying...");
            WiFi.reconnect();
        }
        return;
    }

    // 處理 WebSocket
    _webSocket.loop();

    // 處理 MQTT 控制
    if (_remoteControlEnabled) {
        ensureMqttConnection();
        _mqttClient.loop();
    }
    
    // 定期心跳
    if (millis() - _lastHeartbeat > _heartbeatInterval) {
        reportStatus();
        _lastHeartbeat = millis();
    }
}

void ESP_IoT_Manager::enableProvisioning(
    bool enable,
    const char* apNamePrefix,
    const char* apPassword,
    uint16_t portalTimeoutSec
) {
    _useProvisioning = enable;
    _apNamePrefix = apNamePrefix ? apNamePrefix : "ESP-IoT-Setup";
    _apPassword = apPassword ? apPassword : "";
    _portalTimeoutSec = portalTimeoutSec;
}

void ESP_IoT_Manager::setWiFiCredentials(const char* ssid, const char* password) {
    _ssid = ssid;
    _password = password;
}

void ESP_IoT_Manager::clearWiFiCredentials() {
    WiFiManager wm;
    wm.resetSettings();
    Serial.println("[WiFi] Cleared saved WiFi settings");
}

bool ESP_IoT_Manager::connectWiFi() {
    WiFi.mode(WIFI_STA);

    if (_useProvisioning) {
        WiFiManager wm;
        wm.setConfigPortalTimeout(_portalTimeoutSec);

        String apName = _apNamePrefix;
        String mac = WiFi.macAddress();
        mac.replace(":", "");
        if (mac.length() >= 4) {
            apName += "-" + mac.substring(mac.length() - 4);
        }

        Serial.printf("[WiFi] Starting provisioning portal: %s\n", apName.c_str());
        bool connected = false;
        if (_apPassword.length() >= 8) {
            connected = wm.autoConnect(apName.c_str(), _apPassword.c_str());
        } else {
            connected = wm.autoConnect(apName.c_str());
        }

        if (connected && WiFi.status() == WL_CONNECTED) {
            Serial.println("[WiFi] Provisioning success");
            return true;
        }

        Serial.println("[WiFi] Provisioning timeout or failed");
        return false;
    }

    if (_ssid == nullptr || _ssid[0] == '\0') {
        Serial.println("[WiFi] SSID is empty and provisioning is disabled");
        return false;
    }

    Serial.printf("Connecting to %s...", _ssid);
    WiFi.begin(_ssid, _password);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(" Connected!");
        return true;
    } else {
        Serial.println(" Failed!");
        return false;
    }
}

bool ESP_IoT_Manager::reportStatus() {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    StaticJsonDocument<256> doc;
    doc["mac"] = _macAddress;
    doc["ip"] = WiFi.localIP().toString();
    doc["version"] = _deviceVersion;
    doc["chip_type"] = _chipType;
    
    String payload;
    serializeJson(doc, payload);

    int httpCode = 0;
    bool success = httpPostJson("/api/update_status", payload, &httpCode, nullptr);

    if (success) {
        Serial.printf("[HTTP] Status reported (Code: %d)\n", httpCode);
    } else {
        Serial.printf("[HTTP] Failed (Code: %d)\n", httpCode);
    }
    return success;
}

// Blynk 相容 API - 發送數據
bool ESP_IoT_Manager::sendData(const char* pin, float value) {
    String val = String(value, 2);
    return sendData(pin, val.c_str());
}

bool ESP_IoT_Manager::sendData(const char* pin, int value) {
    String val = String(value);
    return sendData(pin, val.c_str());
}

bool ESP_IoT_Manager::sendData(const char* pin, const char* value) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    String path = "/blynk/" + _macAddress + "/update/" + String(pin) + "?value=" + String(value);
    int httpCode = 0;
    bool success = httpGet(path, &httpCode, nullptr);

    if (success) {
        Serial.printf("[DATA] Sent %s=%s\n", pin, value);
    } else {
        Serial.printf("[DATA] Failed to send %s (Code: %d)\n", pin, httpCode);
    }
    return success;
}

bool ESP_IoT_Manager::sendMultiple(const char* pins[], const char* values[], int count) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    String path = "/blynk/" + _macAddress + "/update?";

    for (int i = 0; i < count; i++) {
        if (i > 0) path += "&";
        path += String(pins[i]) + "=" + String(values[i]);
    }

    int httpCode = 0;
    return httpGet(path, &httpCode, nullptr);
}

bool ESP_IoT_Manager::registerDatastream(
    const char* pin,
    const char* name,
    float minValue,
    float maxValue,
    const char* unit,
    const char* dataType
) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    StaticJsonDocument<320> doc;
    doc["device_mac"] = _macAddress;
    doc["pin"] = pin;
    doc["name"] = name;
    doc["data_type"] = dataType;
    doc["min"] = minValue;
    doc["max"] = maxValue;
    doc["unit"] = unit;

    String payload;
    serializeJson(doc, payload);

    int httpCode = 0;
    bool success = httpPostJson("/blynk/admin/datastream", payload, &httpCode, nullptr);

    if (success) {
        Serial.printf("[DATASTREAM] Registered %s (%s)\n", name, pin);
    } else {
        Serial.printf("[DATASTREAM] Failed %s (Code: %d)\n", pin, httpCode);
    }

    return success;
}

void ESP_IoT_Manager::onControlMessage(void (*callback)(String pin, String value)) {
    _controlCallback = callback;
}

void ESP_IoT_Manager::onSystemCommand(void (*callback)(String action, String payload)) {
    _systemCallback = callback;
}

void ESP_IoT_Manager::enableRemoteControl(bool enable, const char* mqttHost, uint16_t mqttPort) {
    _remoteControlEnabled = enable;
    if (mqttHost != nullptr && mqttHost[0] != '\0') {
        _mqttHost = mqttHost;
    }
    if (mqttPort > 0) {
        _mqttPort = mqttPort;
    }
    _mqttClient.setServer(_mqttHost.c_str(), _mqttPort);
}

void ESP_IoT_Manager::setMqttServer(const char* mqttHost, uint16_t mqttPort) {
    if (mqttHost != nullptr && mqttHost[0] != '\0') {
        _mqttHost = mqttHost;
    }
    if (mqttPort > 0) {
        _mqttPort = mqttPort;
    }
    _mqttClient.setServer(_mqttHost.c_str(), _mqttPort);
}

void ESP_IoT_Manager::mapControlPin(const char* virtualPin, uint8_t gpio, uint8_t mode, int minValue, int maxValue) {
    if (virtualPin == nullptr || virtualPin[0] == '\0') {
        return;
    }

    for (int i = 0; i < _controlMappingCount; i++) {
        if (_controlMappings[i].virtualPin.equalsIgnoreCase(virtualPin)) {
            _controlMappings[i].gpio = gpio;
            _controlMappings[i].mode = mode;
            _controlMappings[i].minValue = minValue;
            _controlMappings[i].maxValue = maxValue;
            pinMode(gpio, OUTPUT);
            return;
        }
    }

    if (_controlMappingCount >= MAX_CONTROL_MAPPINGS) {
        Serial.println("[CTRL] Max mapping count reached");
        return;
    }

    _controlMappings[_controlMappingCount].virtualPin = virtualPin;
    _controlMappings[_controlMappingCount].gpio = gpio;
    _controlMappings[_controlMappingCount].mode = mode;
    _controlMappings[_controlMappingCount].minValue = minValue;
    _controlMappings[_controlMappingCount].maxValue = maxValue;
    _controlMappingCount++;

    pinMode(gpio, OUTPUT);
}

void ESP_IoT_Manager::clearControlPinMappings() {
    _controlMappingCount = 0;
}

void ESP_IoT_Manager::handleWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("[WS] Disconnected");
            _wsConnected = false;
            break;
            
        case WStype_CONNECTED:
            Serial.println("[WS] Connected");
            _wsConnected = true;
            // 發送認證訊息
            _webSocket.sendTXT("{\"type\":\"auth\",\"mac\":\"" + _macAddress + "\"}");
            break;
            
        case WStype_TEXT:
            Serial.printf("[WS] Received: %s\n", payload);
            
            // 解析控制指令
            if (_controlCallback) {
                StaticJsonDocument<256> doc;
                DeserializationError error = deserializeJson(doc, payload, length);
                
                if (!error && doc.containsKey("pin") && doc.containsKey("value")) {
                    String pin = doc["pin"].as<String>();
                    String value = doc["value"].as<String>();
                    _controlCallback(pin, value);
                }
            }
            break;
    }
}

void ESP_IoT_Manager::checkOTA() {
    String url = buildUrl("/api/ota/firmware.bin");
    Serial.printf("[OTA] Checking update from %s\n", url.c_str());
    
#ifdef ESP32
    t_httpUpdate_return ret = httpUpdate.update(url);
#else
    WiFiClient client;
    t_httpUpdate_return ret = ESPhttpUpdate.update(client, url);
#endif
    
    switch (ret) {
        case HTTP_UPDATE_FAILED:
            Serial.println("[OTA] Update failed");
            break;
        case HTTP_UPDATE_NO_UPDATES:
            Serial.println("[OTA] No updates available");
            break;
        case HTTP_UPDATE_OK:
            Serial.println("[OTA] Update successful, rebooting...");
            break;
    }
}

void ESP_IoT_Manager::ensureMqttConnection() {
    if (!_remoteControlEnabled) {
        return;
    }

    if (_mqttClient.connected()) {
        return;
    }

    if (millis() - _lastMqttRetry < _mqttRetryInterval) {
        return;
    }
    _lastMqttRetry = millis();

    String clientId = "esp-iot-" + _macAddress;
    clientId.replace(":", "");

    Serial.printf("[MQTT] Connecting to %s:%d ...\n", _mqttHost.c_str(), _mqttPort);
    if (!_mqttClient.connect(clientId.c_str())) {
        Serial.printf("[MQTT] Connect failed rc=%d\n", _mqttClient.state());
        return;
    }

    String controlTopic = "devices/" + _macAddress + "/control/+";
    bool ok = _mqttClient.subscribe(controlTopic.c_str(), 1);
    if (ok) {
        Serial.printf("[MQTT] Subscribed %s\n", controlTopic.c_str());
        publishControlAck("connected", "remote control online");
    } else {
        Serial.printf("[MQTT] Subscribe failed %s\n", controlTopic.c_str());
    }
}

void ESP_IoT_Manager::handleMqttMessage(char* topic, byte* payload, unsigned int length) {
    String topicStr = topic ? String(topic) : String();
    String payloadStr;
    payloadStr.reserve(length + 1);
    for (unsigned int i = 0; i < length; i++) {
        payloadStr += (char)payload[i];
    }

    handleControlTopic(topicStr, payloadStr);
}

void ESP_IoT_Manager::handleControlTopic(const String& topic, const String& payload) {
    String prefix = "devices/" + _macAddress + "/control/";
    if (!topic.startsWith(prefix)) {
        return;
    }

    String controlPin = topic.substring(prefix.length());
    Serial.printf("[CTRL] %s = %s\n", controlPin.c_str(), payload.c_str());

    if (controlPin.equalsIgnoreCase("system")) {
        StaticJsonDocument<192> doc;
        DeserializationError err = deserializeJson(doc, payload);
        if (err) {
            publishControlAck("error", "invalid system payload");
            return;
        }

        String action = doc["action"] | "";
        if (action.length() == 0) {
            publishControlAck("error", "system action missing");
            return;
        }

        if (_systemCallback) {
            _systemCallback(action, payload);
        } else {
            if (action.equalsIgnoreCase("reboot")) {
                publishControlAck("reboot", "restarting");
                delay(150);
#ifdef ESP32
                ESP.restart();
#else
                ESP.reset();
#endif
            }
        }
        return;
    }

    bool mapped = applyMappedControl(controlPin, payload);
    if (_controlCallback) {
        _controlCallback(controlPin, payload);
    }

    if (mapped || _controlCallback != nullptr) {
        publishControlAck("ok", controlPin + "=" + payload);
    } else {
        publishControlAck("warn", "unhandled control pin " + controlPin);
    }
}

bool ESP_IoT_Manager::applyMappedControl(const String& pin, const String& value) {
    for (int i = 0; i < _controlMappingCount; i++) {
        if (!_controlMappings[i].virtualPin.equalsIgnoreCase(pin)) {
            continue;
        }

        int gpio = _controlMappings[i].gpio;
        uint8_t mode = _controlMappings[i].mode;
        int numeric = value.toInt();

        if (mode == OUTPUT_PWM) {
#ifdef ESP32
            int pwm = constrain(numeric, _controlMappings[i].minValue, _controlMappings[i].maxValue);
            int duty = map(pwm, _controlMappings[i].minValue, _controlMappings[i].maxValue, 0, 255);
            analogWrite(gpio, duty);
#else
            int pwm = constrain(numeric, _controlMappings[i].minValue, _controlMappings[i].maxValue);
            analogWrite(gpio, pwm);
#endif
        } else {
            bool isOn = (numeric > 0) || value.equalsIgnoreCase("ON") || value.equalsIgnoreCase("HIGH") || value.equalsIgnoreCase("true");
            digitalWrite(gpio, isOn ? HIGH : LOW);
        }
        return true;
    }

    return false;
}

void ESP_IoT_Manager::publishControlAck(const String& event, const String& message) {
    if (!_mqttClient.connected()) {
        return;
    }

    String topic = "devices/" + _macAddress + "/status";
    StaticJsonDocument<192> doc;
    doc["event"] = event;
    doc["message"] = message;
    doc["ip"] = WiFi.localIP().toString();
    doc["version"] = _deviceVersion;
    doc["online"] = true;

    String payload;
    serializeJson(doc, payload);
    _mqttClient.publish(topic.c_str(), payload.c_str(), false);
}

String ESP_IoT_Manager::buildUrl(const String& path) {
    return "http://" + String(_serverIP) + ":" + String(_serverPort) + path;
}

bool ESP_IoT_Manager::httpGet(const String& path, int* code, String* response) {
    HTTPClient http;
    String url = buildUrl(path);

#ifdef ESP32
    http.begin(url);
#else
    WiFiClient client;
    http.begin(client, url);
#endif

    http.setTimeout(5000);
    int httpCode = http.GET();

    if (response != nullptr && httpCode > 0) {
        *response = http.getString();
    }
    if (code != nullptr) {
        *code = httpCode;
    }

    http.end();
    return httpCode >= 200 && httpCode < 300;
}

bool ESP_IoT_Manager::httpPostJson(const String& path, const String& body, int* code, String* response) {
    HTTPClient http;
    String url = buildUrl(path);

#ifdef ESP32
    http.begin(url);
#else
    WiFiClient client;
    http.begin(client, url);
#endif

    http.setTimeout(5000);
    http.addHeader("Content-Type", "application/json");
    int httpCode = http.POST(body);

    if (response != nullptr && httpCode > 0) {
        *response = http.getString();
    }
    if (code != nullptr) {
        *code = httpCode;
    }

    http.end();
    return httpCode >= 200 && httpCode < 300;
}

bool ESP_IoT_Manager::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

bool ESP_IoT_Manager::isRemoteControlEnabled() {
    return _remoteControlEnabled;
}

String ESP_IoT_Manager::getMacAddress() {
    return _macAddress;
}

String ESP_IoT_Manager::getLocalIP() {
    return WiFi.localIP().toString();
}
