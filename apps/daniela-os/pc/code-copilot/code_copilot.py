"""
System 6: AI Code Copilot Overlay
Floating overlay that explains, suggests, and finds bugs in code
"""

import re

from flask import Flask, jsonify, request

app = Flask(__name__)

# Code analysis patterns
BUG_PATTERNS = {
    "eval": {"severity": "high", "msg": "Use of eval() is dangerous - injection risk"},
    "exec": {"severity": "high", "msg": "Use of exec() is dangerous - injection risk"},
    "password.*=.*['\"]": {"severity": "medium", "msg": "Hardcoded password detected"},
    "TODO": {"severity": "low", "msg": "TODO comment found"},
    "FIXME": {"severity": "medium", "msg": "FIXME comment found"},
    "except:": {"severity": "medium", "msg": "Bare except clause - catch specific exceptions"},
    "print(": {"severity": "info", "msg": "Print statement - consider using logging"},
    "import \\*": {"severity": "medium", "msg": "Wildcard import - import specific items"},
    "global ": {"severity": "low", "msg": "Global variable usage - consider refactoring"},
    "sleep\\(": {"severity": "info", "msg": "Sleep call - may block event loop"},
}

EXPLANATIONS = {
    "def ": "Function definition",
    "class ": "Class definition",
    "import ": "Module import",
    "return ": "Return statement",
    "async ": "Async function",
    "await ": "Await expression",
    "lambda ": "Lambda expression",
    "with ": "Context manager",
    "for ": "For loop",
    "while ": "While loop",
    "if ": "Conditional",
    "try:": "Try block",
    "except": "Exception handler",
}


@app.route("/")
def index():
    return COPILOT_HTML


@app.route("/api/copilot/analyze", methods=["POST"])
def analyze_code():
    data = request.json or {}
    code = data.get("code", "")

    bugs = []
    explanations = []
    suggestions = []

    lines = code.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Bug detection
        for pattern, info in BUG_PATTERNS.items():
            if re.search(pattern, stripped):
                bugs.append(
                    {
                        "line": i + 1,
                        "severity": info["severity"],
                        "msg": info["msg"],
                        "code": stripped[:80],
                    }
                )

        # Explanation detection
        for pattern, explanation in EXPLANATIONS.items():
            if stripped.startswith(pattern) or pattern in stripped:
                explanations.append(
                    {"line": i + 1, "explanation": explanation, "code": stripped[:80]}
                )

    # Suggestions
    if len(lines) > 50:
        suggestions.append("Consider splitting into smaller functions (>50 lines)")
    if not any("def " in l or "class " in l for l in lines):
        suggestions.append("No functions/classes defined - consider encapsulating logic")
    if code.count("import") > 10:
        suggestions.append("Many imports - consider using __all__ or grouping")
    if len(set(re.findall(r"#.*", code))) > 5:
        suggestions.append("Multiple comments - consider docstrings instead")

    return jsonify({"bugs": bugs, "explanations": explanations, "suggestions": suggestions})


@app.route("/api/copilot/explain", methods=["POST"])
def explain_line():
    data = request.json or {}
    line = data.get("line", "")

    explanation = "No explanation available"
    for pattern, desc in EXPLANATIONS.items():
        if pattern in line:
            explanation = desc
            break

    if not line.strip():
        explanation = "Empty line"
    elif line.strip().startswith("#"):
        explanation = "Comment"
    elif "=" in line and "==" not in line:
        explanation = "Variable assignment"

    return jsonify({"explanation": explanation})


COPILOT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AI Code Copilot</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#030814; color:#e2e8f0; font-family:'Rajdhani',sans-serif; display:flex; height:100vh; }
#editor-panel { flex:1; display:flex; flex-direction:column; padding:20px; }
#analysis-panel { width:350px; background:rgba(3,8,20,0.9); border-left:1px solid rgba(0,240,255,0.2); padding:16px; overflow-y:auto; }
h1 { font-family:'Orbitron',monospace; color:#00f0ff; font-size:16px; letter-spacing:3px; margin-bottom:12px; }
h2 { font-size:12px; color:#00f0ff; margin:12px 0 6px; letter-spacing:1px; }
textarea { flex:1; background:rgba(0,240,255,0.03); border:1px solid rgba(0,240,255,0.15); color:#e2e8f0; font-family:'Share Tech Mono',monospace; font-size:13px; padding:12px; border-radius:8px; resize:none; line-height:1.5; }
textarea:focus { outline:none; border-color:#00f0ff; }
.analyze-btn { background:rgba(0,240,255,0.1); border:1px solid #00f0ff; color:#00f0ff; padding:8px 16px; border-radius:6px; cursor:pointer; font-family:inherit; margin:8px 0; }
.analyze-btn:hover { background:rgba(0,240,255,0.2); }
.bug { padding:6px; border-radius:6px; margin-bottom:4px; font-size:11px; border-left:3px solid; }
.bug.high { border-color:#ef4444; background:rgba(239,68,68,0.05); }
.bug.medium { border-color:#f59e0b; background:rgba(245,158,11,0.05); }
.bug.low { border-color:#22c55e; background:rgba(34,197,94,0.05); }
.bug.info { border-color:#0ea5e9; background:rgba(14,165,233,0.05); }
.explanation { font-size:11px; color:#94a3b8; padding:4px 0; border-bottom:1px solid rgba(0,240,255,0.05); }
.suggestion { font-size:11px; color:#f59e0b; padding:4px 0; }
.line-num { color:#64748b; margin-right:6px; }
.stats { position:fixed; bottom:10px; left:20px; font-size:10px; color:#64748b; font-family:'Share Tech Mono',monospace; }
</style></head><body>
<div id="editor-panel">
  <h1>🤖 AI CODE COPILOT</h1>
  <textarea id="code" placeholder="Paste your code here..." spellcheck="false">
# Example: Paste your code
def process_data(items):
    result = []
    for item in items:
        # TODO: Add validation
        eval(item)  # Bug: dangerous!
        result.append(item)
    return result
</textarea>
  <button class="analyze-btn" onclick="analyze()">Analyze Code</button>
</div>
<div id="analysis-panel">
  <h2>🔴 BUGS</h2><div id="bugs"></div>
  <h2>📝 EXPLANATIONS</h2><div id="explanations"></div>
  <h2>💡 SUGGESTIONS</h2><div id="suggestions"></div>
</div>
<div class="stats" id="stats"></div>
<script>
async function analyze() {
  const code = document.getElementById('code').value;
  const r = await fetch('/api/copilot/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code})});
  const d = await r.json();

  document.getElementById('bugs').innerHTML = d.bugs.length ?
    d.bugs.map(b => '<div class="bug ' + b.severity + '"><b>L' + b.line + '</b> ' + b.msg + '<br><code>' + b.code + '</code></div>').join('') :
    '<div class="bug info">No bugs found ✅</div>';

  document.getElementById('explanations').innerHTML = d.explanations.map(e =>
    '<div class="explanation"><span class="line-num">L' + e.line + '</span>' + e.explanation + '</div>'
  ).join('');

  document.getElementById('suggestions').innerHTML = d.suggestions.map(s =>
    '<div class="suggestion">💡 ' + s + '</div>'
  ).join('') || '<div style="color:#64748b;font-size:11px">No suggestions</div>';

  document.getElementById('stats').textContent = d.bugs.length + ' bugs | ' + d.explanations.length + ' explained | ' + d.suggestions.length + ' suggestions';
}
analyze();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 6] AI Code Copilot starting on port 5015...")
    app.run(host="0.0.0.0", port=5015, debug=False)
