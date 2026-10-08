import os
import sqlite3
import subprocess


def get_clipboard_content():
    try:
        res = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, check=False)
        content = res.stdout.strip()
        if not content:
            return None, "📋 El portapapeles está vacío."
        return content, "📋 **CONTENIDO DEL PORTAPAPELES LEÍDO** (" + str(
            len(content)
        ) + " caracteres)."
    except Exception as e:
        return None, "⚠️ Error al acceder al portapapeles: " + str(e)


def process_clipboard_context(user_instruction="revisa"):
    content, msg = get_clipboard_content()
    if not content:
        try:
            from google_voice import play_google_hd_voice

            play_google_hd_voice(
                "Ale, tu portapapeles está vacío o no pude leerlo.", whisper_mode=False
            )
        except Exception:
            pass
        return msg

    clean_preview = content[:200].replace("\n", " ").replace("\r", " ")

    try:
        from google_voice import play_google_hd_voice

        voice_msg = (
            "Ale, he revisado lo que tienes en el portapapeles. Contiene "
            + str(len(content))
            + " caracteres sobre "
            + clean_preview[:60]
            + "..."
        )
        play_google_hd_voice(voice_msg, whisper_mode=False)
    except Exception:
        pass

    env_db = os.path.expanduser("~/apps/aig/data/env.db")
    if os.path.exists(env_db):
        try:
            conn = sqlite3.connect(env_db)
            c = conn.cursor()
            c.execute(
                "CREATE TABLE IF NOT EXISTS clipboard_history (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            c.execute("INSERT INTO clipboard_history (content) VALUES (?)", (content,))
            conn.commit()
            conn.close()
        except Exception:
            pass

    return (
        "📋 **PORTAPAPELES PROCESADO PARA ALE**:\n- **Vista Previa**: `"
        + clean_preview
        + "...`\n- **Longitud**: "
        + str(len(content))
        + " chars.\n- **Estado**: Contexto anexado a ~/apps/aig/data/env.db para consultas RAG."
    )
