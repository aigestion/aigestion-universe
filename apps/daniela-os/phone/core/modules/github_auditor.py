import os
import sqlite3
import subprocess

import requests

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")
REPO_DIR = os.path.expanduser("~/apps/aig")


def get_token_from_db():
    """Extrae el token en O(1) directamente desde SQLite"""
    if os.path.exists(ENV_DB):
        try:
            conn = sqlite3.connect(ENV_DB)
            c = conn.cursor()
            c.execute(
                "SELECT value FROM env_vars WHERE key IN ('GITHUB_TOKEN', 'GITHUB_PERSONAL_ACCESS_TOKEN') LIMIT 1"
            )
            row = c.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass
    return os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")


def audit_full_github():
    token = get_token_from_db()
    report = ["🔍 **AUDITORÍA EN TIEMPO REAL - GITHUB & REPOSITORIO LOCAL**:\n"]

    # 1. Inspección Git Local Real
    if os.path.exists(REPO_DIR):
        try:
            res = subprocess.run(
                ["git", "-C", REPO_DIR, "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            changes = res.stdout.strip().splitlines() if res.stdout.strip() else []
            if not changes:
                report.append("✅ **Árbol Git Local**: Limpio (0 archivos pendientes).")
            else:
                report.append(
                    f"⚠️ **Árbol Git Local**: {len(changes)} archivo(s) pendientes de commit."
                )

            branch_res = subprocess.run(
                ["git", "-C", REPO_DIR, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=3.0,
            )
            branch = branch_res.stdout.strip()
            report.append(f"📌 **Rama Activa**: `{branch}`")

            unpushed = subprocess.run(
                ["git", "-C", REPO_DIR, "log", "@{u}..HEAD", "--oneline"],
                capture_output=True,
                text=True,
                timeout=3.0,
            )
            if unpushed.returncode == 0:
                pending_commits = (
                    len(unpushed.stdout.strip().splitlines()) if unpushed.stdout.strip() else 0
                )
                if pending_commits == 0:
                    report.append("✅ **Sincronización Remote**: Sincronizado con origin/main.")
                else:
                    report.append(
                        f"🚀 **Commits pendientes de Push**: {pending_commits} commit(s)."
                    )
        except Exception as e:
            report.append(f"⚠️ **Git Local**: Error al consultar estado ({e}).")
    else:
        report.append(f"⚠️ **Git Local**: No se encontró la ruta `{REPO_DIR}`.")

    # 2. Conexión Real a la API de GitHub
    if token and (token.startswith(("ghp_", "github_pat_"))):
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            }
            r = requests.get("https://api.github.com/user", headers=headers, timeout=5.0)
            if r.status_code == 200:
                user_info = r.json()
                report.append(
                    f"✅ **API Remote**: Autenticado como **@{user_info.get('login')}** ({user_info.get('public_repos', 0)} repos públicos)."
                )
            else:
                report.append(f"❌ **API Remote**: Error HTTP {r.status_code} - Token no válido.")
        except Exception as e:
            report.append(f"⚠️ **API Remote**: Error de red ({e}).")
    else:
        report.append("❌ **API Remote**: Token de GitHub no encontrado en ~/apps/aig/data/env.db.")

    return "\n".join(report)


def commit_and_sync_repo(
    commit_message="feat(core): actualización de módulos y sincronización de Daniela OS",
):
    if os.path.exists(REPO_DIR):
        try:
            subprocess.run(["git", "-C", REPO_DIR, "add", "."], check=True)
            subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", commit_message], check=True)
            return (
                "✅ Todos los cambios locales fueron empaquetados y guardados con un nuevo commit."
            )
        except Exception as e:
            return f"❌ Error al realizar commit: {e}"
    return "❌ No se encontró la ruta del repositorio."


if __name__ == "__main__":
    print(audit_full_github())
