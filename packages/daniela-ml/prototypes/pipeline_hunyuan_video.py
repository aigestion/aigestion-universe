import json
import os
import time
from typing import Any

import requests

# Ruta al archivo de storyboard generado anteriormente
STORYBOARD_PATH = r"C:\Users\Alejandro\aig\prototypes\storyboard_production.json"
OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_videos"

# API Keys para la generación de vídeo (Configurar en  si usas proveedor en la nube)
FAL_KEY = os.getenv("FAL_KEY", "")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

def cargar_storyboard(ruta_file):
    if not os.path.exists(ruta_file):
        raise FileNotFoundError(f"No se encontró el archivo storyboard en: {ruta_file}")

    with open(ruta_file, encoding="utf-8") as f:
        data = json.load(f)
    return data

def enviar_prompt_hunyuan_api_fal(prompt_visual: str, escena_id: int):
    """
    Envía la solicitud de generación de vídeo utilizando la API de HunyuanVideo en fal.ai
    """
    url = "https://queue.fal.run/fal-ai/hunyuan-video"
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload: dict[str, Any] = {
        "prompt": prompt_visual,
        "aspect_ratio": "16:9",
        "resolution": "720p",
        "num_frames": 129,
        "pro_mode": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code in [200, 201, 202]:
            res_json = response.json()
            request_id = res_json.get("request_id", "N/A")
            print(f"  ✅ [Escena {escena_id}] Tarea enviada a Fal.ai. Request ID: {request_id}")
            return {"status": "success", "request_id": request_id, "provider": "fal.ai"}
        else:
            print(f"  ❌ [Escena {escena_id}] Error HTTP {response.status_code}: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        print(f"  ❌ [Escena {escena_id}] Excepción de red: {str(e)}")
        return {"status": "error", "message": str(e)}

def simular_generacion_local(prompt_visual: str, escena_id: int, duracion: int):
    """
    Simula el envío al pipeline local de HunyuanVideo (para desarrollo/pruebas)
    """
    print(f"  ⚙️ [Escena {escena_id}] Preparando tensores para HunyuanVideo Local...")
    print(f"     Prompt: \"{prompt_visual[:75]}...\"")
    print(f"     Duración requerida: {duracion}s (129 frames @ 24fps)")
    time.sleep(1.5)  # Simulación de encolado en GPU
    video_mock_path = os.path.join(OUTPUT_DIR, f"scene_{escena_id:02d}_hunyuan.mp4")
    print(f"  🎬 [Escena {escena_id}] Renderizado simulado correctamente -> {video_mock_path}")
    return {"status": "simulated", "output_file": video_mock_path}

def procesar_pipeline_multimedia():
    print("🚀 Daniela OS - Pipeline de Generación de Vídeo Hunyuan\n")

    # Asegurar que el directorio de salida existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        storyboard = cargar_storyboard(STORYBOARD_PATH)
    except Exception as e:
        print(f"❌ Error al cargar storyboard: {str(e)}")
        return

    metadata = storyboard.get("metadata", {})
    escenas = storyboard.get("escenas", [])

    print(f"📋 Proyecto: {metadata.get('titulo', 'Sin Título')}")
    print(f"🎨 Estilo Visual: {metadata.get('estilo_visual', 'Standard')}")
    print(f"⏱️ Duración Total: {metadata.get('duracion', 'N/A')}")
    print(f"🎥 Total Escenas a procesar: {len(escenas)}\n")
    print("=" * 60)

    resultados_pipeline = []

    for escena in escenas:
        num_escena = escena.get("numero_escena")
        duracion = escena.get("duracion_segundos", 10)
        prompt_hunyuan = escena.get("prompt_visual_hunyuan", "")
        locucion = escena.get("locucion_es", "")

        print(f"\n▶️ Procesando Escena #{num_escena} ({duracion} seg)")
        print(f"   Locución (ES): \"{locucion[:60]}...\"")

        # Si existe una clave API activa de Fal.ai la usa; de lo contrario usa el modo simulación local
        if FAL_KEY:
            resultado = enviar_prompt_hunyuan_api_fal(prompt_hunyuan, num_escena)
        else:
            resultado = simular_generacion_local(prompt_hunyuan, num_escena, duracion)

        resultados_pipeline.append({
            "escena": num_escena,
            "prompt": prompt_hunyuan,
            "resultado": resultado
        })

    print("\n" + "=" * 60)
    print("✨ ¡Pipeline finalizado con éxito!")
    print(f"📁 Los archivos de vídeo procesados se guardarán en: {OUTPUT_DIR}")

if __name__ == "__main__":
    procesar_pipeline_multimedia()
