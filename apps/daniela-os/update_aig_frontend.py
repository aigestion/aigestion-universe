with open("index.html") as f:
    html = f.read()

# Reemplazo de etiquetas a AIG Token
html = html.replace(
    '<span>⚡ <span id="credits-count">200</span> PTS</span>',
    '<span>🪙 <span id="credits-count">200</span> AIG</span>',
)
html = html.replace("1,000 PTS = 15,000 SATS", "1,000 AIG = 15,000 SATS")
html = html.replace(
    "1,000 Créditos añadidos a tu Universo!",
    "1,000 Tokens AIG acreditados en tu billetera sintética!",
)
html = html.replace("⚡ RECARGAR CRÉDITOS VÍA BITCOIN", "⚡ COMPRAR TOKENS AIG CON BITCOIN")

with open("index.html", "w") as f:
    f.write(html)

print("Interfaz visual actualizada con la criptomoneda AIG.")
