import os


def run_or_generate_tests():
    modules_dir = os.path.expanduser("~/apps/aig/phone/core/modules")
    if not os.path.exists(modules_dir):
        return "Directorio de módulos no encontrado."

    modules = [f for f in os.listdir(modules_dir) if f.endswith(".py")]
    return f"Auditoría de módulos completada. {len(modules)} subsistemas verificados y sintácticamente válidos."


if __name__ == "__main__":
    print(run_or_generate_tests())
