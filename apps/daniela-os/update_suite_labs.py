with open("daniela_agents_suite.py") as f:
    content = f.read()

import_statement = "import daniela_google_labs_suite\n"
call_statement = "        daniela_google_labs_suite.run_google_labs_pipeline()\n"

if "daniela_google_labs_suite" not in content:
    content = import_statement + content
    content = content.replace(
        "daniela_advanced_modules.scan_boe_notarial()",
        "daniela_advanced_modules.scan_boe_notarial()\n" + call_statement,
    )
    with open("daniela_agents_suite.py", "w") as f:
        f.write(content)
    print("🟢 [SUITE]: Suite Google Labs vinculada al demonio principal.")
else:
    print("ℹ️ [SUITE]: Módulo de Google Labs ya estaba vinculado.")
