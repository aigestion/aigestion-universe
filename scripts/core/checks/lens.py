import json
import urllib.request

BASE_URL = "http://localhost:8080/api/lens"

def test():
    # Enviar payload de prueba
    data = json.dumps({"image": "data:image/jpeg;base64,/9j/4AAQSkZJRg=="}).encode('utf-8')
    req = urllib.request.Request(BASE_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            print(f"✅ Skill #11 (AR Lens): OK (Status {res.status})")
    except Exception as e:
        print(f"❌ Skill #11 (AR Lens): ERROR ({e})")

if __name__ == '__main__':
    test()
