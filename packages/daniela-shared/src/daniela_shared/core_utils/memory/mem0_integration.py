"""
mem0 Integration for Daniela OS - Long-term Agent Memory
Replaces/augments existing memory system with mem0's semantic, episodic, procedural memory.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from mem0 import Memory


@dataclass
class MemoryConfig:
    """Configuration for mem0 memory backend."""
    provider: str = "qdrant"
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "daniela_memory"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "gpt-4o-mini"
    api_key: str | None = None


class DanielaMemory:
    """
    Wrapper around mem0 Memory for Daniela OS.
    Provides semantic, episodic, and procedural memory with automatic extraction.
    """

    def __init__(self, config: MemoryConfig | None = None):
        self.config = config or MemoryConfig()
        self._memory: Memory | None = None
        self._client: Memory | None = None
        self._init_memory()

    def _init_memory(self) -> None:
        """Initialize mem0 memory client."""
        config_dict = {
            "vector_store": {
                "provider": self.config.provider,
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "collection_name": self.config.collection_name,
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": self.config.embedding_model,
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": self.config.llm_model,
                    "api_key": self.config.api_key or os.getenv("OPENAI_API_KEY"),
                }
            },
            "version": "v1.1"
        }

        try:
            self._memory = Memory.from_config(config_dict)
            self._client = self._memory
        except Exception as e:
            print(f"[mem0] Failed to initialize: {e}")
            self._memory = None

    def add(self, user_id: str, messages: list[dict[str, str]], metadata: dict | None = None) -> dict:
        """
        Add conversation to memory with automatic fact extraction.

        Args:
            user_id: Unique identifier for the user/agent
            messages: List of messages with role and content
            metadata: Additional metadata (session_id, agent_id, etc.)

        Returns:
            Result with extracted memories
        """
        if not self._memory:
            return {"error": "Memory not initialized"}

        try:
            result = self._memory.add(
                messages=messages,
                user_id=user_id,
                metadata=metadata or {}
            )
            return result
        except Exception as e:
            return {"error": str(e)}

    def search(self, user_id: str, query: str, limit: int = 10) -> list[dict]:
        """
        Search relevant memories for a query.

        Args:
            user_id: User/agent identifier
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant memories
        """
        if not self._memory:
            return []

        try:
            results = self._memory.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            return results.get("results", [])
        except Exception as e:
            print(f"[mem0] Search error: {e}")
            return []

    def get_all(self, user_id: str) -> list[dict]:
        """Get all memories for a user."""
        if not self._memory:
            return []
        try:
            return self._memory.get_all(user_id=user_id)
        except Exception as e:
            print(f"[mem0] Get all error: {e}")
            return []

    def delete(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        if not self._memory:
            return False
        try:
            self._memory.delete(memory_id=memory_id)
            return True
        except Exception as e:
            print(f"[mem0] Delete error: {e}")
            return False

    def update_memory(self, user_id: str, memory_id: str, data: dict) -> bool:
        """Update a memory entry."""
        if not self._memory:
            return False
        try:
            self._memory.update(memory_id=memory_id, data=data)
            return True
        except Exception as e:
            print(f"[mem0] Update error: {e}")
            return False


class AgentMemoryManager:
    """
    High-level memory manager for multi-agent system.
    Handles memory isolation per agent and cross-agent memory sharing.
    """

    def __init__(self, base_config: MemoryConfig | None = None):
        self.base_config = base_config or MemoryConfig()
        self.agent_memories: dict[str, DanielaMemory] = {}

    def get_agent_memory(self, agent_id: str) -> DanielaMemory:
        """Get or create memory instance for an agent."""
        if agent_id not in self.agent_memories:
            config = MemoryConfig(
                collection_name=f"daniela_memory_{agent_id}",
                host=self.base_config.host,
                port=self.base_config.port,
            )
            self.agent_memories[agent_id] = DanielaMemory(config)
        return self.agent_memories[agent_id]

    def add_interaction(self, agent_id: str, user_id: str, messages: list[dict], metadata: dict | None = None) -> dict:
        """Add interaction to agent's memory."""
        memory = self.get_agent_memory(agent_id)
        meta = metadata or {}
        meta.update({"agent_id": agent_id, "timestamp": datetime.utcnow().isoformat()})
        return memory.add(user_id=user_id, messages=messages, metadata=meta)

    def search_agent_memory(self, agent_id: str, user_id: str, query: str, limit: int = 10) -> list[dict]:
        """Search agent's memory."""
        memory = self.get_agent_memory(agent_id)
        return memory.search(user_id=user_id, query=query, limit=limit)

    def get_shared_context(self, query: str, agent_ids: list[str], limit: int = 5) -> dict[str, list[dict]]:
        """Get relevant memories from multiple agents for shared context."""
        results = {}
        for agent_id in agent_ids:
            memory = self.get_agent_memory(agent_id)
            # Use a shared user_id for cross-agent context
            results[agent_id] = memory.search(user_id="shared_context", query=query, limit=limit)
        return results


# Global instance for easy access
_default_manager: AgentMemoryManager | None = None


def get_memory_manager() -> AgentMemoryManager:
    """Get global memory manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = AgentMemoryManager()
    return _default_manager


# Convenience functions
def add_memory(agent_id: str, user_id: str, messages: list[dict], metadata: dict | None = None) -> dict:
    """Add memory using global manager."""
    return get_memory_manager().add_interaction(agent_id, user_id, messages, metadata)


def search_memory(agent_id: str, user_id: str, query: str, limit: int = 10) -> list[dict]:
    """Search memory using global manager."""
    return get_memory_manager().search_agent_memory(agent_id, user_id, query, limit)


def get_shared_context(query: str, agent_ids: list[str], limit: int = 5) -> dict[str, list[dict]]:
    """Get shared context across agents."""
    return get_memory_manager().get_shared_context(query, agent_ids, limit)
