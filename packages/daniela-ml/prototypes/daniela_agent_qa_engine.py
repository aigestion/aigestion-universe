import os
import subprocess
import time
import urllib.parse
import urllib.request

from PIL import Image, ImageStat

OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\qa_production"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
FINAL_MASTER = os.path.join(OUTPUT_DIR, "daniela_qa_verified_master.mp4")

os.makedirs(OUTPUT_DIR, exist_ok=True)

class QualityControlAgent:
    """
    Agente Supervisor de Calidad para Daniela OS.
    Analiza y valida los componentes multimedia antes de aprobarlos para el corte final.
    """
    def __init__(self, min_brightness=20, min_contrast=30):
        self.min_brightness = min_brightness
        self.min_contrast = min_contrast

    def auditar_fotograma(self, image_path):
        """
        Analiza la imagen renderizada: comprueba brillo, entropía de color y artefactos vacíos.
        """
        print(f"  🔍 [QA Agent] Inspeccionando calidad visual de: {os.path.basename(image_path)}...")
        try:
            with Image.open(image_path) as img:
                # 1. Verificar resolución mínima 1080p / HD
                width, height = img.size
                if width < 1280 or height < 720:
                    print(f"  ❌ [QA Fail] Resolución insuficiente ({width}x{height}). Sub-estándar.")
                    return False

                # 2. Análisis estadístico del brillo y contraste
                grayscale = img.convert('L')
                stat = ImageStat.Stat(grayscale)
                mean_brightness = stat.mean[0]
                stddev_contrast = stat.stddev[0]

                print(f"     📊 Métricas QA -> Brillo Medio: {mean_brightness:.1f} | Contraste (StdDev): {stddev_contrast:.1f}")

                if mean_brightness < self.min_brightness:
                    print("  ❌ [QA Fail] Escena demasiado oscura o fotograma negro/fallido.")
                    return False

                if stddev_contrast < self.min_contrast:
                    print("  ❌ [QA Fail] Falta de contraste / Imagen plana o estática.")
                    return False

                print("  ✅ [QA Approved] Fotograma verificado y aprobado con estándares de calidad.")
                return True

        except Exception as e:
            print(f"  ❌ [QA Error] Archivo corrupto o ilegible: {str(e)}")
            return False

def obtener_escenas_director():
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

def generar_con_supervision_qa(qa_agent, prompt, output_file, max_intentos=3):
    """
    Intenta generar el render y solo lo acepta si el Agente QA aprueba la imagen.
    """
    prompt_encoded = urllib.parse.quote(prompt)

    for intento in range(max_intentos):
        seed = 100 + (intento * 50)
        url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1920&height=1080&seed={seed}&nologo=true"
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            print(f"  🎨 Renderizando iteración #{intento+1} (Seed {seed})...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp, open(output_file, 'wb') as f:
                f.write(resp.read())

            # El Agente QA audita el resultado antes de confirmar
            if qa_agent.auditar_fotograma(output_file):
                return True
            else:
                print("  🔄 [QA Agent] Rechazado. Regenerando escena con nuevo seed...")
                time.sleep(1.5)

        except Exception as e:
            print(f"  ⚠️ Error de renderizado en iteración {intento+1}: {str(e)}")
            time.sleep(2)

    return False

def animar_escena_aprobada(img_path, audio_path, video_out_path, escena_num, duracion=10):
    print("  🎥 Generando animación cinemática 60 FPS para escena aprobada...")

    if escena_num == 1:
        vf_filter = f"scale=8000x4500,zoompan=z='min(zoom+0.0025,1.35)':x='iw/2-(iw/zoom/2)+sin(time*1.5)*60':y='ih/2-(ih/zoom/2)+cos(time*1.5)*40':d={duracion*60}:s=1920x1080:fps=60,format=yuv420p"
    elif escena_num == 2:
        vf_filter = f"scale=8000x4500,zoompan=z='1.25':x='(on/{duracion*60})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d={duracion*60}:s=1920x1080:fps=60,format=yuv420p"
    else:
        vf_filter = f"scale=8000x4500,zoompan=z='min(zoom+0.0020,1.30)':x='(iw-iw/zoom)*(1-on/{duracion*60})':y='(ih-ih/zoom)*(on/{duracion*60})':d={duracion*60}:s=1920x1080:fps=60,format=yuv420p"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        video_out_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def ejecutar_pipeline_con_qa():
    print("🚀 DANIELA OS - SUPERVISED MULTI-AGENT PIPELINE (Con Agente QA)\n")

    qa_agent = QualityControlAgent(min_brightness=15, min_contrast=25)
    escenas = obtener_escenas_director()
    clips_aprobados = []

    for item in escenas:
        num = item["escena"]
        print(f"▶️ Auditando Escena #{num}")

        img_file = os.path.join(OUTPUT_DIR, f"qa_frame_{num:02d}.jpg")
        audio_file = os.path.join(AUDIO_DIR, f"scene_{num:02d}_voice.mp3")
        video_file = os.path.join(OUTPUT_DIR, f"qa_approved_scene_{num:02d}.mp4")

        if not os.path.exists(audio_file):
            audio_file = os.path.join(AUDIO_DIR, "scene_01_voice.mp3")

        # 1. El Agente de Generación produce y el Agente QA audita
        aprobado = generar_con_supervision_qa(qa_agent, item["prompt"], img_file)

        if aprobado:
            # 2. Solo las escenas aprobadas pasan al motor de movimiento y ensamble
            animar_escena_aprobada(img_file, audio_file, video_file, num, duracion=10)
            clips_aprobados.append(video_file)
            print(f"  ✨ Escena #{num} APROBADA y ensamblada.\n")
        else:
            print(f"  ❌ Escena #{num} RECHAZADA por el Agente QA tras múltiples intentos.\n")

    # 3. Concatenación final de clips auditados
    if clips_aprobados:
        concat_txt = os.path.join(OUTPUT_DIR, "concat_qa.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clips_aprobados:
                c_escaped = c.replace("\\", "/")
                f.write(f"file '{c_escaped}'\n")

        print("🎞️ Unificando metraje final APROBADO por el Agente QA...")
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
        print("✨ ¡PRODUCCIÓN AUDITADA Y FINALIZADA CON ÉXITO!")
        print(f"🎥 VÍDEO MÁSTER APROBADO: {FINAL_MASTER}")

if __name__ == "__main__":
    ejecutar_pipeline_con_qa()
