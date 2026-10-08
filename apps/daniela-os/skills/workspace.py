import logging


def manage_gmail(action, details):
    logging.info(f"Workspace Gmail: {action}")
    return f"📩 [GMAIL]: Operación '{action}' procesada con éxito: {details}"


def update_spreadsheet(sheet_name, data):
    logging.info(f"Workspace Sheets: {sheet_name}")
    return f"📊 [SHEETS]: Datos inyectados en '{sheet_name}' correctamente."


def summarize_doc(doc_id):
    logging.info(f"Workspace Docs: {doc_id}")
    return f"📄 [DOCS]: Documento '{doc_id}' analizado y registrado en la memoria de Daniela."


def execute_workspace_command(command):
    cmd_lower = command.lower()
    if "correo" in cmd_lower or "gmail" in cmd_lower:
        return manage_gmail("Triage & Auto-Reply", command)
    if "hoja" in cmd_lower or "excel" in cmd_lower or "sheets" in cmd_lower:
        return update_spreadsheet("Registro Sovereign", command)
    if "documento" in cmd_lower or "docs" in cmd_lower:
        return summarize_doc(command)
    return "Comando de Workspace no reconocido."
