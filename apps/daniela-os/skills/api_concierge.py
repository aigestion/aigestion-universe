import re

from skills import env_vault

# Catálogo de consolas oficiales y patrones de claves
CONSOLE_MAP = {
    "GEMINI": {
        "url": "https://aistudio.google.com/app/apikey",
        "env_var": "GEMINI_API_KEY",
        "pattern": r"^AIzaSy[A-Za-z0-9_-]{33}$",
        "steps": [
            "1. Haz clic en el enlace oficial de Google AI Studio.",
            "2. Presiona el botón azul 'Create API key'.",
            "3. Copia el string resultante (empieza por 'AIzaSy') y envíamelo aquí.",
        ],
    },
    "GITHUB": {
        "url": "https://github.com/settings/tokens/new",
        "env_var": "GITHUB_TOKEN",
        "pattern": r"^(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})$",
        "steps": [
            "1. Abre el enlace de configuración de GitHub Personal Access Tokens.",
            "2. Asigna un nombre (ej. 'Daniela-OS') y selecciona alcance 'repo' y 'workflow'.",
            "3. Presiona 'Generate token', copia el código ('ghp_...') y pégalo aquí.",
        ],
    },
    "OPENAI": {
        "url": "https://platform.openai.com/api-keys",
        "env_var": "OPENAI_API_KEY",
        "pattern": r"^sk-[A-Za-z0-9_-]{32,}$",
        "steps": [
            "1. Entra a la consola de desarrolladores de OpenAI.",
            "2. Presiona 'Create new secret key'.",
            "3. Copia la clave ('sk-...') y pégala directamente en este chat.",
        ],
    },
}


def get_provisioning_guide(provider: str) -> str:
    """Genera la ficha interactiva y enlace directo para obtener una credencial."""
    prov_upper = provider.strip().upper()
    info = CONSOLE_MAP.get(prov_upper)

    if not info:
        return f"📍 Proveedores soportados: {', '.join(CONSOLE_MAP.keys())}.\nUsa: `daniela-cli 'clave GEMINI'` o `daniela-cli 'clave GITHUB'`"

    steps_str = "\n".join(info["steps"])
    return f"""🎯 **APROVISIONAMIENTO DE API KEY / TOKEN [{prov_upper}]**

🔗 **Enlace Directo a la Consola:**
{info["url"]}

📋 **Instrucciones Paso a Paso:**
{steps_str}

💡 *Cuando la tengas, responde con:* `save_key {prov_upper} <TU_LLAVE>`"""


def save_and_validate_key(provider: str, raw_key: str) -> str:
    """Valida la sintaxis de la clave recibida e inyecta en .env usando ENV Vault (#71)."""
    prov_upper = provider.strip().upper()
    info = CONSOLE_MAP.get(prov_upper)

    if not info:
        # Modo genérico para cualquier clave personalizada
        env_var = (
            f"{prov_upper}_API_KEY"
            if not prov_upper.endswith("_KEY") and not prov_upper.endswith("_TOKEN")
            else prov_upper
        )
        return env_vault.set_env_variable(env_var, raw_key)

    env_var = info["env_var"]
    key_clean = raw_key.strip()

    # Validación de patrón si está definido
    pattern = info.get("pattern")
    if pattern and not re.match(pattern, key_clean):
        return f"⚠️ [CONCIERGE WARNING]: El formato de la clave no parece válido para {prov_upper}.\nAsegúrate de haber copiado el código completo e inténtalo de nuevo."

    # Guardar usando Skill #71
    return env_vault.set_env_variable(env_var, key_clean)


if __name__ == "__main__":
    print(get_provisioning_guide("GEMINI"))
