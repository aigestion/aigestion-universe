import requests
from env_fast_loader import get_env_var, load_optimized_env


def find_and_check_github_tokens():
    total_vars = load_optimized_env()
    token = get_env_var("GITHUB_TOKEN") or get_env_var("GITHUB_PERSONAL_ACCESS_TOKEN")

    results = [f"⚡ **ENTORNO HIGH-PERFORMANCE OPERATIVO ({total_vars} VARIABLES INDEXADAS)**:\n"]

    if not token:
        results.append("⚠️ No se detectó token de GitHub en el almacenamiento indexado.")
        return "\n".join(results)

    masked_token = f"{token[:6]}...{token[-4:]}" if len(token) > 10 else "N/A"

    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get("https://api.github.com/user", headers=headers, timeout=3.0)
        if r.status_code == 200:
            user_data = r.json()
            results.append(
                f"• **GitHub Token**: `{masked_token}` 🟢 **VÁLIDO** (Usuario: @{user_data.get('login')})"
            )
        else:
            results.append(
                f"• **GitHub Token**: `{masked_token}` 🔴 **INVÁLIDO / EXPIRADO** (HTTP {r.status_code})"
            )
    except Exception as e:
        results.append(f"• **GitHub Token**: `{masked_token}` ⚠️ Error de conexión ({e})")

    results.append(
        "\n✅ **Rendimiento**: Búsqueda en $O(1)$ desde SQLite (`~/apps/aig/data/env.db`). Cero colisiones en memoria."
    )
    return "\n".join(results)


if __name__ == "__main__":
    print(find_and_check_github_tokens())
