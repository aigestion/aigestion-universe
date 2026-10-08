import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\brand_studio"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generar_storyboard_marca():
    return {
        "id_proyecto": "BRAND_NEXO_DANIELA_OS",
        "marca": "AntiGravity / Winsoft",
        "estilo_visual": "Cyber-Corporativo Premium, tonos cian/ámbar, interfaces holográficas, Iluminación volumétrica 8K",
        "escenas": [
            {
                "numero_escena": 1,
                "duracion_seg": 10,
                "prompt_visual": "Cinematic macro shot of an obsidian microchip opening, glowing cyan holographic neural core, volumetrical neon fog, 8k resolution, unreal engine 5 render, raytracing",
                "locucion": "Bienvenidos al ecosistema de inteligencia artificial distribuida de AntiGravity y Winsoft.",
                "transicion": "Zoom in continuo hacia el núcleo"
            },
            {
                "numero_escena": 2,
                "duracion_seg": 12,
                "prompt_visual": "Futuristic dark server room with golden laser beams scanning translucent glass data crystals in mid air, Dune aesthetic, high contrast, cinematic depth of field, 8k",
                "locucion": "Agentes autónomos colaborando en tiempo real con precisión milimétrica y RAG avanzado.",
                "transicion": "Pan panorámico a la derecha"
            },
            {
                "numero_escena": 3,
                "duracion_seg": 10,
                "prompt_visual": "Infinite glowing blue neural network expanding over a dark horizon, gold particles floating, hyper realistic light reflections, cinematic wide angle, 8k",
                "locucion": "El futuro del software no es monolítico: es colaborativo, distribuido y preciso.",
                "transicion": "Vuelo de cámara hacia el horizonte"
            }
        ]
    }

def generar_fotograma_con_reintentos(prompt, output_file, max_retries=3):
    """
    Intenta descargar el fotograma con reintentos automáticos si la red falla.
    """
    prompt_encoded = urllib.parse.quote(prompt)
    urls = [
        f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1920&height=1080&seed=100&nologo=true",
        f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1920&height=1080&seed=200&nologo=true"
    ]

    headers = {'User-Agent': 'Mozilla/5.0'}

    for intento in range(max_retries):
        url = urls[intento % len(urls)]
        req = urllib.request.Request(url, headers=headers)
        try:
            print(f"  🎨 Renderizando fotograma HD (Intento {intento+1}/{max_retries})...")
            with urllib.request.urlopen(req, timeout=45) as resp, open(output_file, 'wb') as f:
                f.write(resp.read())
            print(f"  ✅ Guardado: {output_file}")
            return True
        except Exception as e:
            print(f"  ⚠️ Intento {intento+1} falló ({str(e)}). Reintentando en 2 segundos...")
            time.sleep(2)

    print(f"  ❌ No se pudo descargar la escena #{output_file}")
    return False

def ensamblar_video_escena(img_path, audio_path, video_out_path, duracion=10):
    print("  🎬 Aplicando movimiento cinematográfico de cámara (Ken Burns Effect)...")
    vf_filter = f"scale=8000x4500,zoompan=z='min(zoom+0.0012,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={duracion*25}:s=1920x1080:fps=25,format=yuv420p"

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

def ejecutar_brand_studio():
    print("🚀 DANIELA OS - BRAND STORYBOARD STUDIO (Con Reintentos)\n")

    sb = generar_storyboard_marca()

    json_vids = os.path.join(OUTPUT_DIR, "VIDEO_STORYBOARD.json")
    with open(json_vids, "w", encoding="utf-8") as f:
        json.dump(sb, f, indent=4, ensure_ascii=False)
    print(f"📋 Storyboard de Marca listo para Google Vids en: {json_vids}\n")

    video_clips = []

    for escena in sb["escenas"]:
        num = escena["numero_escena"]
        print(f"▶️ Procesando Escena #{num}")

        img_path = os.path.join(OUTPUT_DIR, f"brand_frame_{num:02d}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"scene_{num:02d}_voice.mp3")
        video_clip = os.path.join(OUTPUT_DIR, f"brand_clip_{num:02d}.mp4")

        # Intentar renderizar la imagen HD
        exito = generar_fotograma_con_reintentos(escena["prompt_visual"], img_path)

        if exito:
            if not os.path.exists(audio_path):
                audio_path = os.path.join(AUDIO_DIR, "scene_01_voice.mp3")

            ensamblar_video_escena(img_path, audio_path, video_clip, duracion=escena["duracion_seg"])
            video_clips.append(video_clip)
            print(f"  ✨ Clip #{num} completado.\n")

    # Concatenar todos los clips válidos
    if video_clips:
        concat_txt = os.path.join(OUTPUT_DIR, "brand_concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for clip in video_clips:
                clip_escaped = clip.replace("\\", "/")
                f.write(f"file '{clip_escaped}'\n")

        master_final = os.path.join(OUTPUT_DIR, "brand_master_vids.mp4")
        print("🎞️ Unificando vídeo máster corporativo...")
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-c", "copy",
            master_final
        ]
        subprocess.run(cmd_concat, capture_output=True, check=True)

        print("\n" + "=" * 60)
        print("✨ ¡PRODUCCIÓN DE MARCA COMPLETA Y REGENERADA!")
        print(f"🎥 VÍDEO MÁSTER GENERADO: {master_final}")
        print(f"📄 JSON PARA GOOGLE VIDS: {json_vids}")

if __name__ == "__main__":
    ejecutar_brand_studio()
