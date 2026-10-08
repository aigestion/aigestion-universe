with open("templates/index.html") as f:
    html = f.read()

multichannel_code = """
        function fetchInvoiceAudit() {
            fetch('/api/invoice/audit')
                .then(r => r.json())
                .then(data => {
                    if (data.detected_issue && data.proposal) {
                        const prop = data.proposal;
                        const history = document.getElementById('chatHistory');
                        const card = document.createElement('div');
                        card.className = 'proposal-card';
                        card.style.borderColor = '#ff0055';
                        card.innerHTML = `
                            <div class="proposal-header">
                                <span class="proposal-title"><i class="fa-solid fa-file-invoice-dollar"></i> ALERTA FORENSE</span>
                                <span class="proposal-tag" style="background:#ff0055; color:#fff;">${prop.tag}</span>
                            </div>
                            <div style="font-weight:bold; font-size:11px; color:#ff0055;">${prop.title}</div>
                            <div class="proposal-body">${prop.body}</div>
                            <div class="proposal-actions">
                                <button class="btn-approve" onclick="respondProposal(this, true)"><i class="fa-solid fa-check"></i> ENVIAR RECLAMO</button>
                                <button class="btn-reject" onclick="respondProposal(this, false)"><i class="fa-solid fa-xmark"></i> IGNOAR</button>
                            </div>
                        `;
                        history.appendChild(card);
                        history.scrollTop = history.scrollHeight;
                        speak(prop.audioText);
                    }
                })
                .catch(() => {});
        }
        window.addEventListener('load', () => { setTimeout(fetchInvoiceAudit, 5000); });
"""

if "function fetchInvoiceAudit()" not in html:
    html = html.replace(
        "window.addEventListener('load', () => { setTimeout(fetchRealContext, 2000); });",
        "window.addEventListener('load', () => { setTimeout(fetchRealContext, 2000); });\n"
        + multichannel_code,
    )
    with open("templates/index.html", "w") as f:
        f.write(html)
    print("✅ HUD actualizado con conector multifuente (Forense + Contexto).")
