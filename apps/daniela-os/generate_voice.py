import asyncio
import sys

import edge_tts


async def main():
    text = sys.argv[1] if len(sys.argv) > 1 else "Hola, soy Daniela. Bienvenido a AIGestion Studio."
    output_file = "static/response.mp3"

    # Voz española humana de alta fidelidad (Elvira - Neuronal)
    communicate = edge_tts.Communicate(text, "es-ES-ElviraNeural")
    await communicate.save(output_file)
    print("✅ Audio de Daniela generado con éxito:", output_file)


if __name__ == "__main__":
    asyncio.run(main())
