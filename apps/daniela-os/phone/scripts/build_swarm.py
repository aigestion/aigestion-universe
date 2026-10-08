import os

repo_dir = os.path.expanduser("~/aig-monorepo/pixela8/app/agents")
os.makedirs(repo_dir, exist_ok=True)

# 1. agent_devops.py
devops_code = """#!/usr/bin/env python3
import os, json, subprocess, sqlite3, time

DB_PATH = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")
REPO_DIR = os.path.expanduser("~/aig-monorepo")

class DevOpsAgent:
    def get_battery_status(self):
        try:
            res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return json.loads(res.stdout)
        except Exception:
            pass
        return {"percentage": 0, "temperature": 0, "status": "UNKNOWN"}

    def run_git_sync(self, commit_msg="Auto-sync via DevOps Agent"):
        try:
            subprocess.run(["git", "-C", REPO_DIR, "add", "."], check=True)
            subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", commit_msg], check=False)
            res = subprocess.run(["git", "-C", REPO_DIR, "push"], capture_output=True, text=True, check=False)
            return "✅ Monorepo sincronizado con GitHub." if res.returncode == 0 else "⚠️ Git Sync completado."
        except Exception as e:
            return f"❌ Error en Git Sync: {e}"

    def get_top_processes(self, limit=8):
        try:
            res = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
            return "\\n".join(res.stdout.splitlines()[:limit])
        except Exception as e:
            return f"Error: {e}"
"""

# 2. agent_secretary.py
secretary_code = """#!/usr/bin/env python3
import os, sqlite3, time

DB_PATH = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")
ROADMAP_PATH = os.path.expanduser("~/aig-monorepo/ROADMAP.md")

class SecretaryAgent:
    def __init__(self):
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS quick_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, key_tag TEXT, content TEXT)')
        conn.commit()
        conn.close()

    def save_note(self, tag: str, content: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO quick_memory (timestamp, key_tag, content) VALUES (?, ?, ?)", (ts, tag, content))
        conn.commit()
        conn.close()

    def search_note(self, query: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, content FROM quick_memory WHERE content LIKE ? ORDER BY id DESC LIMIT 5", (f"%{query}%",))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_to_roadmap(self, task_text: str, user_name: str = "Daniela"):
        ts = time.strftime("%Y-%m-%d %H:%M")
        entry = f"- [ ] **[{ts}]** {task_text} *(Añadido por: {user_name})*\\n"
        with open(ROADMAP_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"💡 Añadido al Roadmap: «{task_text}»"
"""

# 3. agent_rag.py
rag_code = """#!/usr/bin/env python3
import os, glob

REPO_DIR = os.path.expanduser("~/aig-monorepo")

class RAGAgent:
    def search_codebase(self, query: str, max_results=3):
        results = []
        search_terms = query.lower().split()
        pattern = os.path.join(REPO_DIR, "**/*.[pm][yd]*")
        files = glob.glob(pattern, recursive=True)

        for filepath in files:
            if ".git" in filepath or "__pycache__" in filepath:
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines()
                    for idx, line in enumerate(lines):
                        if any(term in line.lower() for term in search_terms):
                            rel_path = os.path.relpath(filepath, REPO_DIR)
                            snippet = "\\n".join(lines[max(0, idx-2):min(len(lines), idx+3)])
                            results.append({"file": rel_path, "line": idx + 1, "snippet": snippet})
                            break
            except Exception:
                continue
        return results[:max_results]
"""

# 4. agent_coder.py
coder_code = """#!/usr/bin/env python3
import os, requests
from agent_rag import RAGAgent

try:
    from config import OPENROUTER_API_KEY
except ImportError:
    OPENROUTER_API_KEY = ""

class CoderAgent:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.rag = RAGAgent()

    def ask_code_assistant(self, prompt: str):
        local_context = self.rag.search_codebase(prompt)
        context_str = ""
        if local_context:
            context_str = "\\n\\nContexto de tu Monorepo local:\\n"
            for item in local_context:
                context_str += f"--- {item['file']} (Línea {item['line']}) ---\\n{item['snippet']}\\n"

        if not self.api_key:
            return f"⚠️ OpenRouter API Key no configurada.{context_str}"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        full_user_prompt = f"Consulta: {prompt}\\n{context_str}"
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": "Eres un asistente experto de código para un monorepo personal en Termux."},
                {"role": "user", "content": full_user_prompt}
            ],
            "temperature": 0.2
        }
        try:
            r = requests.post(self.api_url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                ans = r.json()["choices"][0]["message"]["content"]
                if local_context:
                    ans += "\\n\\n*(💡 Contexto extraído automáticamente de tus archivos locales)*"
                return ans
            return f"❌ Error OpenRouter HTTP {r.status_code}: {r.text}"
        except Exception as e:
            return f"❌ Excepción: {e}"
"""

# 5. telegram_bot.py
bot_code = """#!/usr/bin/env python3
import os, sys, time, subprocess, threading, tarfile, asyncio
from flask import Flask, request, jsonify

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

from config import TELEGRAM_TOKEN
from agent_devops import DevOpsAgent
from agent_secretary import SecretaryAgent
from agent_coder import CoderAgent

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

devops = DevOpsAgent()
secretary = SecretaryAgent()
coder = CoderAgent()

BACKUP_PATH = os.path.expanduser("~/aig-monorepo/daniela_backup.tar.gz")
ROADMAP_PATH = os.path.expanduser("~/aig-monorepo/ROADMAP.md")

def speak(text: str):
    try:
        subprocess.run(["termux-tts-speak", text], check=False)
    except Exception:
        pass

flask_app = Flask(__name__)

@flask_app.route('/n8n-webhook', methods=['POST'])
def n8n_webhook():
    data = request.json or {}
    msg = data.get("message", "Evento n8n.")
    if data.get("speak", False):
        speak(msg)
    return jsonify({"status": "success", "received": msg}), 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🗺️ Roadmap", callback_data="btn_roadmap"), InlineKeyboardButton("⚡ Git Sync", callback_data="btn_sync")],
        [InlineKeyboardButton("🔋 Telemetría", callback_data="btn_health"), InlineKeyboardButton("📊 Procesos TOP", callback_data="btn_top")],
        [InlineKeyboardButton("📦 Backup DB", callback_data="btn_backup"), InlineKeyboardButton("📅 Briefing", callback_data="btn_briefing")]
    ]
    await update.message.reply_text("🐝 **¡Daniela Swarm v8.0 + RAG!**\\n\\n• `/code <pregunta>`\\n• `/sync` | `/health` | `/top`\\n• `/recuerda` | `/busca` | `/alarma`", reply_markup=InlineKeyboardMarkup(keyboard))

async def code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Uso: `/code explica la clase RAG`")
        return
    await update.message.reply_text("💻 **Agente Coder consultando IA + RAG...**")
    res = coder.ask_code_assistant(prompt)
    await update.message.reply_text(f"💻 **Respuesta Coder:**\\n\\n{res[:3500]}")

async def sync_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 **Iniciando Git Sync...**")
    res = devops.run_git_sync()
    speak("Sincronización Git realizada.")
    await update.message.reply_text(res)

async def health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bat = devops.get_battery_status()
    await update.message.reply_text(f"📱 **TELEMETRÍA:**\\n• Batería: **{bat.get('percentage')}%** ({bat.get('status')})\\n• Temp: **{bat.get('temperature')}°C**")

async def top_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    output = devops.get_top_processes()
    await update.message.reply_text(f"📊 **Procesos Termux:**\\n```\\n{output}\\n```", parse_mode="Markdown")

async def recuerda_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("⚠️ Uso: `/recuerda Nota importante` ")
        return
    secretary.save_note("USER_NOTE", text)
    secretary.add_to_roadmap(text, user_name="Telegram_User")
    speak("Nota guardada.")
    await update.message.reply_text(f"🧠 **Secretario:** Nota guardada:\\n«{text}»")

async def busca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("⚠️ Uso: `/busca nota` ")
        return
    results = secretary.search_note(query)
    if not results:
        await update.message.reply_text(f"🔍 Sin resultados para «{query}».")
        return
    msg = f"🔍 **Resultados:**\\n\\n" + "\\n".join([f"• **[{ts}]** {content}" for ts, content in results])
    await update.message.reply_text(msg)

async def alarma_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Uso: `/alarma 5 Tomar agua` ")
        return
    try:
        mins = float(context.args[0])
        mensaje = " ".join(context.args[1:])
        seconds = int(mins * 60)
        chat_id = update.effective_chat.id
        await update.message.reply_text(f"⏱️ **Alarma programada en {mins} minutos:**\\n«{mensaje}»")
        async def timer_task():
            await asyncio.sleep(seconds)
            speak(f"Atención Comandante: {mensaje}")
            await context.bot.send_message(chat_id=chat_id, text=f"🔔 **RECORDATORIO:**\\n«{mensaje}»")
        asyncio.create_task(timer_task())
    except ValueError:
        await update.message.reply_text("❌ Minutos no válidos.")

async def backup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📦 **Creando backup...**")
    try:
        with tarfile.open(BACKUP_PATH, "w:gz") as tar:
            db_file = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")
            if os.path.exists(db_file): tar.add(db_file, arcname="daniela_memory.db")
            if os.path.exists(ROADMAP_PATH): tar.add(ROADMAP_PATH, arcname="ROADMAP.md")
        with open(BACKUP_PATH, "rb") as doc:
            await update.message.reply_document(document=doc, filename="daniela_backup.tar.gz", caption="✅ Backup listo.")
        speak("Backup generado.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "btn_sync":
        await query.edit_message_text("🔄 **Sincronizando...**")
        res = devops.run_git_sync()
        await query.edit_message_text(f"✅ {res}")
    elif query.data == "btn_top":
        output = devops.get_top_processes(limit=8)
        await query.edit_message_text(f"📊 **Procesos:**\\n```\\n{output}\\n```", parse_mode="Markdown")
    elif query.data == "btn_backup":
        await query.edit_message_text("📦 Usa `/backup` para recibir la base de datos.")
    elif query.data == "btn_health":
        bat = devops.get_battery_status()
        await query.edit_message_text(f"🔋 **Batería:** {bat.get('percentage')}% | 🌡️ **Temp:** {bat.get('temperature')}°C")
    elif query.data == "btn_briefing":
        speak("Swarm activo y listo.")
        await query.edit_message_text("📅 **Briefing:** Daniela Swarm + RAG operativa.")
    elif query.data == "btn_roadmap":
        if os.path.exists(ROADMAP_PATH):
            with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
                await query.edit_message_text(f"🗺️ **ROADMAP:**\\n\\n{f.read()[:3500]}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.effective_user.first_name
    secretary.save_note("CHAT_LOG", f"{user_name}: {user_text}")
    await update.message.reply_text(f"🐝 **Daniela Swarm:** Tarea registrada:\\n📝 «{user_text}»")

def main():
    if not TELEGRAM_TOKEN:
        print("⚠️ Token no configurado.")
        return
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", start))
    app.add_handler(CommandHandler("code", code_handler))
    app.add_handler(CommandHandler("sync", sync_handler))
    app.add_handler(CommandHandler("health", health_handler))
    app.add_handler(CommandHandler("top", top_handler))
    app.add_handler(CommandHandler("recuerda", recuerda_handler))
    app.add_handler(CommandHandler("busca", busca_handler))
    app.add_handler(CommandHandler("alarma", alarma_handler))
    app.add_handler(CommandHandler("backup", backup_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🐝 [Daniela Swarm v8.0 + RAG] ¡Desplegado!")
    app.run_polling()

if __name__ == "__main__":
    main()
"""

files = {
    "agent_devops.py": devops_code,
    "agent_secretary.py": secretary_code,
    "agent_rag.py": rag_code,
    "agent_coder.py": coder_code,
    "telegram_bot.py": bot_code,
}

for filename, content in files.items():
    filepath = os.path.join(repo_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(filepath, 0o755)

print("✨ [SWARM BUILD] ¡Todos los módulos generados correctamente sin fallos!")
