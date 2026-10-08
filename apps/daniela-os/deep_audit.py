import os
import sqlite3
from pathlib import Path


def auditar_sistema():
    print("\n==================================================")
    print("🔍 DANIELA OS — AUDITORÍA PROFUNDA DE ESTRUCTURA")
    print("==================================================")

    home = Path.home()
    rutas = [home / "daniela-os", home / "apps" / "AIGESTION-MONOREPO", home / "apps"]

    print("\n📂 [1/4] INSPECCIÓN DE DIRECTORIOS Y ESTRUCTURA")
    for ruta in rutas:
        if ruta.exists():
            print(f"\n📍 Ruta: {ruta}")
            for root, _dirs, files in os.walk(ruta):
                depth = root.replace(str(ruta), "").count(os.sep)
                if depth > 2:  # Limitar profundidad visual
                    continue
                indent = "  " * depth
                print(f"{indent}📁 {os.path.basename(root)}/")
                subindent = "  " * (depth + 1)
                for f in files[:8]:  # Mostrar los primeros 8 archivos por carpeta
                    print(f"{subindent}📄 {f}")
                if len(files) > 8:
                    print(f"{subindent}... (+{len(files) - 8} archivos)")
        else:
            print(f"⚠️ Ruta no encontrada: {ruta}")

    print("\n🔑 [2/4] BÚSQUEDA DE CONFIGURACIONES Y ARCHIVOS .ENV")
    env_files = list(home.glob("**/.env"))
    if env_files:
        for ef in env_files:
            print(f"🟢 Archivo .env hallado: {ef}")
            try:
                with open(ef) as f:
                    keys = [
                        line.split("=")[0].strip()
                        for line in f
                        if "=" in line and not line.startswith("#")
                    ]
                print(f"   Variables definidas: {', '.join(keys) if keys else 'Ninguna'}")
            except Exception as e:
                print(f"   ❌ Error al leer {ef}: {e}")
    else:
        print("🔴 No se encontraron archivos .env en el árbol de directorios.")

    print("\n💾 [3/4] INSPECCIÓN DE BASES DE DATOS SQLITE")
    db_files = list(home.glob("**/*.db"))
    for db in db_files:
        print(f"🗄️ Base de datos: {db}")
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            tablas_str = ", ".join([t[0] for t in tables]) if tables else "Sin tablas"
            print(f"   Tablas internas: {tablas_str}")
            conn.close()
        except Exception as e:
            print(f"   ❌ Error al leer DB: {e}")

    print("\n📦 [4/4] PAQUETES PYTHON CLAVE ENTORNO 3.14")
    modulos = ["flask", "requests", "dotenv", "sqlite3"]
    for m in modulos:
        try:
            __import__(m)
            print(f"  🟢 Módulo '{m}': Instalado")
        except ImportError:
            print(f"  🔴 Módulo '{m}': NO instalado")

    print("\n==================================================\n")


if __name__ == "__main__":
    auditar_sistema()
