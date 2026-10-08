with open("daniela_agents_suite.py") as f:
    content = f.read()

import_code = "import daniela_workspace_master\n"
call_code = "        daniela_workspace_master.run_workspace_pipeline()\n"

if "daniela_workspace_master" not in content:
    content = import_code + content
    content = content.replace("auto_git_backup()", "auto_git_backup()\n" + call_code)
    with open("daniela_agents_suite.py", "w") as f:
        f.write(content)
    print("🟢 [SUITE]: Integración completa de Google Workspace vinculada al demonio principal.")
else:
    print("ℹ️ [SUITE]: Módulo maestro de Workspace ya vinculado.")
