"""Storyboard validation, normalization and example template."""
from __future__ import annotations

from typing import Any

REQUIRED_SCENE_KEYS = ("duracion_seg", "prompt_visual", "locucion", "transicion")


def ejemplo(marca: str = "Mi Marca", estilo: str = "Cyber-Corporativo Premium") -> dict[str, Any]:
    return {
        "id_proyecto": "BRAND_EJEMPLO",
        "marca": marca,
        "estilo_visual": estilo,
        "escenas": [
            {
                "numero_escena": 1,
                "duracion_seg": 5,
                "prompt_visual": "Cinematic macro shot, glowing core, fog",
                "locucion": "Bienvenidos.",
                "transicion": "Zoom in",
            },
            {
                "numero_escena": 2,
                "duracion_seg": 5,
                "prompt_visual": "Dark server room, laser beams, crystals",
                "locucion": "Colaboracion precisa.",
                "transicion": "Pan a la derecha",
            },
        ],
    }


def validar(board: Any) -> tuple[bool, str, dict[str, Any] | None]:
    """Returns (ok, error, normalized). Never raises on bad input."""
    if not isinstance(board, dict):
        return False, "storyboard debe ser un objeto", None
    escenas = board.get("escenas")
    if not isinstance(escenas, list) or not escenas:
        return False, "escenas debe ser una lista no vacia", None
    normalizadas = []
    total = 0.0
    for i, esc in enumerate(escenas, start=1):
        if not isinstance(esc, dict):
            return False, f"escena {i} debe ser un objeto", None
        faltan = [k for k in REQUIRED_SCENE_KEYS if k not in esc]
        if faltan:
            return False, f"escena {i} sin claves: {','.join(faltan)}", None
        try:
            dur = float(esc["duracion_seg"])
        except (TypeError, ValueError):
            return False, f"escena {i}: duracion_seg no numerica", None
        if dur <= 0 or dur > 600:
            return False, f"escena {i}: duracion_seg fuera de rango (0,600]", None
        total += dur
        normalizadas.append(
            {
                "numero_escena": i,
                "duracion_seg": dur,
                "prompt_visual": str(esc["prompt_visual"]),
                "locucion": str(esc["locucion"]),
                "transicion": str(esc["transicion"]),
            }
        )
    return True, "", {
        "id_proyecto": str(board.get("id_proyecto", "BRAND_SIN_ID")),
        "marca": str(board.get("marca", "")),
        "estilo_visual": str(board.get("estilo_visual", "")),
        "escenas": normalizadas,
        "duracion_total_seg": round(total, 2),
        "num_escenas": len(normalizadas),
    }
