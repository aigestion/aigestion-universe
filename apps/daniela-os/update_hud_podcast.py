with open("templates/index.html") as f:
    html = f.read()

podcast_code = """
        function fetchDailyPodcast() {
            fetch('/api/podcast/daily')
                .then(r => r.json())
                .then(data => {
                    if (data.proposal) {
                        const prop = data.proposal;
                        const history = document.getElementById('chatHistory');
                        const card = document.createElement('div');
                        card.className = 'proposal-card';
                        card.style.borderColor = '#ffaa00';
                        card.innerHTML = `
                            <div class="proposal-header">
                                <span class="proposal-title"><i class="fa-solid fa-podcast"></i> AUDIO OVERVIEW DIARIO</span>
                                <span class="proposal-tag" style="background:#ffaa00; color:#03060a;">${prop.tag}</span>
                            </div>
                            <div style="font-weight:bold; font-size:11px; color:#ffaa00;">${prop.title}</div>
                            <div class="proposal-body">${prop.body}</div>
                            <div class="proposal-actions">
                                <button class="btn-approve" style="border-color:#ffaa00; color:#ffaa00; background:rgba(255,170,0,0.15);" onclick="respondProposal(this, true)"><i class="fa-solid fa-play"></i> REPRODUCIR</button>
                                <button class="btn-reject" onclick="respondProposal(this, false)"><i class="fa-solid fa-xmark"></i> OMITIR</button>
                            </div>
                        `;
                        history.appendChild(card);
                        history.scrollTop = history.scrollHeight;
                        speak(prop.audioText);
                    }
                })
                .catch(() => {});
        }
        window.addEventListener('load', () => { setTimeout(fetchDailyPodcast, 8000); });
"""

if "function fetchDailyPodcast()" not in html:
    html = html.replace(
        "window.addEventListener('load', () => { setTimeout(fetchInvoiceAudit, 5000); });",
        "window.addEventListener('load', () => { setTimeout(fetchInvoiceAudit, 5000); });\n"
        + podcast_code,
    )
    with open("templates/index.html", "w") as f:
        f.write(html)
    print("✅ HUD actualizado con reproductor de Podcast Ejecutivo.")
