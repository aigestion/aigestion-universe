import os
import subprocess

REPO_DIR = os.path.expanduser("~/apps/aig")


def generate_daily_changelog():
    """Genera un resumen de los commits de las últimas 24 horas"""
    try:
        res = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "--since=24.hours", "--pretty=format:• %s (%h)"],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        logs = res.stdout.strip()
        if not logs:
            return (
                "📝 **CHANGELOG (24h)**: No se registraron nuevos commits en las últimas 24 horas."
            )
        return f"📝 **CHANGELOG DANIELA OS (Últimas 24h)**:\n{logs}"
    except Exception as e:
        return f"⚠️ Error al generar changelog: {e}"


def create_feature_worktree(feature_name):
    """Crea un entorno de trabajo aislado usando Git Worktree"""
    worktree_path = os.path.expanduser(f"~/apps/worktrees/{feature_name}")
    try:
        subprocess.run(
            [
                "git",
                "-C",
                REPO_DIR,
                "worktree",
                "add",
                "-b",
                f"feature/{feature_name}",
                worktree_path,
            ],
            check=True,
        )
        return f"🌱 **WORKTREE CREADO**: Entorno aislado listo en `{worktree_path}` para desarrollar `feature/{feature_name}`."
    except Exception as e:
        return f"❌ Error al crear Worktree: {e}"


if __name__ == "__main__":
    print(generate_daily_changelog())
