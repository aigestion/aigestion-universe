import os
import sqlite3

db_path = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS finops_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now', 'localtime')),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    model_used TEXT,
    tier TEXT,
    estimated_cost_usd REAL,
    saved_cost_usd REAL,
    task_type TEXT
)
""")

conn.commit()
conn.close()
print("✨ [FinOps DB] Tabla 'finops_metrics' creada/verificada en daniela_memory.db.")
