import os
import subprocess
import urllib.parse
import urllib.request

OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\epic_production"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
FINAL_MASTER = os.path.join(OUTPUT_DIR, "daniela_epic_master_final.mp4")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def obtener_prompts_epicos():
    return [
        {
            "escena": 1,
            "prompt": "Cinematic macro shot of an obsidian microchip opening, glowing cyan holographic neural core, volumetrical neon fog, 8k resolution, unreal engine 5 render, raytracing",
            "locucion": "Bienvenidos al núcleo de la inteligencia artificial distribuida de Daniela OS."
        },
        {
            "escena": 2,
            "prompt": "Futuristic dark server room with golden laser beams scanning translucent glass data crystals in mid air, Dune aesthetic, high contrast, cinematic depth of field, 8k",
            "locucion": "Agentes autónomos colaborando en tiempo real con precisión milimétrica y RAG avanzado."
        },
        {
            "escena": 3,
            "prompt": "Infinite glowing blue neural network expanding over a dark horizon, gold particles floating, hyper realistic light reflections, cinematic wide angle, 8k",
            "locucion": "El futuro de la IA es colaborativo, distribuido y libre de alucinaciones."
        }
    ]

def descargar_imagen_pollinations(prompt, output_file):
    """
    Motor visual gratuito de alta res con endpoint directo sin bloqueos DNS.
    """
    prompt_encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1920&height=1080&seed=42&nologo=true"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)

    try:
        print("  🎨 Descargando render HD desde motor visual...")
        with urllib.request.urlopen(req, timeout=30) as response, open(output_file, 'wb') as f:
            f.write(response.read())
        print(f"  ✅ Fotograma creado: {output_file}")
        return True
    except Exception as e:
        print(f"  ❌ Fallo en motor visual: {str(e)}")
        return False

def animar_imagen_a_video(img_path, audio_path, video_out_path, duracion=10):
    """
    Aplica movimiento cinematográfico de cámara (Zoom/Pan Ken Burns)
    sobre la imagen fotorrealista sincronizada con la voz.
    """
    print("  🎬 Aplicando movimiento de cámara y audio...")

    # Efecto Ken Burns en FFmpeg (Zoom suave hacia el centro)
    vf_filter = f"scale=8000x4500,zoompan=z='min(zoom+0.0015,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={duracion*25}:s=1920x1080:fps=25,format=yuv420p"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        video_out_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def ejecutar_pipeline_master():
    print("🚀 DANIELA OS - RUTAS INTELIGENTES HÍBRIDAS (Imágenes HD + Animación FFmpeg)\n")

    escenas = obtener_prompts_epicos()
    videos_escenas = []

    for item in escenas:
        num = item["escena"]
        print(f"▶️ Procesando Escena Épica #{num}")

        img_file = os.path.join(OUTPUT_DIR, f"epic_frame_{num:02d}.jpg")
        audio_file = os.path.join(AUDIO_DIR, f"scene_{num:02d}_voice.mp3")
        video_file = os.path.join(OUTPUT_DIR, f"epic_scene_{num:02d}.mp4")

        # 1. Generar imagen fotorrealista HD
        if descargar_imagen_pollinations(item["prompt"], img_file):
            # 2. Sincronizar voz y animar movimiento de cámara
            animar_imagen_a_video(img_file, audio_file, video_file, duracion=10)
            videos_escenas.append(video_file)
            print(f"  ✨ Escena #{num} renderizada correctamente.\n")

    # 3. Concatenación final del vídeo
    concat_txt = os.path.join(OUTPUT_DIR, "concat_epic.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for v in videos_escenas:
            v_escaped = v.replace("\\", "/")
            f.write(f"file '{v_escaped}'\n")

    print("🎞️ Ensamblando película final...")
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
    print("✨ ¡ PRODUCCIÓN ÉPICA FINALIZADA !")
    print(f"🎥 VÍDEO CON CONTENIDO REAL Y ANIMACIÓN: {FINAL_MASTER}")

if __name__ == "__main__":
    ejecutar_pipeline_master()
