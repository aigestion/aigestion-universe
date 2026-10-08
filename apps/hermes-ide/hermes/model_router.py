import json
import os
from dataclasses import dataclass
from enum import Enum

import aiohttp


class Provider(Enum):
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    HUGGINGFACE = "huggingface"

@dataclass
class ModelSpec:
    provider: Provider
    model: str
    cost: float = 0.0
    max_tokens: int = 4096
    temperature: float = 0.7

class FreeModelRouter:
    """Routes tasks to best free model (local first, then cloud free tier)"""

    def __init__(self):
        self.ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base = "https://openrouter.ai/api/v1"
        self.routes = self._load_routes()
        self.available_local = set()
        self._refresh_local_models()

    def _load_routes(self) -> dict:
        """Load routing rules from config"""
        config_path = os.path.join(os.path.dirname(__file__), "..", ".opencode", "openrouter.json")
        try:
            with open(config_path) as f:
                config = json.load(f)
            return config.get("routing_rules", {})
        except Exception:
            return self._default_routes()

    def _default_routes(self) -> dict:
        return {
            "code_generation": {"local": "qwen2.5-coder:32b", "cloud_free": "deepseek/deepseek-chat-v3-0324:free"},
            "code_review": {"local": "qwen2.5-coder:32b", "cloud_free": "qwen/qwen-2.5-coder-32b-instruct:free"},
            "architecture": {"local": "nemotron-3-ultra", "cloud_free": "google/gemma-2-9b-it:free"},
            "debugging": {"local": "deepseek-coder:33b", "cloud_free": "deepseek/deepseek-chat-v3-0324:free"},
            "documentation": {"local": "phi3.5:14b", "cloud_free": "meta-llama/llama-3.1-8b-instruct:free"},
            "testing": {"local": "starcoder2:15b", "cloud_free": "microsoft/phi-3-medium-128k-instruct:free"},
            "refactoring": {"local": "qwen2.5-coder:32b", "cloud_free": "qwen/qwen-2.5-coder-32b-instruct:free"},
            "security_audit": {"local": "gemma2:27b", "cloud_free": "google/gemma-2-9b-it:free"},
            "planning": {"local": "nemotron-3-ultra", "cloud_free": "google/gemma-2-9b-it:free"},
            "quick_fix": {"local": "phi3.5:14b", "cloud_free": "google/gemma-2-2b-it:free"},
        }

    async def _refresh_local_models(self):
        """Refresh available local models from Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.available_local = {m["name"].split(":")[0] for m in data.get("models", [])}
        except Exception:
            pass

    async def route(self, task_type: str, context: dict = None) -> 'ModelSpec':
        """Route task to best available free model"""
        await self._refresh_local_models()

        route = self.routes.get(task_type, {})

        # Try local first
        local_model = route.get("local")
        if local_model and local_model in self.available_local:
            return ModelSpec(
                provider="ollama",
                model=local_model,
                cost=0.0
            )

        # Try cloud free
        cloud_model = route.get("cloud_free")
        if cloud_model and self.openrouter_key:
            return ModelSpec(
                provider="openrouter",
                model=cloud_model,
                cost=0.0
            )

        # Fallback chain
        fallback_local = ["qwen2.5-coder:32b", "deepseek-coder:33b", "phi3.5:14b", "gemma2:27b"]
        for model in fallback_local:
            if model in self.available_local:
                return ModelSpec(provider="ollama", model=model, cost=0.0)

        # Ultimate fallback
        return ModelSpec(
            provider="ollama",
            model="qwen2.5-coder:32b" if "qwen2.5-coder:32b" in self.available_local else "deepseek-coder:latest",
            cost=0.0
        )

    async def chat(self, messages: list[dict], task_type: str = "general", **kwargs) -> str:
        """Chat with best free model for task"""
        spec = await self.route("general", {})
        return await self._chat_with_spec(messages, spec, **kwargs)

    async def _chat_with_spec(self, messages: list[dict], spec: 'ModelSpec', **kwargs) -> str:
        if spec.provider == "ollama":
            return await self._ollama_chat(messages, spec.model, **kwargs)
        elif spec.provider == "openrouter":
            return await self._openrouter_chat(messages, spec.model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {spec.provider}")

    async def _ollama_chat(self, messages: list[dict], model: str, **kwargs) -> str:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 4096),
                }
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.ollama_base}/api/chat", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["message"]["content"]
                    else:
                        raise Exception(f"Ollama error: {resp.status}")

    async def _openrouter_chat(self, messages: list[dict], model: str, **kwargs) -> str:
        if not self.openrouter_key:
            raise Exception("OpenRouter API key not configured")

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/aig/AIG",
            "X-Title": "aig Free Model Router"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.openrouter_base}/chat/completions",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    text = await resp.text()
                    raise Exception(f"OpenRouter error: {resp.status} - {text}")

# Singleton instance
_router_instance = None

def get_router() -> FreeModelRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = FreeModelRouter()
    return _router_instance
