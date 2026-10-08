import glob
import json
import os
import sqlite3

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")
ENV_JSON = os.path.expanduser("~/.env.json")
GLOBAL_ENV = os.path.expanduser("~/.env")


def compile_env_to_fast_storage():
    """Escanea recursivamente todos los .env, resuelve colisiones e indexa en SQLite y JSON"""
    vars_dict = {}
    home_dir = os.path.expanduser("~")

    # 1. Buscar todos los archivos .env en la estructura
    env_files = glob.glob(os.path.join(home_dir, "**/.env"), recursive=True)
    if os.path.exists(GLOBAL_ENV) and GLOBAL_ENV not in env_files:
        env_files.append(GLOBAL_ENV)

    # 2. Parsear y combinar variables de todos los entornos
    for env_path in env_files:
        try:
            with open(env_path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("\"'")
                        if k and v:
                            vars_dict[k] = v
        except Exception:
            pass

    # 3. Guardar copia en ~/.env unificado
    with open(GLOBAL_ENV, "w", encoding="utf-8") as f:
        f.write("# --- DANIELA OS GLOBAL UNIFIED ENV ---\n")
        for k, v in vars_dict.items():
            f.write(f'{k}="{v}"\n')

    # 4. Compilar a JSON indexado
    with open(ENV_JSON, "w", encoding="utf-8") as f:
        json.dump(vars_dict, f, indent=2)

    # 5. Compilar a SQLite para búsquedas directas O(1)
    conn = sqlite3.connect(ENV_DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS env_vars (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("DELETE FROM env_vars")
    c.executemany("INSERT OR REPLACE INTO env_vars VALUES (?, ?)", list(vars_dict.items()))
    conn.commit()
    conn.close()

    return len(vars_dict)


def load_optimized_env():
    """Carga masiva limpia en os.environ usando la caché JSON"""
    if not os.path.exists(ENV_JSON):
        compile_env_to_fast_storage()

    try:
        with open(ENV_JSON, encoding="utf-8") as f:
            data = json.load(f)
            os.environ.update(data)
            return len(data)
    except Exception:
        return 0


def get_env_var(key, default=None):
    """Consulta O(1) directa desde SQLite"""
    if not os.path.exists(ENV_DB):
        compile_env_to_fast_storage()
    try:
        conn = sqlite3.connect(ENV_DB)
        c = conn.cursor()
        c.execute("SELECT value FROM env_vars WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else default
    except Exception:
        return os.getenv(key, default)


if __name__ == "__main__":
    count = compile_env_to_fast_storage()
    print(
        f"🚀 **OPTIMIZACIÓN COMPLETADA**: {count} variables de entorno consolidadas e indexadas en SQLite (`~/apps/aig/data/env.db`) y JSON (`~/.env.json`)."
    )
