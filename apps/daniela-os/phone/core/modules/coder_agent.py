import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request


def auto_generate_and_execute(prompt):
    print("🤖 **DANIELA CODER AGENT**: Procesando instrucción para Ale: '" + str(prompt) + "'...")

    clean_key = os.getenv("GEMINI_API_KEY", "").strip()

    system_instruction = "Eres el Agente Programador de Daniela OS en Termux. Dada la instrucción del usuario, genera CÓDIGO PYTHON VÁLIDO que ejecute la tarea solicitada (por ejemplo usando subprocess para comandos gcloud). Responde ÚNICAMENTE con el código ejecutable, sin explicaciones, sin markdown, sin bloques de código ```python."
    prompt_text = system_instruction + "\n\nInstrucción: " + str(prompt)

    # URL estrictamente limpia
    raw_url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=){clean_key}"
    clean_url = re.sub(r"[^a-zA-Z0-9:\/\.\_\?\=\&\-]", "", raw_url).strip()

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(clean_url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)

            generated_code = res_json["candidates"][0]["content"]["parts"][0]["text"]
            clean_code = generated_code.replace("```python", "").replace("```", "").strip()

            target_script = os.path.expanduser("~/generated_task.py")
            with open(target_script, "w", encoding="utf-8") as f:
                f.write(clean_code)

            print("⚡ **EJECUTANDO CÓDIGO GENERADO DIRECTAMENTE EN TERMUX**...")
            run_res = subprocess.run(
                ["python3", target_script], capture_output=True, text=True, timeout=20
            )

            if run_res.returncode == 0:
                output = run_res.stdout.strip()
                try:
                    from google_voice import play_google_hd_voice

                    play_google_hd_voice(
                        "Ale, el código fue generado y ejecutado con éxito.", whisper_mode=False
                    )
                except Exception:
                    pass
                return "✅ **CÓDIGO EJECUTADO CON ÉXITO**:\n```\n" + output + "\n```"
            else:
                err_msg = run_res.stderr.strip()
                return "⚠️ **ERROR DE EJECUCIÓN**:\n```\n" + err_msg + "\n```"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        return "⚠️ Error en Gemini API (HTTP " + str(e.code) + "): " + err_body[:180]
    except Exception as e:
        return "⚠️ Error en Coder Agent: " + str(e)


if __name__ == "__main__":
    prompt_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "revisar espacio en disco"
    print(auto_generate_and_execute(prompt_query))
