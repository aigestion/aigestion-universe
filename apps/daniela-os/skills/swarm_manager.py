import os
import subprocess

from google import genai


def orchestrate_swarm(goal: str) -> str:
    """Orquesta sub-agentes para cumplir metas complejas de inspección e informe."""
    if not goal:
        goal = "Analiza el entorno y reporta el estado del sistema."

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [SWARM MANAGER]: Se requiere GEMINI_API_KEY configurada."

    try:
        # Recolección técnica real del entorno
        ps_info = subprocess.getoutput("ps aux | grep python3 | head -n 5")
        port_info = subprocess.getoutput("fuser 8085/tcp 2>/dev/null || echo 'Puerto 8085 libre'")
        log_info = subprocess.getoutput(
            "tail -n 10 ~/daniela-os/server.log 2>/dev/null || echo 'Sin log'"
        )

        client = genai.Client(api_key=api_key)
        prompt = f"""Actúa como el Agentic Swarm Manager de Daniela OS.
Meta recibida: "{goal}"

Telemetría capturada por los sub-agentes de inspección:
- Procesos activos:
{ps_info}
- Estado de Puerto 8085:
{port_info}
- Últimos Logs:
{log_info}

Genera un informe ejecutivo consolidado con el estado del servidor, salud de procesos y recomendaciones en formato Markdown."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        report = res.text.strip()
        return (
            f"🐝 [AGENTIC SWARM MANAGER]: Meta ejecutada exitosamente por el enjambre.\n\n{report}"
        )

    except Exception as e:
        return f"❌ [SWARM MANAGER ERROR]: {e}"


if __name__ == "__main__":
    print(orchestrate_swarm("Analiza el estado del servidor"))
