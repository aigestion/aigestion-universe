import json
import urllib.request


def run_background_triage():
    url = "http://localhost:8085/api/chat"
    data = json.dumps({"message": "escanea correo"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            print("🕒 [CRON TRIAGE]:", json.loads(response.read().decode("utf-8"))["response"])
    except Exception as e:
        print("⚠️ Error en Cron Triage:", e)


if __name__ == "__main__":
    run_background_triage()
