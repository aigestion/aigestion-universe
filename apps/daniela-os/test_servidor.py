import json
import subprocess
import sys
import time
import unittest
import urllib.request


class TestDanielaServer(unittest.TestCase):
    BASE_URL = "http://127.0.0.1:8080"
    process = None

    @classmethod
    def setUpClass(cls):
        # Arrancar el servidor en segundo plano
        cls.process = subprocess.Popen([sys.executable, "app_daniela.py"])
        time.sleep(2)  # Dar tiempo al servidor para iniciar

    @classmethod
    def tearDownClass(cls):
        # Detener el servidor al terminar
        if cls.process:
            cls.process.terminate()
            cls.process.wait()

    def test_01_index_accesible(self):
        req = urllib.request.Request(f"{self.BASE_URL}/")
        with urllib.request.urlopen(req) as res:
            self.assertEqual(res.status, 200)

    def test_02_chat_endpoint(self):
        data = json.dumps({"message": "Hola Daniela"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.BASE_URL}/chat", data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            self.assertEqual(res.status, 200)
            res_json = json.loads(res.read().decode("utf-8"))
            self.assertTrue("reply" in res_json or "response" in res_json)

    def test_03_upload_endpoint(self):
        data = b"fake_image_bytes"
        req = urllib.request.Request(
            f"{self.BASE_URL}/upload", data=data, headers={"Content-Type": "image/jpeg"}
        )
        with urllib.request.urlopen(req) as res:
            self.assertEqual(res.status, 200)


if __name__ == "__main__":
    unittest.main()
