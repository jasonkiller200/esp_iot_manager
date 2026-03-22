"""
ESP-IoT Manager - MQTT 整合模組
處理 MQTT Broker 的訂閱與資料存儲
"""

import paho.mqtt.client as mqtt
import json
import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from app import db
from app.models.device import Device
from app.models.datastream import DataStream, DataPoint
from app.models.command import DeviceCommand

TAIPEI_TZ = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)


class MQTTManager:
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.connected = False

        # 寫入優化：資料點緩衝區（批次落盤）
        self._data_buffer = []
        self._buffer_lock = threading.Lock()
        self._last_flush_ts = time.time()
        self._flush_batch_size = 100
        self._flush_interval_sec = 2
        self._stop_event = threading.Event()
        self._flusher_thread = None

        # 快取：降低每筆都 hit DB 查詢 device/datastream
        self._known_devices = set()
        self._known_streams = set()

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """初始化 MQTT 客戶端"""
        self.app = app

        # 從配置讀取 MQTT 設定
        mqtt_host = app.config.get("MQTT_BROKER_HOST", "localhost")
        mqtt_port = app.config.get("MQTT_BROKER_PORT", 1883)
        mqtt_user = app.config.get("MQTT_USERNAME", None)
        mqtt_pass = app.config.get("MQTT_PASSWORD", None)
        self._flush_batch_size = int(app.config.get("MQTT_FLUSH_BATCH_SIZE", 100))
        self._flush_interval_sec = int(app.config.get("MQTT_FLUSH_INTERVAL_SEC", 2))

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
            self._start_flusher_thread()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT Broker: {e}")

    def _start_flusher_thread(self):
        if self._flusher_thread and self._flusher_thread.is_alive():
            return

        self._stop_event.clear()

        def _worker():
            while not self._stop_event.is_set():
                time.sleep(max(1, self._flush_interval_sec))
                self.flush_data_buffer()

        self._flusher_thread = threading.Thread(
            target=_worker, name="mqtt-flusher", daemon=True
        )
        self._flusher_thread.start()

    def _on_connect(self, client, userdata, flags, rc):
        """連線成功回調"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Connected to MQTT Broker")

            # 訂閱所有設備的主題
            topics = [
                ("devices/+/data/+", 1),  # 所有設備的數據（QoS 1）
                ("devices/+/status", 0),  # 設備狀態
                ("devices/+/log", 0),  # 設備日誌
            ]
            if self.client:
                self.client.subscribe(topics)
            logger.info(f"Subscribed to topics: {[t[0] for t in topics]}")
        else:
            logger.error(f"❌ Failed to connect, return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """斷線回調"""
        self.connected = False
        self.flush_data_buffer()
        if rc != 0:
            logger.warning(f"⚠️ Unexpected disconnection, return code: {rc}")

    def _on_message(self, client, userdata, msg):
        """收到訊息回調"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")

            logger.debug(f"📨 Received: {topic} = {payload}")

            # 解析 Topic: devices/{mac}/data/{pin}
            parts = topic.split("/")

            if len(parts) >= 3:
                mac_address = parts[1]
                message_type = parts[2]

                if message_type == "data" and len(parts) == 4:
                    # 數據訊息
                    pin = parts[3]
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
        if not self.app:
            return
        with self.app.app_context():
            try:
                self._ensure_device_and_stream(mac_address, pin)

                self._enqueue_data_point(mac_address, pin, value)
                self._flush_if_needed()

                # 透過 WebSocket 推送即時數據
                try:
                    from app.routes.dashboard import broadcast_data_update

                    broadcast_data_update(mac_address, pin, value)
                except Exception as e:
                    logger.error(f"Failed to broadcast data update: {e}")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error: {e}")

    def _ensure_device_and_stream(self, mac_address, pin):
        device_key = mac_address
        stream_key = f"{mac_address}:{pin}"

        created = False

        if device_key not in self._known_devices:
            device = Device.query.filter_by(mac=mac_address).first()
            if not device:
                device = Device(mac=mac_address)
                db.session.add(device)
                created = True
                logger.warning(f"Unknown device: {mac_address}, creating...")
            self._known_devices.add(device_key)

        if stream_key not in self._known_streams:
            datastream = DataStream.query.filter_by(
                device_mac=mac_address, pin=pin
            ).first()
            if not datastream:
                datastream = DataStream(device_mac=mac_address, pin=pin, name=pin)
                db.session.add(datastream)
                created = True
            self._known_streams.add(stream_key)

        if created:
            db.session.commit()

    def _enqueue_data_point(self, mac_address, pin, value):
        row = {
            "device_mac": mac_address,
            "pin": pin,
            "value": value,
            "timestamp": datetime.now(TAIPEI_TZ),
        }
        with self._buffer_lock:
            self._data_buffer.append(row)

    def _flush_if_needed(self):
        with self._buffer_lock:
            size = len(self._data_buffer)
            expired = (time.time() - self._last_flush_ts) >= self._flush_interval_sec

        if size >= self._flush_batch_size or (size > 0 and expired):
            self.flush_data_buffer()

    def flush_data_buffer(self):
        if not self.app:
            return 0
        with self._buffer_lock:
            if not self._data_buffer:
                return 0
            rows = self._data_buffer
            self._data_buffer = []

        try:
            with self.app.app_context():
                db.session.bulk_insert_mappings(DataPoint, rows)
                db.session.commit()
            self._last_flush_ts = time.time()
            logger.debug(f"📥 Flushed {len(rows)} datapoints")
            return len(rows)
        except Exception as e:
            with self._buffer_lock:
                self._data_buffer = rows + self._data_buffer
            db.session.rollback()
            logger.error(f"Failed to flush datapoints: {e}")
            return 0

    def _handle_status_message(self, mac_address, payload):
        """處理設備狀態訊息"""
        if not self.app:
            return
        with self.app.app_context():
            try:
                status = json.loads(payload)

                device = Device.query.filter_by(mac=mac_address).first()
                if device:
                    if "online" in status:
                        device.last_seen = datetime.now(TAIPEI_TZ)
                    if "ip" in status:
                        device.ip = status["ip"]
                    if "version" in status:
                        device.version = status["version"]

                    db.session.commit()
                    logger.info(f"Updated device status: {mac_address}")

                    # 透過 WebSocket 推送設備狀態
                    try:
                        from app.routes.dashboard import broadcast_device_status

                        broadcast_device_status(mac_address, status)
                    except Exception as e:
                        logger.error(f"Failed to broadcast device status: {e}")

                    # command ACK lifecycle 更新
                    try:
                        self._update_command_ack(mac_address, status)
                    except Exception as e:
                        logger.error(f"Failed to update command ack: {e}")

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
        if self.connected and self.client:
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

    def _update_command_ack(self, mac_address, status_payload):
        event = status_payload.get("event")
        if not event:
            return

        message = status_payload.get("message", "")
        cmd_id = status_payload.get("command_id")

        query = DeviceCommand.query.filter_by(device_mac=mac_address)
        if cmd_id:
            command = query.filter_by(command_id=cmd_id).first()
        else:
            command = (
                query.filter(DeviceCommand.status.in_(["queued", "sent"]))
                .order_by(DeviceCommand.created_at.desc())
                .first()
            )

        if not command:
            return

        command.ack_event = str(event)
        command.ack_message = str(message)
        command.ack_at = datetime.now(TAIPEI_TZ)

        if event in ["ok", "connected", "reboot"]:
            command.status = "ack"
        elif event in ["error", "warn"]:
            command.status = "failed"
            command.error_message = message
        else:
            command.status = "ack"

        db.session.commit()

    def disconnect(self):
        """斷開 MQTT 連線"""
        self._stop_event.set()
        self.flush_data_buffer()
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Client disconnected")


# 全局 MQTT 管理器實例
mqtt_manager = MQTTManager()
