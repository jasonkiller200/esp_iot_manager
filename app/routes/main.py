import os
from flask import (
    Blueprint,
    render_template,
    current_app,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from app.models.device import Device
from app.models.firmware import Firmware
from app import db
from app.auth import require_write_token

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    devices = Device.query.order_by(Device.last_seen.desc()).all()
    firmwares = Firmware.query.order_by(Firmware.uploaded_at.desc()).all()
    return render_template("index.html", devices=devices, firmwares=firmwares)


@main_bp.route("/ota/<filename>")
def download_ota(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@main_bp.route("/upload", methods=["POST"])
@require_write_token()
def upload_file():
    if "file" not in request.files:
        flash("沒有選擇檔案", "danger")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    version = request.form.get("version", "1.0.0")
    chip_type = request.form.get("chip_type", "ESP8266")
    description = request.form.get("description", "")

    if file.filename == "":
        flash("沒有選擇檔案", "danger")
        return redirect(url_for("main.index"))

    if not file.filename.endswith(".bin"):
        flash("只能上傳 .bin 檔案", "danger")
        return redirect(url_for("main.index"))

    try:
        filename = file.filename
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        fw = Firmware(
            filename=filename,
            version=version,
            chip_type=chip_type,
            description=description,
        )
        db.session.add(fw)
        db.session.commit()

        flash(f"上傳成功: {filename} (v{version})", "success")
    except Exception as e:
        flash(f"上傳失敗: {str(e)}", "danger")

    return redirect(url_for("main.index"))


@main_bp.route("/firmware/delete/<int:fw_id>", methods=["POST"])
@require_write_token()
def delete_firmware(fw_id):
    fw = Firmware.query.get_or_404(fw_id)
    try:
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], fw.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(fw)
        db.session.commit()
        flash(f"已刪除: {fw.filename} (v{fw.version})", "success")
    except Exception as e:
        flash(f"刪除失敗: {str(e)}", "danger")
    return redirect(url_for("main.index"))


@main_bp.route("/firmware/set_latest/<int:fw_id>", methods=["POST"])
@require_write_token()
def set_latest_version(fw_id):
    fw = Firmware.query.get_or_404(fw_id)
    try:
        Firmware.query.update({"is_active": False})
        fw.is_active = True
        db.session.commit()
        flash(f"已設定最新版本: v{fw.version}", "success")
    except Exception as e:
        flash(f"設定失敗: {str(e)}", "danger")
    return redirect(url_for("main.index"))


@main_bp.route("/device/push_update/<int:device_id>", methods=["POST"])
@require_write_token()
def push_update(device_id):
    device = Device.query.get_or_404(device_id)
    version = request.form.get("version")

    if not version:
        flash("請選擇要推送的版本", "danger")
        return redirect(url_for("main.index"))

    try:
        # 先只根據版本號查找，不限制晶片類型
        fw = Firmware.query.filter_by(version=version).first()

        if not fw:
            # 如果找不到，嘗試模糊匹配
            fw = Firmware.query.filter(Firmware.version.like(f"%{version}%")).first()

        if not fw:
            flash(
                f"找不到該版本韌體 (v{version})，可用版本: "
                + ", ".join([f.version for f in Firmware.query.all()]),
                "danger",
            )
            return redirect(url_for("main.index"))

        device.pending_update = True
        device.target_version = version
        db.session.commit()

        flash(f"已發送更新請求到 {device.ip}，等待設備回報後自動更新", "success")
    except Exception as e:
        flash(f"發送失敗: {str(e)}", "danger")

    return redirect(url_for("main.index"))
