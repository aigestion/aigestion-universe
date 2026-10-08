import json
import os
import time

import requests

# Directorios de salida de Daniela OS
OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\epic_production"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generar_prompts_cinematograficos_gemini(tema):
    """
    Simula la dirección de arte con Google Gemini 1.5 Pro para generar
    prompts épicos fotorrealistas con coherencia de estilo.
    """
    print(f"🧠 [Google Gemini] Creando Dirección de Arte Épica para: {tema}...")

    # Prompts épicos diseñados bajo la estética Cyber-Corporativa de Daniela OS
    prompts_epic = [
        {
            "escena": 1,
            "prompt_imagen": "Cinematic macro shot of a sleek obsidian microchip opening to reveal a glowing cyan holographic neural core, volumetrical neon fog, 8k, Unreal Engine 5 render style, raytracing, ultra realistic",
            "movimiento_video": "Slow zoom in towards the glowing core",
            "audio": "Bienvenidos al núcleo de la inteligencia artificial distribuida."
        },
        {
            "escena": 2,
            "prompt_imagen": "A vast futuristic dark server hall with golden laser beams scanning translucent glass data crystals floating in mid-air, high contrast, cinematic depth of field, Dune aesthetic",
            "movimiento_video": "Camera panning smoothly to the right across the crystals",
            "audio": "Agentes autónomos colaborando en tiempo real con precisión milimétrica."
        },
        {
            "escena": 3,
            "prompt_imagen": "An infinite glowing blue neural network expanding over a dark horizon, gold particles floating, hyper-realistic reflections, 8k resolution, cinematic lighting",
            "movimiento_video": "Camera flying forward through the neural network",
            "audio": "El futuro de la IA no es un solo cerebro, es un ecosistema colaborativo."
        }
    ]
    return prompts_epic

def generar_imagen_free_huggingface(prompt, output_path):
    """
    Utiliza APIs públicas y gratuitas de HuggingFace para generar
    imágenes base cinematográficas (FLUX / CogView4).
    """
    print("  🎨 Generando frame de alta calidad para el prompt...")
    # URL pública de inferencia gratuita para FLUX.1-schnell
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"  ✅ Imagen HD generada correctamente -> {output_path}")
            return True
        else:
            print("  ⚠️ Servidor ocupado. Activando fallback gráfico...")
            return False
    except Exception as e:
        print(f"  ❌ Error de conexión con motor visual: {str(e)}")
        return False

def ejecutar_pipeline_epico():
    print("🚀 DANIELA OS - MOTOR MULTIMEDIA ÉPICO HÍBRIDO (Google + Open Source)\n")

    tema = "Arquitectura de Agentes IA Distribuidos y RAG Avanzado"
    escenas_epicas = generar_prompts_cinematograficos_gemini(tema)

    storyboard_final = []

    for item in escenas_epicas:
        num = item["escena"]
        print(f"\n🎬 Procesando Escena Épica #{num}")
        img_file = os.path.join(OUTPUT_DIR, f"frame_{num:02d}.jpg")

        # Generar fotograma de alta fidelidad
        exito = generar_imagen_free_huggingface(item["prompt_imagen"], img_file)

        storyboard_final.append({
            "escena": num,
            "prompt": item["prompt_imagen"],
            "movimiento": item["movimiento_video"],
            "locucion": item["audio"],
            "frame_path": img_file if exito else "mock_frame.jpg"
        })
        time.sleep(1)

    # Guardar la escaleta épica
    json_path = os.path.join(OUTPUT_DIR, "epic_storyboard.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(storyboard_final, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("✨ ¡ Escaleta Épica Lista !")
    print(f"📁 Proyecto guardado en: {json_path}")

if __name__ == "__main__":
    ejecutar_pipeline_epico()
