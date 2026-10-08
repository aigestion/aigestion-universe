import math
import os
import re
import sqlite3
from typing import Any

DB_PATH = os.path.expanduser("~/apps/aig/phone/core/daniela_memory.db")


class MobileRAG:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicializa la tabla de documentos y embeddings locales en SQLite."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _tokenize(self, text: str) -> list[str]:
        """Normalización y tokenización ligera de texto."""
        text = text.lower()
        return re.findall(r"\w+", text)

    def _compute_tf(self, tokens: list[str]) -> dict[str, float]:
        tf_dict = {}
        total = len(tokens)
        if total == 0:
            return tf_dict
        for token in tokens:
            tf_dict[token] = tf_dict.get(token, 0) + 1
        for token in tf_dict:
            tf_dict[token] /= total
        return tf_dict

    def add_document(self, title: str, content: str, category: str = "general") -> int:
        """Inserta o actualiza un conocimiento en la base vectorial del Pixel 8."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO knowledge_base (title, content, category) VALUES (?, ?, ?)",
                (title, content, category),
            )
            conn.commit()
            return cursor.lastrowid

    def search(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Búsqueda vectorial/semántica ligera local mediante similitud de coseno en TF-IDF."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        query_tf = self._compute_tf(query_tokens)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, category FROM knowledge_base")
            rows = cursor.fetchall()

        results = []
        for doc_id, title, content, category in rows:
            doc_tokens = self._tokenize(f"{title} {content}")
            doc_tf = self._compute_tf(doc_tokens)

            # Coseno de similitud
            dot_product = sum(
                query_tf.get(token, 0) * doc_tf.get(token, 0) for token in query_tokens
            )
            q_magnitude = math.sqrt(sum(val**2 for val in query_tf.values()))
            d_magnitude = math.sqrt(sum(val**2 for val in doc_tf.values()))

            similarity = 0.0
            if q_magnitude > 0 and d_magnitude > 0:
                similarity = dot_product / (q_magnitude * d_magnitude)

            if similarity > 0.05:
                results.append(
                    {
                        "id": doc_id,
                        "title": title,
                        "content": content,
                        "category": category,
                        "score": round(similarity, 4),
                    }
                )

        # Ordenar por mayor puntuación semántica
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# Seed de prueba inicial
if __name__ == "__main__":
    rag = MobileRAG()
    # Insertar conocimientos base del sistema
    rag.add_document(
        "Comandos de Emergencia",
        "Para forzar el reinicio de los servicios usa d-fix. El servidor central responde en la IP 100.98.235.124.",
        "sistema",
    )
    rag.add_document(
        "Arquitectura Daniela OS",
        "El Pixel 8 actúa como nodo Edge autónomo con fallback local en puerto 8001.",
        "arquitectura",
    )

    print("🧠 [MOBILE RAG]: Base de datos vectorial SQLite cargada.")
    print("🔍 Probando búsqueda local: '¿Qué IP usa el servidor?'")
    res = rag.search("IP del servidor")
    for r in res:
        print(f"  • [{r['score']}] {r['title']}: {r['content']}")
