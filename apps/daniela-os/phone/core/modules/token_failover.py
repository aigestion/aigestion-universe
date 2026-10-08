import os
import re
import sqlite3

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")


def clean_str(val):
    if not val:
        return ""
    # Eliminar cualquier corchete, comilla o espacio residual
    return re.sub(r"[^a-zA-Z0-9_\-]", "", str(val))


def get_var(key):
    if os.path.exists(ENV_DB):
        try:
            conn = sqlite3.connect(ENV_DB)
            c = conn.cursor()
            c.execute("SELECT value FROM env_vars WHERE key = ? LIMIT 1", (key,))
            row = c.fetchone()
            conn.close()
            if row:
                return clean_str(row[0])
        except Exception:
            pass
    return clean_str(os.getenv(key, ""))


def set_var(key, value):
    clean_val = clean_str(value)
    if os.path.exists(ENV_DB):
        try:
            conn = sqlite3.connect(ENV_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO env_vars (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, clean_val),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            pass
    return False


def get_active_api_key():
    active_key = get_var("GEMINI_API_KEY")
    if not active_key or "ADMIN_KEY_HERE" in active_key:
        active_key = get_var("GEMINI_BACKUP_KEY")
    return active_key


def switch_to_backup_key(reason="Cuota agotada en cuenta principal"):
    backup_key = get_var("GEMINI_BACKUP_KEY")
    if backup_key:
        set_var("GEMINI_API_KEY", backup_key)
        set_var("GEMINI_ACTIVE_ACCOUNT", "noemisanalex@gmail.com (Personal)")
        return "🔄 **FAILOVER ACTIVADO**: Conmutado a API Key de respaldo (noemisanalex@gmail.com)."
    return "❌ No se encontró API Key de respaldo."


def switch_to_primary_key():
    primary_key = get_var("GEMINI_PRIMARY_KEY")
    if primary_key:
        set_var("GEMINI_API_KEY", primary_key)
        set_var("GEMINI_ACTIVE_ACCOUNT", "admin@aigestion.net (Principal)")
        return "🔄 **RESTAURADO**: Conmutado a API Key principal (admin@aigestion.net)."
    return "❌ No se encontró API Key principal."
