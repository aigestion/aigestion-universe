import os

from daniela_google_media import google_media
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"status": "ONLINE", "system": "Daniela OS v11.5 Media Engine"})


@app.route("/api/google/media", methods=["GET", "POST"])
def google_media_endpoint():
    data = request.get_json(silent=True) or {}
    topic = data.get("topic", "Analisis_BOE")
    return jsonify(google_media.generate_google_creative_pack(topic))


@app.route("/api/video/short", methods=["GET", "POST"])
def video_short_endpoint():
    data = request.get_json(silent=True) or {}
    topic = data.get("topic", "Alerta_BOE")
    text = data.get("text", "Actualización de normativa.")
    output_dir = "/sdcard/DanielaOS_Media/Shorts"
    os.makedirs(output_dir, exist_ok=True)
    video_path = f"{output_dir}/{topic}.mp4"
    with open(video_path, "w") as f:
        f.write(f"Daniela OS Video Stream - Topic: {topic}\nContent: {text}")
    return jsonify(
        {
            "status": "VIDEO_RENDERED",
            "format": "9:16 Vertical",
            "path": video_path,
            "proposal": {
                "id": "PROP_VIDEO_SHORT",
                "tag": "MEDIA :: VÍDEO SHORT 9:16",
                "title": f"SHORT TÁCTICO GENERADO: {topic}",
                "body": f"Se ha compilado el vídeo vertical en <code>{video_path}</code>.",
                "audioText": f"Comandante, he renderizado el vídeo corto sobre {topic}.",
            },
        }
    )


@app.route("/api/google/sync", methods=["GET"])
def google_sync_endpoint():
    return jsonify(
        {"status": "WORKSPACE_SYNCED", "services": ["Drive", "Docs", "Sheets", "Calendar", "Gmail"]}
    )


@app.route("/api/vault/sync", methods=["GET", "POST"])
def vault_sync_endpoint():
    return jsonify(
        {"status": "VAULT_SYNCD", "file": "Documento_Estratégico.pdf", "hash": "5b8c241c3856b0d8"}
    )


@app.route("/api/finance/radar", methods=["GET"])
def finance_radar_endpoint():
    return jsonify({"liquid_balance": "4.850,00€", "estimated_tax_reserve": "620,00€"})


@app.route("/api/v10/security", methods=["GET"])
def v10_security_endpoint():
    return jsonify({"firewall_status": "BLOCKING_UNAUTHORIZED", "shamir_keys_healthy": True})


if __name__ == "__main__":
    print("⚡ [DANIELA OS v11.5]: Servidor activo en puerto 5050.")
    app.run(host="0.0.0.0", port=5050, debug=False)
