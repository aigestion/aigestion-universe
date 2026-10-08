import json
import logging
import os
from datetime import datetime

JOURNAL_FILE = "journal.json"

def analyze_and_log(prompt_or_context):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "context": prompt_or_context,
            "analysis": f"Análisis visual registrado a las {timestamp}: Escena procesada correctamente."
        }

        journal_data = []
        if os.path.exists(JOURNAL_FILE):
            with open(JOURNAL_FILE, encoding='utf-8') as f:
                try:
                    journal_data = json.load(f)
                except Exception:
                    journal_data = []

        journal_data.append(entry)

        with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(journal_data, f, ensure_ascii=False, indent=2)

        logging.info(f"Entrada de diario registrada a las {timestamp}")
        return entry["analysis"]
    except Exception as e:
        logging.error(f"Error en diario visual: {str(e)}")
        return "Error al guardar la entrada del diario."
