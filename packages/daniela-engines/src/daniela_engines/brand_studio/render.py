"""Render plan + real ffmpeg execution (lavfi color cards).

Honest placeholder visuals: each scene becomes a solid-color card with
its REAL duration; concat yields a watchable timing preview. No fake
"success": without ffmpeg binary -> explicit 503 with how_to_fix.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

PALETTE = ["0x0a1428", "0x132a13", "0x2b1a08", "0x1a0a2b", "0x081a1a"]


def ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def plan(board: dict[str, Any]) -> dict[str, Any]:
    segmentos = []
    for esc in board["escenas"]:
        color = PALETTE[(esc["numero_escena"] - 1) % len(PALETTE)]
        segmentos.append(
            f"color=c={color}:s=1280x720:r=30:d={esc['duracion_seg']} "
            f"[v{esc['numero_escena']}]"
        )
    filtros = ";".join(segmentos)
    filtros += "".join(f"[v{e['numero_escena']}]" for e in board["escenas"])
    filtros += f"concat=n={len(board['escenas'])}:v=1:a=0[v]"
    return {
        "num_escenas": board["num_escenas"],
        "duracion_total_seg": board["duracion_total_seg"],
        "resolucion": "1280x720@30",
        "visuals": "placeholder (tarjetas de color por escena)",
        "filtro_concat": filtros,
    }


def ejecutar(board: dict[str, Any], destino: str | None = None) -> dict[str, Any]:
    exe = ffmpeg()
    if not exe:
        return {"ok": False, "error": "ffmpeg no disponible",
                "how_to_fix": "instala ffmpeg y reintenta (apt install ffmpeg)"}
    salida = destino or str(Path(tempfile.gettempdir()) / "brand_preview.mp4")
    cmd = [exe, "-y"]
    for esc in board["escenas"]:
        color = PALETTE[(esc["numero_escena"] - 1) % len(PALETTE)]
        cmd += ["-f", "lavfi", "-i",
                f"color=c={color}:s=1280x720:r=30:d={esc['duracion_seg']}"]
    cmd += ["-filter_complex",
            "".join(f"[{i}:v]" for i in range(len(board["escenas"])))
            + f"concat=n={len(board['escenas'])}:v=1:a=0[v]",
            "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", salida]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr[-500:]}
    return {"ok": True, "salida": salida,
            "bytes": Path(salida).stat().st_size,
            "duracion_total_seg": board["duracion_total_seg"]}
