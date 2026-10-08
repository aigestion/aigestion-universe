"""MCP para tools de IA."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ai_tools import deepseek_chat, gemini_chat, gemini_embed, gemini_generate


class AIMCP:
    """MCP para IA."""

    def __init__(self):
        self.tools = {
            "gemini_generate": self.gemini_generate,
            "gemini_chat": self.gemini_chat,
            "gemini_embed": self.gemini_embed,
            "deepseek_chat": self.deepseek_chat,
        }

    def gemini_generate(self, prompt: str, model: str = "gemini-2.0-flash") -> dict[str, Any]:
        """Genera contenido con Gemini."""
        return gemini_generate(prompt, model)

    def gemini_chat(self, messages: list[dict], model: str = "gemini-2.0-flash") -> dict[str, Any]:
        """Chat con Gemini."""
        return gemini_chat(messages, model)

    def gemini_embed(self, text: str) -> dict[str, Any]:
        """Genera embeddings."""
        return gemini_embed(text)

    def deepseek_chat(self, messages: list[dict]) -> dict[str, Any]:
        """Chat con DeepSeek."""
        return deepseek_chat(messages)

    def call(self, tool: str, **kwargs) -> Any:
        """Llama a un tool."""
        if tool in self.tools:
            return self.tools[tool](**kwargs)
        return {"error": f"Tool '{tool}' no encontrado"}
