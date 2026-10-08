import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

if os.path.exists(nexus_path):
    with open(nexus_path, encoding="utf-8") as f:
        code = f.read()

    # 1. Inyectar endpoint /api/thermal-status en do_GET si no existe
    if "/api/thermal-status" not in code:
        old_get = 'elif path == "/api/chat/stream":'
        new_get = 'elif path == "/api/thermal-status":\n            self.send_json_or_html(200, self.get_thermal_summary())\n        elif path == "/api/chat/stream":'
        code = code.replace(old_get, new_get)

    # 2. Inyectar método get_thermal_summary en NexusHandler
    if "def get_thermal_summary(self):" not in code:
        thermal_method = """    def get_thermal_summary(self):
        try:
            from core.thermal_router import ThermalRouter
            router = ThermalRouter()
            status = router.get_device_status()
            policy = router.evaluate_routing_policy()
            return {
                "temperature": status.get("temperature", 0.0),
                "battery": status.get("percentage", 0),
                "plugged": status.get("plugged", "UNPLUGGED"),
                "mode": policy.get("mode", "PERFORMANCE"),
                "reason": policy.get("reason", "")
            }
        except Exception as e:
            return {"temperature": 0.0, "battery": 0, "plugged": "UNKNOWN", "mode": "UNKNOWN", "reason": str(e)}

"""
        code = code.replace(
            "    def handle_chat_stream(self):",
            thermal_method + "    def handle_chat_stream(self):",
        )

    # 3. Añadir tarjeta HTML de Thermal Status en el Dashboard
    if "<h2>🔋 Térmica y Batería (Pixel 8a)</h2>" not in code:
        old_card_grid = "<h2>⚙️ Cola de Tareas (TaskWorker)</h2>"
        new_card_grid = """<h2>🔋 Térmica y Batería (Pixel 8a)</h2>
            <div id="thermal-metrics">
                <p>Temperatura: <strong id="hw-temp" style="color:#38bdf8;">--°C</strong></p>
                <p>Nivel Batería: <strong id="hw-battery" style="color:#4ade80;">--%</strong> (<span id="hw-plugged">--</span>)</p>
                <p>Modo Cómputo: <strong id="hw-mode" style="color:#a855f7;">--</strong></p>
            </div>
        </div>
        <div class="card">
            <h2>⚙️ Cola de Tareas (TaskWorker)</h2>"""
        code = code.replace(old_card_grid, new_card_grid)

    # 4. Añadir función JavaScript updateThermal() para refresco en tiempo real
    old_js = """        setInterval(updateTasks, 4000);
        updateTasks();"""

    new_js = """        setInterval(updateTasks, 4000);
        updateTasks();

        function updateThermal() {{
            fetch('/api/thermal-status')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('hw-temp').innerText = data.temperature + '°C';
                    document.getElementById('hw-battery').innerText = data.battery + '%';
                    document.getElementById('hw-plugged').innerText = data.plugged;
                    document.getElementById('hw-mode').innerText = data.mode;
                }}).catch(() => {{}});
        }}
        setInterval(updateThermal, 5000);
        updateThermal();"""

    if old_js in code and "function updateThermal()" not in code:
        code = code.replace(old_js, new_js)

    with open(nexus_path, "w", encoding="utf-8") as f:
        f.write(code)

    print("✨ [Nexus Dashboard] Tarjeta Thermal & Battery inyectada con éxito.")
