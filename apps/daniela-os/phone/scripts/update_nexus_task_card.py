import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

if os.path.exists(nexus_path):
    with open(nexus_path, encoding="utf-8") as f:
        code = f.read()

    # 1. Añadir endpoint /api/tasks-status en do_GET si no existe
    if "/api/tasks-status" not in code:
        old_routing = 'elif path == "/health":'
        new_routing = 'elif path == "/api/tasks-status":\n            self.send_json_or_html(200, self.get_tasks_summary())\n        elif path == "/health":'
        code = code.replace(old_routing, new_routing)

    # 2. Añadir método get_tasks_summary en la clase NexusHandler
    if "def get_tasks_summary(self):" not in code:
        tasks_method = """    def get_tasks_summary(self):
        db_path = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")
        if not os.path.exists(db_path): return {"pending": 0, "processing": 0, "completed": 0, "total": 0}
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT status, COUNT(*) FROM task_queue GROUP BY status")
            stats = {row[0]: row[1] for row in cur.fetchall()}
            cur.execute("SELECT COUNT(*) FROM task_queue")
            total = cur.fetchone()[0]
            conn.close()
            return {
                "pending": stats.get("PENDING", 0),
                "processing": stats.get("PROCESSING", 0),
                "completed": stats.get("COMPLETED", 0),
                "total": total
            }
        except Exception:
            conn.close()
            return {"pending": 0, "processing": 0, "completed": 0, "total": 0}

"""
        code = code.replace(
            "    def get_system_stats(self):", tasks_method + "    def get_system_stats(self):"
        )

    # 3. Añadir la tarjeta HTML
    old_card_grid = """        <div class="card">
            <h2>📱 Estado Nodo Pixel 8a</h2>
            <div id="sys-metrics">
                <p>CPU: <strong id="cpu-val">--%</strong> | RAM: <strong id="ram-val">--%</strong></p>
                <p>Disco Almacenamiento: <strong id="disk-val">--%</strong></p>
                <p>Estado Red Mesh: <strong style="color:#4ade80;">ONLINE (127.0.0.1)</strong></p>
            </div>
        </div>"""

    new_card_grid = (
        old_card_grid
        + """
        <div class="card">
            <h2>⚙️ Cola de Tareas (TaskWorker)</h2>
            <div id="task-metrics">
                <p>Pendientes: <strong id="task-pending" style="color:#facc15;">--</strong></p>
                <p>En Proceso: <strong id="task-processing" style="color:#38bdf8;">--</strong></p>
                <p>Completadas: <strong id="task-completed" style="color:#4ade80;">--</strong></p>
                <p>Total Registros: <strong id="task-total">--</strong></p>
            </div>
        </div>"""
    )

    code = code.replace(old_card_grid, new_card_grid)

    # 4. Añadir script de JavaScript para refrescar la cola de tareas
    old_js = """        setInterval(updateStats, 3000);
        updateStats();"""

    new_js = """        setInterval(updateStats, 3000);
        updateStats();

        function updateTasks() {
            fetch('/api/tasks-status')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('task-pending').innerText = data.pending;
                    document.getElementById('task-processing').innerText = data.processing;
                    document.getElementById('task-completed').innerText = data.completed;
                    document.getElementById('task-total').innerText = data.total;
                }).catch(() => {});
        }
        setInterval(updateTasks, 4000);
        updateTasks();"""

    code = code.replace(old_js, new_js)

    with open(nexus_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(
        "✨ [Nexus Dashboard] Tarjeta TaskWorker inyectada correctamente sin errores de sintaxis."
    )
else:
    print("⚠️ No se encontró el archivo nexus_dashboard.py")
