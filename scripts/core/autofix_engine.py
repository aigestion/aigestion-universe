import os
import re
import subprocess
import sys

import requests

LOG_FILE = "daniela_audit.log"
DB_FILE = "daniela_multiuser.db"

def load_env():
    if os.path.exists('.env'):
        for line in open('.env'):
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip('\'"')

def get_last_traceback():
    if not os.path.exists(LOG_FILE):
        return None, None

    with open(LOG_FILE, encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extraer el último Traceback y el archivo afectado
    matches = list(re.finditer(r'Traceback \(most recent call last\):[\s\S]+?([a-zA-Z0-9_\-/]+\.py)", line \d+', content))
    if not matches:
        return None, None

    last_match = matches[-1]
    traceback_text = content[last_match.start():]

    # Extraer ruta del archivo defectuoso
    file_match = re.search(r'File "([^"]+\.py)"', traceback_text)
    target_file = file_match.group(1) if file_match else None

    return traceback_text.strip(), target_file

def query_openrouter_patch(traceback_str, source_code):
    load_env()
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        return None

    sys_prompt = (
        "Eres el motor de Auto-Healing de Daniela OS (Termux/SQLite). "
        "Recibirás un Traceback de error y el código fuente completo del archivo. "
        "Devuelve ÚNICAMENTE el código fuente corregido en un bloque ejecutable de Python sin explicaciones adicionales."
    )

    user_prompt = f"TRACEBACK:\n{traceback_str}\n\nCÓDIGO FUENTE ACTUAL:\n{source_code}"

    models = ['nvidia/nemotron-3.5-lightning:free', 'liquid/lfm-2.5-2.6b:free']

    for m in models:
        try:
            r = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {key}', 'HTTP-Referer': 'http://localhost:8082', 'X-Title': 'Daniela OS AutoFix'},
                json={'model': m, 'messages': [{'role': 'system', 'content': sys_prompt}, {'role': 'user', 'content': user_prompt}]},
                timeout=6
            )
            if r.status_code == 200:
                raw_reply = r.json()['choices'][0]['message']['content']
                # Extraer bloque de código
                code_match = re.search(r'```python([\s\S]+?)```', raw_reply)
                return code_match.group(1).strip() if code_match else raw_reply.strip()
        except Exception:
            continue
    return None

def test_and_apply_fix(target_file, new_code):
    if not os.path.exists(target_file):
        return False, "Archivo destino no encontrado"

    # Guardar copia de seguridad temporal
    with open(target_file, encoding='utf-8') as f:
        original_code = f.read()

    # Aplicar el parche
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_code)

    # Validar sintaxis con py_compile
    res = subprocess.run([sys.executable, '-m', 'py_compile', target_file], capture_output=True, text=True)
    if res.returncode != 0:
        # Revertir cambios si la sintaxis falla
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(original_code)
        return False, f"Error de sintaxis en el parche: {res.stderr}"

    # Auto-commit en Git
    subprocess.run(['git', 'add', target_file], capture_output=True)
    subprocess.run(['git', 'commit', '-m', f'fix(autofix): Auto-reparado {os.path.basename(target_file)} vía Skill 58'], capture_output=True)

    return True, f"Parche validado y aplicado con éxito en {target_file}"

def main():
    print("🛠️ [AUTO-HEALING] Analizando logs de auditoría...")
    traceback_str, target_file = get_last_traceback()

    if not traceback_str or not target_file:
        print("✅ No se detectaron fallos críticos o Tracebacks en los logs.")
        return

    print(f"⚠️ Traceback detectado en: {target_file}")

    if not os.path.exists(target_file):
        print(f"❌ El archivo {target_file} no existe en el espacio de trabajo local.")
        return

    with open(target_file, encoding='utf-8') as f:
        source_code = f.read()

    print("🤖 Generando solución con OpenRouter AI Core...")
    fixed_code = query_openrouter_patch(traceback_str, source_code)

    if not fixed_code:
        print("❌ No se pudo obtener un parche válido desde la API.")
        return

    success, msg = test_and_apply_fix(target_file, fixed_code)
    print(f"{'✅' if success else '❌'} {msg}")

if __name__ == '__main__':
    main()
