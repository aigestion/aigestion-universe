import os
import py_compile

BASE_DIR = os.path.expanduser("~/daniela-os")


def read_source_code(filename):
    """Lee el código fuente de un archivo dentro del proyecto."""
    filepath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(filepath):
        return f"Error: El archivo {filename} no existe."
    try:
        with open(filepath, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error al leer {filename}: {str(e)}"


def apply_hotfix(filename, new_content):
    """Verifica sintaxis y aplica un parche directo al archivo."""
    filepath = os.path.join(BASE_DIR, filename)
    backup_path = f"{filepath}.bak"

    # Crear backup
    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as f:
            old_content = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(old_content)

    # Escribir borrador
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Validar sintaxis Python
        py_compile.compile(filepath, doraise=True)
        return f"✅ Parche aplicado con éxito a {filename}. Sintaxis validada. Backup guardado en {filename}.bak"
    except py_compile.PyCompileError as e:
        # Revertir si hay error de sintaxis
        if os.path.exists(backup_path):
            with (
                open(backup_path, encoding="utf-8") as src,
                open(filepath, "w", encoding="utf-8") as dst,
            ):
                dst.write(src.read())
        return f"❌ Parche rechazado por error de sintaxis: {str(e)}. Revertido a versión anterior."
    except Exception as e:
        return f"❌ Error aplicando parche: {str(e)}"
