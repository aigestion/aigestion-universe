"""Modelo de hallazgo de auditoría."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

SEVERIDADES = ("critica", "alta", "media", "baja", "info")

ORDEN = {"critica": 0, "alta": 1, "media": 2, "baja": 3, "info": 4}


@dataclass
class Finding:
    """Un hallazgo: qué, dónde, evidencia y cómo arreglarlo."""

    id: str  # p. ej. "bind-0.0.0.0-9200"
    titulo: str
    severidad: str  # una de SEVERIDADES
    donde: str  # host:puerto, fichero:linea, url...
    evidencia: str = ""
    remedio: str = ""
    auditor: str = ""
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.severidad not in SEVERIDADES:
            raise ValueError(f"severidad inválida: {self.severidad}")


def to_dict(f: Finding) -> dict:
    return asdict(f)


def counts(hallazgos: list[Finding]) -> dict:
    n = dict.fromkeys(SEVERIDADES, 0)
    for h in hallazgos:
        n[h.severidad] += 1
    return n


def ordenar(hallazgos: list[Finding]) -> list[Finding]:
    return sorted(hallazgos, key=lambda h: (ORDEN[h.severidad], h.id))
