import os
import subprocess

REPO_DIR = os.path.expanduser("~/apps/aig")


def run_nightly_maintenance():
    logs = ["🌙 **INICIANDO MANTENIMIENTO NOCTURNO AUTOMÁTICO**"]
    try:
        subprocess.run(["git", "-C", REPO_DIR, "gc", "--prune=now"], check=True)
        logs.append("🧹 Git GC y optimización de repositorio completados.")
    except Exception as e:
        logs.append("⚠️ Error en Git GC: " + str(e))
    try:
        from local_rag import index_repository

        logs.append(index_repository())
    except Exception as e:
        logs.append("⚠️ Error en RAG re-indexing: " + str(e))
    return "\n".join(logs)
