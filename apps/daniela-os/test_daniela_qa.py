import time
import unittest

import requests

BASE_URL = "http://127.0.0.1:8080"
ENDPOINTS_PROBABLES = ["/chat", "/prompt", "/api/chat", "/api/prompt", "/send_message", "/api/send"]


class TestDanielaOSCognitiveSuite(unittest.TestCase):
    def setUp(self):
        try:
            r = requests.get(BASE_URL, timeout=2)
            self.assertEqual(r.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.fail(f"❌ Servidor Daniela OS no encontrado en {BASE_URL}.")

    def test_1_descubrir_y_auditar_endpoint(self):
        payload = {"prompt": "Hola Daniela, reporte rápido de estado."}
        endpoint_valido = None
        latencia = 0

        for ep in ENDPOINTS_PROBABLES:
            url = f"{BASE_URL}{ep}"
            try:
                start_time = time.time()
                res = requests.post(url, json=payload, timeout=8)
                if res.status_code == 200:
                    endpoint_valido = url
                    latencia = time.time() - start_time
                    break
            except Exception:
                continue

        if not endpoint_valido:
            self.fail(
                f"❌ Ninguno de los endpoints probados {ENDPOINTS_PROBABLES} respondió HTTP 200. Revisa las rutas en daniela_os.py."
            )

        print(f"\n✅ [QA Endpoint Detectado]: {endpoint_valido}")
        print(f"✅ [QA Latencia]: Respuesta en {latencia:.2f}s")


if __name__ == "__main__":
    unittest.main()
