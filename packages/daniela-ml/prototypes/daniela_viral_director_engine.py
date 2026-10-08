import os
import subprocess
import urllib.parse
import urllib.request

from PIL import Image, ImageStat

OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\viral_production"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
FINAL_MASTER_16_9 = os.path.join(OUTPUT_DIR, "daniela_viral_tutorial_16x9.mp4")
FINAL_MASTER_9_16 = os.path.join(OUTPUT_DIR, "daniela_viral_shorts_9x16.mp4")

os.makedirs(OUTPUT_DIR, exist_ok=True)

class ViralSocialMediaDirector:
    """
    Agente Director de Contenido Viral y Tutoriales Premium para Daniela OS.
    Optimiza el storytelling, hooks de retención, estética de marca y supervisión QA.
    """
    def __init__(self):
        self.min_brightness = 15
        self.min_contrast = 20

    def generar_escaleta_viral(self, tema):
        print(f"🎬 [Viral Director Agent] Diseñando guion premium y hooks de retención para: '{tema}'...")
        return [
            {
                "escena": 1,
                "hook_type": "VISUAL_HOOK_3SEC",
                "prompt": "Cyberpunk high tech obsidian microchip opening, glowing cyan neural core, hyper-realistic reflections, volumetric fog, Unreal Engine 5 render, cinematic lighting, 8k",
                "locucion": "Esto es lo que las grandes empresas de IA no quieren que sepas sobre los agentes autónomos.",
                "subtitulo_destacado": "⚡ EL SECRETO DE LA IA DISTRIBUIDA",
                "duracion_seg": 5
            },
            {
                "escena": 2,
                "hook_type": "VALUE_PROP",
                "prompt": "Futuristic dark server room with golden laser beams scanning translucent glass data crystals in mid air, Dune aesthetic, cinematic pan, high depth of field, 8k",
                "locucion": "Olvídate de modelos lentos. Un sistema multi-agente con RAG avanzado responde con precisión milimétrica.",
                "subtitulo_destacado": "🧠 PRECISIÓN ABSOLUTA RAG 2.0",
                "duracion_seg": 6
            },
            {
                "escena": 3,
                "hook_type": "CALL_TO_ACTION",
                "prompt": "Cinematic wide angle shot of a massive blue neural network expanding infinitely across a dark horizon with floating golden particles, glowing connections, photorealistic, 8k",
                "locucion": "Con Daniela OS puedes construir esta arquitectura 100% gratis hoy mismo. Guárdalo y pruébalo.",
                "subtitulo_destacado": "🚀 DANIELA OS • 100% GRATIS",
                "duracion_seg": 5
            }
        ]

    def auditar_y_escalar_hd(self, image_path, target_res=(1920, 1080)):
        print(f"  🔍 [QA Inspector] Evaluando frame: {os.path.basename(image_path)}...")
        try:
            with Image.open(image_path) as img:
                if img.size != target_res:
                    print(f"  ⚙️ [Auto-QA] Escalando fotograma a resolución nativa {target_res[0]}x{target_res[1]}...")
                    img_resized = img.resize(target_res, Image.Resampling.LANCZOS)
                    img_resized.save(image_path, quality=95)

                with Image.open(image_path) as img_eval:
                    grayscale = img_eval.convert('L')
                    stat = ImageStat.Stat(grayscale)
                    brightness = stat.mean[0]
                    contrast = stat.stddev[0]

                    print(f"     📊 Métricas de Calidad -> Brillo: {brightness:.1f} | Contraste: {contrast:.1f}")
                    if brightness < self.min_brightness or contrast < self.min_contrast:
                        print("  ❌ [QA Rejection] Iluminación/Contraste subestándar.")
                        return False

                    print("  ✅ [QA Approved] Frame verificado para edición viral.")
                    return True
        except Exception as e:
            print(f"  ❌ Error en auditoría QA: {str(e)}")
            return False

def renderizar_frame_hd(prompt, output_file, seed=42):
    prompt_encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1920&height=1080&seed={seed}&nologo=true"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(output_file, 'wb') as f:
            f.write(resp.read())
        return True
    except Exception as e:
        print(f"  ⚠️ Reintento de descarga en curso: {str(e)}")
        return False

def generar_audio_locucion(texto, output_audio_path):
    import asyncio

    import edge_tts

    async def _tts():
        communicate = edge_tts.Communicate(texto, "es-ES-AlvaroNeural")
        await communicate.save(output_audio_path)

    try:
        asyncio.run(_tts())
        print(f"  🔊 Voz off sincronizada: {os.path.basename(output_audio_path)}")
        return True
    except Exception as e:
        print(f"  ❌ Error TTS: {str(e)}")
        return False

def ensamblar_corte_viral(img_path, audio_path, subtitle_text, video_out_16_9, video_out_9_16, escena_num, duracion=5):
    print("  🎥 Renderizando edición dinámico-viral a 60 FPS con subtítulos dinámicos...")

    if escena_num == 1:
        vf_base = f"scale=8000x4500,zoompan=z='min(zoom+0.0035,1.40)':x='iw/2-(iw/zoom/2)+sin(time*2)*80':y='ih/2-(ih/zoom/2)':d={duracion*60}:s=1920x1080:fps=60"
    elif escena_num == 2:
        vf_base = f"scale=8000x4500,zoompan=z='1.30':x='(on/{duracion*60})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d={duracion*60}:s=1920x1080:fps=60"
    else:
        vf_base = f"scale=8000x4500,zoompan=z='min(zoom+0.0030,1.35)':x='(iw-iw/zoom)*(1-on/{duracion*60})':y='(ih-ih/zoom)*(on/{duracion*60})':d={duracion*60}:s=1920x1080:fps=60"

    subtitle_filter = f",drawtext=text='{subtitle_text}':x=(w-text_w)/2:y=h-140:fontsize=42:fontcolor=yellow:box=1:boxcolor=black@0.7:boxborderw=10:font=Arial"

    # Formato Horizontal 16:9
    cmd_16_9 = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-vf", vf_base + subtitle_filter + ",format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        video_out_16_9
    ]
    subprocess.run(cmd_16_9, capture_output=True, check=True)

    # Formato Vertical 9:16 (Shorts/Reels/TikTok)
    vf_9_16 = vf_base + ",crop=ih*(9/16):ih" + subtitle_filter + ",scale=1080:1920,format=yuv420p"
    cmd_9_16 = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-vf", vf_9_16,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        video_out_9_16
    ]
    subprocess.run(cmd_9_16, capture_output=True, check=True)

def ejecutar_pipeline_director_viral():
    print("🚀 DANIELA OS - VIRAL SOCIAL MEDIA & TUTORIAL DIRECTOR ENGINE\n")

    director = ViralSocialMediaDirector()
    tema = "Arquitectura de Agentes IA Distribuidos y RAG Avanzado"
    escaleta = director.generar_escaleta_viral(tema)

    clips_16_9 = []
    clips_9_16 = []

    for item in escaleta:
        num = item["escena"]
        hook_label = item.get("hook_type", "STANDARD_HOOK")
        print(f"\n▶️ Produciendo Escena Viral #{num} [{hook_label}]")

        img_path = os.path.join(OUTPUT_DIR, f"viral_frame_{num:02d}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"viral_voice_{num:02d}.mp3")
        clip_16_9 = os.path.join(OUTPUT_DIR, f"clip_16x9_{num:02d}.mp4")
        clip_9_16 = os.path.join(OUTPUT_DIR, f"clip_9x16_{num:02d}.mp4")

        # 1. Voz off de alta retención
        generar_audio_locucion(item["locucion"], audio_path)

        # 2. Inferencia visual + QA Audit
        exito_frame = False
        for attempt in range(3):
            seed = 50 + (attempt * 77)
            if renderizar_frame_hd(item["prompt"], img_path, seed=seed):
                if director.auditar_y_escalar_hd(img_path):
                    exito_frame = True
                    break

        if exito_frame:
            # 3. Ensamblado Dual (Horizontal + Vertical)
            ensamblar_corte_viral(
                img_path, audio_path, item["subtitulo_destacado"],
                clip_16_9, clip_9_16, num, duracion=item["duracion_seg"]
            )
            clips_16_9.append(clip_16_9)
            clips_9_16.append(clip_9_16)
            print(f"  ✨ Escena #{num} en formato Horizontal y Vertical finalizada.")

    if clips_16_9 and clips_9_16:
        concat_16_9 = os.path.join(OUTPUT_DIR, "concat_16x9.txt")
        with open(concat_16_9, "w", encoding="utf-8") as f:
            for c in clips_16_9:
                c_clean = c.replace('\\', '/')
                f.write(f"file '{c_clean}'\n")

        cmd_master_16_9 = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_16_9, "-c", "copy", FINAL_MASTER_16_9]
        subprocess.run(cmd_master_16_9, capture_output=True, check=True)

        concat_9_16 = os.path.join(OUTPUT_DIR, "concat_9x16.txt")
        with open(concat_9_16, "w", encoding="utf-8") as f:
            for c in clips_9_16:
                c_clean = c.replace('\\', '/')
                f.write(f"file '{c_clean}'\n")

        cmd_master_9_16 = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_9_16, "-c", "copy", FINAL_MASTER_9_16]
        subprocess.run(cmd_master_9_16, capture_output=True, check=True)

        print("\n" + "=" * 60)
        print("✨ ¡ PRODUCCIÓN VIRAL MULTIFORMATO COMPLETADA CON ÉXITO !")
        print(f"🎥 VÍDEO TUTORIAL PREMIUM (16:9): {FINAL_MASTER_16_9}")
        print(f"📱 VÍDEO VIRAL SHORTS / TIKTOK (9:16): {FINAL_MASTER_9_16}")

if __name__ == "__main__":
    ejecutar_pipeline_director_viral()
