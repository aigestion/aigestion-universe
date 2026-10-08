import json
import subprocess


def inspect_recent_notifications():
    try:
        res = subprocess.run(
            ["termux-notification-list"], capture_output=True, text=True, check=False
        )
        if not res.stdout.strip():
            return "🔕 No hay notificaciones recientes."

        notifs = json.loads(res.stdout)
        urgent = []
        for n in notifs[:5]:
            title = n.get("title", "")
            content = n.get("content", "")
            if any(
                k in (title + content).lower()
                for k in ["urgente", "error", "alert", "github", "fail"]
            ):
                urgent.append(f"{title}: {content}")

        if urgent:
            from google_voice import play_google_hd_voice
            from haptic_proactive import trigger_vibration

            trigger_vibration("critical")
            play_google_hd_voice("Ale, detecté notificaciones prioritarias.", whisper_mode=False)
            return "🚨 **NOTIFICACIONES CRÍTICAS DETECTADAS**:\n" + "\n".join(urgent)

        return "🟢 No se detectaron notificaciones de prioridad crítica."
    except Exception as e:
        return f"⚠️ Error al inspeccionar notificaciones: {e}"


if __name__ == "__main__":
    print(inspect_recent_notifications())
