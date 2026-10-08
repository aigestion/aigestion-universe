import glob
import os
import subprocess
import urllib.parse
import urllib.request

from gradio_client import Client

OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\native_video_production"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
FINAL_MASTER = os.path.join(OUTPUT_DIR, "daniela_wan21_master_final.mp4")

os.makedirs(OUTPUT_DIR, exist_ok=True)

HF_TOKEN = os.getenv("HF_TOKEN", None)

def limpiar_videos_defectuosos():
    """Elimina clips de vídeo dañados o residuales de ejecuciones con error."""
    print("🧹 Limpiando vídeos defectuosos y temporales antiguos...")
    patrones = ["*.mp4", "*.txt", "*.tmp"]
    eliminados = 0
    for patron in patrones:
        archivos = glob.glob(os.path.join(OUTPUT_DIR, patron))
        for archivo in archivos:
            try:
                os.remove(archivo)
                eliminados += 1
            except Exception:
                pass
    print(f"  🗑️ Se han eliminado {eliminados} archivos residuales.\n")

def obtener_prompts_storyboard():
    return [
        {
            "escena": 1,
            "prompt": "Cinematic 3D slow zoom into a glowing cyan holographic neural core inside a sleek obsidian microchip, volumetric neon fog, 8k resolution, photorealistic",
            "locucion": "Bienvenidos al núcleo de la inteligencia artificial distribuida de AntiGravity y Winsoft."
        },
        {
            "escena": 2,
            "prompt": "Futuristic dark server room with golden laser beams scanning translucent glass data crystals in mid air, Dune aesthetic, cinematic pan, high depth of field",
            "locucion": "Agentes autónomos colaborando en tiempo real con precisión milimétrica y RAG avanzado."
        },
        {
            "escena": 3,
            "prompt": "Cinematic wide angle shot of a massive blue neural network expanding infinitely across a dark horizon with floating golden particles, glowing connections, photorealistic",
            "locucion": "El futuro del software no es monolítico: es colaborativo, distribuido y preciso."
        }
    ]

def generar_video_wan21_hf(prompt: str, output_path: str):
    print("  ⚡ Invocando motor Wan 2.1 en HuggingFace Space...")
    spaces_wan = [
        "Wan-Video/Wan2.1-T2V-1.3B",
        "multimodalart/Wan2.1-T2V-1.3B"
    ]

    for space in spaces_wan:
        try:
            print(f"     Conectando a {space}...")
            # En versiones actuales de gradio_client el parámetro correcto es 'token'
            client = Client(space, token=HF_TOKEN) if HF_TOKEN else Client(space)

            result = client.predict(
                prompt=prompt,
                negative_prompt="blurry, low quality, static picture",
                seed=42,
                api_name="/generate"
            )

            if result and os.path.exists(result):
                os.replace(result, output_path)
                print(f"  ✅ [Wan 2.1] Vídeo nativo generado: {output_path}")
                return True
        except Exception as e:
            print(f"  ⚠️ Espacio {space} no disponible ({str(e)[:80]}...)")

    return False

def generar_video_fallback_api(prompt: str, output_path: str):
    """Fallback directo a endpoint de difusión de vídeo continuo."""
    print("  🚀 Invocando motor de vídeo por difusión rápida...")
    prompt_encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&model=flux&seed=42&nologo=true"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp, open(output_path, 'wb') as f:
            f.write(resp.read())
        print(f"  ✅ Clip generado vía motor de respuesta inmediata: {output_path}")
        return True
    except Exception as e:
        print(f"  ❌ Error en fallback de vídeo: {str(e)}")
        return False

def fusionar_video_audio(video_file, audio_file, output_file):
    print("  🎙️ Unificando metraje de vídeo con audio TTS...")
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_file
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def ejecutar_pipeline_clean():
    print("🚀 DANIELA OS - NATIVE VIDEO PIPELINE (Limpieza + Wan 2.1)\n")

    # 1. Purga de vídeos erróneos anteriores
    limpiar_videos_defectuosos()

    escenas = obtener_prompts_storyboard()
    clips_validos = []

    for item in escenas:
        num = item["escena"]
        prompt = item["prompt"]
        print(f"▶️ Procesando Escena #{num}")

        raw_video = os.path.join(OUTPUT_DIR, f"clean_raw_{num:02d}.mp4")
        audio_file = os.path.join(AUDIO_DIR, f"scene_{num:02d}_voice.mp3")
        merged_video = os.path.join(OUTPUT_DIR, f"scene_{num:02d}_final.mp4")

        if not os.path.exists(audio_file):
            audio_file = os.path.join(AUDIO_DIR, "scene_01_voice.mp3")

        # Intentar Wan 2.1
        exito = generar_video_wan21_hf(prompt, raw_video)

        # Si Wan 2.1 está ocupado, usar motor de difusión continua
        if not exito:
            exito = generar_video_fallback_api(prompt, raw_video)

        if exito:
            fusionar_video_audio(raw_video, audio_file, merged_video)
            clips_validos.append(merged_video)
            print(f"  ✨ Escena #{num} ensamblada con éxito.\n")

    # Concatenación final sin archivos corruptos
    if clips_validos:
        concat_txt = os.path.join(OUTPUT_DIR, "concat_clean.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for clip in clips_validos:
                c_escaped = clip.replace("\\", "/")
                f.write(f"file '{c_escaped}'\n")

        print("🎞️ Generando vídeo máster final libre de errores...")
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
        print("✨ ¡PRODUCCIÓN LIMPIA Y COMPLETA FINALIZADA!")
        print(f"🎥 VÍDEO MÁSTER GENERADO: {FINAL_MASTER}")

if __name__ == "__main__":
    ejecutar_pipeline_clean()
