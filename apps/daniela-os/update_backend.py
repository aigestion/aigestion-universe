code = """
# MÓDULO: Kanban & Personalidad Dinámica
KANBAN_FILE = os.path.expanduser("~/daniela-os/research/kanban.json")

@app.route("/kanban", methods=["GET", "POST"])
def kanban():
    if request.method == "POST":
        data = request.get_json() or {}
        with open(KANBAN_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"status": "OK"})
    else:
        if os.path.exists(KANBAN_FILE):
            with open(KANBAN_FILE, "r") as f:
                return jsonify(json.load(f))
        return jsonify({"todo": [], "in_progress": [], "done": []})
"""

with open("daniela_brain_system.py") as f:
    content = f.read()

if "/kanban" not in content:
    content = content.replace('if __name__ == "__main__":', code + '\nif __name__ == "__main__":')
    with open("daniela_brain_system.py", "w") as f:
        f.write(content)
    print("🟢 [BACKEND]: Endpoints de Kanban e Inyección de Prompts integrados.")
else:
    print("ℹ️ [BACKEND]: Módulos ya estaban presentes.")
