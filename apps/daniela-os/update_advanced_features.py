with open("server.py") as f:
    code = f.read()

advanced_routes = '''
# --- WEAKHOOK ONBOARDING WHATSAPP ---
@app.route('/api/whatsapp_onboarding', methods=['POST'])
def whatsapp_onboarding():
    data = request.json or {}
    phone = data.get('phone', '')
    name = data.get('name', 'Usuario B2B')

    if not phone:
        return jsonify({"status": "error", "message": "Teléfono requerido"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Crear usuario si no existe
    cursor.execute("SELECT id, credits_balance FROM users WHERE email = ?", (f"{phone}@whatsapp.com",))
    row = cursor.fetchone()

    if not row:
        cursor.execute("""
            INSERT INTO users (email, full_name, company_name, role, terms_accepted, credits_balance)
            VALUES (?, ?, 'WhatsApp Business', 'TRIAL_USER', 1, 200)
        """, (f"{phone}@whatsapp.com", name))
        user_id = cursor.lastrowid
        conn.commit()
        balance = 200
    else:
        user_id = row[0]
        balance = row[1]

    conn.close()

    return jsonify({
        "status": "success",
        "user_id": user_id,
        "aig_balance": balance,
        "deep_link": f"/index.html?user={user_id}"
    })

# --- PASARELA DE VERIFICACIÓN LIGHTNING / SATS ---
@app.route('/api/verify_lightning_payment', methods=['POST'])
def verify_lightning_payment():
    data = request.json or {}
    user_id = data.get('user_id', 1)
    invoice_hash = data.get('payment_hash', '')

    # Simulación de verificación con nodo LNBits / BTCPay
    # En producción conecta con la API de tu nodo LN
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recarga de 500 AIG por pago verificado
    cursor.execute("UPDATE users SET credits_balance = credits_balance + 500 WHERE id = ?", (user_id,))
    cursor.execute("INSERT INTO credit_transactions (user_id, amount, concept) VALUES (?, 500, 'Recarga Bitcoin Lightning')", (user_id,))

    cursor.execute("SELECT credits_balance FROM users WHERE id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Pago Lightning verificado. 500 AIG acreditados.",
        "new_balance": new_balance
    })
'''

if "/api/whatsapp_onboarding" not in code:
    code = code.replace(
        "if __name__ == '__main__':", advanced_routes + "\nif __name__ == '__main__':"
    )

with open("server.py", "w") as f:
    f.write(code)

print("Módulos de Onboarding WhatsApp y Pasarela Lightning inyectados con éxito.")
