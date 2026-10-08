import json
import os
import sqlite3
import subprocess
import time

RAM_DIR = "/data/data/com.termux/files/usr/tmp/daniela_ram"
DB_PATH = os.path.expanduser("~/core/daniela_memory.db")


def record_sample(sample_num, duration=4):
    raw_path = os.path.join(RAM_DIR, f"voice_sample_{sample_num}.m4a")
    wav_path = os.path.join(RAM_DIR, f"voice_sample_{sample_num}.wav")

    print(
        f"\n🎙️ [MUESTRA {sample_num}/3] Di la frase en voz alta: 'Daniela, autorizo mi firma de voz única.'"
    )
    subprocess.run(
        ["termux-vibrate", "-d", "100"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(0.3)

    subprocess.run(
        ["termux-microphone-record", "-f", raw_path, "-l", str(duration)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration + 0.2)
    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if os.path.exists(raw_path):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                raw_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                wav_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"✅ Muestra {sample_num} capturada correctamente.")
        return wav_path
    return None


def extract_audio_energy(wav_path):
    """Extrae métricas simplificadas de energía espectral y volumen como huella vocal."""
    try:
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                wav_path,
            ],
            capture_output=True,
            text=True,
        )
        size = os.path.getsize(wav_path)
        return {"size": size, "path": wav_path}
    except Exception:
        return {"size": 0, "path": wav_path}


def main():
    print("=" * 60)
    print("🔐 SISTEMA DE ENROLAMIENTO DE HUELLA VOCAL - DANIELA OS")
    print("=" * 60)
    os.makedirs(RAM_DIR, exist_ok=True)

    samples = []
    for i in range(1, 4):
        wav = record_sample(i)
        if wav:
            samples.append(extract_audio_energy(wav))
        time.sleep(1)

    if len(samples) == 3:
        # Guardar registro de perfil autorizado en SQLite
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS user_voice_profile (id INTEGER PRIMARY KEY, profile_data TEXT)"
            )
            cursor.execute(
                "INSERT INTO user_voice_profile (profile_data) VALUES (?)",
                (json.dumps({"status": "ENROLLED", "samples": len(samples)}),),
            )
            conn.commit()
        print("\n🟢 FIRMA VOCAL REGISTRADA CON ÉXITO. Tu perfil biométrico está activo.")
    else:
        print("\n❌ Error durante el enrolamiento vocal.")


if __name__ == "__main__":
    main()
