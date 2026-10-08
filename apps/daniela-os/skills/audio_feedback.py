import subprocess


def play_system_tone(event_type: str = "ok") -> str:
    freqs = {"ok": "1000", "alert": "440", "success": "1760"}
    freq = freqs.get(event_type, "800")
    try:
        # Genera tono utilizando la utilería de Termux
        subprocess.run(
            ["termux-tone-generator", "-f", freq, "-d", "200"], capture_output=True, timeout=2
        )
        return f"🔔 [AUDIO LABS]: Tono '{event_type}' reproducido ({freq} Hz)."
    except Exception:
        return f"🔔 [AUDIO LABS]: Evento auditivo registrado [{event_type.upper()}]."
