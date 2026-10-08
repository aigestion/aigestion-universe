import os

filepath = "index.html"
if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

# 1. CSS y Estructura del Ticker
ticker_ui = """
<style>
#ticker-container {
    width: 100%;
    background: rgba(0, 0, 0, 0.8);
    border-top: 1px solid #00ffcc;
    border-bottom: 1px solid #00ffcc;
    overflow: hidden;
    padding: 5px 0;
    margin-bottom: 10px;
    position: relative;
}
#ticker-content {
    display: inline-block;
    white-space: nowrap;
    color: #00ffcc;
    font-family: monospace;
    font-size: 0.8rem;
    animation: marquee 25s linear infinite;
}
@keyframes marquee {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>

<div id="ticker-container">
    <div id="ticker-content">Iniciando sistema Sovereign... Daniela OS lista para operar.</div>
</div>

<script>
// 2. Lógica del Ticker
const sugerencias = [
    "Sugerencia: ¿Analizamos los documentos pendientes del proyecto?",
    "Sugerencia: El nivel de batería es estable. Tiempo óptimo para tareas intensivas.",
    "Sugerencia: He detectado novedades técnicas. ¿Quieres que las resuma?",
    "Sugerencia: Domingo. Mi recomendación es un descanso táctico tras la sesión de hoy.",
    "Estado del sistema: Todos los nodos activos. Comunicación estable."
];

let i = 0;
setInterval(() => {
    document.getElementById('ticker-content').innerText = sugerencias[i];
    i = (i + 1) % sugerencias.length;
}, 15000);

// 3. LIMPIEZA: Detener el bucle de texto viejo en el PIP
window.clearInterval(window.bucleProactivoViejo);
</script>
"""

# Insertar debajo del área de la imagen (asumiendo que buscas una estructura con 'AI GESTION')
if '<div id="ticker-container">' not in html:
    # Colocamos el ticker debajo del header o del primer contenedor importante
    html = (
        html.replace("</header>", "</header>" + ticker_ui)
        if "</header>" in html
        else html.replace("<body>", "<body>" + ticker_ui)
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Ticker Sovereign instalado y PIP limpio.")
else:
    print("ℹ️ El Ticker ya estaba configurado.")
