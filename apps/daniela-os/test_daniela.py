import sqlite3
import unittest

from server import DB_NAME, init_db, log_event


class TestDanielaOS(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_database_initialization(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs';")
        table = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table, "La tabla 'logs' debe existir en SQLite")

    def test_logging_system(self):
        test_msg = "Prueba unitaria de evento proactivo"
        log_event("TEST", "UNITTEST", test_msg)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT level, source, message FROM logs WHERE source='UNITTEST' ORDER BY id DESC LIMIT 1;"
        )
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "TEST")
        self.assertEqual(row[2], test_msg)


if __name__ == "__main__":
    unittest.main()
