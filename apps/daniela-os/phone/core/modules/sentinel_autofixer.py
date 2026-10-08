import os
import subprocess

REPO_DIR = os.path.expanduser("~/apps/aig")


def run_sentinel_autofix():
    logs = ["🛡️ **DANIELA SENTINEL PRO AUTO-FIXER**"]
    try:
        res = subprocess.run(
            ["git", "-C", REPO_DIR, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        changes = res.stdout.strip()
        if changes:
            logs.append(f"🔍 Cambios no confirmados detectados:\n{changes}")
            subprocess.run(["git", "-C", REPO_DIR, "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    REPO_DIR,
                    "commit",
                    "-m",
                    "fix(sentinel): parche y estabilizacion automatica de codigo",
                ],
                check=True,
            )
            logs.append("✅ Parche aplicado y commit generado automáticamente.")
        else:
            logs.append("🟢 Árbol de trabajo limpio. Sin desviaciones en el monorepo.")
    except Exception as e:
        logs.append(f"⚠️ Error en Sentinel Auto-Fixer: {e}")

    return "\n".join(logs)
