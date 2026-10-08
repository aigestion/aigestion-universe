import os
import datetime
import subprocess

AUDIO_OUTPUT = os.path.expanduser("~/daniela-os/media/podcast_diario.mp3")

def generar_guion_podcast():
    fecha_actual = datetime.datetime.now().strftime("%A %d de %B, %Y")
    return (
        f"Apertura del informe diario de Daniela OS para aigestion.net. "
        f"Hoy es {fecha_actual}. "
        f"Sistemas en Termux: Operativos. "
        f"Google Workspace Sync: Sincronizado. "
        f"Recordatorio de la dirección: Tu negocio, tu vida, en orden absoluto."
    )

def sintetizar_audio(texto, output_file):
    print("🎙️ [DANIELA OS]: Sintetizando locución diaria de mando...")
    cmd = [
        "edge-tts",
        "--voice", "es-ES-ElviraNeural",
        "--text", texto,
        "--write-media", output_file
    ]
    subprocess.run(cmd)
    print(f"✅ Podcast generado en: {output_file}")

if __name__ == "__main__":
    script = generar_guion_podcast()
    sintetizar_audio(script, AUDIO_OUTPUT)
