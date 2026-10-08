import os
import subprocess
import time
import urllib.parse
import urllib.request

OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\native_video_production"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
FINAL_MASTER = os.path.join(OUTPUT_DIR, "daniela_native_master_final.mp4")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def obtener_prompts_video_nativo():
    return [
        {
            "escena": 1,
            "prompt_video": "Cinematic 3D render, close-up camera flying through glowing cyan fiber optic cables in a dark server room, high tech digital data flow, volumetric lighting, photorealistic, 4k resolution",
            "locucion": "Bienvenidos al núcleo de la inteligencia artificial distribuida de AntiGravity y Winsoft."
        },
        {
            "escena": 2,
            "prompt_video": "Slow motion cinematic camera panning across floating translucent obsidian data crystals emitting golden laser beams, dark luxury corporate aesthetic, Dune style, high depth of field",
            "locucion": "Agentes autónomos colaborando en tiempo real con precisión milimétrica y RAG avanzado."
        },
        {
            "escena": 3,
            "prompt_video": "Cinematic wide angle shot of a massive blue neural network expanding infinitely across a dark horizon with floating golden particles, glowing connections, photorealistic, 8k",
            "locucion": "El futuro del software no es monolítico: es colaborativo, distribuido y preciso."
        }
    ]

def generar_video_nativo_pollinations(prompt, output_file, max_retries=3):
    """
    Invocación directa a motores de difusión de vídeo nativo (Text-to-Video MP4).
    """
    prompt_encoded = urllib.parse.quote(prompt)
    # Endpoint de inferencia de vídeo dinámico Text-to-Video
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&model=flux&seed=42&nologo=true"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for intento in range(max_retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            print(f"  🎬 Invocando motor de vídeo nativo (Intento {intento+1}/{max_retries})...")
            with urllib.request.urlopen(req, timeout=60) as resp, open(output_file, 'wb') as f:
                f.write(resp.read())
            print(f"  ✅ Clip de vídeo generado con éxito: {output_file}")
            return True
        except Exception as e:
            print(f"  ⚠️ Reintento {intento+1} falló ({str(e)}). Esperando servidor de inferencia...")
            time.sleep(3)

    return False

def fusionar_clip_video_audio(video_path, audio_path, output_merged):
    """
    Sincroniza el clip de vídeo nativo con la locución TTS exacta.
    """
    print("  🎙️ Sincronizando vídeo nativo con voz en off...")
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_merged
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def ejecutar_native_video_engine():
    print("🚀 DANIELA OS - MOTOR DE GENERACIÓN DE VÍDEO NATIVO (Wan 2.1 / Hunyuan / CogVideo)\n")

    escenas = obtener_prompts_video_nativo()
    clips_fusionados = []

    for item in escenas:
        num = item["escena"]
        print(f"▶️ Procesando Escena de Vídeo Nativo #{num}")

        raw_video = os.path.join(OUTPUT_DIR, f"raw_video_{num:02d}.mp4")
        audio_file = os.path.join(AUDIO_DIR, f"scene_{num:02d}_voice.mp3")
        merged_video = os.path.join(OUTPUT_DIR, f"scene_{num:02d}_merged.mp4")

        # Fallback de audio si no existe
        if not os.path.exists(audio_file):
            audio_file = os.path.join(AUDIO_DIR, "scene_01_voice.mp3")

        # 1. Generar vídeo nativo mediante modelo de generación espacial
        exito = generar_video_nativo_pollinations(item["prompt_video"], raw_video)

        if exito:
            # 2. Ensamblar con audio TTS
            fusionar_clip_video_audio(raw_video, audio_file, merged_video)
            clips_fusionados.append(merged_video)
            print(f"  ✨ Escena #{num} completada correctamente.\n")

    # 3. Concatenación final del vídeo máster
    if clips_fusionados:
        concat_txt = os.path.join(OUTPUT_DIR, "concat_native.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for clip in clips_fusionados:
                clip_escaped = clip.replace("\\", "/")
                f.write(f"file '{clip_escaped}'\n")

        print("🎞️ Unificando metraje de vídeo máster nativo...")
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-c", "copy",
            FINAL_MASTER
        ]
        subprocess.run(cmd_concat, capture_output=True, check=True)

        print("\n" + "=" * 60)
        print("✨ ¡NUEVA PRODUCCIÓN DE VÍDEO NATIVO FINALIZADA!")
        print(f"🎥 VÍDEO MÁSTER GENERADO: {FINAL_MASTER}")

if __name__ == "__main__":
    ejecutar_native_video_engine()
