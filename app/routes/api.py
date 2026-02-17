from flask import Blueprint, request, jsonify, send_from_directory, current_app
from app import db
from app.models.device import Device
from app.models.firmware import Firmware
from datetime import datetime, timezone, timedelta

TAIPEI_TZ = timezone(timedelta(hours=8))

api_bp = Blueprint("api", __name__)


@api_bp.route("/update_status", methods=["POST"])
def update_status():
    data = request.json
    mac = data.get("mac")
    if not mac:
        return jsonify({"error": "No MAC"}), 400

    device = Device.query.filter_by(mac=mac).first()
    if not device:
        device = Device(mac=mac)
        db.session.add(device)

    device.ip = data.get("ip")
    device.version = data.get("version")
    # 統一轉為大寫
    device.chip_type = data.get("chip_type", "").upper()
    device.last_seen = datetime.now(TAIPEI_TZ)

    db.session.commit()

    response = {"status": "ok"}

    # 檢查是否有服務器強制推送的更新
    if device.pending_update:
        device.pending_update = False
        db.session.commit()

        latest_fw = Firmware.query.filter_by(
            chip_type=device.chip_type, version=device.target_version
        ).first()

        if latest_fw:
            response["firmware"] = {
                "version": latest_fw.version,
                "filename": latest_fw.filename,
                "url": f"/api/ota/{latest_fw.filename}",
                "update_available": True,
                "force_update": True,
            }
        return jsonify(response)

    # 一般版本檢查
    latest_fw = Firmware.query.filter_by(
        chip_type=device.chip_type, is_active=True
    ).first()

    if latest_fw:
        response["firmware"] = {
            "version": latest_fw.version,
            "filename": latest_fw.filename,
            "url": f"/api/ota/{latest_fw.filename}",
            "update_available": latest_fw.version != device.version,
        }

    return jsonify(response)


@api_bp.route("/ota/<filename>")
def download_ota(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@api_bp.route("/firmware/check", methods=["GET"])
def check_firmware():
    chip_type = request.args.get("chip_type", "ESP8266").upper()
    current_version = request.args.get("version", "0.0.0")

    latest_fw = Firmware.query.filter_by(chip_type=chip_type, is_active=True).first()

    if not latest_fw:
        return jsonify({"update_available": False})

    return jsonify(
        {
            "update_available": latest_fw.version != current_version,
            "version": latest_fw.version,
            "filename": latest_fw.filename,
            "description": latest_fw.description,
            "url": f"/api/ota/{latest_fw.filename}",
        }
    )
