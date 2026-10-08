import json
import os
import subprocess

STORYBOARD_PATH = r"C:\Users\Alejandro\aig\prototypes\storyboard_production.json"
VIDEO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_videos"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\final_production"
MASTER_OUTPUT = os.path.join(OUTPUT_DIR, "daniela_os_master_final.mp4")

def comprobar_ffmpeg():
    """Verifica si ffmpeg está accesible en el PATH del sistema."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def generar_video_mock_si_falta(ruta_video, duracion_sec=10):
    """
    Si no existe el clip de vídeo (modo simulación), genera un vídeo de prueba sólido
    en 1080p con temporizador de color azul tecnológico.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0f172a:s=1920x1080:d={duracion_sec}",
        "-vf", "drawtext=text='Daniela OS - Render Simulado Escena':x=(w-text_w)/2:y=(h-text_h)/2-50:fontsize=48:fontcolor=white,drawtext=text='%{eif\\:t\\:d}s':x=(w-text_w)/2:y=(h-text_h)/2+30:fontsize=64:fontcolor=0x38bdf8",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        ruta_video
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def ensamblar_produccion():
    print("🎬 Daniela OS - Ensamblado de Vídeo y Audio Máster (FFmpeg)\n")

    if not comprobar_ffmpeg():
        print("❌ Error: FFmpeg no está instalado o no se encuentra en el PATH de Windows.")
        print("💡 Instálalo con: winget install ffmpeg")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(STORYBOARD_PATH, encoding="utf-8") as f:
        storyboard = json.load(f)

    escenas = storyboard.get("escenas", [])
    clips_unificados = []

    print(f"📦 Procesando {len(escenas)} escenas para combinación A/V...\n")

    for escena in escenas:
        num_escena = escena.get("numero_escena")
        duracion_proyectada = escena.get("duracion_segundos", 10)

        file_video = os.path.join(VIDEO_DIR, f"scene_{num_escena:02d}_hunyuan.mp4")
        file_audio = os.path.join(AUDIO_DIR, f"scene_{num_escena:02d}_voice.mp3")
        file_merged = os.path.join(OUTPUT_DIR, f"temp_scene_{num_escena:02d}.mp4")

        print(f"▶️ Unificando Escena #{num_escena}")

        # Genera el vídeo base de prueba en caso de trabajar sobre los renders simulados
        if not os.path.exists(file_video):
            print(f"   ⚠️ Generando clip base sintético para simulación ({duracion_proyectada}s)...")
            generar_video_mock_si_falta(file_video, duracion_proyectada)

        if os.path.exists(file_audio):
            # Combina el vídeo y la voz en MP3 ajustando el vídeo al tiempo exacto de la locución
            cmd_merge = [
                "ffmpeg", "-y",
                "-i", file_video,
                "-i", file_audio,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                file_merged
            ]
        else:
            # Si no hay audio, copia solo el vídeo
            cmd_merge = [
                "ffmpeg", "-y",
                "-i", file_video,
                "-c:v", "copy",
                file_merged
            ]

        subprocess.run(cmd_merge, capture_output=True, check=True)
        clips_unificados.append(file_merged)
        print(f"   ✅ Escena #{num_escena} lista")

    # Crear archivo de lista para concatenación masiva de FFmpeg
    list_txt_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(list_txt_path, "w", encoding="utf-8") as f:
        for clip in clips_unificados:
            path_escaped = clip.replace("\\", "/")
            f.write(f"file '{path_escaped}'\n")

    print("\n🎞️ Concatenando escenas en el archivo Máster final...")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_txt_path,
        "-c", "copy",
        MASTER_OUTPUT
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)

    # Limpieza de archivos temporales de lista
    if os.path.exists(list_txt_path):
        os.remove(list_txt_path)

    print("\n" + "=" * 60)
    print("✨ ¡Proceso completado exitosamente!")
    print(f"🎥 VÍDEO MÁSTER GENERADO: {MASTER_OUTPUT}")

if __name__ == "__main__":
    ensamblar_produccion()
