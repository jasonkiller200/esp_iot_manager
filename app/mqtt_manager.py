"""
ESP-IoT Manager - MQTT 整合模組
處理 MQTT Broker 的訂閱與資料存儲
"""

import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime, timezone, timedelta
from app import db
from app.models.device import Device
from app.models.datastream import DataStream, DataPoint

TAIPEI_TZ = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)


class MQTTManager:
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.connected = False
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化 MQTT 客戶端"""
        self.app = app
        
        # 從配置讀取 MQTT 設定
        mqtt_host = app.config.get('MQTT_BROKER_HOST', 'localhost')
        mqtt_port = app.config.get('MQTT_BROKER_PORT', 1883)
        mqtt_user = app.config.get('MQTT_USERNAME', None)
        mqtt_pass = app.config.get('MQTT_PASSWORD', None)
        
        # 建立 MQTT 客戶端
        self.client = mqtt.Client(client_id="esp_iot_manager")
        
        # 設定回調函式
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # 設定認證（如果有）
        if mqtt_user and mqtt_pass:
            self.client.username_pw_set(mqtt_user, mqtt_pass)
        
        # 連接 Broker
        try:
            self.client.connect(mqtt_host, mqtt_port, 60)
            self.client.loop_start()  # 非阻塞模式
            logger.info(f"MQTT Client connecting to {mqtt_host}:{mqtt_port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT Broker: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """連線成功回調"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Connected to MQTT Broker")
            
            # 訂閱所有設備的主題
            topics = [
                ("devices/+/data/+", 1),      # 所有設備的數據（QoS 1）
                ("devices/+/status", 0),       # 設備狀態
                ("devices/+/log", 0),          # 設備日誌
            ]
            self.client.subscribe(topics)
            logger.info(f"Subscribed to topics: {[t[0] for t in topics]}")
        else:
            logger.error(f"❌ Failed to connect, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """斷線回調"""
        self.connected = False
        if rc != 0:
            logger.warning(f"⚠️ Unexpected disconnection, return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """收到訊息回調"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            print(f"📨 MQTT Received: {topic} = {payload}")  # 添加 print 調試
            logger.debug(f"📨 Received: {topic} = {payload}")
            
            # 解析 Topic: devices/{mac}/data/{pin}
            parts = topic.split('/')
            
            if len(parts) >= 3:
                mac_address = parts[1]
                message_type = parts[2]
                
                if message_type == "data" and len(parts) == 4:
                    # 數據訊息
                    pin = parts[3]
                    print(f"🔧 Calling _handle_data_message({mac_address}, {pin}, {payload})")  # 調試
                    self._handle_data_message(mac_address, pin, payload)
                    
                elif message_type == "status":
                    # 狀態訊息
                    self._handle_status_message(mac_address, payload)
                    
                elif message_type == "log":
                    # 日誌訊息
                    self._handle_log_message(mac_address, payload)
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_data_message(self, mac_address, pin, value):
        """處理設備數據訊息"""
        with self.app.app_context():
            try:
                # 確保設備存在
                device = Device.query.filter_by(mac=mac_address).first()
                if not device:
                    logger.warning(f"Unknown device: {mac_address}, creating...")
                    device = Device(mac=mac_address)
                    db.session.add(device)
                    db.session.commit()
                
                # 確保 DataStream 存在
                datastream = DataStream.query.filter_by(
                    device_mac=mac_address, 
                    pin=pin
                ).first()
                
                if not datastream:
                    datastream = DataStream(
                        device_mac=mac_address,
                        pin=pin,
                        name=pin
                    )
                    db.session.add(datastream)
                
                # 儲存數據點
                data_point = DataPoint(
                    device_mac=mac_address,
                    pin=pin,
                    value=value,
                    timestamp=datetime.now(TAIPEI_TZ)
                )
                db.session.add(data_point)
                db.session.commit()
                
                print(f"✅ Saved: {mac_address}/{pin} = {value}")  # 調試
                logger.info(f"✅ Saved: {mac_address}/{pin} = {value}")
                
                # 透過 WebSocket 推送即時數據
                try:
                    from app.routes.dashboard import broadcast_data_update
                    broadcast_data_update(mac_address, pin, value)
                except Exception as e:
                    logger.error(f"Failed to broadcast data update: {e}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error: {e}")
    
    def _handle_status_message(self, mac_address, payload):
        """處理設備狀態訊息"""
        with self.app.app_context():
            try:
                status = json.loads(payload)
                
                device = Device.query.filter_by(mac=mac_address).first()
                if device:
                    if 'online' in status:
                        device.last_seen = datetime.now(TAIPEI_TZ)
                    if 'ip' in status:
                        device.ip = status['ip']
                    if 'version' in status:
                        device.version = status['version']
                    
                    db.session.commit()
                    logger.info(f"Updated device status: {mac_address}")
                    
                    # 透過 WebSocket 推送設備狀態
                    try:
                        from app.routes.dashboard import broadcast_device_status
                        broadcast_device_status(mac_address, status)
                    except Exception as e:
                        logger.error(f"Failed to broadcast device status: {e}")
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in status message: {payload}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating device status: {e}")
    
    def _handle_log_message(self, mac_address, payload):
        """處理設備日誌訊息（可選）"""
        logger.info(f"[{mac_address}] {payload}")
    
    def publish(self, topic, payload, qos=0, retain=False):
        """發送 MQTT 訊息"""
        if self.connected:
            try:
                result = self.client.publish(topic, payload, qos, retain)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"📤 Published: {topic} = {payload}")
                    return True
                else:
                    logger.error(f"Failed to publish: {result.rc}")
                    return False
            except Exception as e:
                logger.error(f"Publish error: {e}")
                return False
        else:
            logger.warning("MQTT not connected, cannot publish")
            return False
    
    def send_control_command(self, mac_address, pin, value):
        """發送控制指令到設備"""
        topic = f"devices/{mac_address}/control/{pin}"
        return self.publish(topic, str(value), qos=1)
    
    def disconnect(self):
        """斷開 MQTT 連線"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Client disconnected")


# 全局 MQTT 管理器實例
mqtt_manager = MQTTManager()
