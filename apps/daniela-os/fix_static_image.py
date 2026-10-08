import os

path = os.path.expanduser("~/daniela-os/index.html")
with open(path) as f:
    content = f.read()

# Buscamos la línea que hace rotar al holograma y la comentamos/eliminamos
if "danielaHolo.rotation.y += 0.004;" in content:
    content = content.replace(
        "danielaHolo.rotation.y += 0.004;", "// danielaHolo.rotation.y += 0.004; // Estático"
    )

with open(path, "w") as f:
    f.write(content)

print("✅ Imagen fijada como elemento estático en el centro.")
