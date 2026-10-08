with open("server.py") as f:
    code = f.read()

branding_routes = '''
@app.route('/api/branding', methods=['GET', 'POST'])
def handle_branding():
    user_id = request.args.get('user_id', 1)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.json or {}
        universe_name = data.get('universe_name', 'DANIELA OS')
        primary_color = data.get('primary_color', '#00f0ff')
        secondary_color = data.get('secondary_color', '#e024c3')
        avatar_url = data.get('avatar_image_url', '')
        logo_url = data.get('logo_url', '')
        prompt_override = data.get('system_prompt_override', '')

        cursor.execute("""
            INSERT INTO universe_branding (user_id, universe_name, avatar_image_url, logo_url, primary_color, secondary_color, system_prompt_override)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                universe_name=excluded.universe_name,
                primary_color=excluded.primary_color,
                secondary_color=excluded.secondary_color,
                avatar_image_url=excluded.avatar_image_url,
                logo_url=excluded.logo_url,
                system_prompt_override=excluded.system_prompt_override
        """, (user_id, universe_name, avatar_url, logo_url, primary_color, secondary_color, prompt_override))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Branding actualizado correctamente"})

    cursor.execute("SELECT universe_name, avatar_image_url, logo_url, primary_color, secondary_color, system_prompt_override FROM universe_branding WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "universe_name": row[0],
            "avatar_image_url": row[1],
            "logo_url": row[2],
            "primary_color": row[3],
            "secondary_color": row[4],
            "system_prompt_override": row[5]
        })
    return jsonify({
        "universe_name": "DANIELA OS",
        "avatar_image_url": "",
        "logo_url": "",
        "primary_color": "#00f0ff",
        "secondary_color": "#e024c3",
        "system_prompt_override": ""
    })
'''

if "/api/branding" not in code:
    code = code.replace(
        "if __name__ == '__main__':", branding_routes + "\nif __name__ == '__main__':"
    )
    with open("server.py", "w") as f:
        f.write(code)
    print("Endpoints de Branding inyectados con éxito en server.py")
else:
    print("Los endpoints de Branding ya existen en server.py")
