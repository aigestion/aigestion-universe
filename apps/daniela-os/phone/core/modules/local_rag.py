import os
import sqlite3

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")
REPO_DIR = os.path.expanduser("~/apps/aig")


def init_rag_db():
    conn = sqlite3.connect(ENV_DB)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS rag_knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, filepath TEXT UNIQUE, content TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    conn.close()


def index_repository():
    init_rag_db()
    conn = sqlite3.connect(ENV_DB)
    c = conn.cursor()
    count = 0
    for root, _, files in os.walk(REPO_DIR):
        if ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith((".py", ".md", ".json", ".yml")):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()
                    c.execute(
                        "INSERT INTO rag_knowledge (filepath, content) VALUES (?, ?) ON CONFLICT(filepath) DO UPDATE SET content=excluded.content",
                        (full_path, content),
                    )
                    count += 1
                except Exception:
                    pass
    conn.commit()
    conn.close()
    return (
        "🧠 **RAG LOCAL ACTUALIZADO**: "
        + str(count)
        + " archivos indexados en SQLite (~/apps/aig/data/env.db)."
    )


def search_knowledge(query):
    init_rag_db()
    conn = sqlite3.connect(ENV_DB)
    c = conn.cursor()
    c.execute(
        "SELECT filepath, content FROM rag_knowledge WHERE content LIKE ? LIMIT 3",
        ("%" + str(query) + "%",),
    )
    rows = c.fetchall()
    conn.close()
    if not rows:
        return "🔍 No se encontraron coincidencias para " + str(query) + " en la base RAG."
    res = "📚 **RESULTADOS RAG LOCAL (Query: " + str(query) + ")\\n"
    for path, content in rows:
        snippet = content[:120].replace("\\n", " ")
        res += "- `" + os.path.basename(path) + "`: " + snippet + "...\\n"
    return res
