import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from io import BytesIO
from app import create_app, db
from app.models.firmware import Firmware


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["UPLOAD_FOLDER"] = "firmware"
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WRITE_API_TOKEN"] = ""

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class TestBinUpload:
    def test_upload_valid_bin(self, client, app):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        data = {
            "file": (BytesIO(b"\x00\x01\x02\x03test bin content"), "test_led_blink.bin")
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data")
        assert response.status_code == 302

        firmware_path = os.path.join(app.config["UPLOAD_FOLDER"], "test_led_blink.bin")
        assert os.path.exists(firmware_path)
        os.remove(firmware_path)

    def test_upload_invalid_extension(self, client):
        data = {"file": (BytesIO(b"test content"), "test.txt")}
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "只能上傳 .bin 檔案".encode("utf-8") in response.data

    def test_upload_no_file(self, client):
        response = client.post(
            "/upload",
            data={},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "沒有選擇檔案".encode("utf-8") in response.data

    def test_list_firmwares(self, client, app):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        test_bin = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
        with open(test_bin, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        with app.app_context():
            fw = Firmware()
            fw.filename = "firmware.bin"
            fw.version = "1.0.0"
            fw.chip_type = "ESP8266"
            db.session.add(fw)
            db.session.commit()

        response = client.get("/")
        assert response.status_code == 200
        assert b"firmware.bin" in response.data

        os.remove(test_bin)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
