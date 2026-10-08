import asyncio
from typing import Any

from hermes.model_router import FreeModelRouter, get_router


class FreeModelEngineCommunicator:
    """Enables 19 engines to communicate via free models"""

    ENGINE_MODEL_MAP = {
        "daniela": "ollama:nemotron-3-ultra",
        "hermes": "openrouter:google/gemma-2-9b-it:free",
        "swarm": "ollama:qwen2.5-coder:32b",
        "security": "openrouter:google/gemma-2-9b-it:free",
        "perf": "ollama:deepseek-coder:33b",
        "android": "ollama:qwen2.5-coder:32b",
        "data": "ollama:starcoder2:15b",
        "automation": "ollama:phi3.5:14b",
        "infra": "ollama:qwen2.5-coder:32b",
        "agent": "ollama:qwen2.5-coder:32b",
        "ux": "ollama:phi3.5:14b",
        "deploy": "openrouter:google/gemma-2-9b-it:free",
    }

    def __init__(self, router: FreeModelRouter | None = None):
        self.router = get_router()
        self.engine_contexts = {}

    async def cross_engine_call(self, from_engine: str, to_engine: str,
                                action: str, payload: dict) -> dict:
        """Call another engine via free model"""
        model_spec = self.ENGINE_MODEL_MAP.get(to_engine, "ollama:qwen2.5-coder:32b")
        provider, model = model_spec.split(":", 1)

        # Get engine context
        context = await self._get_engine_context(to_engine)

        # Build message
        system_prompt = f"""You are the {to_engine} engine in aig.
Context: {context}
Respond to the action with appropriate output for your engine."""


        # Route to best free model
        router = get_router()
        spec = await router.route(f"engine_{to_engine}", {"target": to_engine})

        try:
            result = await router._chat_with_spec(
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": f"Action: {action}\nPayload: {payload}"}],
                spec=spec
            )
            return {"success": True, "result": result, "engine": to_engine}
        except Exception as e:
            return {"success": False, "error": str(e), "engine": to_engine}

    async def _get_engine_context(self, engine: str) -> str:
        """Get context for target engine"""
        contexts = {
            "daniela": "Daniela AI Core: 50 Omnipresente dimensions, 12,480 memory nodes, port 9200",
            "hermes": "Hermes Gateway: 10 cognitive skills, 3 memory tiers, port 9900",
            "swarm": "Swarm Intelligence: Raft consensus, cross-engine, port 8080",
            "security": "Security Engine: audit, scan, audit, zero-cost tools",
            "perf": "Performance Engine: k6, profiling, benchmarks, port 9090",
            "android": "Android Edge: Kotlin/Compose, Pixel/Termux, offline-first",
            "data": "Data Engine: storage, query, analytics, port 5432",
            "automation": "Automation Engine: workflows, scheduling, orchestration",
            "infra": "Infrastructure: docker, k8s, networking, monitoring",
            "agent": "Agent Engine: registry, lifecycle, communication",
            "ux": "UX Engine: Compose M3, PWA, accessibility, design system",
            "deploy": "Deploy Engine: docker, health gates, rollback, zero-cost",
        }
        return contexts.get(engine, f"Engine: {engine}")

    async def broadcast(self, action: str, payload: dict,
                       target_engines: list = None) -> dict[str, Any]:
        """Broadcast action to multiple engines"""
        if target_engines is None:
            target_engines = list(self.ENGINE_MODEL_MAP.keys())

        tasks = [
            self.cross_engine_call("orchestrator", engine, action, payload)
            for engine in target_engines
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            engine: result if isinstance(result, dict) else {"error": str(result)}
            for engine, result in zip(target_engines, results)
        }

# Usage example
async def main():
    comm = FreeModelEngineCommunicator()

    # Single engine call
    result = await comm.cross_engine_call("orchestrator", "daniela",
        "process_memory", {"query": "user preferences", "limit": 10})
    print(result)

    # Broadcast to multiple engines
    results = await comm.broadcast("health_check", {},
        ["daniela", "hermes", "swarm", "security", "perf"])
    for engine, result in results.items():
        print(f"{engine}: {result}")

if __name__ == "__main__":
    asyncio.run(main())
