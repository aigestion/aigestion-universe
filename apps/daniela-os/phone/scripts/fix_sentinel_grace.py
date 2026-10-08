import os

sentinel_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/sentinel.py")

if os.path.exists(sentinel_path):
    with open(sentinel_path, encoding="utf-8") as f:
        code = f.read()

    # Aumentar tiempo de chequeo e ignorar fallos en los primeros 10 segundos
    old_init = "def __init__(self, check_interval: float = 15.0):"
    new_init = "def __init__(self, check_interval: float = 20.0):"
    code = code.replace(old_init, new_init)

    old_loop = "nexus_ok = self.check_nexus_health()"
    new_loop = """# Dar tiempo de arranque inicial antes de reiniciar
            time.sleep(5)
            nexus_ok = self.check_nexus_health()"""

    if old_loop in code:
        code = code.replace(old_loop, new_loop)

    with open(sentinel_path, "w", encoding="utf-8") as f:
        f.write(code)

    print("✨ [Sentinel] Período de gracia de inicio inyectado.")
