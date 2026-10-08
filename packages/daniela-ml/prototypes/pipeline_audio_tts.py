import asyncio
import json
import os

STORYBOARD_PATH = r"C:\Users\Alejandro\aig\prototypes\storyboard_production.json"
AUDIO_OUTPUT_DIR = r"C:\Users\Alejandro\aig\prototypes\rendered_audio"

# Voz neuronal en español por defecto (Elegante y clara)
VOICE_NAME = "es-ES-AlvaroNeural"  # Alternativa: "es-ES-ElviraNeural" o "es-MX-JorgeNeural"

def cargar_storyboard(ruta_file):
    if not os.path.exists(ruta_file):
        raise FileNotFoundError(f"No se encontró el archivo storyboard en: {ruta_file}")
    with open(ruta_file, encoding="utf-8") as f:
        return json.load(f)

async def generar_audio_edge(texto: str, ruta_salida: str):
    import edge_tts
    communicate = edge_tts.Communicate(texto, VOICE_NAME)
    await communicate.save(ruta_salida)

def generar_audio_gtts(texto: str, ruta_salida: str):
    from gtts import gTTS
    tts = gTTS(text=texto, lang='es')
    tts.save(ruta_salida)

async def procesar_locuciones():
    print("🎙️ Daniela OS - Pipeline de Síntesis de Voz (TTS)\n")

    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

    try:
        storyboard = cargar_storyboard(STORYBOARD_PATH)
    except Exception as e:
        print(f"❌ Error al cargar storyboard: {str(e)}")
        return

    escenas = storyboard.get("escenas", [])
    print(f"🗣️ Total de escenas a sintetizar: {len(escenas)}\n")
    print("=" * 60)

    # Comprobar qué motor TTS está disponible
    use_edge = True
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        use_edge = False
        print("⚠️ 'edge-tts' no está instalado. Utilizando 'gTTS' como alternativa...")

    for escena in escenas:
        num_escena = escena.get("numero_escena")
        locucion = escena.get("locucion_es", "")
        duracion_target = escena.get("duracion_segundos", 10)

        output_file = os.path.join(AUDIO_OUTPUT_DIR, f"scene_{num_escena:02d}_voice.mp3")

        print(f"\n▶️ Generando voz para Escena #{num_escena} ({duracion_target}s proyectados)")
        print(f"   Guion: \"{locucion}\"")

        try:
            if use_edge:
                await generar_audio_edge(locucion, output_file)
            else:
                generar_audio_gtts(locucion, output_file)

            print(f"  🔊 [Escena {num_escena}] Audio generado -> {output_file}")
        except Exception as e:
            print(f"  ❌ Error al sintetizar Escena #{num_escena}: {str(e)}")

    print("\n" + "=" * 60)
    print("✨ ¡Pipeline de Audio finalizado!")
    print(f"📁 Locuciones MP3 guardadas en: {AUDIO_OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(procesar_locuciones())
