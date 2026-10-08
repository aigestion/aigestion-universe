import json
import unittest
import urllib.request

BASE_URL = "http://localhost:8080/api/chat"


class TestDanielaOSFull(unittest.TestCase):
    def send_cmd(self, msg):
        data = json.dumps({"message": msg}).encode("utf-8")
        req = urllib.request.Request(
            BASE_URL, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            return res.status

    def test_01_creative(self):
        self.assertEqual(self.send_cmd("genera un gato"), 200)

    def test_02_video(self):
        self.assertEqual(self.send_cmd("anima un bosque"), 200)

    def test_03_journal(self):
        self.assertEqual(self.send_cmd("diario evento"), 200)

    def test_04_social(self):
        self.assertEqual(self.send_cmd("crea un post de ai"), 200)

    def test_05_audio(self):
        self.assertEqual(self.send_cmd("escucha voz"), 200)

    def test_06_alerts(self):
        self.assertEqual(self.send_cmd("alerta prueba"), 200)

    def test_07_sensors(self):
        self.assertEqual(self.send_cmd("batería"), 200)

    def test_08_web(self):
        self.assertEqual(self.send_cmd("busca en https://example.com"), 200)

    def test_09_terminal(self):
        self.assertEqual(self.send_cmd("ejecuta ls"), 200)

    def test_10_memory(self):
        self.assertEqual(self.send_cmd("recuerda usuario: Ale"), 200)


if __name__ == "__main__":
    unittest.main()
