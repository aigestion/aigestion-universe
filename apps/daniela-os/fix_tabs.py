with open("/data/data/com.termux/files/home/daniela-os/index.html") as f:
    html = f.read()

# Lógica limpia para las 3 pestañas superiores
tabs_fix = """
        // --- VINCULACIÓN DE BOTONES SUPERIORES (P1, P2, LOGS) ---
        document.addEventListener('DOMContentLoaded', () => {
            const tabs = document.querySelectorAll('.tab-btn');
            const canvas = document.getElementById('webglCanvas');
            const hudBanner = document.getElementById('hudBanner');
            const radialHub = document.getElementById('radialHub');
            const viewport = document.querySelector('.viewport');

            tabs.forEach((tab, index) => {
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');

                    // Crear o recuperar vista de consola de logs
                    let consoleView = document.getElementById('consoleLogView');
                    if (!consoleView) {
                        consoleView = document.createElement('div');
                        consoleView.id = 'consoleLogView';
                        consoleView.style.cssText = 'position:absolute; inset:0; background:#020617; color:#22c55e; padding:15px; font-family:monospace; font-size:0.75rem; overflow-y:auto; z-index:50; display:none;';
                        viewport.appendChild(consoleView);
                    }

                    if (index === 0) { // P1: 3D HUD
                        canvas.style.display = 'block';
                        hudBanner.style.display = 'flex';
                        if (radialHub) radialHub.style.display = 'flex';
                        consoleView.style.display = 'none';
                    } else if (index === 1) { // P2: CHAT
                        canvas.style.display = 'block';
                        hudBanner.style.display = 'flex';
                        if (radialHub) radialHub.style.display = 'none';
                        consoleView.style.display = 'none';
                    } else if (index === 2) { // LOGS
                        canvas.style.display = 'none';
                        hudBanner.style.display = 'none';
                        if (radialHub) radialHub.style.display = 'none';
                        consoleView.style.display = 'block';

                        const logs = (typeof systemLogs !== 'undefined' && systemLogs.length > 0)
                            ? systemLogs.join('<br>')
                            : '[SYS_OK] Consola de eventos iniciada. Registrando actividad...';
                        consoleView.innerHTML = '<strong>=== AIGESTION TERMINAL LOGS ===</strong><br><br>' + logs;
                    }
                });
            });
        });
"""

if "VINCULACIÓN DE BOTONES SUPERIORES" not in html:
    html = html.replace("</script>", tabs_fix + "\n    </script>")
    with open("/data/data/com.termux/files/home/daniela-os/index.html", "w") as f:
        f.write(html)
    print("Corrección de pestañas aplicada.")
else:
    print("El parche de pestañas ya está activo.")
