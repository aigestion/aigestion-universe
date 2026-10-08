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

def _git(*args, timeout=60):
    """git sin shell. Devuelve (rc, stdout). Nunca lanza."""
    try:
        from safe_exec import run_cmd

        r = run_cmd(["git", *args], timeout=timeout)
        return r.returncode, (r.stdout or "").strip()
    except Exception as e:
        return 1, str(e)[:200]


def test_and_apply_fix(target_file, new_code, rama_auto=True, merge_if_green=False):
    """Aplica un parche pasando por el Safe Gate (Fase 3, idea #9).

    NUNCA commitea en la rama original: crea `autofix/<fich>-<ts>`,
    commitea ahi, corre el gate quick y vuelve a la rama original.
    Solo fusiona con merge_if_green=True Y gate verde.
    Devuelve (ok, mensaje). Nunca lanza.
    """
    if not os.path.exists(target_file):
        return False, "Archivo destino no encontrado"

    # Guardar copia de seguridad temporal
    with open(target_file, encoding='utf-8') as f:
        original_code = f.read()

    def _revertir():
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(original_code)
        except OSError:
            pass

    # Aplicar el parche
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_code)

    # Validar sintaxis con py_compile
    res = subprocess.run([sys.executable, '-m', 'py_compile', target_file], capture_output=True, text=True)
    if res.returncode != 0:
        # Revertir cambios si la sintaxis falla
        _revertir()
        return False, f"Error de sintaxis en el parche: {res.stderr}"

    if not rama_auto:
        # Modo legacy (solo pruebas): parche en arbol, sin commit.
        return True, f"Parche validado (sin commit) en {target_file}"

    # Rama dedicada: jamas tocar la original sin gate verde.
    rc, original = _git("rev-parse", "--abbrev-ref", "HEAD")
    original = original if rc == 0 else "main"
    # Solo bloquean cambios YA versionados en el fichero objetivo
    # (no borraría ediciones del usuario; untracked ajenos no importan).
    rc, estado = _git("status", "--porcelain", "--", target_file)
    tocado = any(lin[:2].strip() and not lin.startswith("??")
                 for lin in estado.splitlines()) if rc == 0 else True
    if rc != 0 or tocado:
        _revertir()
        return False, "El fichero tiene cambios sin commitear: parche revertido, nada commiteado"

    import time

    rama = f"autofix/{os.path.basename(target_file)}-{int(time.time())}"
    rc, out = _git("checkout", "-b", rama)
    if rc != 0:
        _revertir()
        return False, f"No se pudo crear la rama: {out[:150]}"

    _git("add", target_file)
    rc, out = _git("commit", "-m",
                   f"fix(autofix): parche en rama {rama} para {os.path.basename(target_file)}")
    if rc != 0:
        _git("checkout", original)
        _revertir()
        return False, f"Commit fallo: {out[:150]}"

    # Gate sobre la rama con el parche.
    try:
        from sil.safe_gate import evaluar_gate, fusionar_si_verde

        gate = evaluar_gate("quick")
    except Exception as e:
        gate = {"ok": False, "fallidos": ["gate"], "error": str(e)[:200]}

    _git("checkout", original)

    if not gate.get("ok"):
        return False, (f"Gate en rojo en {rama} "
                       f"(fallidos: {gate.get('fallidos')}). Rama conservada para revision.")

    if merge_if_green:
        fusion = fusionar_si_verde(rama, nivel="quick")
        if fusion.get("ok"):
            return True, f"Parche validado, gate verde y fusionado desde {rama}"
        return False, f"Gate verde pero fusion fallo: {fusion.get('error')} (rama {rama} conservada)"

    return True, f"Parche validado y gate verde en {rama}. Fusiona con: safe_gate.py fusionar {rama}"

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
