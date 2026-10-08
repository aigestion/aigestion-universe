import os
import subprocess

from google import genai


def speak_morph(text: str, mood: str = "neutral") -> str:
    """Modula la voz mediante SSML y la ejecuta vía espeak-ng."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [VOICE MORPH]: Se requiere GEMINI_API_KEY."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""Actúa como un Diseñador de Prosodia para Daniela OS.
Texto: '{text}'
Mood/Contexto: {mood}

Genera el texto formateado en SSML (Speech Synthesis Markup Language) para ajustar el tono (pitch), la tasa (rate) y el énfasis para sonar:
- {mood.upper()}.
Devuelve solo el string SSML limpio."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        res.text.strip().replace("```xml", "").replace("```", "")

        # Ejecución local vía espeak-ng
        # espeak-ng soporta etiquetas básicas; para control avanzado, usamos parámetros de comando
        if "alerta" in mood.lower() or "emergencia" in mood.lower():
            cmd = ["espeak-ng", "-s", "180", "-p", "70", "-a", "200", text]
        else:
            cmd = ["espeak-ng", "-s", "140", "-p", "40", "-a", "150", text]

        subprocess.run(cmd, check=True)
        return f"🎙️ [SOVEREIGN VOICE]: Mensaje emitido en modo {mood.upper()}."

    except Exception as e:
        return f"❌ [VOICE MORPH ERROR]: {e}"


if __name__ == "__main__":
    print(speak_morph("Sistema asegurado, todos los protocolos online.", "calm"))
