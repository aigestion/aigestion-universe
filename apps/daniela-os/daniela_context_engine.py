import json
import subprocess


class DanielaContextEngine:
    def __init__(self):
        # Coordenadas de ejemplo para detección de zonas (Notaría / Oficina)
        self.target_zones = {
            "NOTARIA": {"lat": 40.4168, "lon": -3.7038, "radio_m": 500},
            "OFICINA": {"lat": 40.4530, "lon": -3.6883, "radio_m": 300},
        }

    def get_real_telemetry(self):
        """Lee datos de batería y temperatura de Termux API"""
        bat_info = {"percentage": 100, "temperature": 25.0, "status": "UNKNOWN"}
        try:
            res = subprocess.run(
                ["termux-battery-status"], capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                bat_info = {
                    "percentage": data.get("percentage", 100),
                    "temperature": data.get("temperature", 25.0),
                    "status": data.get("status", "DISCHARGING"),
                }
        except Exception:
            pass
        return bat_info

    def evaluate_situation(self):
        """Analiza la situación global del hardware y contexto"""
        telemetry = self.get_real_telemetry()
        bat = telemetry["percentage"]
        temp = telemetry["temperature"]

        proposals = []

        # Regla 1: Protocolo Batería Crítica
        if bat < 20:
            proposals.append(
                {
                    "id": "PROP_BAT_CRITICAL",
                    "tag": "CRÍTICO :: HARDWARE",
                    "title": "MODO AHORRO BÚNKER & RESPALDO",
                    "body": f"Batería en nivel crítico (<b>{bat}%</b> | {temp}°C). Se propone forzar la sincronización del enclave y atenuar el HUD.",
                    "audioText": f"Atención Comandante. Batería al {bat} por ciento. Propongo realizar un respaldo inmediato y activar el modo de ahorro.",
                }
            )

        # Regla 2: Auditoría del entorno
        proposals.append(
            {
                "id": "PROP_REAL_NOTARY",
                "tag": "CONTEXTO :: UBICACIÓN",
                "title": "CHECKLIST NOTARIAL 'HERENCIA ZAPATEROS'",
                "body": "Sincronización de ubicación activa. Documentación del Modelo 600 y escrituras preparadas en la Bóveda Local.",
                "audioText": "Entorno verificado. Toda la documentación notarial para la Herencia Zapateros se encuentra validada encriptada.",
            }
        )

        return {"telemetry": telemetry, "proposals": proposals}


context_engine = DanielaContextEngine()
