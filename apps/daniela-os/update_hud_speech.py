with open("templates/index.html") as f:
    html = f.read()

# Mejorar el handler de mensajes de chat
old_send = """            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            })
            .then(res => res.json())
            .then(data => {
                appendMsg('ai', data.response);
                speakingAmplitude = 1.0;
                speak(data.response);
            });"""

new_send = """            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            })
            .then(res => res.json())
            .then(data => {
                appendMsg('ai', data.response);
                speakingAmplitude = 1.5;
                const textToSpeak = data.audio_speech || data.response;
                speak(textToSpeak);
            });"""

if "data.audio_speech" not in html:
    html = html.replace(old_send, new_send)
    with open("templates/index.html", "w") as f:
        f.write(html)
    print("✅ HUD actualizado con Salidas Audiovisuales mejoradas.")
