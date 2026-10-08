import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HERMES_DIR = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData/Local/hermes"))
DANIELA_URL = "http://localhost:9200"
HERMES_URL = "http://localhost:9300"
WEB_PORT = 9300

def load_json(path, default=None):
    path = Path(path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
