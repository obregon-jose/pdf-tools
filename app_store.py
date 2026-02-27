import json
from pathlib import Path
from datetime import datetime, timedelta

DATA_FILE = Path("app_data.json")
SAFETY_MARGIN = 60  # segundos


# ---------- BASE ----------
def _read():
    if not DATA_FILE.exists():
        return {"auth": {}, "config": {}}

    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write(data):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ---------- AUTH ----------
def get_token(api_name):
    data = _read()
    auth = data.get("auth", {}).get(api_name)

    if not auth:
        return None

    try:
        expires_at = datetime.fromisoformat(auth["expires_at"])
        if expires_at > datetime.now() + timedelta(seconds=SAFETY_MARGIN):
            return auth["access_token"]
    except Exception:
        pass

    return None


def save_token(api_name, access_token, expires_in):
    data = _read()

    expires_at = datetime.now() + timedelta(seconds=expires_in)

    data.setdefault("auth", {})[api_name] = {
        "access_token": access_token,
        "expires_at": expires_at.isoformat()
    }

    _write(data)


def delete_token(api_name):
    data = _read()

    if api_name in data.get("auth", {}):
        del data["auth"][api_name]
        _write(data)


# ---------- CONFIG ----------
def get_config(key, default=None):
    data = _read()
    return data.get("config", {}).get(key, default)


def set_config(key, value):
    data = _read()
    data.setdefault("config", {})[key] = value
    _write(data)
