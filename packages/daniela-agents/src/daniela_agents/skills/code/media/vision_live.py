import os
import subprocess


def capture_live_frame():
    frame_path = os.path.expanduser("~/daniela-os/static/live_frame.jpg")
    try:
        subprocess.run(["termux-camera-photo", "-c", "0", frame_path], check=True)
        return f"📹 [VISION LIVE]: Frame analizado correctamente en {frame_path}"
    except Exception as e:
        return f"⚠️ [VISION ERROR]: {e}"
