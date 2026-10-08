from flask import Blueprint, jsonify, request

mood_detect_bp = Blueprint("mood_detection", __name__)

MOOD_KEYWORDS = {
    "happy": ["great", "awesome", "love", "amazing", "perfect", "genial", "increible"],
    "sad": ["bad", "terrible", "hate", "worst", "horrible", "triste", "malo"],
    "angry": ["angry", "furious", "hate", "stupid", "enfadado", "furioso"],
    "neutral": []
}

@mood_detect_bp.route("/api/hermes/personality/mood/detect", methods=["POST"])
def md_detect():
    text = request.json.get("text", "").lower()
    mood = "neutral"
    for m, keywords in MOOD_KEYWORDS.items():
        if any(k in text for k in keywords):
            mood = m
            break
    return jsonify({"mood": mood, "confidence": 0.8 if mood != "neutral" else 0.5})

@mood_detect_bp.route("/api/hermes/personality/mood/web")
def md_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Mood Detection</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.mood{text-align:center}
.face{font-size:80px;margin:20px 0}
textarea{width:300px;height:80px;background:#111;border:1px solid #333;color:#00f0ff;padding:10px;border-radius:8px;font-family:monospace}
button{padding:10px 20px;background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;border-radius:8px;cursor:pointer;margin-top:10px}
</style></head><body><div class="mood"><h2>MOOD DETECTION</h2><div class="face" id="face">😐</div>
<textarea id="text" placeholder="Type something..."></textarea><br>
<button onclick="detect()">Detect Mood</button></div>
<script>const emojis={happy:'😊',sad:'😢',angry:'😠',neutral:'😐'};
function detect(){fetch('/api/hermes/personality/mood/detect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:document.getElementById('text').value})}).then(r=>r.json()).then(d=>{document.getElementById('face').textContent=emojis[d.mood]||'😐'})}</script></body></html>"""
