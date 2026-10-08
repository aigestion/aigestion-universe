import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

with open(nexus_path, encoding="utf-8") as f:
    code = f.read()

# Corrección de la inyección de JS con llaves dobles {{ }} para el f-string
old_js_single = """        function updateTasks() {
            fetch('/api/tasks-status')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('task-pending').innerText = data.pending;
                    document.getElementById('task-processing').innerText = data.processing;
                    document.getElementById('task-completed').innerText = data.completed;
                    document.getElementById('task-total').innerText = data.total;
                }).catch(() => {});
        }"""

new_js_double = """        function updateTasks() {{
            fetch('/api/tasks-status')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('task-pending').innerText = data.pending;
                    document.getElementById('task-processing').innerText = data.processing;
                    document.getElementById('task-completed').innerText = data.completed;
                    document.getElementById('task-total').innerText = data.total;
                }}).catch(() => {{}});
        }}"""

if old_js_single in code:
    code = code.replace(old_js_single, new_js_double)

with open(nexus_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ Parche de f-string aplicado correctamente a nexus_dashboard.py.")
