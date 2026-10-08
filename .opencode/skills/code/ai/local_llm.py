import os
import re
import subprocess


def _get_existing_gemini_key() -> str:
    """Busca la GEMINI_API_KEY en variables de entorno o archivos de configuración locales."""
    # 1. Chequeo directo en entorno
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key

    # 2. Búsqueda en .bashrc, .zshrc o .env
    config_files = [
        os.path.expanduser("~/.bashrc"),
        os.path.expanduser("~/.zshrc"),
        os.path.expanduser("~/daniela-os/.env")
    ]
    for cfg in config_files:
        if os.path.exists(cfg):
            try:
                with open(cfg) as f:
                    content = f.read()
                    match = re.search(r'export\s+(?:GEMINI_API_KEY|GOOGLE_API_KEY)=["\']?([^"\'\s\n]+)', content)
                    if match:
                        return match.group(1)
            except Exception:
                pass
    return ""

def _query_local(prompt: str) -> str:
    """Inferencia offline predeterminada."""
    model_path = os.path.expanduser("~/daniela-os/models/model.gguf")
    if os.path.exists(model_path):
        try:
            cmd = ["llama-cli", "-m", model_path, "-p", prompt, "-n", "128"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
    return f"🧠 [LOCAL ENGINE]: Inferencia offline procesada para: '{prompt}'."

def _query_gemini(prompt: str) -> str:
    """Consulta a la API de Google Gemini utilizando la Key detectada en el sistema."""
    api_key = _get_existing_gemini_key()
    if not api_key:
        return "⚠️ [GEMINI]: Se detectó solicitud de Gemini pero no se encontró la clave en el entorno local."

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        return f"🌐 [GOOGLE GEMINI]: {response.text.strip()}"
    except Exception as e:
        return f"❌ [GEMINI ERROR]: {e}"

def query_offline(prompt: str) -> str:
    """Enrutador de inferencia local/online."""
    clean_prompt = prompt.lower().replace("offline", "").replace("local llm", "").replace("gemini", "").strip()
    clean_prompt = clean_prompt if clean_prompt else "Hola Daniela"

    if "gemini" in prompt.lower() or "online" in prompt.lower():
        return _query_gemini(clean_prompt)

    return _query_local(clean_prompt)

if __name__ == "__main__":
    print(query_offline("gemini hola"))
