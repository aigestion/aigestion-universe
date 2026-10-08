import urllib.request

try:
    with urllib.request.urlopen("http://localhost:5000/") as response:
        print(f"✅ SERVIDOR VIVO: Código {response.status}")
except Exception as e:
    print(f"❌ SERVIDOR MUERTO O NO RESPONDE: {e}")
