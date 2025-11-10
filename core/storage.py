import json, os
from core.config import DATA_DIR

DATA_FILE = os.path.join(DATA_DIR, "user_data.json")

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data({})
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
