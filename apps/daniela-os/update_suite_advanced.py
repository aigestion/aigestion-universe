with open("daniela_agents_suite.py") as f:
    content = f.read()

import_statement = "import daniela_advanced_modules\n"
call_statement = "        daniela_advanced_modules.scan_boe_notarial()\n"

if "daniela_advanced_modules" not in content:
    content = import_statement + content
    content = content.replace(
        "daniela_workspace_master.run_workspace_pipeline()",
        "daniela_workspace_master.run_workspace_pipeline()\n" + call_statement,
    )
    with open("daniela_agents_suite.py", "w") as f:
        f.write(content)
    print("🟢 [SUITE]: Módulos avanzados integrados en el bucle principal.")
