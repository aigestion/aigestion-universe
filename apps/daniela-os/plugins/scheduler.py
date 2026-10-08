import json, os, time, importlib

TASKS_FILE = "/data/data/com.termux/files/home/daniela-os/tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE): 
        return []
    try:
        with open(TASKS_FILE, 'r') as f: 
            return json.load(f)
    except: 
        return []

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def add_task(plugin_name, interval_seconds):
    tasks = load_tasks()
    # Evitar duplicados del mismo plugin
    for t in tasks:
        if t.get("plugin") == plugin_name:
            t["interval"] = interval_seconds
            save_tasks(tasks)
            return f"⏱️ [SCHEDULER]: Tarea '{plugin_name}' actualizada a un intervalo de {interval_seconds}s."

    new_task = {
        "id": len(tasks) + 1,
        "plugin": plugin_name,
        "interval": interval_seconds,
        "last_run": 0
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return f"⏱️ [SCHEDULER]: Tarea programada para '{plugin_name}' cada {interval_seconds}s."

def check_and_execute_due_tasks():
    tasks = load_tasks()
    now = time.time()
    executed = []
    
    for task in tasks:
        if now - task.get("last_run", 0) >= task.get("interval", 3600):
            try:
                mod = importlib.import_module(f"plugins.{task['plugin']}")
                res = mod.run(f"auto_{task['plugin']}")
                task["last_run"] = now
                executed.append(f"Task #{task['id']} ({task['plugin']}): Executed")
            except Exception as e:
                executed.append(f"Task #{task['id']} Error: {e}")
                
    if executed:
        save_tasks(tasks)
    return executed

def run(context):
    cmd = context.lower()
    
    if "programa" in cmd or "add" in cmd:
        parts = context.split()
        if len(parts) >= 3:
            plugin_name = parts[1]
            try:
                interval = int(parts[2])
                return add_task(plugin_name, interval)
            except ValueError:
                return "❌ [SCHEDULER]: El intervalo debe ser un número entero (segundos)."
        return "❌ [SCHEDULER]: Formato incorrecto. Usa: 'programa <plugin> <segundos>'."
        
    elif "tareas" in cmd or "list" in cmd:
        tasks = load_tasks()
        if not tasks: 
            return "🗂️ [SCHEDULER]: No hay tareas programadas."
        res = ["🗂️ [SCHEDULER]: Tareas activas:"]
        for t in tasks:
            res.append(f"• ID #{t['id']}: Módulo `{t['plugin']}` cada {t['interval']}s (Última ejec.: {int(t['last_run'])})")
        return "\n".join(res)
        
    return "❌ [SCHEDULER]: Comando no reconocido. Usa 'programa <plugin> <segundos>' o 'tareas'."
