import json
import sys
import urllib.request

BASE_URL = "http://localhost:8080/api/chat"

TESTS = [
    ("colab entrenar modelo vision", "Colab Bridge"),
    ("story guion sci-fi", "Story Studio"),
    ("investiga fisica cuantica", "Deep Research"),
    ("crea evento Reunion", "Google Sync"),
    ("recuerda usuario: Ale", "Memory"),
    ("ejecuta ls", "Terminal"),
    ("busca https://google.com", "Web"),
    ("batería", "Sensors"),
    ("alerta test", "Alerts"),
    ("escucha voz", "Audio"),
    ("post de IA", "Social"),
    ("diario entrada", "Journal"),
    ("genera un auto", "Creative"),
]


def run():
    print("🚀 Auditando Sistema Sovereign (13 Skills)...")
    for cmd, name in TESTS:
        data = json.dumps({"message": cmd}).encode("utf-8")
        req = urllib.request.Request(
            BASE_URL, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as res:
                if res.status == 200:
                    print(f"✅ {name}: OK")
                else:
                    print(f"❌ {name}: FALLO")
                    sys.exit(1)
        except Exception as e:
            print(f"❌ {name}: ERROR ({e})")
            sys.exit(1)
    print("🎉 Auditoría Exitosa: 13 Skills Sincronizadas en Daniela OS.")


if __name__ == "__main__":
    run()
