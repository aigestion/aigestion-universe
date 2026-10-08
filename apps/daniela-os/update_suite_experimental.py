with open("daniela_agents_suite.py") as f:
    content = f.read()

import_statement = "import daniela_experimental_labs\n"
call_statement = "        daniela_experimental_labs.run_experimental_pipeline()\n"

if "daniela_experimental_labs" not in content:
    content = import_statement + content
    content = content.replace(
        "daniela_google_labs_suite.run_google_labs_pipeline()",
        "daniela_google_labs_suite.run_google_labs_pipeline()\n" + call_statement,
    )
    with open("daniela_agents_suite.py", "w") as f:
        f.write(content)
    print("🟢 [SUITE]: Motor Experimental de Fase 11 vinculado al demonio principal.")
else:
    print("ℹ️ [SUITE]: Módulo Experimental ya estaba vinculado.")
