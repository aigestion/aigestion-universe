import re

with open("server.py") as f:
    code = f.read()

# Actualización del endpoint de créditos para responder con el estándar AIG Token
aig_endpoint_code = """
@app.route('/api/credits', methods=['GET'])
def get_credits():
    user_id = request.args.get('user_id', 1)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT credits_balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    balance = row[0] if row and row[0] is not None else 200
    return jsonify({"user_id": user_id, "token": "AIG", "credits_balance": balance})

@app.route('/api/pay_bitcoin', methods=['POST'])
def pay_bitcoin():
    data = request.json or {}
    user_id = data.get('user_id', 1)
    package_aig = data.get('credits', 1000) # Ej. 1,000 AIG Tokens

    # Cálculo dinámico de SATs por AIG Token
    sats_amount = package_aig * 15
    btc_invoice = f"lnbc{sats_amount}u1p3...aig_token_ref_{user_id}"

    return jsonify({
        "status": "pending",
        "user_id": user_id,
        "aig_tokens_to_add": package_aig,
        "sats_amount": sats_amount,
        "btc_invoice": btc_invoice,
        "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={btc_invoice}"
    })
"""

if "/api/pay_bitcoin" in code:
    # Reemplazar endpoints anteriores con la nomenclatura AIG
    code = re.sub(
        r"@app\.route\(\'/api/credits\'.*?return jsonify\(.*?\n\n", "", code, flags=re.DOTALL
    )

code = code.replace(
    "if __name__ == '__main__':", aig_endpoint_code + "\nif __name__ == '__main__':"
)

with open("server.py", "w") as f:
    f.write(code)

print("Backend actualizado con la nomenclatura AIG Token.")
