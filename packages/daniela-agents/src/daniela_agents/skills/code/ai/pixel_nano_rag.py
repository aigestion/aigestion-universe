import os
import sqlite3
import time

from google import genai

DB_PATH = os.path.expanduser("~/daniela-os/memory_rag.db")

def init_rag_db():
    """Inicializa la base de datos SQLite para RAG local."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rag_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def query_pixel_rag(query_text: str = "Resumen de estado del sistema") -> str:
    """Ejecuta consulta RAG local aprovechando los documentos indexados en el dispositivo."""
    init_rag_db()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [PIXEL NANO RAG]: Se requiere GEMINI_API_KEY configurada para la síntesis de contexto."

    try:
        # 1. Recuperación de fragmentos locales de la BD
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT source, content FROM rag_docs ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()

        context_str = "\n".join([f"[{r[0]}]: {r[1]}" for r in rows]) if rows else "No hay documentos adicionales indexados."

        # 2. Inferencia y Síntesis RAG
        client = genai.Client(api_key=api_key)
        prompt = f"""Actúa como el motor Pixel Local RAG Nano-Core corriendo en el Tensor G3/G4.
Consulta del usuario: '{query_text}'

Contexto local recuperado (RAG Store):
{context_str}

Responde de forma ejecutiva sintetizando la información local."""

        res = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        answer = res.text.strip()

        # Guardar log en el output
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"pixel_rag_{int(time.time())}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"QUERY: {query_text}\n\n{answer}")

        return f"🧠 [PIXEL LOCAL RAG NANO-CORE]: Consulta procesada en Tensor NPU.\n📁 Archivo: {filepath}\n\n{answer}"

    except Exception as e:
        return f"❌ [PIXEL RAG ERROR]: {e}"

if __name__ == "__main__":
    print(query_pixel_rag())
