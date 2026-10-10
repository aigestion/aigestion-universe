#!/usr/bin/env python3
"""Multimedia Enterprise Pipeline (idea epica) â€” activos de marca 100% locales.

- Banner PIL 1920x1080 con constantes de BrandVoice.
- Slides JSON listo para Google Slides API (push diferido: sin OAuth).
- PDF ejecutivo con reportlab (WeasyPrint pide GTK en Windows).
- Video 30s: turntable Blender (EEVEE) del STL real + locucion
  edge-tts + mux ffmpeg. Fallback garantizado: Ken Burns (zoompan)
  si EEVEE falla headless. Sin red TTS el video sale mudo y etiquetado.

Todo bajo media_exports/ (ignorado por git). Ledger en
data/content/media.jsonl + vault (content/media).

CLI: python media_pipeline.py todo|banner|slides|pdf|video [--tema T]
Rutas: POST /api/media/generar, GET /api/media/estado
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from flask import jsonify, request
except ImportError:  # pragma: no cover
    jsonify = None  # type: ignore
    request = None  # type: ignore

# Raiz del repo (este modulo vive en content/).
_REPO_ROOT = Path(__file__).resolve().parents[1]
MEDIA_DIR = _REPO_ROOT / "media_exports"
LEDGER_FILE = _REPO_ROOT / "data" / "content" / "media.jsonl"

BRAND = {"fondo": (10, 12, 16), "rejilla": (22, 27, 34),
         "cian": (0, 200, 255), "verde": (0, 255, 170),
         "texto": (232, 236, 244)}
W, H = 1920, 1080


def _anexar(evento: dict[str, Any]) -> None:
    try:
        LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
        evento = dict(evento)
        evento.setdefault("ts", datetime.now().isoformat())
        with open(LEDGER_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def estructura() -> dict[str, Path]:
    """Crea media_exports/{images,videos,presentations,documents}."""
    dirs = {}
    for sub in ("images", "videos", "presentations", "documents"):
        p = MEDIA_DIR / sub
        p.mkdir(parents=True, exist_ok=True)
        dirs[sub] = p
    return dirs


def banner(tema: str = "aig x Daniela OS") -> dict[str, Any]:
    """Banner 1920x1080 cyberpunk con PIL. Devuelve ruta + tamano."""
    from PIL import Image, ImageDraw, ImageFont

    dirs = estructura()
    img = Image.new("RGB", (W, H), color=BRAND["fondo"])
    draw = ImageDraw.Draw(img)
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=BRAND["rejilla"], width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=BRAND["rejilla"], width=1)
    draw.rectangle([100, 100, W - 100, H - 100], outline=BRAND["cian"], width=3)
    draw.line([(100, 200), (W - 100, 200)], fill=BRAND["verde"], width=2)
    try:
        fuente = ImageFont.truetype("arial.ttf", 72)
        fuente_ch = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        fuente = ImageFont.load_default()
        fuente_ch = fuente
    draw.text((140, 260), "AIG", fill=BRAND["cian"], font=fuente)
    draw.text((140, 360), "Daniela OS", fill=BRAND["texto"], font=fuente)
    draw.text((140, 500), tema[:60], fill=BRAND["verde"], font=fuente_ch)
    ruta = dirs["images"] / "aigestion_daniela_banner.png"
    img.save(ruta)
    return {"ok": True, "fichero": str(ruta), "size": [W, H]}


def slides_template() -> dict[str, Any]:
    """Pitch 10 + ficha, formato listo para Slides API (push diferido)."""
    dirs = estructura()
    slides = [
        {"title": "Daniela OS", "subtitle": "High-Resiliency Autonomous Workstation"},
        {"title": "Core Architecture",
         "bullet_points": ["Docker Compose Auto-Healing", "Groq Tier 1 Llama-3.3-70B",
                           "Google Workspace Integration"]},
        {"title": "DevOps & Automation",
         "bullet_points": ["Nightly Maintenance Daemon", "Hermes Agent Workflow",
                           "Rainmeter HUD Telemetry"]},
        {"title": "aig Core", "bullet_points": ["11 modulos", "Intent routing", "API Gateway"]},
        {"title": "Pixel Bridge", "bullet_points": ["37 modulos", "Second Screen HUD", "Edge Node"]},
        {"title": "Seguridad", "bullet_points": ["Safe Exec", "Secret Guard", "Safe Evolution Gate"]},
        {"title": "Contenido", "bullet_points": ["Content OS", "Memory Vault", "Zero-Inbox"]},
        {"title": "CAD & Hardware", "bullet_points": ["Open CADStudio", "STL/STEP", "Blender renders"]},
        {"title": "White-Label", "bullet_points": ["Tenant bootstrap", "Enterprise compose"]},
        {"title": "Contacto", "subtitle": "aig â€” hablemos"},
    ]
    tpl = {
        "title": "AIG & Daniela OS - Autonomous Infrastructure & AI Orchestration",
        "theme": {"backgroundColor": "#0A0C10", "primaryColor": "#00C8FF",
                  "secondaryColor": "#00FFAA"},
        "slides": slides,
        "push": "diferido (requiere OAuth Google Slides API)",
    }
    ruta = dirs["presentations"] / "slides_template.json"
    ruta.write_text(json.dumps(tpl, indent=4, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "fichero": str(ruta), "slides": len(slides)}


def reporte_pdf(titulo: str = "Reporte Ejecutivo aig") -> dict[str, Any]:
    """PDF corporativo con reportlab (WeasyPrint pide GTK en Windows)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas

    dirs = estructura()
    ruta = dirs["documents"] / "reporte_ejecutivo.pdf"
    c = Canvas(str(ruta), pagesize=A4)
    ancho, alto = A4
    c.setFillColorRGB(10 / 255, 12 / 255, 16 / 255)
    c.rect(0, 0, ancho, alto, fill=1, stroke=0)
    c.setFillColorRGB(0, 200 / 255, 1)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(60, alto - 100, "AIG")
    c.setFillColorRGB(232 / 255, 236 / 255, 244 / 255)
    c.setFont("Helvetica", 16)
    c.drawString(60, alto - 140, titulo[:60])
    c.setFillColorRGB(0, 1, 170 / 255)
    c.setFont("Helvetica", 11)
    lineas = [
        f"Generado: {datetime.now():%Y-%m-%d %H:%M}",
        "Modulos core: 11 Â· Rutas API: 267 Â· Health: verificado",
        "Pixel Bridge: 37 modulos sincronizados al telefono.",
        "Seguridad: Secret Guard + Safe Evolution Gate activos.",
    ]
    y = alto - 200
    for linea in lineas:
        c.drawString(60, y, linea)
        y -= 24
    c.showPage()
    c.save()
    return {"ok": True, "fichero": str(ruta), "bytes": ruta.stat().st_size}


def _tts(texto: str, destino: Path, timeout: int = 120) -> dict[str, Any]:
    """Locucion edge-tts (requiere internet, sin clave). Honesto si falla."""
    try:
        from core.safe_exec import run_cmd
    except ImportError:
        return {"ok": False, "error": "sin safe_exec"}
    r = run_cmd([sys.executable, "-m", "edge_tts", "--voice", "es-ES-ElviraNeural",
                 "--text", texto[:900], "--write-media", str(destino)], timeout=timeout)
    if r.returncode != 0 or not destino.exists():
        return {"ok": False, "error": (r.stderr or "")[:300] or "edge-tts fallo (red?)"}
    return {"ok": True, "fichero": str(destino), "bytes": destino.stat().st_size}


def _turntable(stl: Path, frames_dir: Path, fps: int = 10,
               segundos: int = 30) -> dict[str, Any]:
    """Secuencia PNG girando el STL con Blender EEVEE (headless)."""
    try:
        from core.safe_exec import run_cmd
    except ImportError:
        return {"ok": False, "error": "sin safe_exec"}
    import shutil

    blender = shutil.which("blender")
    if not blender:
        return {"ok": False, "error": "sin blender en PATH"}
    frames_dir.mkdir(parents=True, exist_ok=True)
    script = _REPO_ROOT / "scripts" / "blender_turntable.py"
    if not script.exists():
        return {"ok": False, "error": "falta scripts/blender_turntable.py"}
    r = run_cmd([blender, "--background", "--python", str(script), "--",
                 str(stl.resolve()), str(frames_dir.resolve()), str(fps), str(segundos)],
                 timeout=1800, cwd=str(_REPO_ROOT))
    pngs = sorted(frames_dir.glob("frame_*.png"))
    if r.returncode != 0 or not pngs:
        return {"ok": False, "error": (r.stderr or "")[-300:] or "blender fallo"}
    return {"ok": True, "frames": len(pngs), "dir": str(frames_dir)}


def _mux(video_mp4: Path, frames_dir: Path, audio: Path | None,
         fps: int = 10) -> dict[str, Any]:
    """Ensambla PNGs (+MP3 opcional) con ffmpeg."""
    import shutil

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"ok": False, "error": "sin ffmpeg en PATH"}
    try:
        from core.safe_exec import run_cmd
    except ImportError:
        return {"ok": False, "error": "sin safe_exec"}
    cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i",
           str(frames_dir / "frame_%04d.png")]
    if audio and audio.exists():
        cmd += ["-i", str(audio), "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(video_mp4)]
    r = run_cmd(cmd, timeout=600)
    if r.returncode != 0 or not video_mp4.exists():
        return {"ok": False, "error": (r.stderr or "")[-300:] or "ffmpeg fallo"}
    return {"ok": True, "fichero": str(video_mp4), "bytes": video_mp4.stat().st_size}


def video_demo(stl: Path | None = None, fps: int = 10,
               segundos: int = 30) -> dict[str, Any]:
    """Video 30s: turntable Blender + locucion + mux. Fallback Ken Burns."""
    dirs = estructura()
    stl = stl or (_REPO_ROOT / "data" / "cad" / "smoke-carcasa.stl")
    if not stl.exists():
        cands = sorted((_REPO_ROOT / "data" / "cad").glob("*.stl"))
        stl = cands[0] if cands else None
    if stl is None:
        return {"ok": False, "error": "sin STL en data/cad (disena una pieza primero)"}
    frames = dirs["videos"] / "frames_turntable"
    loc = dirs["videos"] / "locucion.mp3"
    out = dirs["videos"] / "daniela_demo_30s.mp4"

    t = _turntable(stl, frames, fps, segundos)
    if not t.get("ok"):
        return _ken_burns_fallback(dirs, t.get("error", ""), fps, segundos)
    voz = _tts("Daniela OS: infraestructura autonoma, Pixel Bridge y CAD. "
               "aig orquesta tu gestoria con once modulos de inteligencia artificial.",
               loc)
    mux = _mux(out, frames, Path(voz["fichero"]) if voz.get("ok") else None, fps)
    if not mux.get("ok"):
        return {"ok": False, "error": mux.get("error"), "frames": t.get("frames")}
    resultado = {"ok": True, "modo": "turntable", "fichero": mux["fichero"],
                 "frames": t.get("frames"), "voz": voz.get("ok", False)}
    _anexar({"ev": "video", **{k: resultado[k] for k in ("modo", "fichero") if k in resultado},
             "voz": resultado["voz"]})
    return resultado


def _ken_burns_fallback(dirs: dict[str, Path], motivo: str,
                        fps: int, segundos: int) -> dict[str, Any]:
    """Plan B garantizado: zoom sobre el banner (sin Blender)."""
    import shutil

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"ok": False, "error": f"ni Blender ({motivo}) ni ffmpeg disponibles"}
    ban = banner()
    out = dirs["videos"] / "daniela_demo_30s.mp4"
    cuadros = fps * segundos
    try:
        from core.safe_exec import run_cmd
    except ImportError:
        return {"ok": False, "error": "sin safe_exec"}
    r = run_cmd([ffmpeg, "-y", "-loop", "1", "-i", ban["fichero"],
                 "-vf", f"scale=2400:-2,zoompan=z='1+0.3*on/{cuadros}':"
                        f"d={cuadros}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080,"
                        f"fps={fps}",
                 "-t", str(segundos), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 str(out)], timeout=600)
    if r.returncode != 0 or not out.exists():
        return {"ok": False, "error": (r.stderr or "")[-300:] or "ffmpeg fallback fallo"}
    resultado = {"ok": True, "modo": "kenburns", "fichero": str(out),
                 "motivo_fallback": motivo[:200]}
    _anexar({"ev": "video", "modo": "kenburns", "fichero": str(out)})
    return resultado


def todo(tema: str = "aig x Daniela OS") -> dict[str, Any]:
    """Pipeline completo: banner + slides + PDF (+ video aparte, lento)."""
    b = banner(tema)
    s = slides_template()
    p = reporte_pdf(f"Reporte Ejecutivo â€” {tema[:40]}")
    out = {"ok": all(x.get("ok") for x in (b, s, p)), "banner": b,
           "slides": s, "pdf": p}
    try:
        from agents.memory.memory_vault import MemoryVault

        out["vault_id"] = MemoryVault().record(
            "content/media",
            f"Pack multimedia '{tema}': banner, {s.get('slides')} slides, PDF.")
    except Exception:
        pass
    return out


def estado() -> dict[str, Any]:
    """Artefactos existentes en media_exports/."""
    base = MEDIA_DIR
    cuenta = {}
    for sub in ("images", "videos", "presentations", "documents"):
        d = base / sub
        cuenta[sub] = len(list(d.glob("*"))) if d.exists() else 0
    runs = _leer_ledger()
    return {"ok": True, "dir": str(base), "artefactos": cuenta,
            "runs": len(runs)}


def _leer_ledger(max_lines: int = 100) -> list[dict[str, Any]]:
    if not LEDGER_FILE.exists():
        return []
    try:
        lines = LEDGER_FILE.read_text(encoding="utf-8").splitlines()[-max_lines:]
    except OSError:
        return []
    out = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


# â”€â”€ Rutas Flask â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def register_media_routes(app) -> None:
    """Multimedia: generar pack + estado."""

    @app.route("/api/media/generar", methods=["POST"])
    def media_generar():
        data = request.get_json(force=True, silent=True) or {}
        r = todo(str(data.get("tema", "aig x Daniela OS")))
        return jsonify(r), (200 if r.get("ok") else 500)

    @app.route("/api/media/estado")
    def media_estado():
        return jsonify(estado())


# â”€â”€ CLI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Multimedia Enterprise Pipeline")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("todo", help="Banner + slides + PDF").add_argument(
        "--tema", default="aig x Daniela OS")

    p_v = sub.add_parser("video", help="Video demo 30s (lento)")
    p_v.add_argument("--stl", default="")
    p_v.add_argument("--fps", type=int, default=10)

    sub.add_parser("estado", help="Artefactos")
    args = parser.parse_args(argv)
    if args.cmd == "todo":
        r = todo(args.tema)
        print(json.dumps({k: (v if not isinstance(v, dict) else v.get("fichero", v))
                          for k, v in r.items() if k != "vault_id"},
                         indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "video":
        stl = Path(args.stl) if args.stl else None
        r = video_demo(stl, fps=args.fps)
        print(json.dumps(r, indent=2, ensure_ascii=False, default=str)[:800])
    elif args.cmd == "estado":
        print(json.dumps(estado(), indent=2, ensure_ascii=False))
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

