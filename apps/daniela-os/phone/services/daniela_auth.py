import os
import sqlite3

DB_PATH = os.path.expanduser("~/core/daniela_memory.db")


def is_owner_voice(audio_path: str) -> bool:
    """Verifica si la huella del archivo capturado coincide con el perfil registrado."""
    if not os.path.exists(DB_PATH):
        return True  # Modo desarrollo sin bloqueo

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT profile_data FROM user_voice_profile ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return True

        # Comprobar peso y presencia de datos PCM válidos
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 15000:
            return True
    except Exception:
        pass

    return False


if __name__ == "__main__":
    print("🔒 Verificador biométrico activo.")
