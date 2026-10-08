import json
import urllib.request

BASE_URL = "http://localhost:8080"


def audit():
    print("🚀 Iniciando Auditoría Sovereign...")

    # 1. Obtener Token JWT
    req_token = urllib.request.Request(
        f"{BASE_URL}/v1/admin/token",
        data=json.dumps({"api_key": "demo-key-001"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req_token) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            token = data.get("access_token")
    except Exception as e:
        print(f"❌ Error obteniendo JWT Token: {e}")
        return

    # 2. Casos de prueba alineados con los intents de aigestion_core.py
    test_cases = [
        {
            "skill": "code_gen",
            "payload": {"skill": "code_gen", "query": "desarrollar funcion python para sumar"},
        },
        {
            "skill": "email_zero_inbox",
            "payload": {
                "skill": "email_zero_inbox",
                "query": "revisar bandeja de correo electronico",
            },
        },
        {
            "skill": "smart_invoice",
            "payload": {"skill": "smart_invoice", "query": "procesar factura de proveedor"},
        },
        {
            "skill": "meeting_intel",
            "payload": {"skill": "meeting_intel", "query": "resumir minuta de reunion"},
        },
        {
            "skill": "sentiment_dashboard",
            "payload": {
                "skill": "sentiment_dashboard",
                "query": "analisis de sentimiento de cliente",
            },
        },
        {
            "skill": "customer_support",
            "payload": {"skill": "customer_support", "query": "soporte y ticket de atencion"},
        },
        {
            "skill": "social_media",
            "payload": {"skill": "social_media", "query": "publicar post en redes sociales"},
        },
        {
            "skill": "daniela_proactive",
            "payload": {
                "skill": "daniela_proactive",
                "action": "daily_briefing",
                "query": "revisar agenda y calendario",
            },
        },
        {
            "skill": "content_factory",
            "payload": {"skill": "content_factory", "query": "redaccion de articulo y contenido"},
        },
        {
            "skill": "swarm_intel",
            "payload": {"skill": "swarm_intel", "query": "orquestacion de agentes swarm"},
        },
    ]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    all_ok = True

    for item in test_cases:
        skill = item["skill"]
        payload = json.dumps(item["payload"]).encode("utf-8")
        req = urllib.request.Request(f"{BASE_URL}/v1/ask", data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("success"):
                    print(f"✅ Skill {skill}: OK")
                else:
                    print(f"❌ Skill {skill}: FAIL")
                    all_ok = False
        except Exception as e:
            print(f"❌ Skill {skill}: ERROR ({e})")
            all_ok = False

    if all_ok:
        print("🎉 Auditoría Completa: Sistema Soberano Estable (10/10 Módulos Activos).")


if __name__ == "__main__":
    audit()
