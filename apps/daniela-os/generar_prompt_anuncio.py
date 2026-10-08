import json
import os

BASE_DIR = os.path.expanduser("~/daniela-os/research")
os.makedirs(BASE_DIR, exist_ok=True)

prompt_anuncio_premium = {
    "proyecto": "Anuncio Comercial Premium - AIGestion.net",
    "personaje": "Daniela (Ciber-Ejecutiva con traje de alta costura futurista)",
    "escenario": "Oficina virtual de cristal con vistas nocturnas a una metrópolis ciberpunk, iluminación neón cian y magenta",
    "prompt_imagen3": (
        "Cinematic high-end commercial photo of Daniela, an elegant AI executive woman "
        "wearing a sleek futuristic dark suit in a luxurious virtual glass office. "
        "Surrounded by interactive holographic data dashboards displaying AIGestion.net metrics. "
        "Neon cyan and magenta rim lighting, 8k resolution, photorealistic, ultra-detailed."
    ),
    "estructura_guion": [
        "Plano 1: Entrada triunfal a la oficina virtual de AIGestion.net",
        "Plano 2: Daniela interactuando con holograma de datos burocráticos",
        "Plano 3: Transformación del caos en métricas de rendimiento en verde",
        "Plano 4: Cierre con logotipo AIGestion.net y llamada a la acción",
    ],
}

file_path = os.path.join(BASE_DIR, "prompt_anuncio_premium.json")
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(prompt_anuncio_premium, f, indent=2, ensure_ascii=False)

print(f"✨ [PROMPT GENERADO]: Estructura de anuncio premium guardada en: {file_path}")
