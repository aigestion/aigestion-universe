import os

from tools_registry import daniela_tool


@daniela_tool(
    keywords=["limpia", "organiza", "cuentas", "drive", "mega"],
    description="Activa la purga de Google Drive y sincronización a MEGA.",
)
def clean_accounts_tool(prompt):
    os.system("python3 ~/core/danielas_guardians.py &")
    return "Iniciando purga de Google Drive y sincronización a MEGA en segundo plano."
