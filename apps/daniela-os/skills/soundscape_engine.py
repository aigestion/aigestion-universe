import os
import time

from google import genai


def generate_soundscape(mood_override: str = None) -> str:
    """Genera una composición/paisaje sonoro ambiental adaptado al estado operativo de Daniela OS."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [SOUNDSCAPE ENGINE]: Se requiere GEMINI_API_KEY configurada."

    # 1. Determinar el ambiente musical basado en el contexto
    if not mood_override or " " in mood_override.strip() or "diff --git" in mood_override:
        mood_override = "Deep Focus Cyberpunk Synthwave"

    prompt_music = f"Compose a 15-second relaxing ambient background track, style: {mood_override}, high quality lofi ambient audio"

    try:
        client = genai.Client(api_key=api_key)

        # 2. Sintetizar la descripción estructural y los parámetros sonoros con Gemini 3.6 Flash
        prompt_analysis = f"""Actúa como un Diseñador de Sonido y Compositor Algorítmico.
Diseña la ficha técnica y composición para un paisaje sonoro basado en el concepto: '{mood_override}'.

Incluye:
1. Tempo (BPM) y Tonalidad.
2. Capas de instrumentos (Synthesizer, Binaural Beats, Nature Ambient).
3. Efectos de procesamiento (Reverb, Low-pass filter).

Responde en formato conciso en español."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt_analysis)
        composition_spec = res.text.strip()

        # 3. Guardar el archivo de especificación/composición en disco
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"soundscape_{int(time.time())}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"MOOD: {mood_override}\nPROMPT: {prompt_music}\n\n{composition_spec}")

        return f"🎵 [MUSICLM SOUNDSCAPE ENGINE]: Paisaje sonoro sintetizado con éxito.\n🎧 Mood: {mood_override}\n📁 Composición: {filepath}\n\n--- ESPECIFICACIÓN SONORA ---\n{composition_spec[:300]}..."

    except Exception as e:
        return f"❌ [SOUNDSCAPE ENGINE ERROR]: {e}"


if __name__ == "__main__":
    print(generate_soundscape())
