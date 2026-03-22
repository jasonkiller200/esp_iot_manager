from functools import wraps
from flask import current_app, request, jsonify, flash, redirect, url_for


def _get_bearer_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return ""


def require_write_token():
    """保護寫入/控制端點：Bearer token 或 X-API-Token"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            required = current_app.config.get("WRITE_API_TOKEN", "")
            if not required:
                # 沒設定 token 時，維持向後相容（開發用）
                return fn(*args, **kwargs)

            provided = (
                _get_bearer_token()
                or request.headers.get("X-API-Token", "")
                or request.form.get("write_token", "")
            )
            if provided != required:
                if not request.is_json:
                    flash("未授權：請先設定 WRITE_API_TOKEN", "danger")
                    return redirect(request.referrer or url_for("main.index"))
                return jsonify({"status": "error", "message": "unauthorized"}), 401

            return fn(*args, **kwargs)

        return wrapper

    return decorator
