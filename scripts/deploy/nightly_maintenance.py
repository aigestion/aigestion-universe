import glob
import os
import sqlite3

# 1. Purgar temporales
os.system('powershell -Command "Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue"')

# 2. Compactar SQLite DBs
db_paths = glob.glob(os.path.expanduser('~\\AppData\\Local\\hermes\\*.db')) + glob.glob('C:\\Users\\Alejandro\\aig\\*.db')
for db in db_paths:
    try:
        conn = sqlite3.connect(db)
        conn.execute('VACUUM;')
        conn.close()
    except Exception:
        pass

print("Mantenimiento nocturno completado.")
