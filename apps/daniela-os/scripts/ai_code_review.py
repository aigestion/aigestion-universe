import json
import subprocess
import sys
import urllib.request


def get_staged_python_files():
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "*.py"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return [f for f in res.stdout.strip().split("\n") if f]


def get_staged_diff(filepath):
    cmd = ["git", "diff", "--cached", filepath]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout


def review_code_with_llm(diff_text):
    prompt = f"offline Revisa este diff de Python y detecta errores de sintaxis, seguridad o indentación:\n{diff_text[:1000]}"
    try:
        req = urllib.request.Request(
            "http://localhost:8085/api/chat",
            data=json.dumps({"message": prompt}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data.get("response", "")
    except Exception as e:
        return f"⚠️ No se pudo conectar con Skill #32A: {e}"


files = get_staged_python_files()
if not files or files == [""]:
    print("🤖 [AI PRE-COMMIT]: Sin archivos Python para revisar.")
    sys.exit(0)

print(f"🤖 [AI PRE-COMMIT]: Analizando {len(files)} archivo(s) Python con Skill #32A...")

for f in files:
    diff = get_staged_diff(f)
    if diff:
        print(f"\n🔍 Revisando '{f}'...")
        review = review_code_with_llm(diff)
        print(review)

print("\n✅ [AI PRE-COMMIT]: Inspección finalizada.")
sys.exit(0)
