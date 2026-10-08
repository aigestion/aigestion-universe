import json
import logging
import os

NOTEBOOK_DB = os.path.expanduser("~/daniela-os/notebook_db.json")


def query_notebooklm_context(topic):
    """
    Skill #22: NotebookLM Bridge.
    Recupera contexto técnico, requisitos y fuentes estructuradas desde NotebookLM.
    """
    try:
        if not os.path.exists(NOTEBOOK_DB):
            return "📘 [NOTEBOOKLM]: No se encontró 'notebook_db.json'. Genera fuentes usando 'setup_notebooklm_pipeline.py'."

        with open(NOTEBOOK_DB, encoding="utf-8") as f:
            db = json.load(f)

        matches = [item for item in db if topic.lower() in json.dumps(item).lower()]

        if not matches:
            return f"📘 [NOTEBOOKLM]: No hay notas o fuentes asociadas a '{topic}'."

        summary = "\n".join(
            [f"• [{m.get('title', 'Nota')}]: {m.get('content', '')[:200]}..." for m in matches[:3]]
        )
        return f"📖 [NOTEBOOKLM CONTEXT] ({len(matches)} fuentes encontradas):\n{summary}"

    except Exception as e:
        logging.error(f"Error en NotebookLM Bridge: {e}")
        return f"⚠️ [NOTEBOOKLM ERROR]: {e}"
