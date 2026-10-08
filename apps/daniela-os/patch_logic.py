with open("/data/data/com.termux/files/home/daniela-os/index.html") as f:
    html = f.read()

# Inyección de Lógica de Logs y LocalStorage sin alterar HTML/CSS
script_addition = """
        // --- MOTOR DE LOGS Y PERSISTENCIA (AIGESTION CORE) ---
        const systemLogs = [];

        function logEvent(type, msg) {
            const time = new Date().toLocaleTimeString();
            const logEntry = `[${time}] [${type}] ${msg}`;
            systemLogs.push(logEntry);
            localStorage.setItem('daniela_logs', JSON.stringify(systemLogs.slice(-50)));
            console.log(logEntry);
        }

        // Recuperar Estado Anterior
        window.addEventListener('DOMContentLoaded', () => {
            logEvent('SYS', 'Daniela OS v32.0 Iniciada. Núcleo Estable.');
            const savedLogs = localStorage.getItem('daniela_logs');
            if(savedLogs) {
                const parsed = JSON.parse(savedLogs);
                systemLogs.push(...parsed);
            }
        });

        // Evento Tab Logs
        document.querySelectorAll('.tab-btn').forEach((btn, idx) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const canvas = document.getElementById('webglCanvas');
                const hudOverlay = document.getElementById('hudBanner');
                const radialHub = document.getElementById('radialHub');

                if(idx === 0) { // P1: 3D
                    canvas.style.display = 'block';
                    hudOverlay.style.display = 'flex';
                    if(hubOpen) radialHub.style.display = 'flex';
                    const oldConsole = document.getElementById('consoleLogView');
                    if(oldConsole) oldConsole.remove();
                } else if(idx === 2) { // LOGS
                    canvas.style.display = 'none';
                    hudOverlay.style.display = 'none';
                    radialHub.style.display = 'none';

                    let consoleView = document.getElementById('consoleLogView');
                    if(!consoleView) {
                        consoleView = document.createElement('div');
                        consoleView.id = 'consoleLogView';
                        consoleView.style.cssText = 'position:absolute; inset:0; background:#020617; color:#22c55e; padding:15px; font-family:monospace; font-size:0.75rem; overflow-y:auto; z-index:50;';
                        document.querySelector('.viewport').appendChild(consoleView);
                    }
                    consoleView.innerHTML = '<strong>=== AIGESTION SYSTEM LOGS ===</strong><br><br>' + systemLogs.join('<br>');
                }
            });
        });
"""

# Insertar antes del cierre de script
if "MOTOR DE LOGS" not in html:
    html = html.replace("</script>", script_addition + "\n    </script>")
    with open("/data/data/com.termux/files/home/daniela-os/index.html", "w") as f:
        f.write(html)
    print("Parche aplicado con éxito.")
else:
    print("El parche ya estaba presente.")
