import json
import os

# 1. Actualizar archivo JSON
file_path = "family_whitelist.json"
nuevos_nombres = ["Fati", "mamá", "José cuevas", "a-gorde"]

if os.path.exists(file_path):
    with open(file_path) as f:
        data = json.load(f)
else:
    data = {"familia": [], "prioridad_alta": ["Emergencia", "Banco", "AEAT"]}

for nombre in nuevos_nombres:
    if nombre not in data["familia"]:
        data["familia"].append(nombre)

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Lista Blanca actualizada con éxito.")

# 2. Inyectar función de gestión dinámica en el backend (Para que Daniela lo haga sola)
app_path = "app_daniela.py"
if os.path.exists(app_path):
    with open(app_path, encoding="utf-8") as f:
        code = f.read()

    gestion_dinamica = """
def agregar_a_familia(nombre):
    with open("family_whitelist.json", "r+") as f:
        data = json.load(f)
        if nombre not in data["familia"]:
            data["familia"].append(nombre)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            return f"He añadido a {nombre} a tu lista blanca. Tendrán acceso prioritario."
        return f"{nombre} ya estaba en tu lista."
"""
    if "def agregar_a_familia" not in code:
        with open(app_path, "a", encoding="utf-8") as f:
            f.write("\n" + gestion_dinamica)
        print("✅ Daniela ya tiene capacidad de auto-gestión de familia.")
