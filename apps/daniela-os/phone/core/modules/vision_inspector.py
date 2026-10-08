import base64
import os
import subprocess
import sys

import requests

sys.path.append(os.path.expanduser("~/apps/aig/phone/core/modules"))

from token_failover import get_active_api_key

PHOTO_PATH = os.path.expanduser("~/captura_enfrente.jpg")


def get_available_vision_models(api_key):
    endpoints = ["v1beta", "v1"]
    discovered = []

    for ver in endpoints:
        url = f"https://generativelanguage.googleapis.com/{ver}/models?key={api_key}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods and (
                        "flash" in m["name"] or "vision" in m["name"] or "pro" in m["name"]
                    ):
                        model_id = m["name"].replace("models/", "")
                        discovered.append((ver, model_id))
        except Exception:
            continue

    fallback_models = [
        ("v1beta", "gemini-flash-lite-latest"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash"),
    ]
    return discovered if discovered else fallback_models


def capture_and_analyze_front():
    print("📸 **INICIANDO CAPTURA CON CÁMARA TRASERA EN PIXEL**...")

    if os.path.exists(PHOTO_PATH):
        try:
            os.remove(PHOTO_PATH)
        except Exception:
            pass

    try:
        subprocess.run(
            ["termux-camera-photo", "-c", "0", PHOTO_PATH],
            capture_output=True,
            text=True,
            timeout=6,
        )
        if not os.path.exists(PHOTO_PATH) or os.path.getsize(PHOTO_PATH) == 0:
            return "⚠️ La cámara del Pixel no generó una foto (verifica permisos de Cámara en Termux:API)."
    except subprocess.TimeoutExpired:
        return "⚠️ Timeout en cámara del Pixel."
    except Exception as e:
        return "⚠️ Error al acceder a la cámara: " + str(e)

    try:
        with open(PHOTO_PATH, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        return "⚠️ Error al procesar la imagen: " + str(e)

    api_key = get_active_api_key()
    if not api_key:
        return "❌ No se encontró API Key válida."

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Describe de forma concisa y profesional lo que ves en esta imagen para Ale. Si hay código, texto u objetos clave, menciónalos."
                    },
                    {"inline_data": {"mime_type": "image/jpeg", "data": encoded_string}},
                ]
            }
        ]
    }

    target_models = get_available_vision_models(api_key)
    last_err = ""

    for api_ver, model_name in target_models:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={api_key}"
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                analysis = r.json()["candidates"][0]["content"]["parts"][0]["text"]

                try:
                    from google_voice import play_google_hd_voice

                    play_google_hd_voice(
                        "Ale, he analizado lo que tienes enfrente. " + analysis[:120] + "...",
                        whisper_mode=False,
                    )
                except Exception:
                    pass

                return (
                    f"👁️ **ANÁLISIS MULTIMODAL CON {model_name.upper()} ({api_ver}) PARA ALE**:\n\n"
                    + analysis
                )
            else:
                last_err = f"[{api_ver}/{model_name} HTTP {r.status_code}]: " + r.text[:100]
        except Exception as e:
            last_err = str(e)
            continue

    return "⚠️ Error en la API de Visión: " + last_err
