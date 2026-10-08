import os

code = """#!/usr/bin/env python3
import os, sys, sqlite3, time, subprocess, threading, requests, tarfile, asyncio
from flask import Flask, request, jsonify

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

from config import TELEGRAM_TOKEN
from god_mode import check_system_health, auto_git_sync, speak
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

DB_PATH = os.path.expanduser('~/aig-monorepo/pixela8/app/daniela_memory.db')
ROADMAP_PATH = os.path.expanduser('~/aig-monorepo/ROADMAP.md')
BACKUP_PATH = os.path.expanduser('~/aig-monorepo/daniela_backup.tar.gz')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS quick_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, key_tag TEXT, content TEXT)')
    conn.commit()
    conn.close()

init_db()

def save_memory(tag: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO quick_memory (timestamp, key_tag, content) VALUES (?, ?, ?)', (ts, tag, content))
    conn.commit()
    conn.close()

def search_memory(query: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, content FROM quick_memory WHERE content LIKE ? ORDER BY id DESC LIMIT 5', (f'%{query}%',))
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_to_nexus(task_payload: str, source: str = 'Telegram_Daniela'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO nexus_jobs (timestamp, target_node, task_payload) VALUES (?, ?, ?)', (ts, 'MINI_PC', task_payload))
    cursor.execute('INSERT INTO semantic_events (timestamp, source, content) VALUES (?, ?, ?)', (ts, source, task_payload))
    conn.commit()
    conn.close()

flask_app = Flask(__name__)

@flask_app.route('/n8n-webhook', methods=['POST'])
def n8n_webhook():
    data = request.json or {}
    msg = data.get('message', 'Evento n8n.')
    if data.get('speak', False):
        speak(msg)
    return jsonify({'status': 'success', 'received': msg}), 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton('🗺️ Roadmap', callback_data='btn_roadmap'), InlineKeyboardButton('⚡ Git Sync', callback_data='btn_sync')],
        [InlineKeyboardButton('🔋 Telemetría', callback_data='btn_health'), InlineKeyboardButton('📊 Procesos TOP', callback_data='btn_top')],
        [InlineKeyboardButton('📦 Backup DB', callback_data='btn_backup'), InlineKeyboardButton('📅 Briefing', callback_data='btn_briefing')]
    ]
    await update.message.reply_text('🧠 **¡Daniela AI v7.0 Activa!**\\n\\n• `/alarma <mins> <msg>`\\n• `/resumen <texto>`\\n• `/recuerda` | `/busca`\\n• `/sync` | `/backup` | `/health`', reply_markup=InlineKeyboardMarkup(keyboard))

async def alarma_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text('⚠️ Uso: `/alarma 10 Comprobar correo`')
        return
    try:
        mins = float(context.args[0])
        mensaje = ' '.join(context.args[1:])
        seconds = int(mins * 60)
        chat_id = update.effective_chat.id
        await update.message.reply_text(f'⏱️ **Alarma programada en {mins} minutos:**\\n«{mensaje}»')
        async def timer_task():
            await asyncio.sleep(seconds)
            speak(f'Atención Comandante. Recordatorio: {mensaje}')
            await context.bot.send_message(chat_id=chat_id, text=f'🔔 **RECORDATORIO DANIELA:**\\n«{mensaje}»')
        asyncio.create_task(timer_task())
    except ValueError:
        await update.message.reply_text('❌ Uso: `/alarma <minutos> <mensaje>`')

async def resumen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text('⚠️ Pega el texto tras el comando.')
        return
    lines = [line.strip() for line in text.split('.') if line.strip()]
    summary = lines[:3]
    msg = '📌 **Resumen Ejecutivo:**\\n\\n' + '\\n'.join([f'• {s}.' for s in summary])
    await update.message.reply_text(msg)

async def top_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        lines = res.stdout.splitlines()[:10]
        output = '\\n'.join(lines)
        await update.message.reply_text(f'📊 **Procesos Termux:**\\n```\\n{output}\\n```', parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {e}')

async def recuerda_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text('⚠️ Ejemplo: `/recuerda Nota` ')
        return
    save_memory('USER_NOTE', text)
    speak('Nota guardada.')
    await update.message.reply_text(f'🧠 **Memoria registrada:**\\n«{text}»')

async def busca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text('⚠️ Ejemplo: `/busca nota` ')
        return
    results = search_memory(query)
    if not results:
        await update.message.reply_text(f'🔍 Sin resultados para «{query}».')
        return
    msg = '🔍 **Resultados:**\\n\\n' + '\\n'.join([f'• **[{ts}]** {content}' for ts, content in results])
    await update.message.reply_text(msg)

async def backup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('📦 **Creando backup...**')
    try:
        with tarfile.open(BACKUP_PATH, 'w:gz') as tar:
            if os.path.exists(DB_PATH): tar.add(DB_PATH, arcname='daniela_memory.db')
            if os.path.exists(ROADMAP_PATH): tar.add(ROADMAP_PATH, arcname='ROADMAP.md')
        with open(BACKUP_PATH, 'rb') as doc:
            await update.message.reply_document(document=doc, filename='daniela_backup.tar.gz', caption='✅ Backup listo.')
        speak('Backup generado.')
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {e}')

async def sync_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🔄 **Iniciando Git Sync...**')
    res = auto_git_sync()
    speak('Sincronización Git realizada.')
    await update.message.reply_text(res)

async def health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    h = check_system_health()
    await update.message.reply_text(f'📱 **TELEMETRÍA:**\\n• Batería: **{h["percentage"]}%** ({h["status"]})\\n• Temp: **{h["temperature"]}°C**')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'btn_sync':
        await query.edit_message_text('🔄 **Sincronizando...**')
        res = auto_git_sync()
        await query.edit_message_text(f'✅ {res}')
    elif query.data == 'btn_top':
        res = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        output = '\\n'.join(res.stdout.splitlines()[:8])
        await query.edit_message_text(f'📊 **Procesos:**\\n```\\n{output}\\n```', parse_mode='Markdown')
    elif query.data == 'btn_backup':
        await query.edit_message_text('📦 Usa `/backup` para recibir la base de datos.')
    elif query.data == 'btn_health':
        h = check_system_health()
        await query.edit_message_text(f'🔋 **Batería:** {h["percentage"]}% | 🌡️ **Temp:** {h["temperature"]}°C')
    elif query.data == 'btn_briefing':
        speak('Reporte listo. Daniela v7 operativa.')
        await query.edit_message_text('📅 **Briefing:** Agente v7 listo.')
    elif query.data == 'btn_roadmap':
        if os.path.exists(ROADMAP_PATH):
            with open(ROADMAP_PATH, 'r', encoding='utf-8') as f:
                await query.edit_message_text(f'🗺️ **ROADMAP:**\\n\\n{f.read()[:3500]}')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.effective_user.first_name
    save_to_nexus(user_text, source=f'Telegram_Daniela')
    save_memory('CHAT_LOG', f'{user_name}: {user_text}')
    await update.message.reply_text(f'⚡ **Daniela:** Tarea procesada:\\n📝 «{user_text}»')

def main():
    if not TELEGRAM_TOKEN:
        print('⚠️ Token no configurado.')
        return
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('panel', start))
    app.add_handler(CommandHandler('alarma', alarma_handler))
    app.add_handler(CommandHandler('resumen', resumen_handler))
    app.add_handler(CommandHandler('top', top_handler))
    app.add_handler(CommandHandler('recuerda', recuerda_handler))
    app.add_handler(CommandHandler('busca', busca_handler))
    app.add_handler(CommandHandler('backup', backup_handler))
    app.add_handler(CommandHandler('sync', sync_handler))
    app.add_handler(CommandHandler('health', health_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print('🚀 [Daniela AI v7.0] ¡Activa!')
    app.run_polling()

if __name__ == '__main__':
    main()
"""

target_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/telegram_bot.py")
with open(target_path, "w") as f:
    f.write(code)
print("¡Archivo escrito correctamente!")
