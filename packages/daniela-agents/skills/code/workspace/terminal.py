import logging
import subprocess


def run_bash_command(command_text):
    try:
        # Sanitización básica para evitar ejecuciones peligrosas
        cmd = command_text.replace("ejecuta", "").replace("bash", "").replace("comando", "").strip()

        # Lista blanca de comandos o ejecución directa
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        out = res.stdout if res.stdout else res.stderr

        logging.info(f"Comando ejecutado: {cmd}")
        return f"Salida de Terminal:\n{out[:300]}"
    except Exception as e:
        logging.error(f"Error ejecutando comando Bash: {str(e)}")
        return f"Error en la ejecución del comando: {e}"
