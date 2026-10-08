import os

DOCS_DIR = os.path.expanduser("~/daniela-os/docs")


def search_local_docs(query):
    """Busca fragmentos relevantes dentro de los archivos de la carpeta docs."""
    if not os.path.exists(DOCS_DIR):
        return "Directorio de documentos no encontrado."

    results = []
    query_words = query.lower().split()

    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith((".txt", ".md", ".json", ".py", ".log")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if any(word in content.lower() for word in query_words):
                            results.append(f"--- ARCHIVO: {file} ---\n{content[:500]}...")
                except Exception:
                    pass

    return "\n\n".join(results) if results else "No se encontraron documentos relevantes."
