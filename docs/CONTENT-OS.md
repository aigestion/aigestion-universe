# Content OS (idea #7) — pipeline único con preview real

Factory → Brand → Viral → Calendar → Preview → Publicación, en
`aig/content/content_os.py`. Sin pasos fingidos: cada etapa
produce artefactos verificables.

## Etapas (reales)

| Etapa | Módulo | Sale |
|-------|--------|------|
| Factory | `content_factory_ai` (local, sin red) | texto por plataforma |
| Brand | `BrandVoice` (constantes) | check CTA + hashtags de marca |
| Viral | empaquetado propio | hook + recorte a límites de `RedesAgent.platforms` |
| Calendar | `ContentSlot` + `BEST_TIMES` + `export_calendar_json` | `static/brand/content_os_<slug>.json` (su esquema) |
| Preview | plantilla propia | `static/content/preview_<slug>.html` (ignorado por git) |
| Publicación | `RedesAgent.multi_post` | `en_cola` (cola persistente) o `sin_canal` |

## Decisiones honestas

- **Blog/newsletter → `sin_canal`**: no hay clave social para ellos;
  antes esto se habría contado como "publicado".
- **Cola persistente**: `scheduled_queue` era solo memoria (se perdía
  al salir). Ahora `data/social/cola.json` con carga tolerante.
- **Sin CTA → flag, no silencio**: `cta=no` cita la regla
  (`BrandVoice.DO`).
- **Video-factory fuera**: `viral_content_factory` es pipeline de
  vídeo (trends, TTS, Veo): otro medio, otras dependencias. Este
  loop es texto+social.
- **Consola Windows**: los contenidos traen emojis (🚀) que tumban
  `print` en cp1252. `_imprimir()` degrada a escapes; el JSON
  canónico está en el ledger, no en stdout.

## Resucitado en el camino

`content_factory_ai.py` **no importaba** (f-string con backslash,
línea 575, roto desde HEAD): el adapter devolvía stub siempre.
Extraído `_slug_archivo()` → el adapter `content_factory` ahora
responde de verdad sin tocar el adapter.

## Superficies

- CLI: `python content_os.py "tema" [--plataformas a,b] [--tono T]`
- Rutas: `/api/content/campana`, `/api/content/estado`
  (258 → 260 reglas). Ledger `data/content/campanas.jsonl` + vault.
