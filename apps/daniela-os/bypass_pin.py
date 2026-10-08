import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    # Inyectar CSS que oculta cualquier ventana de login/pin automáticamente
    css_bypass = """
    <style>
        /* Desactivar capas de login/pin */
        #login-modal, .login-overlay, .modal, .auth-screen, .pin-pad {
            display: none !important;
        }
    </style>
    """

    if "display: none !important" not in html:
        html = html.replace("</head>", css_bypass + "\n</head>")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ PIN deshabilitado. Acceso directo restaurado.")
    else:
        print("ℹ️ El bypass ya estaba aplicado.")
