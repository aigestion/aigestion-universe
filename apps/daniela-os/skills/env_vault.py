import os
import shutil
import time

ENV_PATH = os.path.expanduser("~/daniela-os/.env")


def set_env_variable(key: str, value: str) -> str:
    """Agrega o actualiza claves en .env con respaldo previo y reload en caliente."""
    if not key or not value:
        return "⚠️ [ENV VAULT]: Proporciona clave y valor válidos."

    key, value = key.strip().upper(), value.strip()

    try:
        if os.path.exists(ENV_PATH):
            shutil.copyfile(ENV_PATH, f"{ENV_PATH}.bak_{int(time.time())}")

        lines = []
        key_found = False
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, encoding="utf-8") as f:
                lines = f.readlines()

        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f"\n{key}={value}\n")

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        os.environ[key] = value
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        return f"🔐 [ENV MASTER VAULT]: Clave '{key}' guardada exitosamente.\n🔑 Valor asignado: {masked}"
    except Exception as e:
        return f"❌ [ENV VAULT ERROR]: {e}"


if __name__ == "__main__":
    print(set_env_variable("TEST_KEY", "123456789ABC"))
