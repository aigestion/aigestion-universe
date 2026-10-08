import json
import os
import re

from openai import OpenAI

API_KEY = os.getenv("TENCENT_HUNYUAN_API_KEY", "YOUR_VALUE_HERE")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://tokenhub-us.tencentcloudmaas.com/v1"
)

def generar_storyboard_hunyuan_video(tema: str):
    prompt_sistema = (
        "Eres el Director Multimedia Máster de Daniela OS. Tu tarea es responder ÚNICAMENTE "
        "con un objeto JSON válido, sin textos introductorios ni bloques de markdown. "
        "Estructura obligatoria: 'metadata' (titulo, concepto, estilo_visual, duracion) y 'escenas' "
        "(numero_escena, duracion_segundos, prompt_visual_hunyuan en inglés fotorrealista, locucion_es, diseno_sonoro)."
    )

    prompt_usuario = f"Crea la estructura de producción multimedia completa para: {tema}"

    try:
        response = client.chat.completions.create(
            model="glm-5.2",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.6,
            max_tokens=4000
        )

        contenido_raw = response.choices[0].message.content.strip()

        # Eliminar posibles etiquetas markdown `json ... `
        contenido_raw = re.sub(r"^`(?:json)?\s*", "", contenido_raw)
        contenido_raw = re.sub(r"\s*`$", "", contenido_raw)

        return json.loads(contenido_raw)

    except json.JSONDecodeError as e:
        return {"error": f"JSON incompleto o malformado: {str(e)}", "raw_snippet": contenido_raw[-300:]}
    except Exception as e:
        return {"error": f"Error de conexión con TokenHub: {str(e)}"}

if __name__ == "__main__":
    print("🚀 Daniela OS - Generando Storyboard Estructurado Completo...")
    tema_proyecto = "Arquitectura de Agentes IA Distribuidos y RAG Avanzado"
    resultado = generar_storyboard_hunyuan_video(tema_proyecto)

    if "error" in resultado:
        print("\n⚠️ Ocurrió un problema:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        print("\n✅ ¡Storyboard JSON generado y validado con éxito!")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

        # Guardar en archivo utilizando json.dump (método correcto para archivos)
        ruta_salida = r"C:\Users\Alejandro\aig\prototypes\storyboard_production.json"
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Archivo de producción guardado en: {ruta_salida}")
