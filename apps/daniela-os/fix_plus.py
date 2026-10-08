with open("/data/data/com.termux/files/home/daniela-os/index.html") as f:
    html = f.read()

# Reemplazo de la función toggleRadialHub para forzar la apertura del menú
old_func = """function toggleRadialHub() {
            hubOpen = !hubOpen;
            document.getElementById('radialHub').classList.toggle('open', hubOpen);
            document.getElementById('btnPlus').classList.toggle('active', hubOpen);
            if(!hubOpen) mat.color.setHex(isListening ? 0x22c55e : 0x38bdf8);
            else mat.color.setHex(0xf59e0b);
        }"""

new_func = """function toggleRadialHub() {
            hubOpen = !hubOpen;
            const hub = document.getElementById('radialHub');
            const btn = document.getElementById('btnPlus');

            if (hubOpen) {
                hub.style.display = 'flex';
                hub.classList.add('open');
                if(btn) btn.classList.add('active');
                if(typeof mat !== 'undefined') mat.color.setHex(0xf59e0b);
            } else {
                hub.classList.remove('open');
                hub.style.display = 'none';
                if(btn) btn.classList.remove('active');
                if(typeof mat !== 'undefined') mat.color.setHex(typeof isListening !== 'undefined' && isListening ? 0x22c55e : 0x38bdf8);
            }
        }"""

if "function toggleRadialHub()" in html:
    # Si la función existe, la actualizamos con la lógica forzada
    import re

    html = re.sub(r"function toggleRadialHub\(\)\s*\{[\s\S]*?\}", new_func, html)
    with open("/data/data/com.termux/files/home/daniela-os/index.html", "w") as f:
        f.write(html)
    print("Reparación del botón + aplicada con éxito.")
else:
    print("No se encontró la función exacta, verifica el archivo.")
