import os

sentinel_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/sentinel.py")

if os.path.exists(sentinel_path):
    with open(sentinel_path, encoding="utf-8") as f:
        code = f.read()

    # Reemplazar la lógica agresiva de pkill por un log defensivo
    old_nexus_check = """            nexus_ok = self.check_nexus_health()
            if not nexus_ok:
                print("⚠️ [Sentinel] Nexus Dashboard no responde. Relanzando servicio...")
                subprocess.run(["pkill", "-9", "-f", "nexus_dashboard.py"])
                subprocess.Popen(["python3", os.path.join(repo_dir, "apps/nexus-command-center/nexus_dashboard.py")])"""

    new_nexus_check = """            # Comprobar Nexus sin pkill destructivo
            nexus_ok = self.check_nexus_health()
            if not nexus_ok:
                print("ℹ️ [Sentinel] Nexus Dashboard no responde en este ciclo (esperando estabilización)...")"""

    if old_nexus_check in code:
        code = code.replace(old_nexus_check, new_nexus_check)

    with open(sentinel_path, "w", encoding="utf-8") as f:
        f.write(code)

    print("✨ [Sentinel] Desactivado el pkill automático en Sentinel para garantizar estabilidad.")
