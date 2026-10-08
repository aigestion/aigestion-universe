import os

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/api/voice/process", methods=["POST"])
def process_voice():
    if "audio_file" not in request.files:
        return jsonify({"status": "error", "message": "No audio file provided"}), 400

    audio = request.files["audio_file"]
    agent_id = request.form.get("agent_id", "orchestrator")

    save_path = os.path.join("assets", "temp_user_voice.webm")
    os.makedirs("assets", exist_ok=True)
    audio.save(save_path)

    print(f"🎙️ Audio de voz recibido ({os.path.getsize(save_path)} bytes) para agente: {agent_id}")

    return jsonify(
        {
            "status": "success",
            "agent_id": agent_id,
            "execution": f"VOICE_PROCESSED [{agent_id.upper()}]: Muestra de audio WebM procesada con exito.",
            "audio_saved_at": save_path,
        }
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5059)
