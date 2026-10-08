import os
import subprocess
import threading

RAM_IMG_PATH = "/data/data/com.termux/files/usr/tmp/daniela_ram/capture.jpg"


def _async_take_photo(camera_id="0"):
    os.makedirs(os.path.dirname(RAM_IMG_PATH), exist_ok=True)
    try:
        subprocess.run(
            ["termux-camera-photo", "-c", camera_id, RAM_IMG_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        pass


def trigger_async_photo(camera_id="0") -> str:
    """Inicia la captura en un hilo secundario sin congelar el hilo principal HTTP."""
    thread = threading.Thread(target=_async_take_photo, args=(camera_id,))
    thread.daemon = True
    thread.start()
    return RAM_IMG_PATH


if __name__ == "__main__":
    path = trigger_async_photo()
    print(f"📷 Captura asíncrona iniciada hacia: {path}")
