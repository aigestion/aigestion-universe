import json
import logging
import os
from datetime import datetime

KNOWLEDGE_DIR = os.path.expanduser("~/daniela-os/knowledge_db")
KNOWLEDGE_FILE = os.path.join(KNOWLEDGE_DIR, "documents.json")

def _init_knowledge_base():
    """Asegura que el directorio y el archivo de base de conocimientos existan."""
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    if not os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def index_document(title, text):
    """Indexa un documento en la base de datos local."""
    _init_knowledge_base()
    try:
        with open(KNOWLEDGE_FILE, "r+", encoding="utf-8") as f:
            docs = json.load(f)
            doc_id = len(docs) + 1
            docs.append({
                "id": doc_id,
                "title": title,
                "content": text,
                "timestamp": datetime.now().isoformat()
            })
            f.seek(0)
            json.dump(docs, f, ensure_ascii=False, indent=2)
            f.truncate()
        return f"📚 [RAG]: Documento '{title}' indexado con éxito (ID: #{doc_id})."
    except Exception as e:
        logging.error(f"Error indexando en RAG: {e}")
        return f"⚠️ [RAG ERROR]: {e}"

def query_knowledge(query):
    """Busca y recupera la información relevante de la base de conocimientos local."""
    _init_knowledge_base()
    try:
        with open(KNOWLEDGE_FILE, encoding="utf-8") as f:
            docs = json.load(f)

        if not docs:
            return "📚 [RAG]: La base de conocimientos local está vacía. Indexa documentos con 'indexa <título>: <contenido>'."

        query_words = set(query.lower().split())
        results = []

        for doc in docs:
            content_words = set(doc["content"].lower().split())
            title_words = set(doc["title"].lower().split())
            score = len(query_words.intersection(content_words | title_words))
            if score > 0:
                results.append((score, doc))

        results.sort(key=lambda x: x[0], reverse=True)

        if not results:
            return f"📚 [RAG]: No se encontraron coincidencias relevantes para '{query}'."

        best_matches = [f"• #{d['id']} [{d['title']}]: {d['content'][:150]}..." for _, d in results[:3]]
        matches_str = "\n".join(best_matches)
        return f"🧠 [RAG SEARCH]: {len(results)} fragmento(s) encontrado(s):\n{matches_str}"

    except Exception as e:
        logging.error(f"Error consultando RAG: {e}")
        return f"⚠️ [RAG ERROR]: {e}"
