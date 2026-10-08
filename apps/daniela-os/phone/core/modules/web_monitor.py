import os
import sqlite3

import requests


def monitor_url_target(url="https://github.com/aig/AIGESTION-MONOREPO"):
    try:
        r = requests.get(url, timeout=5)
        status = r.status_code
        content_length = len(r.text)

        env_db = os.path.expanduser("~/apps/aig/data/env.db")
        if os.path.exists(env_db):
            conn = sqlite3.connect(env_db)
            c = conn.cursor()
            c.execute(
                "CREATE TABLE IF NOT EXISTS web_monitor (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, status INTEGER, length INTEGER, checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            c.execute(
                "INSERT INTO web_monitor (url, status, length) VALUES (?, ?, ?)",
                (url, status, content_length),
            )
            conn.commit()
            conn.close()

        return f"🕷️ **WEB MONITOR**: URL `{url}` verificada (HTTP {status}, {content_length} bytes)."
    except Exception as e:
        return f"⚠️ Error monitoreando {url}: {e}"
