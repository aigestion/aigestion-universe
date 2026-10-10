#!/usr/bin/env python3
"""Content OS (Fase 3, idea #7) â€” pipeline unico de contenido.

Factory â†’ Brand â†’ Viral â†’ Calendar â†’ Preview â†’ Publicacion:

1. **Factory** (`content_factory_ai`, local): genera por plataforma.
2. **Brand** (`BrandVoice`): verifica CTA, pega hashtags de marca.
3. **Viral**: hook (primera linea) + recorte a limites de cada red
   (los de `RedesAgent.platforms`, no inventados).
4. **Calendar**: slots `ContentSlot` con `BEST_TIMES` del calendar,
   exportados con `export_calendar_json` (su propio esquema).
5. **Preview**: HTML real en `static/content/preview_<slug>.html`.
6. **Publicacion**: `RedesAgent.multi_post` (cola real). Sin canal
   para blog/newsletter â†’ `sin_canal` honesto, nunca "publicado"
   fingido. Sin credenciales API las redes quedan en cola (el propio
   `get_analytics` lo declara: `platforms_active`).

Todo queda en `data/content/campanas.jsonl` + vault
(`content/campanas`). La video-factory (`viral_content_factory`,
pipeline de video con TTS/Veo) es otro medio: fuera de este loop.

CLI: python content_os.py "tema" [--plataformas blog,twitter] [--tono T]
Rutas: POST /api/content/campana, GET /api/content/estado
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from flask import jsonify, request
except ImportError:  # pragma: no cover
    jsonify = None  # type: ignore
    request = None  # type: ignore

# Raiz del repo (este modulo vive en content/).
_REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_FILE = _REPO_ROOT / "data" / "content" / "campanas.jsonl"
PREVIEW_DIR = _REPO_ROOT / "static" / "content"

# factory -> clave de RedesAgent (blog/newsletter no tienen canal social).
CANAL_SOCIAL = {"twitter": "twitter", "linkedin": "linkedin"}

CTA_PATRON = re.compile(
    r"(contacta|descubre|prueba|empieza|agenda|suscr[iÃ­]bete|descarga|"
    r"escribe|llama|visita|reg[iÃ­]strate|http)", re.IGNORECASE)


def _slug(texto: str) -> str:
    limpio = re.sub(r"[^\w\s-]", "", texto).strip().replace(" ", "-")[:30].lower()
    return limpio or "campana"


def _anexar(evento: dict[str, Any]) -> None:
    try:
        LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
        evento = dict(evento)
        evento.setdefault("ts", datetime.now().isoformat())
        with open(LEDGER_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _leer_ledger(max_lines: int = 200) -> list[dict[str, Any]]:
    if not LEDGER_FILE.exists():
        return []
    try:
        lines = LEDGER_FILE.read_text(encoding="utf-8").splitlines()[-max_lines:]
    except OSError:
        return []
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _paso_brand(texto: str, hashtags_marca: list[str]) -> dict[str, Any]:
    """Chequeo de voz de marca: CTA presente + hashtags pegados."""
    tiene_cta = bool(CTA_PATRON.search(texto or ""))
    return {"cta_ok": tiene_cta, "hashtags": list(hashtags_marca),
            "nota": "" if tiene_cta else "sin CTA detectado (BrandVoice.DO)"}


def _paso_viral(texto: str, limites: dict[str, Any],
                hashtags: list[str]) -> dict[str, Any]:
    """Hook + recorte a limites reales de la red + hashtags."""
    lineas = [ln.strip() for ln in (texto or "").splitlines() if ln.strip()]
    hook = lineas[0][:120] if lineas else ""
    max_desc = int(limites.get("max_description", 2000) or 2000)
    cuerpo = (texto or "")[:max_desc]
    tags = list(dict.fromkeys(hashtags))[:8]
    return {"hook": hook, "cuerpo": cuerpo, "hashtags": tags,
            "longitud": len(cuerpo)}


def campana(tema: str, plataformas: list[str] | None = None,
            tono: str = "profesional") -> dict[str, Any]:
    """Ejecuta el pipeline completo. Nunca lanza excepcion."""
    from content.brand_kit import BrandVoice
    from content.content_calendar import ContentSlot, MonthlyCalendar
    from content.content_factory_ai import ContentFactoryAI

    plataformas = plataformas or ["blog", "twitter", "linkedin"]
    piezas: list[dict[str, Any]] = []
    try:
        factory = ContentFactoryAI(output_dir=str(_REPO_ROOT / "content_output"))
        redes = None
        try:
            from agents.agent_redes import RedesAgent

            redes = RedesAgent()
            limites_red = {k: {"max_title": v.get("max_title", 200),
                               "max_description": v.get("max_description", 2000)}
                           for k, v in (redes.platforms or {}).items()}
        except Exception:
            redes = None
            limites_red = {}

        hashtags_marca = list(getattr(BrandVoice, "HASHTAGS", []) or [])[:5]
        slots = []
        hoy = datetime.now()
        for i, plat in enumerate(plataformas):
            gen = factory.generate(topic=tema, platform=plat, tone=tono)
            texto = gen.get("content", "") if isinstance(gen, dict) else str(gen)
            brand = _paso_brand(texto, hashtags_marca)
            limites = limites_red.get(CANAL_SOCIAL.get(plat, ""), {})
            viral = _paso_viral(texto, limites, brand["hashtags"])
            dia = (hoy + timedelta(days=i + 1)).day
            slots.append(ContentSlot(
                day=dia, platform=plat, content_type="campana",
                title=viral["hook"][:70] or tema,
                description=viral["cuerpo"][:200],
                script_source="content_os.py",
                best_time=MonthlyCalendar.BEST_TIMES.get(plat, "09:00"),
                estimated_reach="pipeline",
                hashtags=viral["hashtags"]))
            piezas.append({"plataforma": plat, "longitud": len(texto),
                           "brand": brand, "viral_hook": viral["hook"],
                           "texto": texto})

        slug = _slug(tema)
        cal_path = MonthlyCalendar.export_calendar_json(
            slots, output_path=str(
                _REPO_ROOT / "static" / "brand" / f"content_os_{slug}.json"))
        preview_path = _escribir_preview(slug, tema, tono, piezas)

        # Publicacion: solo donde hay canal social real.
        publicacion = []
        if redes is not None:
            for p in piezas:
                canal = CANAL_SOCIAL.get(p["plataforma"])
                if not canal:
                    publicacion.append({"plataforma": p["plataforma"],
                                        "estado": "sin_canal"})
                    continue
                try:
                    res = redes.multi_post(
                        {"title": p["viral_hook"][:80], "description": p["texto"][:500],
                         "tags": []}, [canal])
                    publicacion.append({"plataforma": p["plataforma"],
                                        "estado": "en_cola",
                                        "ids": [r.get("id") for r in (res or [])
                                                if isinstance(r, dict)]})
                except Exception as e:
                    publicacion.append({"plataforma": p["plataforma"],
                                        "estado": "error", "error": str(e)[:200]})
        else:
            publicacion = [{"plataforma": p["plataforma"], "estado": "sin_motor_redes"}
                           for p in piezas]

        resultado = {"ok": True, "tema": tema, "tono": tono,
                     "fecha": hoy.isoformat(),
                     "piezas": [{k: p[k] for k in ("plataforma", "longitud", "brand",
                                                  "viral_hook")} for p in piezas],
                     "calendario": cal_path, "preview": str(preview_path),
                     "publicacion": publicacion}
        _anexar({"ev": "campana", **{k: resultado[k] for k in
                                     ("tema", "tono", "fecha")},
                 "plataformas": plataformas, "publicacion": publicacion})
        try:
            from agents.memory.memory_vault import MemoryVault

            resultado["vault_id"] = MemoryVault().record(
                "content/campanas",
                f"Campana '{tema}' ({tono}): " +
                ", ".join(f"{p['plataforma']}->{pub['estado']}"
                          for p, pub in zip(piezas, publicacion)))
        except Exception:
            pass
        return resultado
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


def _escribir_preview(slug: str, tema: str, tono: str,
                      piezas: list[dict[str, Any]]) -> Path:
    """HTML de preview por plataforma en static/content/."""
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    bloques = []
    for p in piezas:
        texto_html = (p.get("texto", "").replace("&", "&amp;")
                      .replace("<", "&lt;").replace("\n", "<br>")[:6000])
        bloques.append(
            f"<section><h2>{p['plataforma']}</h2>"
            f"<p class='hook'>{p.get('viral_hook', '')}</p>"
            f"<div>{texto_html}</div></section>")
    html = (f"<!doctype html><html lang='es'><head><meta charset='utf-8'>"
            f"<title>{tema} â€” preview</title>"
            f"<style>body{{font-family:sans-serif;max-width:800px;margin:auto;"
            f"background:#0b1020;color:#e8ecf4}}h1{{color:#00ff88}}"
            f".hook{{color:#ffd166}}section{{border:1px solid #333;"
            f"padding:1em;margin:1em 0}}</style></head><body>"
            f"<h1>{tema}</h1><p>tono: {tono} Â· {datetime.now():%Y-%m-%d}</p>"
            + "".join(bloques) + "</body></html>")
    ruta = PREVIEW_DIR / f"preview_{slug}.html"
    ruta.write_text(html, encoding="utf-8")
    return ruta


def estado() -> dict[str, Any]:
    """Campanas registradas desde el ledger."""
    camps = _leer_ledger()
    return {"ok": True, "campanas": len(camps),
            "ultima": camps[-1].get("ts") if camps else None,
            "temas": [c.get("tema", "?") for c in camps[-10:]]}


# â”€â”€ Rutas Flask â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def register_content_routes(app) -> None:
    """Pipeline unico: campana + estado."""

    @app.route("/api/content/campana", methods=["POST"])
    def content_campana():
        data = request.get_json(force=True, silent=True) or {}
        plats = data.get("plataformas")
        if isinstance(plats, str):
            plats = [p.strip() for p in plats.split(",") if p.strip()]
        r = campana(str(data.get("tema", "")), plats, str(data.get("tono", "profesional")))
        return jsonify(r), (200 if r.get("ok") else 400)

    @app.route("/api/content/estado")
    def content_estado():
        return jsonify(estado())


# â”€â”€ CLI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _imprimir(texto: str) -> None:
    """print() que no muere en consolas Windows (cp1252) cuando el
    contenido trae emojis (las plantillas usan ðŸš€ habitualmente)."""
    try:
        print(texto)
    except UnicodeEncodeError:
        print(texto.encode("ascii", errors="backslashreplace").decode("ascii"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Content OS: pipeline unico")
    parser.add_argument("tema", nargs="?")
    parser.add_argument("--plataformas", default="blog,twitter,linkedin")
    parser.add_argument("--tono", default="profesional")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.tema:
        parser.print_help()
        return 1
    plats = [p.strip() for p in args.plataformas.split(",") if p.strip()]
    r = campana(args.tema, plats, args.tono)
    if args.json:
        _imprimir(json.dumps(r, indent=2, ensure_ascii=False, default=str))
    else:
        lineas = [f"campana '{r.get('tema')}' ok={r.get('ok')}"]
        for p in r.get("piezas", []):
            lineas.append(
                f"  {p['plataforma']:10} {p['longitud']:5} chars "
                f"cta={'SI' if p['brand']['cta_ok'] else 'no'} hook={p['viral_hook'][:60]}")
        for pub in r.get("publicacion", []):
            lineas.append(f"  -> {pub['plataforma']}: {pub['estado']}")
        lineas.append(f"  preview: {r.get('preview')}")
        _imprimir("\n".join(lineas))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

