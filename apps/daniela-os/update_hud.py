with open("templates/index.html") as f:
    html = f.read()

# Inyectar CDN de Mermaid.js en el <head>
mermaid_cdn = '<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>\n<script>mermaid.initialize({startOnLoad:true, theme:"dark"});</script>'
if "mermaid" not in html:
    html = html.replace("</head>", f"{mermaid_cdn}\n</head>")

# Guardar la interfaz mejorada
with open("templates/index.html", "w") as f:
    f.write(html)

print("🟢 [HUD]: Soporte para diagramas Mermaid.js inyectado con éxito.")
