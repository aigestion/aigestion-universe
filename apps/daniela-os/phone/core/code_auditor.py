import ast
import os

import requests

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

PATHS_TO_AUDIT = [os.path.expanduser("~/core"), os.path.expanduser("~/apps/AIGESTION-MONOREPO")]


def check_syntax(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            ast.parse(f.read(), filename=file_path)
        return True, None
    except Exception as e:
        return False, str(e)


def auto_heal_file(file_path, error_msg):
    if not GEMINI_KEY:
        print(f"⚠️ Imposible auto-reparar {file_path}: GEMINI_API_KEY no detectada.")
        return False

    print(f"🛠️ Intentando auto-reparación con IA para: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        code_content = f.read()

    prompt = (
        f"Corrige el siguiente código Python de Daniela OS que falló con este error:\n"
        f"ERROR: {error_msg}\n\n"
        f"CÓDIGO ORIGINAL:\n```python\n{code_content}\n```\n\n"
        f"Devuelve ÚNICAMENTE el código Python corregido, sin bloques markdown extra ni explicaciones."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }

    try:
        r = requests.post(url, json=payload, timeout=10.0)
        if r.status_code == 200:
            fixed_code = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            if fixed_code.startswith("```python"):
                fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
            elif fixed_code.startswith("```"):
                fixed_code = fixed_code.split("```")[1].split("```")[0].strip()

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            print(f"✅ Archivo auto-reparado con éxito: {file_path}")
            return True
    except Exception as e:
        print(f"❌ Error en auto-reparación: {e}")
    return False


def audit_and_heal():
    print("==================================================")
    print("🛡️ DANIELA OS - AGENTE SELF-HEALING CODE")
    print("==================================================")

    total_files = 0
    errors_found = 0

    for path in PATHS_TO_AUDIT:
        if not os.path.exists(path):
            continue
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    total_files += 1
                    full_path = os.path.join(root, file)
                    is_valid, err = check_syntax(full_path)
                    if not is_valid:
                        errors_found += 1
                        print(f"❌ Error de sintaxis en: {full_path}\n   Details: {err}")
                        auto_heal_file(full_path, err)

    if errors_found == 0:
        print(f"✨ Todos los {total_files} archivos Python auditados están limpios y funcionales.")


if __name__ == "__main__":
    audit_and_heal()
