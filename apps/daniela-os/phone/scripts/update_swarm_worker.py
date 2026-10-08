import os

repo_dir = os.path.expanduser("~/aig-monorepo/pixela8/app/agents")

worker_code = """#!/usr/bin/env python3
import os, sqlite3, time

DB_PATH = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")

class WorkerAgent:
    def __init__(self):
        self.init_worker_db()

    def init_worker_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS background_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, task_name TEXT, status TEXT, result TEXT)')
        conn.commit()
        conn.close()

    def enqueue_task(self, task_name: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO background_jobs (timestamp, task_name, status) VALUES (?, ?, ?)", (ts, task_name, "PENDING"))
        conn.commit()
        job_id = cursor.lastrowid
        conn.close()
        return job_id

    def process_next_job(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_name FROM background_jobs WHERE status = 'PENDING' LIMIT 1")
        job = cursor.fetchone()
        if job:
            job_id, task_name = job
            cursor.execute("UPDATE background_jobs SET status = 'PROCESSING' WHERE id = ?", (job_id,))
            conn.commit()
            conn.close()

            # Ejecución simulada de trabajo pesado
            time.sleep(2)
            res = f"Tarea '{task_name}' completada con éxito."

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE background_jobs SET status = 'COMPLETED', result = ? WHERE id = ?", (res, job_id))
            conn.commit()
            conn.close()
            return task_name, res
        conn.close()
        return None, None
"""

with open(os.path.join(repo_dir, "agent_worker.py"), "w", encoding="utf-8") as f:
    f.write(worker_code)
os.chmod(os.path.join(repo_dir, "agent_worker.py"), 0o755)

print("⚙️ agent_worker.py actualizado con éxito.")
