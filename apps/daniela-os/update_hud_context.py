with open("templates/index.html") as f:
    html = f.read()

# Insertar función de auto-evaluación al cargar
js_patch = """
        function fetchRealContext() {
            fetch('/api/context/evaluate')
                .then(r => r.json())
                .then(data => {
                    if (data.proposals && data.proposals.length > 0) {
                        const prop = data.proposals[0];
                        const history = document.getElementById('chatHistory');
                        const card = document.createElement('div');
                        card.className = 'proposal-card';
                        card.innerHTML = `
                            <div class="proposal-header">
                                <span class="proposal-title"><i class="fa-solid fa-satellite-dish"></i> PROPUESTA DE CONTEXTO REAL</span>
                                <span class="proposal-tag">${prop.tag}</span>
                            </div>
                            <div style="font-weight:bold; font-size:11px; color:#00f0ff;">${prop.title}</div>
                            <div class="proposal-body">${prop.body}</div>
                            <div class="proposal-actions">
                                <button class="btn-approve" onclick="respondProposal(this, true)"><i class="fa-solid fa-check"></i> APROBAR</button>
                                <button class="btn-reject" onclick="respondProposal(this, false)"><i class="fa-solid fa-xmark"></i> RECHAZAR</button>
                            </div>
                        `;
                        history.appendChild(card);
                        history.scrollTop = history.scrollHeight;
                        speak(prop.audioText);
                    }
                })
                .catch(() => {});
        }
        window.addEventListener('load', () => { setTimeout(fetchRealContext, 2000); });
"""

if "function fetchRealContext()" not in html:
    html = html.replace(
        "window.onload = () => { initFilteredSpeech(); };",
        "window.onload = () => { initFilteredSpeech(); };\n" + js_patch,
    )
    with open("templates/index.html", "w") as f:
        f.write(html)
    print("✅ HUD actualizado con auto-evaluación contextual.")
