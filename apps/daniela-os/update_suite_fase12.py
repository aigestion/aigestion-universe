with open("daniela_agents_suite.py") as f:
    content = f.read()

import_statement = "import daniela_fase12_quantum_swarm\n"
call_statement = "        daniela_fase12_quantum_swarm.run_fase12_pipeline()\n"

if "daniela_fase12_quantum_swarm" not in content:
    content = import_statement + content
    content = content.replace(
        "daniela_experimental_labs.run_experimental_pipeline()",
        "daniela_experimental_labs.run_experimental_pipeline()\n" + call_statement,
    )
    with open("daniela_agents_suite.py", "w") as f:
        f.write(content)
    print("🟢 [SUITE]: Motor Fase 12 vinculado al demonio principal.")
else:
    print("ℹ️ [SUITE]: Módulo Fase 12 ya estaba vinculado.")
