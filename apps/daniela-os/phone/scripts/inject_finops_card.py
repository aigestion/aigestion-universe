import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

with open(nexus_path, encoding="utf-8") as f:
    code = f.read()

# 1. Inyectar endpoint /api/finops-status
if "/api/finops-status" not in code:
    old_get = 'elif path == "/api/thermal-status":'
    new_get = 'elif path == "/api/finops-status":\n            self.send_json_or_html(200, self.get_finops_summary())\n        elif path == "/api/thermal-status":'
    code = code.replace(old_get, new_get)

# 2. Inyectar método get_finops_summary en NexusHandler
if "def get_finops_summary(self):" not in code:
    finops_method = """    def get_finops_summary(self):
        try:
            from core.finops_advisor import FinOpsAdvisor
            advisor = FinOpsAdvisor()
            return advisor.get_financial_summary()
        except Exception as e:
            return {"total_spent_usd": 0.0, "total_saved_usd": 0.0, "efficiency_ratio": "0%", "error": str(e)}

"""
    code = code.replace(
        "    def get_thermal_summary(self):", finops_method + "    def get_thermal_summary(self):"
    )

# 3. Añadir tarjeta HTML FinOps en el Dashboard
if "<h2>💳 FinOps & Ahorro IA</h2>" not in code:
    old_card = "<h2>🔋 Térmica y Batería (Pixel 8a)</h2>"
    new_card = """<h2>💳 FinOps & Ahorro IA</h2>
            <div id="finops-metrics">
                <p>Gasto Est. API: <strong id="finops-spent" style="color:#f87171;">$--</strong></p>
                <p>Ahorro Total: <strong id="finops-saved" style="color:#4ade80;">$--</strong></p>
                <p>Eficiencia enrutado: <strong id="finops-eff" style="color:#38bdf8;">--%</strong></p>
            </div>
        </div>
        <div class="card">
            <h2>🔋 Térmica y Batería (Pixel 8a)</h2>"""
    code = code.replace(old_card, new_card)

# 4. Añadir función JavaScript updateFinops()
old_js = """        function updateThermal() {{"""
new_js = """        function updateFinops() {{
            fetch('/api/finops-status')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('finops-spent').innerText = '$' + data.total_spent_usd;
                    document.getElementById('finops-saved').innerText = '$' + data.total_saved_usd;
                    document.getElementById('finops-eff').innerText = data.efficiency_ratio;
                }}).catch(() => {{}});
        }}
        setInterval(updateFinops, 6000);
        updateFinops();

        function updateThermal() {{"""

if old_js in code and "function updateFinops()" not in code:
    code = code.replace(old_js, new_js)

with open(nexus_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [Nexus Dashboard] Tarjeta FinOps inyectada con éxito.")
