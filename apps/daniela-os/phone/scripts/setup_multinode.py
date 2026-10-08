import os

repo_dir = os.path.expanduser("~/aig-monorepo")

dirs = [
    "core",
    "nodes/edge_pixela8/app/agents",
    "nodes/home_minipc/app/agents",
    "nodes/cloud_vps/app/agents",
    "shared_data",
]

for d in dirs:
    path = os.path.join(repo_dir, d)
    os.makedirs(path, exist_ok=True)
    # Crear un __init__.py vacío para que Python los reconozca como módulos
    open(os.path.join(path, "__init__.py"), "a").close()

print("✨ [MULTI-NODO] Estructura de directorios core/nodes creada con éxito.")
