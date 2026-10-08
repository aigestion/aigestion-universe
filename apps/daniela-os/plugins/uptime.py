import subprocess
def run(context):
    try:
        # 'uptime -p' nos da un formato legible como "up 2 hours, 15 minutes"
        res = subprocess.run(['uptime', '-p'], capture_output=True, text=True)
        return f"⏱️ [PLUGIN UPTIME]: {res.stdout.strip()}"
    except Exception as e:
        return f"❌ Error obteniendo uptime: {e}"
