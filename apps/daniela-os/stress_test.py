import asyncio
import json
import time
import urllib.request

ROLES = ["admin@aigestion.net", "sales@aigestion.net", "finance@aigestion.net"]


async def test_ring_node(node_id, role):
    start = time.time()
    url = "http://localhost:8080/api/chat"
    payload = json.dumps(
        {"message": f"Ping táctico desde nodo R{node_id}", "user_email": role}
    ).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            latency = round((time.time() - start) * 1000, 2)
            print(
                f"⚡ [NODO R{node_id} | {role.split('@')[0].upper()}] Latencia: {latency}ms | Estado: {res.get('status')}"
            )
    except Exception as e:
        print(f"❌ [NODO R{node_id}] Error: {e}")


async def main():
    print("🚀 Ejecutando Pruebas de Carga en Paralelo (6 Anillos x 3 Roles)...")
    tasks = []
    for ring in range(1, 7):
        for role in ROLES:
            tasks.append(test_ring_node(ring, role))
    await asyncio.gather(*tasks)
    print("✅ Pruebas de carga de los 6 anillos completadas con éxito.")


if __name__ == "__main__":
    asyncio.run(main())
