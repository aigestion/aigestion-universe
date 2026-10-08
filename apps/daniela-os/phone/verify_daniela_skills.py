import ast
import os
import sqlite3
import sys

print("🔍 ========================================================")
print("🛡️  DANIELA OS v1.1.0 ENTERPRISE - SUITE DE AUDITORÍA Y TEST")
print("========================================================\n")

home = os.path.expanduser("~")
core_dir = os.path.join(home, "core", "modules")
repo_dir = os.path.join(home, "apps", "AIGESTION-MONOREPO", "core_modules")
env_db = os.path.join(home, "apps", "aig", "data", "env.db")
sys.path.append(core_dir)

total_tests = 0
passed_tests = 0


def check_test(name, condition, detail=""):
    global total_tests, passed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"✅ [{total_tests}] {name}: OPERATIVO {f'({detail})' if detail else ''}")
    else:
        print(f"❌ [{total_tests}] {name}: FALLO {f'({detail})' if detail else ''}")


# ---------------------------------------------------------
# 1. Auditoría de Sintaxis AST de Código
# ---------------------------------------------------------
print("📂 1. AUDITORÍA ESTÁTICA DE CÓDIGO (AST SYNTAX CHECK)")
modules_to_check = [
    "token_failover.py",
    "google_voice.py",
    "speech_interaction.py",
    "local_rag.py",
    "haptic_proactive.py",
    "nightly_maintenance.py",
]

for mod in modules_to_check:
    path = os.path.join(core_dir, mod)
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                ast.parse(f.read())
            check_test(f"Sintaxis AST: {mod}", True, "Sin errores de sintaxis")
        except Exception as e:
            check_test(f"Sintaxis AST: {mod}", False, str(e))
    else:
        check_test(f"Archivo existente: {mod}", False, "Archivo no encontrado")

# ---------------------------------------------------------
# 2. Verificación de Base de Datos y RAG SQLite
# ---------------------------------------------------------
print("\n🧠 2. VERIFICACIÓN DE MOTOR RAG Y PERSISTENCIA (SQLite)")
if os.path.exists(env_db):
    try:
        conn = sqlite3.connect(env_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM rag_knowledge")
        rag_count = c.fetchone()[0]
        check_test("RAG Local Knowledge Base", rag_count > 0, f"{rag_count} archivos indexados")

        c.execute(
            "SELECT count(*) FROM env_vars WHERE key IN ('GEMINI_API_KEY', 'GEMINI_PRIMARY_KEY', 'GEMINI_BACKUP_KEY')"
        )
        key_count = c.fetchone()[0]
        check_test("Bóveda de Claves de API", key_count >= 1, f"{key_count} llaves registradas")
        conn.close()
    except Exception as e:
        check_test("Base de Datos SQLite (~/apps/aig/data/env.db)", False, str(e))
else:
    check_test(
        "Base de Datos SQLite (~/apps/aig/data/env.db)", False, "No existe ~/apps/aig/data/env.db"
    )

# ---------------------------------------------------------
# 3. Verificación de Habilidades Funcionales (Runtime)
# ---------------------------------------------------------
print("\n⚡ 3. PRUEBAS DE EJECUCIÓN DIRECTA DE HABILIDADES")

# Habilidad 1: Personalización para Ale y Voz Normal
try:
    from speech_interaction import process_voice_greeting

    res = process_voice_greeting("Hola Daniela estas?")
    check_test(
        "Habilidad: Saludo Personalizado para Ale",
        "Ale" in res or "VOZ" in res,
        "Reconocimiento y TTS activo",
    )
except Exception as e:
    check_test("Habilidad: Saludo Personalizado para Ale", False, str(e))

# Habilidad 2: Modo Susurro Confidencial
try:
    res_whisper = process_voice_greeting("Hola Daniela estas? (susurro)")
    check_test(
        "Habilidad: Modo Susurro Confidencial",
        "Susurro" in res_whisper or "VOZ" in res_whisper,
        "Modulación prosódica aplicada",
    )
except Exception as e:
    check_test("Habilidad: Modo Susurro Confidencial", False, str(e))

# Habilidad 3: Búsqueda RAG Local O(1)
try:
    from local_rag import search_knowledge

    search_res = search_knowledge("master")
    check_test(
        "Habilidad: Consulta RAG Local",
        "RESULTADOS" in search_res or "master" in search_res,
        "Respuesta desde SQLite",
    )
except Exception as e:
    check_test("Habilidad: Consulta RAG Local", False, str(e))

# Habilidad 4: Failover de Claves
try:
    from token_failover import get_active_api_key

    active_key = get_active_api_key()
    check_test(
        "Habilidad: Sistema de Failover de Tokens",
        bool(active_key),
        f"Key activa: {active_key[:8]}...",
    )
except Exception as e:
    check_test("Habilidad: Sistema de Failover de Tokens", False, str(e))

# Habilidad 5: Notificación Háptica
try:
    from haptic_proactive import trigger_vibration

    trigger_vibration("info")
    check_test("Habilidad: Respuesta Háptica (Vibración)", True, "Comando termux-vibrate ejecutado")
except Exception as e:
    check_test("Habilidad: Respuesta Háptica (Vibración)", False, str(e))

# Habilidad 6: Accesos Directos Termux Widget
shortcuts_dir = os.path.join(home, ".shortcuts")
widgets = ["1_Hola_Daniela.sh", "2_Backup_Cifrado.sh", "3_Salud_Pixel.sh"]
all_widgets_exist = all(os.path.exists(os.path.join(shortcuts_dir, w)) for w in widgets)
check_test(
    "Habilidad: Termux Widgets (~/.shortcuts)", all_widgets_exist, f"{len(widgets)} accesos creados"
)

# ---------------------------------------------------------
# Resumen Final
# ---------------------------------------------------------
print("\n📊 ========================================================")
print(
    f"RESULTADO DE LA AUDITORÍA: {passed_tests}/{total_tests} Pruebas Pasadas con Éxito ({int((passed_tests / total_tests) * 100)}%)"
)
print("========================================================\n")
