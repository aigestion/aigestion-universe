import os
import subprocess

from gradio_client import Client

OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\native_video_production"
AUDIO_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"
FINAL_MASTER = os.path.join(OUTPUT_DIR, "daniela_wan21_master_final.mp4")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Token opcional de HuggingFace (Si tienes HF_TOKEN en tu entorno, la prioridad en cola es alta)
HF_TOKEN = os.getenv("HF_TOKEN", None)

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
    """
    Invoca el modelo Wan 2.1 (o espacio alternativo de Wan2.1 T2V) vía Gradio Client.
    """
    print("  ⚡ Invocando motor Wan 2.1 en HuggingFace Space...")
    spaces_wan = [
        "Wan-Video/Wan2.1-T2V-1.3B",
        "Wan-Video/Wan2.1",
        "multimodalart/Wan2.1-T2V-1.3B"
    ]

    for space in spaces_wan:
        try:
            print(f"     Conectando a {space}...")
            client = Client(space, hf_token=HF_TOKEN)

            # Llamada al API del Space (los argumentos estándar de Wan 2.1 son: prompt, negative_prompt, seed, steps, etc.)
            result = client.predict(
                prompt=prompt,
                negative_prompt="blurry, low quality, distorted, static picture",
                seed=42,
                api_name="/generate"
            )

            # El resultado suele ser la ruta local del archivo mp4 generado devuelto por Gradio
            if result and os.path.exists(result):
                os.replace(result, output_path)
                print(f"  ✅ [Wan 2.1] Vídeo real generado: {output_path}")
                return True
        except Exception as e:
            print(f"  ⚠️ Intento en {space} omitido: {str(e)[:100]}...")

    return False

def generar_video_cogvideox_hf(prompt: str, output_path: str):
    """
    Fallback a CogVideoX-5B en HuggingFace Space si Wan 2.1 está saturado.
    """
    print("  🚀 Invocando motor secundario CogVideoX-5B...")
    spaces_cog = [
        "THUDM/CogVideoX-5B-Space",
        "THUDM/CogVideoX-5B"
    ]

    for space in spaces_cog:
        try:
            client = Client(space, hf_token=HF_TOKEN)
            result = client.predict(
                prompt=prompt,
                num_inference_steps=50,
                guidance_scale=6.0,
                seed=42,
                api_name="/generate"
            )
            if result and os.path.exists(result):
                os.replace(result, output_path)
                print(f"  ✅ [CogVideoX] Vídeo real generado: {output_path}")
                return True
        except Exception as e:
            print(f"  ⚠️ CogVideoX en {space} ocupado: {str(e)[:100]}...")

    return False

def fusionar_video_audio(video_file, audio_file, output_file):
    """
    Sincroniza el metraje de vídeo real (.mp4) con la voz en off MP3 usando FFmpeg.
    """
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

def ejecutar_pipeline_hf_video():
    print("🚀 DANIELA OS - GRADIO CLIENT NATIVE VIDEO ENGINE (Wan 2.1 / CogVideoX)\n")

    escenas = obtener_prompts_storyboard()
    clips_listos = []

    for item in escenas:
        num = item["escena"]
        prompt = item["prompt"]
        print(f"▶️ Procesando Escena #{num}")

        raw_video = os.path.join(OUTPUT_DIR, f"hf_raw_{num:02d}.mp4")
        audio_file = os.path.join(AUDIO_DIR, f"scene_{num:02d}_voice.mp3")
        merged_video = os.path.join(OUTPUT_DIR, f"scene_{num:02d}_final.mp4")

        if not os.path.exists(audio_file):
            audio_file = os.path.join(AUDIO_DIR, "scene_01_voice.mp3")

        # 1. Intentar generación nativa con Wan 2.1
        exito = generar_video_wan21_hf(prompt, raw_video)

        # 2. Si falla Wan 2.1, intentar CogVideoX
        if not exito:
            exito = generar_video_cogvideox_hf(prompt, raw_video)

        if exito:
            # 3. Ensamblar vídeo real + voz
            fusionar_video_audio(raw_video, audio_file, merged_video)
            clips_listos.append(merged_video)
            print(f"  ✨ Escena #{num} unificada con audio.\n")

    # 4. Concatenación final del máster en 1080p
    if clips_listos:
        concat_txt = os.path.join(OUTPUT_DIR, "concat_hf.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for clip in clips_listos:
                c_escaped = clip.replace("\\", "/")
                f.write(f"file '{c_escaped}'\n")

        print("🎞️ Unificando metraje máster final...")
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
        print("✨ ¡PRODUCCIÓN CON VÍDEO REAL WAN 2.1 / COGVIDEOX FINALIZADA!")
        print(f"🎥 VÍDEO MÁSTER GENERADO: {FINAL_MASTER}")

if __name__ == "__main__":
    ejecutar_pipeline_hf_video()
