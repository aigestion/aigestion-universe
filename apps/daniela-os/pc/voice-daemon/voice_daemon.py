"""
System 1: Voice-Controlled AI Desktop
Wake word "Hey Daniela" → voice commands to control PC
"""

import json
import subprocess
import webbrowser

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

COMMANDS = {
    "open": {
        "apps": {
            "chrome": "chrome",
            "firefox": "firefox",
            "edge": "msedge",
            "code": "code",
            "vscode": "code",
            "windsurf": "windsurf",
            "notepad": "notepad",
            "explorer": "explorer",
            "calculator": "calc",
            "spotify": "spotify",
            "discord": "discord",
            "slack": "slack",
            "terminal": "wt",
            "powershell": "pwsh",
            "cmd": "cmd",
            "blender": "blender",
            "obsidian": "obsidian",
        }
    },
    "screenshot": {"action": "screenshot"},
    "volume": {"action": "volume"},
    "search": {"action": "search"},
    "sleep": {"action": "sleep"},
    "lock": {"action": "lock"},
    "restart": {"action": "restart"},
    "shutdown": {"action": "shutdown"},
    "weather": {"action": "weather"},
    "time": {"action": "time"},
    "briefing": {"action": "briefing"},
}


def execute_command(text):
    text = text.lower().strip()

    # Open app
    if text.startswith(("open ", "abre ")):
        app_name = text.replace("open ", "").replace("abre ", "").strip()
        apps = COMMANDS["open"]["apps"]
        if app_name in apps:
            try:
                subprocess.Popen([apps[app_name]], shell=True)
                return f"Opening {app_name}"
            except Exception as e:
                return f"Error opening {app_name}: {e}"
        return f"App '{app_name}' not found"

    # Screenshot
    if "screenshot" in text or "captura" in text:
        try:
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object { $bmp = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height); $gfx = [System.Windows.Forms.Graphics]::FromImage($bmp); $gfx.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size); $bmp.Save('$HOME\\Desktop\\screenshot.png') }",
                ],
                capture_output=True,
            )
            return "Screenshot saved to Desktop"
        except Exception as e:
            return f"Screenshot error: {e}"

    # Volume
    if "volume" in text or "volumen" in text:
        if "up" in text or "sube" in text:
            subprocess.run(["powershell", "-c", "Set-Volume -AccessMask 5"], capture_output=True)
            return "Volume up"
        elif "down" in text or "baja" in text:
            subprocess.run(["powershell", "-c", "Set-Volume -AccessMask -5"], capture_output=True)
            return "Volume down"
        elif "mute" in text or "silencio" in text:
            subprocess.run(["powershell", "-c", "Set-Volume -Mute $true"], capture_output=True)
            return "Muted"
        return "Volume command not clear"

    # Lock
    if "lock" in text or "bloquea" in text:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], capture_output=True)
        return "Locking screen"

    # Weather
    if "weather" in text or "clima" in text or "tiempo" in text:
        try:
            import urllib.request

            data = json.loads(urllib.request.urlopen("https://wttr.in/?format=j1").read())
            current = data["current_condition"][0]
            return f"Weather: {current['weatherDesc'][0]['value']}, {current['temp_C']}°C, Humidity: {current['humidity']}%"
        except Exception:
            return "Weather service unavailable"

    # Time
    if "time" in text or "hora" in text:
        from datetime import datetime

        return f"Current time: {datetime.now().strftime('%H:%M:%S')}"

    # Sleep/Shutdown/Restart
    if "sleep" in text or "dormir" in text:
        subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], capture_output=True
        )
        return "Going to sleep"
    if "shutdown" in text or "apagar" in text:
        subprocess.run(["shutdown", "/s", "/t", "60"], capture_output=True)
        return "Shutting down in 60 seconds"
    if "restart" in text or "reiniciar" in text:
        subprocess.run(["shutdown", "/r", "/t", "60"], capture_output=True)
        return "Restarting in 60 seconds"

    # Default: search
    if text:
        webbrowser.open(f"https://www.google.com/search?q={text}")
        return f"Searching for: {text}"

    return "Command not recognized"


@app.route("/")
def index():
    return render_template_string(VOICE_HTML)


@app.route("/api/voice/command", methods=["POST"])
def voice_command():
    data = request.json or {}
    text = data.get("text", "")
    result = execute_command(text)
    return jsonify({"response": result, "command": text})


@app.route("/api/voice/status")
def voice_status():
    return jsonify(
        {"status": "active", "wake_word": "Hey Daniela", "commands": list(COMMANDS.keys())}
    )


VOICE_HTML = """
<!DOCTYPE html>
<html><head><title>Voice AI Desktop</title>
<style>
body { background: #030814; color: #00f0ff; font-family: 'Orbitron', monospace; text-align: center; padding: 40px; }
h1 { font-size: 24px; letter-spacing: 4px; }
.mic-btn { width: 120px; height: 120px; border-radius: 50%; border: 3px solid #00f0ff; background: rgba(0,240,255,0.1); font-size: 48px; cursor: pointer; margin: 30px; transition: all 0.3s; }
.mic-btn:hover { box-shadow: 0 0 40px rgba(0,240,255,0.5); transform: scale(1.05); }
.mic-btn.listening { border-color: #ff0055; animation: pulse 1s infinite; }
.status { font-family: 'Share Tech Mono', monospace; margin-top: 20px; font-size: 14px; }
.log { text-align: left; max-width: 600px; margin: 20px auto; font-family: 'Share Tech Mono', monospace; font-size: 12px; color: #64748b; max-height: 300px; overflow-y: auto; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 20px #ff0055; } 50% { box-shadow: 0 0 40px #ff0055; } }
</style></head><body>
<h1>🎤 VOICE AI DESKTOP</h1>
<p class="status">Wake word: "Hey Daniela"</p>
<button class="mic-btn" id="mic" onclick="toggleMic()">🎤</button>
<div class="status" id="status">Click to speak</div>
<div class="log" id="log"></div>
<script>
let listening = false;
let recognition;
function toggleMic() {
  if (listening) { recognition?.stop(); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR(); recognition.lang = 'es-ES'; recognition.continuous = false;
  recognition.onresult = async (e) => {
    const text = e.results[0][0].transcript;
    document.getElementById('status').textContent = 'You: ' + text;
    document.getElementById('log').innerHTML += '<div>🗣️ ' + text + '</div>';
    const resp = await fetch('/api/voice/command', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})});
    const data = await resp.json();
    document.getElementById('log').innerHTML += '<div>🤖 ' + data.response + '</div>';
    document.getElementById('status').textContent = data.response;
  };
  recognition.onend = () => { listening = false; document.getElementById('mic').classList.remove('listening'); document.getElementById('status').textContent = 'Click to speak'; };
  recognition.start(); listening = true; document.getElementById('mic').classList.add('listening');
  document.getElementById('status').textContent = 'Listening...';
}
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 1] Voice AI Desktop starting on port 5010...")
    app.run(host="0.0.0.0", port=5010, debug=False)
