import os

repo_dir = os.path.expanduser("~/aig-monorepo/pixela8/app/agents")
bot_path = os.path.join(repo_dir, "telegram_bot.py")

# Leemos el bot actual y le inyectamos el worker
with open(bot_path, encoding="utf-8") as f:
    content = f.read()

# Si no está importado el worker, lo inyectamos
if "from agent_worker import WorkerAgent" not in content:
    old_imports = "from agent_coder import CoderAgent"
    new_imports = "from agent_coder import CoderAgent\nfrom agent_worker import WorkerAgent"
    content = content.replace(old_imports, new_imports)

    old_init = "coder = CoderAgent()"
    new_init = "coder = CoderAgent()\nworker = WorkerAgent()"
    content = content.replace(old_init, new_init)

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(content)

print("🤖 telegram_bot.py actualizado con referencias al Worker.")
