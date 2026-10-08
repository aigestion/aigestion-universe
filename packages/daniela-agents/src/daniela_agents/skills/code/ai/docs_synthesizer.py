import os

from google import genai


def generate_system_prd_doc() -> str:
    """Escanea las skills locales y crea una especificación técnica."""
    skills_dir = os.path.expanduser("~/daniela-os/skills")
    if not os.path.exists(skills_dir):
        return "❌ [DOCS SYNTHESIZER]: No existe directorio de skills."

    skills_files = [f for f in os.listdir(skills_dir) if f.endswith('.py') and not f.startswith('__')]
    inventory = f"Daniela OS v32.0 - Total Skills: {len(skills_files)}\nInventario:\n" + "\n".join(f"- {f}" for f in sorted(skills_files))

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [DOCS SYNTHESIZER]: Se requiere GEMINI_API_KEY."

    prompt = f"Genera un resumen ejecutivo de la arquitectura de Daniela OS en 4 párrafos basado en esto:\n{inventory}"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        prd_text = response.text.strip()
        return f"📄 [DOCS SYNTHESIZER PRD]:\n\n{prd_text}"
    except Exception as e:
        return f"❌ [DOCS SYNTHESIZER ERROR]: {e}"

if __name__ == "__main__":
    print(generate_system_prd_doc())
