"""Firebase: Controla Firebase Spark (1GB, 50K reads/día gratis)."""

import os
from typing import Any

import requests

from ..base import GoogleAgent


class FirebaseAgent(GoogleAgent):
    """Agente para Firebase (Spark plan gratuito)."""

    def __init__(self, config: dict | None = None):
        super().__init__("firebase", config)
        self.project_id = os.getenv("FIREBASE_PROJECT", "")
        self.api_key = os.getenv("FIREBASE_API_KEY", "")
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"

    def list_collections(self) -> dict[str, Any]:
        """Lista colecciones de Firestore."""
        try:
            resp = requests.get(self.base_url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_document(self, collection: str, doc_id: str) -> dict[str, Any]:
        """Obtiene un documento."""
        url = f"{self.base_url}/{collection}/{doc_id}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def create_document(self, collection: str, data: dict) -> dict[str, Any]:
        """Crea un documento."""
        url = f"{self.base_url}/{collection}"
        try:
            resp = requests.post(url, json={"fields": data}, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta verificación de estado."""
        self.start()
        try:
            collections = self.list_collections()
            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.save_metrics()
            return {"collections": collections}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
