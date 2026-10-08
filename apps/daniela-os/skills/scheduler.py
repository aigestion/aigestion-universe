import json
import os
import time

TASKS_DB = os.path.expanduser("~/daniela-os/tasks.json")


def _init_db():
    if not os.path.exists(TASKS_DB):
        with open(TASKS_DB, "w") as f:
            json.dump([], f)


def add_task(command, time_str):
    _init_db()
    with open(TASKS_DB, "r+") as f:
        tasks = json.load(f)
        tasks.append({"command": command, "time": time_str, "last_run": None})
        f.seek(0)
        json.dump(tasks, f)
        f.truncate()
    return f"⏰ [SCHEDULER]: Tarea '{command}' programada para {time_str}"


def list_tasks():
    _init_db()
    with open(TASKS_DB) as f:
        return json.load(f)


def run_scheduler_cycle():
    """Este ciclo corre en background dentro del servidor."""
    while True:
        try:
            # Aquí podrías integrar lógica de ejecución (Simplificado por ahora)
            time.sleep(60)
        except Exception:
            break
