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

class ESP_IoT_Manager {
public:
    // 建構函式
    ESP_IoT_Manager(const char* ssid, const char* password, const char* serverIP, int serverPort = 5000);
    
    // 初始化連線
    bool begin(const char* deviceVersion = "1.0.0");
    
    // 主循環（處理心跳、WebSocket）
    void loop();
    
    // 發送數據到 Virtual Pin（Blynk 相容）
    bool sendData(const char* pin, float value);
    bool sendData(const char* pin, int value);
    bool sendData(const char* pin, const char* value);
    
    // 批量發送多個 Pin
    bool sendMultiple(const char* pins[], const char* values[], int count);
    
    // 註冊接收控制指令的回調函式
    void onControlMessage(void (*callback)(String pin, String value));
    
    // 手動觸發 OTA 更新
    void checkOTA();
    
    // 取得連線狀態
    bool isConnected();
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
    
    // 心跳計時器
    unsigned long _lastHeartbeat;
    unsigned long _heartbeatInterval;
    
    // 回調函式
    void (*_controlCallback)(String pin, String value);
    
    // 內部函式
    bool connectWiFi();
    bool reportStatus();
    void handleWebSocketEvent(WStype_t type, uint8_t* payload, size_t length);
    static void webSocketEventWrapper(WStype_t type, uint8_t* payload, size_t length);
    
    // 靜態實例指標（用於 WebSocket 回調）
    static ESP_IoT_Manager* _instance;
};

#endif
