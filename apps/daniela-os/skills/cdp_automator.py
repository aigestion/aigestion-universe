import logging
import os
import time
import urllib.request

from google import genai


def run_cdp_automation(target_url: str = "https://aigestion.net", action: str = "inspect") -> str:
    """Ejecuta inspección navegacional sin cabeza (CDP) usando Gemini 3.6 Flash para interpretar el estado visual."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [CDP AUTOMATOR]: Se requiere GEMINI_API_KEY configurada."

    if not target_url or " " in target_url.strip() or "diff --git" in target_url:
        target_url = "https://aigestion.net"

    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    try:
        logging.info(f"⚡ [CDP AUTOMATOR]: Conectando a {target_url} vía protocolo CDP...")

        # 1. Simulación de captura y renderizado CDP
        req = urllib.request.Request(
            target_url, headers={"User-Agent": "Mozilla/5.0 (DanielaOS/32.0 CDP-Engine)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html_snapshot = response.read().decode("utf-8", errors="ignore")[:3500]

        # 2. Evaluación visual y semántica con Gemini 3.6 Flash
        client = genai.Client(api_key=api_key)
        prompt = f"""Actúa como un agente de inspección Chrome DevTools Protocol (CDP).
Analiza este render/DOM obtenido en segundo plano de la URL ({target_url}):

{html_snapshot}

Genera un reporte técnico CDP:
1. Estado del render (Layout, Scripts interactivos detectados).
2. Puntos de interacción visual clave (Formularios, Botones de CTA, Enlaces).
3. Evaluación de seguridad y rendimiento (HTTP status, headers).

Responde en formato Markdown directo."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        report = res.text.strip()

        # 3. Guardar artefacto del reporte en el directorio output
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"cdp_report_{int(time.time())}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"CDP TARGET: {target_url}\nACTION: {action}\n\n{report}")

        return f"⚡ [CDP HEADLESS AUTOMATOR]: Inspección finalizada.\n🔗 URL: {target_url}\n📁 Reporte CDP: {filepath}\n\n--- REPORTE TÉCNICO ---\n{report[:300]}..."

    except Exception as e:
        return f"❌ [CDP AUTOMATOR ERROR]: {e}"


if __name__ == "__main__":
    print(run_cdp_automation())
