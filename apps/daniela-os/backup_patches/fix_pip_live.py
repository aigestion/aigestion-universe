import os

index_file = "templates/index.html"
if not os.path.exists(index_file) and os.path.exists("index.html"):
    index_file = "index.html"

with open(index_file, encoding="utf-8") as f:
    html = f.read()

pip_script = """
<script>
let liveTimer = null;

function updatePipView(url) {
    const pipArea = document.getElementById('pipDisplayArea') || document.querySelector('.pip-window .pip-content') || document.querySelector('.pip-content');
    if (!pipArea) return;

    if (liveTimer) clearInterval(liveTimer);

    pipArea.innerHTML = `<img id="pipLiveImg" src="${url}?t=${Date.now()}" style="width:100%; height:100%; object-fit:cover; border-radius:4px;">`;

    liveTimer = setInterval(() => {
        const img = document.getElementById('pipLiveImg');
        if (img) {
            img.src = `${url}?t=${Date.now()}`;
        } else {
            clearInterval(liveTimer);
        }
    }, 200);
}

// Interceptar respuestas del chat
const nativeFetch = window.fetch;
window.fetch = async function(...args) {
    const res = await nativeFetch(...args);
    if (args[0] && args[0].includes('/api/chat')) {
        const clone = res.clone();
        try {
            const data = await clone.json();
            if (data.pip_type === 'stream' || data.pip_type === 'camera' || data.pip_type === 'photo') {
                updatePipView(data.url || '/static/cam_feed.jpg');
            }
        } catch(e){}
    }
    return res;
};
</script>
"""

if "updatePipView" not in html:
    html = html.replace("</body>", pip_script + "\n</body>")
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Visor PIP actualizado con refresco en tiempo real.")
