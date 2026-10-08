import time
import unittest

import requests

URL = "http://127.0.0.1:8080/api/chat"


class TestDanielaOSMemorySuite(unittest.TestCase):
    def test_retencion_de_contexto_y_memoria(self):
        print("\n--- 🧠 Auditando Memoria y Contexto Conversacional ---")

        # 1. Inyección de Contexto
        payload_1 = {
            "prompt": "Daniela, guarda este dato en memoria: el código de acceso prioritario para la reunión de hoy es 'AIGESTION-DELTA-9'."
        }
        print("1️⃣ Enviando dato clave al sistema...")
        r1 = requests.post(URL, json=payload_1, timeout=10)
        self.assertEqual(r1.status_code, 200, f"Error en endpoint: HTTP {r1.status_code}")

        time.sleep(1)  # Pausa breve para simular interacción humana

        # 2. Verificación de Retención
        payload_2 = {
            "prompt": "¿Cuál es el código de acceso prioritario que te acabo de dar para la reunión de hoy?"
        }
        print("2️⃣ Solicitando recuperar la información desde la memoria...")
        start_time = time.time()
        r2 = requests.post(URL, json=payload_2, timeout=10)
        latencia = time.time() - start_time

        self.assertEqual(r2.status_code, 200)

        data = r2.json()
        respuesta = data.get("response", "") or data.get("reply", "") or str(data)

        print(f'💬 Respuesta recibida ({latencia:.2f}s):\n"{respuesta.strip()}"\n')

        # Validar si contiene la clave del contexto
        contiene_clave = "AIGESTION-DELTA-9" in respuesta or "delta-9" in respuesta.lower()

        if contiene_clave:
            print("✅ [QA Memoria]: RETENCIÓN PERFECTA. Daniela recordó la clave exacta.")
        else:
            print("⚠️ [QA Memoria]: El modelo respondió pero no retuvo el token de memoria corto.")

        self.assertTrue(
            contiene_clave, "❌ Fallo de Memoria: Daniela no retuvo la información entre turnos."
        )


if __name__ == "__main__":
    unittest.main()
