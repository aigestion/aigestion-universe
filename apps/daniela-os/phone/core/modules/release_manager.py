import os
import sqlite3

import requests

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")


def get_token():
    if os.path.exists(ENV_DB):
        try:
            conn = sqlite3.connect(ENV_DB)
            c = conn.cursor()
            c.execute(
                "SELECT value FROM env_vars WHERE key IN ('GITHUB_TOKEN', 'GITHUB_PERSONAL_ACCESS_TOKEN') LIMIT 1"
            )
            row = c.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass
    return os.getenv("GITHUB_TOKEN")


def create_github_release(tag_name, release_name, body_text):
    token = get_token()
    if not token:
        return "❌ Token no encontrado para crear el Release en GitHub."

    url = "https://api.github.com/repos/aig/AIGESTION-MONOREPO/releases"
    headers = {"Authorization": "Bearer " + str(token), "Accept": "application/vnd.github.v3+json"}
    payload = {
        "tag_name": tag_name,
        "target_commitish": "ui-stable",
        "name": release_name,
        "body": body_text,
        "draft": False,
        "prerelease": False,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 201:
            return (
                "🎉 **RELEASE "
                + str(tag_name)
                + " PUBLICADO EN GITHUB**: "
                + str(r.json().get("html_url"))
            )
        else:
            return "⚠️ Error al crear Release (HTTP " + str(r.status_code) + "): " + str(r.text)
    except Exception as e:
        return "❌ Excepción al conectar con la API de GitHub: " + str(e)


if __name__ == "__main__":
    print("Módulo release_manager listo.")
