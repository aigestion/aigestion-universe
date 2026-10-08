"""
Persona Manager - Identity and personality for Daniela.

Daniela can be renamed and her personality tuned: empathy, creativity,
formality, humor. Coherent Level 4 is the default stability target.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Persona:
    name: str = "Daniela"
    empathy: float = 0.96
    creativity: float = 0.7
    formality: float = 0.5
    humor: float = 0.4
    coherence_level: int = 4
    greeting_style: str = "warm"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "empathy": self.empathy,
            "creativity": self.creativity,
            "formality": self.formality,
            "humor": self.humor,
            "coherence_level": self.coherence_level,
            "greeting_style": self.greeting_style,
        }


class EmptyNameError(ValueError):
    """Persona name cannot be empty."""

    def __init__(self) -> None:
        super().__init__("name cannot be empty")


class TraitRangeError(ValueError):
    """Personality trait out of range."""

    def __init__(self, attr: str) -> None:
        super().__init__(f"{attr} must be between 0 and 1")


class PersonaManager:
    """Manages Daniela's identity: rename, personality traits, greeting."""

    def __init__(self) -> None:
        self.persona = Persona()
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        pass

    async def rename(self, name: str) -> Persona:
        clean = name.strip().title()[:32]
        if not clean:
            raise EmptyNameError()
        self.persona.name = clean
        return self.persona

    async def tune(
        self,
        *,
        empathy: float | None = None,
        creativity: float | None = None,
        formality: float | None = None,
        humor: float | None = None,
    ) -> Persona:
        for attr, value in (
            ("empathy", empathy),
            ("creativity", creativity),
            ("formality", formality),
            ("humor", humor),
        ):
            if value is not None:
                if not 0.0 <= value <= 1.0:
                    raise TraitRangeError(attr)
                setattr(self.persona, attr, value)
        return self.persona

    async def greet(self) -> str:
        styles = {
            "warm": f"Hello! {self.persona.name} here — ready to help. 💙",
            "formal": f"Good day. {self.persona.name} at your service.",
            "playful": f"Hey hey! {self.persona.name} reporting for duty! ✨",
        }
        return styles.get(self.persona.greeting_style, styles["warm"])

    def as_dict(self) -> dict[str, Any]:
        return self.persona.as_dict()
