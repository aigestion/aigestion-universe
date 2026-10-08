import os
import sys

sys.path.append(os.path.expanduser("~/core/modules"))

from clipboard_reader import process_clipboard_context
from coder_agent import auto_generate_and_execute
from executive_briefing import get_daily_briefing
from github_auditor import audit_full_github, commit_and_sync_repo
from google_integrations import (
    backup_db_to_drive,
)
from haptic_proactive import notify_user_proactively
from health_guardian import check_system_health
from local_rag import index_repository, search_knowledge
from nightly_maintenance import run_nightly_maintenance
from project_orchestrator import execute_deep_research_and_artifacts
from sentinel_autofixer import run_sentinel_autofix
from speech_interaction import process_voice_greeting
from telemetry_server import start_telemetry_server
from token_failover import get_active_api_key, switch_to_backup_key, switch_to_primary_key
from vision_inspector import capture_and_analyze_front
from web_monitor import monitor_url_target


def process_master_command(user_input):
    cmd_lower = user_input.lower()

    if any(w in cmd_lower for w in ["programa", "codifica", "haz un script", "crea un script"]):
        instruction = (
            user_input.replace("programa", "")
            .replace("codifica", "")
            .replace("haz un script", "")
            .replace("crea un script", "")
            .strip()
        )
        return auto_generate_and_execute(instruction)

    if any(w in cmd_lower for w in ["briefing", "resumen del dia", "buenos dias", "agenda"]):
        return get_daily_briefing()

    if any(w in cmd_lower for w in ["monitor", "scraper", "monitorear", "web"]):
        return monitor_url_target()

    if any(w in cmd_lower for w in ["autofix", "sentinel fix", "corregir repo"]):
        return run_sentinel_autofix()

    if any(
        w in cmd_lower
        for w in ["analiza lo que tengo enfrente", "mira esto", "que ves", "foto enfrente"]
    ):
        return capture_and_analyze_front()

    if any(
        w in cmd_lower for w in ["portapapeles", "copiado", "revisa lo que tengo", "lo que copie"]
    ):
        return process_clipboard_context(user_input)

    if any(w in cmd_lower for w in ["crear proyecto", "crear plan", "revisa el tema", "investiga"]):
        topic = (
            user_input.replace("crear proyecto", "")
            .replace("crear plan", "")
            .replace("revisa el tema", "")
            .replace("investiga", "")
            .strip()
        )
        if not topic:
            topic = "General"
        return execute_deep_research_and_artifacts(topic)

    if any(w in cmd_lower for w in ["hola daniela", "daniela estas", "estas?"]):
        return process_voice_greeting(user_input)

    if any(w in cmd_lower for w in ["habla", "vibra", "proactivo", "notificar"]):
        return notify_user_proactively("Daniela OS reporta estado nominal del sistema.")

    if any(w in cmd_lower for w in ["cambiar key", "failover", "usar personal", "backup key"]):
        return switch_to_backup_key("Solicitado por el usuario")

    if any(w in cmd_lower for w in ["usar principal", "reset key", "key admin"]):
        return switch_to_primary_key()

    if any(w in cmd_lower for w in ["key activa", "estado token", "que key"]):
        key = get_active_api_key()
        return "🔑 **API KEY ACTIVA EN DANIELA OS**: " + (
            key[:12] + "..." if key else "No configurada"
        )

    if any(w in cmd_lower for w in ["indexar", "index", "conocimiento", "rag"]):
        if "buscar" in cmd_lower or "search" in cmd_lower:
            query = user_input.split()[-1] if len(user_input.split()) > 1 else "master"
            return search_knowledge(query)
        return index_repository()

    if any(w in cmd_lower for w in ["mantenimiento", "nocturno", "limpieza"]):
        return run_nightly_maintenance()

    if any(w in cmd_lower for w in ["dashboard", "web", "servidor", "8080"]):
        return start_telemetry_server()

    if any(w in cmd_lower for w in ["backup", "drive", "respaldo", "cifrar"]):
        return backup_db_to_drive()

    if any(w in cmd_lower for w in ["salud", "sensores", "bateria", "pixel"]):
        return check_system_health()

    if any(w in cmd_lower for w in ["github", "repo", "audit"]):
        return audit_full_github()

    if any(w in cmd_lower for w in ["guardar", "commit", "sync"]):
        return commit_and_sync_repo()

    return '🤖 Comando "' + str(user_input) + '" procesado.'


if __name__ == "__main__":
    query = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "programa un script para revisar el espacio en disco"
    )
    print(process_master_command(query))
