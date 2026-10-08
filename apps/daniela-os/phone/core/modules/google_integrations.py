import json
import os
import sqlite3
import subprocess

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")


def get_env_var(key):
    if os.path.exists(ENV_DB):
        try:
            conn = sqlite3.connect(ENV_DB)
            c = conn.cursor()
            c.execute("SELECT value FROM env_vars WHERE key = ? LIMIT 1", (key,))
            row = c.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass
    return os.getenv(key)


def backup_db_to_drive():
    db_path = os.path.expanduser("~/apps/aig/data/env.db")
    backup_path = os.path.expanduser("~/apps/aig/data/env.db.gpg")
    passphrase = get_env_var("BACKUP_PASSPHRASE") or "DanielaSecure2026"

    if not os.path.exists(db_path):
        return "❌ Base de datos ~/apps/aig/data/env.db no encontrada."

    try:
        subprocess.run(
            [
                "gpg",
                "--batch",
                "--yes",
                "--passphrase",
                passphrase,
                "-c",
                "-o",
                backup_path,
                db_path,
            ],
            check=True,
        )
        return (
            "🛡️ **RESPALDO CIFRADO GENERADO**: Base de datos cifrada en "
            + backup_path
            + " lista para sincronizar con Google Drive."
        )
    except Exception as e:
        return "⚠️ Error al cifrar respaldo: " + str(e)


def send_gmail_alert(subject, message_body):
    return '✉️ **ALERTA GMAIL PREPARADA**: Mensaje "' + str(subject) + '" listo para enviar.'


def analyze_image_with_gemini(image_path):
    api_key = get_env_var("GEMINI_API_KEY") or get_env_var("GOOGLE_API_KEY")
    if not api_key:
        return "❌ API Key de Gemini/Google no configurada en ~/apps/aig/data/env.db."
    return "👁️ **DANIELA VISION**: Análisis activo para " + str(image_path) + "."


def get_location_context():
    try:
        res = subprocess.run(["termux-location"], capture_output=True, text=True, timeout=5.0)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            lat, lon = data.get("latitude"), data.get("longitude")
            return "📍 **CONTEXTO GEOGRÁFICO**: Ubicación (" + str(lat) + ", " + str(lon) + ")."
    except Exception:
        pass
    return "📍 **CONTEXTO GEOGRÁFICO**: Modo Estación de Trabajo (GPS inactivo)."


if __name__ == "__main__":
    print(backup_db_to_drive())
