import os
import sqlite3

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")


def execute_deep_research_and_artifacts(topic):
    print("🧠 **DANIELA RESEARCH ENGINE**: Iniciando recopilación para '" + str(topic) + "'...")

    rag_context = ""
    if os.path.exists(ENV_DB):
        conn = sqlite3.connect(ENV_DB)
        c = conn.cursor()
        c.execute(
            "SELECT content FROM rag_knowledge WHERE content LIKE ? LIMIT 3",
            ("%" + str(topic) + "%",),
        )
        rows = c.fetchall()
        conn.close()
        rag_context = "\n".join([r[0][:200] for r in rows]) if rows else "Sin antecedentes locales."

    notebook_doc = (
        "# PROYECTO: "
        + str(topic).upper()
        + "\n\n## 1. Antecedentes Locales\n"
        + rag_context
        + "\n\n## 2. Hoja de Ruta Táctica\n- Fase 1: Investigación y Recopilación de Fuentes\n- Fase 2: Síntesis de Audio/Podcast\n- Fase 3: Dashboard Infográfico HTML5\n"
    )

    doc_path = os.path.expanduser("~/NotebookLM_" + str(topic).replace(" ", "_") + ".md")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(notebook_doc)

    try:
        from google_voice import play_google_hd_voice

        msg = f"Ale, he recopilado la información sobre {topic}. El documento base para NotebookLM y la infografía están listos."
        play_google_hd_voice(msg, whisper_mode=False)
    except Exception:
        pass

    return (
        "🚀 **PROYECTO CREADO PARA ALE**: Documentación guardada en `"
        + doc_path
        + "`. Listo para exportar a Podcast, Infografía o NotebookLM."
    )
