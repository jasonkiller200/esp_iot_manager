#include "ESP_IoT_Manager.h"

ESP_IoT_Manager* ESP_IoT_Manager::_instance = nullptr;

ESP_IoT_Manager::ESP_IoT_Manager(const char* ssid, const char* password, const char* serverIP, int serverPort) {
    _ssid = ssid;
    _password = password;
    _serverIP = serverIP;
    _serverPort = serverPort;
    _lastHeartbeat = 0;
    _heartbeatInterval = 30000;  // 30 秒
    _controlCallback = nullptr;
    _wsConnected = false;
    _instance = this;
    
#ifdef ESP32
    _chipType = "ESP32";
#else
    _chipType = "ESP8266";
#endif
}

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
    
    Serial.println("=== Initialization Complete ===\n");
    return true;
}

void ESP_IoT_Manager::loop() {
    // 處理 WebSocket
    _webSocket.loop();
    
    // 定期心跳
    if (millis() - _lastHeartbeat > _heartbeatInterval) {
        reportStatus();
        _lastHeartbeat = millis();
    }
}

bool ESP_IoT_Manager::connectWiFi() {
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
    
    HTTPClient http;
    String url = "http://" + String(_serverIP) + ":" + String(_serverPort) + "/api/update_status";
    
#ifdef ESP32
    http.begin(url);
#else
    WiFiClient client;
    http.begin(client, url);
#endif
    
    http.addHeader("Content-Type", "application/json");
    
    StaticJsonDocument<256> doc;
    doc["mac"] = _macAddress;
    doc["ip"] = WiFi.localIP().toString();
    doc["version"] = _deviceVersion;
    doc["chip_type"] = _chipType;
    
    String payload;
    serializeJson(doc, payload);
    
    int httpCode = http.POST(payload);
    bool success = (httpCode > 0);
    
    if (success) {
        Serial.printf("[HTTP] Status reported (Code: %d)\n", httpCode);
    } else {
        Serial.printf("[HTTP] Failed (Code: %d)\n", httpCode);
    }
    
    http.end();
    return success;
}

// Blynk 相容 API - 發送數據
bool ESP_IoT_Manager::sendData(const char* pin, float value) {
    return sendData(pin, String(value, 2).c_str());
}

bool ESP_IoT_Manager::sendData(const char* pin, int value) {
    return sendData(pin, String(value).c_str());
}

bool ESP_IoT_Manager::sendData(const char* pin, const char* value) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    HTTPClient http;
    String url = "http://" + String(_serverIP) + ":" + String(_serverPort) + 
                 "/blynk/" + _macAddress + "/update/" + String(pin) + 
                 "?value=" + String(value);
    
#ifdef ESP32
    http.begin(url);
#else
    WiFiClient client;
    http.begin(client, url);
#endif
    
    int httpCode = http.GET();
    bool success = (httpCode == 200);
    
    if (success) {
        Serial.printf("[DATA] Sent %s=%s\n", pin, value);
    } else {
        Serial.printf("[DATA] Failed to send %s (Code: %d)\n", pin, httpCode);
    }
    
    http.end();
    return success;
}

bool ESP_IoT_Manager::sendMultiple(const char* pins[], const char* values[], int count) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    HTTPClient http;
    String url = "http://" + String(_serverIP) + ":" + String(_serverPort) + 
                 "/blynk/" + _macAddress + "/update?";
    
    for (int i = 0; i < count; i++) {
        if (i > 0) url += "&";
        url += String(pins[i]) + "=" + String(values[i]);
    }
    
#ifdef ESP32
    http.begin(url);
#else
    WiFiClient client;
    http.begin(client, url);
#endif
    
    int httpCode = http.GET();
    bool success = (httpCode == 200);
    
    http.end();
    return success;
}

void ESP_IoT_Manager::onControlMessage(void (*callback)(String pin, String value)) {
    _controlCallback = callback;
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
    String url = "http://" + String(_serverIP) + ":" + String(_serverPort) + "/api/ota/firmware.bin";
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

bool ESP_IoT_Manager::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

String ESP_IoT_Manager::getMacAddress() {
    return _macAddress;
}

String ESP_IoT_Manager::getLocalIP() {
    return WiFi.localIP().toString();
}
