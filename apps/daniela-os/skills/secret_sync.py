import base64
import os
import subprocess

REPO_TARGET = "aigestion/AIGESTION-MONOREPO"
ENV_SOURCE = os.path.expanduser("~/downloads/.env")


def sync_env_to_github_secrets() -> str:
    """Codifica el .env local en Base64 y lo sube de forma segura a GitHub Secrets."""
    if not os.path.exists(ENV_SOURCE):
        return f"❌ [SECRET SYNC]: No se encontró el archivo en '{ENV_SOURCE}'."

    try:
        # 1. Verificar autenticación en GH CLI
        auth_check = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if auth_check.returncode != 0:
            return "⚠️ [SECRET SYNC]: No estás autenticado en GitHub CLI. Ejecuta 'gh auth login' primero."

        # 2. Leer y codificar en Base64
        with open(ENV_SOURCE, "rb") as f:
            raw_content = f.read()
            b64_content = base64.b64encode(raw_content).decode("utf-8")

        lines_count = len(raw_content.decode("utf-8", errors="ignore").splitlines())

        # 3. Subir secreto usando 'gh secret set'
        process = subprocess.Popen(
            ["gh", "secret", "set", "MASTER_ENV_B64", "--repo", REPO_TARGET],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=b64_content)

        if process.returncode == 0:
            return f"🔐 [SECRET VAULT]: ¡Éxito! Archivo .env de {lines_count} líneas cifrado e inyectado en GitHub Secrets ('MASTER_ENV_B64')."
        else:
            return f"❌ [SECRET VAULT ERROR]: Fallo al guardar en GitHub: {stderr.strip()}"

    except Exception as e:
        return f"❌ [SECRET VAULT EXCEPTION]: {e}"


if __name__ == "__main__":
    print(sync_env_to_github_secrets())
