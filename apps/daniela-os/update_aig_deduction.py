import re

with open("server.py") as f:
    code = f.read()

# Inyección de descuento en /api/chat y /api/upload_brand_pdf
deduct_chat_code = """
@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.json or {}
    user_id = data.get('user_id', 1)
    user_message = data.get('message', '')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Comprobar balance de AIG
    cursor.execute("SELECT credits_balance FROM users WHERE id = ?", (user_id,))
    row_user = cursor.fetchone()
    balance = row_user[0] if row_user and row_user[0] is not None else 200

    if balance < 1:
        conn.close()
        return jsonify({"status": "error", "response": "❌ Saldo insuficiente de AIG Tokens. Recarga mediante Bitcoin."}), 402

    # Descontar 1 AIG
    new_balance = balance - 1
    cursor.execute("UPDATE users SET credits_balance = ? WHERE id = ?", (new_balance, user_id))
    cursor.execute("INSERT INTO credit_transactions (user_id, amount, concept) VALUES (?, -1, 'Inferencia Chat')", (user_id,))

    cursor.execute("SELECT universe_name, system_prompt_override FROM universe_branding WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    universe_name = row[0] if row and row[0] else "DANIELA OS"
    system_prompt = row[1] if row and row[1] else "Eres una IA sintética avanzada."

    response_text = f"[{universe_name}]: Consulta procesada ('{user_message}'). Directriz: {system_prompt[:80]}..."

    return jsonify({
        "status": "success",
        "universe": universe_name,
        "response": response_text,
        "aig_balance": new_balance
    })
"""

if "/api/chat" in code:
    code = re.sub(
        r"@app\.route\(\'/api/chat\'.*?return jsonify\(.*?\n\n", "", code, flags=re.DOTALL
    )

code = code.replace("if __name__ == '__main__':", deduct_chat_code + "\nif __name__ == '__main__':")

with open("server.py", "w") as f:
    f.write(code)

print("Sistema de consumo y descuento de AIG Tokens inyectado correctamente en server.py")
