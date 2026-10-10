import sys
from pathlib import Path

from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parent))
from supabase_env import get_supabase_creds  # noqa: E402

env_path = Path.home() / ".env"
env_vars = {}
if env_path.exists():
    with open(env_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

url, key = get_supabase_creds()
supabase = create_client(url, key)

# Conteo de registros en la nube
res = supabase.table('obsidian_embeddings').select('id', count='exact').execute()
print(f"🟢 Registros vectoriales activos en Supabase pgvector: {res.count}")

# Muestra de las últimas 3 notas sincronizadas
latest = supabase.table('obsidian_embeddings').select('file_name, updated_at').limit(3).execute()
print("\n📝 Muestra de notas indexadas en la nube:")
for item in latest.data:
    print(f"  📄 {item['file_name']}")
