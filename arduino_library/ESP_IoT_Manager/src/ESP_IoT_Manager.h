#ifndef ESP_IOT_MANAGER_H
#define ESP_IOT_MANAGER_H

#include <Arduino.h>

#ifdef ESP32
  #include <WiFi.h>
  #include <HTTPClient.h>
  #include <HTTPUpdate.h>
  #include <WebSocketsClient.h>
#else
  #include <ESP8266WiFi.h>
  #include <ESP8266HTTPClient.h>
  #include <ESP8266httpUpdate.h>
  #include <WebSocketsClient.h>
#endif

#include <ArduinoJson.h>
#include <WiFiManager.h>
#include <PubSubClient.h>

#define OUTPUT_DIGITAL 0
#define OUTPUT_PWM 1

class ESP_IoT_Manager {
public:
    // 建構函式
    ESP_IoT_Manager(const char* ssid, const char* password, const char* serverIP, int serverPort = 5000);
    ESP_IoT_Manager(const char* serverIP, int serverPort = 5000);
    
    // 初始化連線
    bool begin(const char* deviceVersion = "1.0.0");

    // 啟用配網引導（Captive Portal）
    void enableProvisioning(
        bool enable = true,
        const char* apNamePrefix = "ESP-IoT-Setup",
        const char* apPassword = nullptr,
        uint16_t portalTimeoutSec = 180
    );

    // 動態設定 WiFi 帳密（可與配網併用）
    void setWiFiCredentials(const char* ssid, const char* password);

    // 清除已儲存 WiFi 設定（下次開機重新配網）
    void clearWiFiCredentials();
    
    // 主循環（處理心跳、WebSocket）
    void loop();
    
    // 發送數據到 Virtual Pin（Blynk 相容）
    bool sendData(const char* pin, float value);
    bool sendData(const char* pin, int value);
    bool sendData(const char* pin, const char* value);
    
    // 批量發送多個 Pin
    bool sendMultiple(const char* pins[], const char* values[], int count);

    // 註冊 Datastream 定義
    bool registerDatastream(
        const char* pin,
        const char* name,
        float minValue,
        float maxValue,
        const char* unit,
        const char* dataType = "double"
    );
    
    // 註冊接收控制指令的回調函式
    void onControlMessage(void (*callback)(String pin, String value));

    // 註冊系統指令回調（例如 reboot）
    void onSystemCommand(void (*callback)(String action, String payload));

    // 啟用 MQTT 遠端控制模組
    void enableRemoteControl(bool enable = true, const char* mqttHost = nullptr, uint16_t mqttPort = 1883);

    // 動態調整 MQTT Broker
    void setMqttServer(const char* mqttHost, uint16_t mqttPort = 1883);

    // 設定控制 Pin 映射（讓使用者只需 map，不必手寫 parser）
    void mapControlPin(const char* virtualPin, uint8_t gpio, uint8_t mode = OUTPUT_DIGITAL, int minValue = 0, int maxValue = 255);
    void clearControlPinMappings();
    
    // 手動觸發 OTA 更新
    void checkOTA();
    
    // 取得連線狀態
    bool isConnected();
    bool isRemoteControlEnabled();
    String getMacAddress();
    String getLocalIP();

private:
    // WiFi 設定
    const char* _ssid;
    const char* _password;
    
    // 伺服器設定
    const char* _serverIP;
    int _serverPort;
    String _deviceVersion;
    String _macAddress;
    String _chipType;
    
    // WebSocket 客戶端
    WebSocketsClient _webSocket;
    bool _wsConnected;

    // MQTT 客戶端（遠端控制）
    WiFiClient _mqttWiFiClient;
    PubSubClient _mqttClient;
    bool _remoteControlEnabled;
    String _mqttHost;
    uint16_t _mqttPort;
    unsigned long _lastMqttRetry;
    unsigned long _mqttRetryInterval;

    // 控制映射
    static const int MAX_CONTROL_MAPPINGS = 16;
    struct ControlPinMapping {
        String virtualPin;
        uint8_t gpio;
        uint8_t mode;
        int minValue;
        int maxValue;
    };
    ControlPinMapping _controlMappings[MAX_CONTROL_MAPPINGS];
    int _controlMappingCount;

    // 配網設定
    bool _useProvisioning;
    String _apNamePrefix;
    String _apPassword;
    uint16_t _portalTimeoutSec;
    
    // 心跳計時器
    unsigned long _lastHeartbeat;
    unsigned long _heartbeatInterval;
    unsigned long _lastWiFiRetry;
    unsigned long _wifiRetryInterval;
    
    // 回調函式
    void (*_controlCallback)(String pin, String value);
    void (*_systemCallback)(String action, String payload);
    
    // 內部函式
    bool connectWiFi();
    bool reportStatus();
    void ensureMqttConnection();
    void handleMqttMessage(char* topic, byte* payload, unsigned int length);
    void handleControlTopic(const String& topic, const String& payload);
    bool applyMappedControl(const String& pin, const String& value);
    void publishControlAck(const String& event, const String& message);
    String buildUrl(const String& path);
    bool httpGet(const String& path, int* code = nullptr, String* response = nullptr);
    bool httpPostJson(const String& path, const String& body, int* code = nullptr, String* response = nullptr);
    void handleWebSocketEvent(WStype_t type, uint8_t* payload, size_t length);
    static void webSocketEventWrapper(WStype_t type, uint8_t* payload, size_t length);
    
    // 靜態實例指標（用於 WebSocket 回調）
    static ESP_IoT_Manager* _instance;
};

#endif
