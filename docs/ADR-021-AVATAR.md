# ADR-021 - Avatar 3D de Daniela que habla (PC + Pixel)

**Estado:** aceptado (2026-10-03)

## Contexto

Daniela conversaba por texto en PC (`gev/static/web_ui.html`) y en la PWA
del Pixel (`mobile-app/js/views.js`), pero no tenía cuerpo: en PC solo había
un icosaedro abstracto de fondo, y en la PWA un GLB 100% estático
(0 morphs, 0 skins, 0 anims) con boca procedural por volumen. El TTS
(`voice_pipeline.py`, edge-tts Elvira gratis) existía pero hablaba por el
altavoz del servidor, nunca por el chat, así que el avatar jamás se movía
al responder.

## Decisión

1. **Rig procedural con Blender headless** (`scripts/avatar/rig_daniela.py`),
   conservando el look: plantilla `assets/daniela3d.glb` (75,5 MB, intacta)
   → shape keys gaussianas por máscara de vértices (`blink`, `jawOpen`,
   `browUp`, calibradas con renders) → `assets/daniela3d_rigged.glb`
   (4,5 MB tras `gltf-transform optimize`: meshopt + webp).
2. **Un solo módulo de avatar** (`mobile-app/js/daniela-avatar.js`): lee los
   morph targets (`jawOpen` ← envelope de audio, `blink` aleatorio,
   `browUp` en *thinking*); sin GLB rigged, fallback al estático sin cambiar
   la API. La PWA carga el rigged (`MODEL_URL` + fallback).
3. **Voz cableada al chat**: `synthesize(text) -> mp3` (sin reproducir, cache
   por hash en `data/voice_pipeline/`) + `POST /api/voice/tts` →
   `DanielaAvatar.hablarTTS()` → `speakAudio(url)`; si falla, `speak()`
   (voz del dispositivo). El chat avisa con `onHablar(texto)` y solo programa
   el reposo si el avatar no tomó la palabra. De paso se corrigió
   `register_voice_routes`: usaba `flask_app.request`/`flask_app.jsonify`,
   que no existen (todas las rutas de voz devolvían 500).
4. **PC** (`gev/static/web_ui.html`): el icosaedro (three r128 por CDN) se
   sustituye por importmap al **three vendored** + el módulo compartido
   (`shift: 0.25`, busto a la derecha del chat). `daniela_unified.py` sirve
   `/shared/`, `/vendor/three/`, `/assets/` y registra las rutas de voz.
   Sin duplicar ficheros.

## Motivos

1. **Identidad**: se conserva la cara de Daniela; no se migró a VRM/Ready
   Player Me (cambiaría el look y añade dependencias).
2. **Un solo modelo y un solo motor** para PC y Pixel: el bug se arregla una
   vez, no dos.
3. **Degradación honesta**: sin red (edge-tts) habla la voz del dispositivo;
   sin WebGL/rigged, el avatar estático de antes.
4. **Zero-cost**: Blender local + edge-tts gratis + three vendored (sin CDN
   en producción).

## Consecuencias

- `tests/test_daniela_avatar_model.py`: el GLB debe tener los 3 morphs y
  pesar < 10 MB. `tests/test_daniela_avatar_motor.py`: contrato del motor,
  la voz y el montaje en PC. `tests/test_gev_pwa.py` intacto.
- `data/voice_pipeline/tts_*.mp3` es cache runtime (ignorado, se poda a 7 días).
- Limitación conocida: el addon glTF de Blender 4.5 no reimporta
  `EXT_meshopt_compression` (solo afecta a re-renderizar el comprimido;
  three.js lo lee sin problema).
