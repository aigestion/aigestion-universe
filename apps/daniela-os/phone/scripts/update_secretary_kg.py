import os

sec_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/agent_secretary.py")

if os.path.exists(sec_path):
    with open(sec_path, encoding="utf-8") as f:
        content = f.read()

    if "from core.knowledge_graph import KnowledgeGraph" not in content:
        content = (
            "import sys\nrepo_dir = os.path.expanduser('~/aig-monorepo')\nif repo_dir not in sys.path: sys.path.insert(0, repo_dir)\nfrom core.knowledge_graph import KnowledgeGraph\n"
            + content
        )
        content = content.replace(
            "def __init__(self):", "def __init__(self):\n        self.kg = KnowledgeGraph()"
        )

        # Inyectar ingestión automática en save_note
        old_save = 'cursor.execute("INSERT INTO quick_memory (timestamp, key_tag, content) VALUES (?, ?, ?)", (ts, key_tag, content))'
        new_save = (
            old_save
            + '\n            try:\n                self.kg.extract_and_ingest(content)\n            except Exception as e:\n                print(f"⚠️ Error inyectando al Grafo: {e}")'
        )

        content = content.replace(old_save, new_save)

    with open(sec_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✨ [Agente Secretario] Integrada auto-ingestión en Knowledge Graph con éxito.")
else:
    print("⚠️ No se encontró agent_secretary.py, omitiendo parche.")
