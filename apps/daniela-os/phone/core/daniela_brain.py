import os
import sys

import requests


def load_env() -> None:
    env_p = os.path.expanduser("~/apps/aig/.env")
    if os.path.exists(env_p):
        with open(env_p, encoding="utf-8", errors="ignore") as f:
            for ln in f:
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    k, v = ln.split("=", 1)
                    k, v = k.strip(), v.strip().strip("\"'")
                    if not os.getenv(k):
                        os.environ[k] = v


load_env()

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_PERSONAL_API_KEY")

SYSTEM_INSTRUCTION = (
    "Eres Daniela OS, la IA táctica y asistente conversacional del Google Pixel. "
    "Responde siempre en español neutro, cercano, dinámico y natural (máximo 2 a 3 frases cortas)."
)


def query_daniela(user_prompt: str) -> str:
    if not user_prompt:
        return "Hola, ¿en qué te ayudo hoy?"

    # 1. OpenRouter (Modelos Gratuitos Ultra-rápidos: Gemini 2.5/Llama 3.3)
    if OPENROUTER_KEY:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "google/gemini-2.5-flash:free",
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 100,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=3.0)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # 2. DeepSeek API (Fallback 1)
    if DEEPSEEK_KEY:
        try:
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 100,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=3.0)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # 3. Google AI Studio (Fallback 2 si hay Gemini Key tipo AIza...)
    if GEMINI_KEY and GEMINI_KEY.startswith("AIza"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"maxOutputTokens": 100, "temperature": 0.4},
            }
            r = requests.post(url, json=payload, timeout=2.5)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    return "Sistemas tácticos operando en modo de resiliencia local."


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "¿Cuál es tu estado actual?"
    print(query_daniela(query))
