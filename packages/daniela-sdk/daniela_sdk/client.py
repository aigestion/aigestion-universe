"""HTTP client for the Daniela Core API."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx

from .models import BrainStats, EngineInfo, MemoryItem, ProcessResult


class DanielaClient:
    """Synchronous client for Daniela Core (port 9200)."""

    def __init__(
        self,
        base_url: str = "http://localhost:9200",
        *,
        timeout: float = 30.0,
        api_key: Optional[str] = None,
    ) -> None:
        headers: Dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DanielaClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # --- Brain ---
    def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> ProcessResult:
        r = self._client.post(
            "/api/v1/brain/process",
            json={"input": input_text, "context": context or {}},
        )
        r.raise_for_status()
        return ProcessResult(**r.json())

    def brain_stats(self) -> BrainStats:
        r = self._client.get("/api/v1/brain/stats")
        r.raise_for_status()
        return BrainStats(**r.json())

    # --- Memory ---
    def memory_store(self, tier: str, content: str, importance: float = 0.5) -> Dict[str, Any]:
        r = self._client.post(
            "/api/v1/memory/store",
            json={"tier": tier, "content": content, "importance": importance},
        )
        r.raise_for_status()
        return r.json()

    def memory_recall(self, query: str, limit: int = 10) -> List[MemoryItem]:
        r = self._client.post(
            "/api/v1/memory/recall",
            json={"query": query, "limit": limit},
        )
        r.raise_for_status()
        data = r.json()
        return [MemoryItem(**m) for m in data.get("memories", [])]

    def memory_stats(self) -> Dict[str, int]:
        r = self._client.get("/api/v1/memory/stats")
        r.raise_for_status()
        return r.json()

    # --- Orchestrator ---
    def delegate(self, description: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = self._client.post(
            "/api/v1/orchestrator/delegate",
            json={"description": description, "payload": payload or {}},
        )
        r.raise_for_status()
        return r.json()

    def engines(self) -> List[EngineInfo]:
        r = self._client.get("/api/v1/orchestrator/engines")
        r.raise_for_status()
        data = r.json()
        return [EngineInfo(**e) for e in data.get("engines", [])]

    # --- Persona ---
    def greet(self) -> str:
        r = self._client.get("/api/v1/persona/greet")
        r.raise_for_status()
        return r.json()["greeting"]

    def rename(self, name: str) -> Dict[str, Any]:
        r = self._client.post("/api/v1/persona/rename", json={"name": name})
        r.raise_for_status()
        return r.json()

    # --- Health ---
    def health(self) -> Dict[str, Any]:
        r = self._client.get("/health")
        r.raise_for_status()
        return r.json()
