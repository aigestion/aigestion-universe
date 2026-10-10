# ADR-019 — `phone/`: runtime de Daniela en Termux

**Estado:** aceptado (2026-09-30, tras unificación de home → repo)

## Contexto

Antes de la unificación, el runtime de Daniela en Termux vivía disperso en el home:

| En home | Función |
|---|---|
| `~/core/` | Cerebro de Daniela: `daniela_brain.py`, `daniela_master.py`, `daniela_rag.py`, `daniela_router.py`, `modules/`, `tools/` |
| `~/services/` | Servicios: `daniela_daemon.py`, `daniela_sentinel.py`, `daniela_auth.py`, wakeword, duplex, shake, panic, stt, vision |
| `~/scripts/` | Scripts operativos: `fix_nexus*`, `update_bot*`, `inject_*` |
| `~/assets/` | Wavs de prueba de voz |
| `~/audit.py`, `~/verify_daniela_skills.py` | Auditoría de la estructura |

El monorepo (`~/apps/aig`) ya tenía `mobile-app/` como árbol de cliente (ADR-016), pero `phone/` es un árbol **separado** con su propia estructura interna (`core/`, `services/`, `scripts/`).

## Decisión

**`phone/` se conserva como árbol separado dentro del repo**, con subestructura propia:

```
phone/
  core/       Cerebro de Daniela (daniela_brain, daniela_master, rag, router, modules/, tools/)
  services/   Servicios (daniela_daemon, daniela_sentinel, auth, wakeword, duplex, shake, panic, stt, vision)
  scripts/    Scripts operativos (fix_nexus*, update_bot*, inject_*)
  agents/     Agentes de runtime (brain, scout, swarm, initiative, caller, ...;
              ~42 ficheros importan `phone.agents`) - añadido tras este ADR
  assets/     Wavs de prueba de voz
  audit.py    Auditoría de estructura
  verify_daniela_skills.py  Suite de auditoría y test
```

> **Actualización 2026-10-05**: desde el commit `4d0bf8b1` (2026-10-03,
> unificación home -> repo) el árbol vive en **`daniela-os/phone/`**; los
> imports siguen siendo `phone.*` vía `sys.path`. `mobile-app/` (cliente) y
> `phone/` (runtime) siguen siendo árboles distintos: 0 ficheros compartidos
> en `services/`.

## Motivos

1. **Separación de responsabilidades**: `mobile-app/` es el cliente Android (Java/Kotlin + puentes Python organizados por destino: `services/`, `bridges/`, `core/`). `phone/` es el runtime de Termux (Python puro, organizado por capa: `core/`, `services/`, `scripts/`).
2. **Ciclo de vida diferente**: `mobile-app/` se compila y despliega como APK. `phone/` se ejecuta directamente en Termux con `python3` y se actualiza en caliente.
3. **Dependencias diferentes**: `mobile-app/` usa `adb`, `termux-api`, `zeroconf`. `phone/` usa `sqlite3`, `requests`, `flask`.
4. **No colisionan**: `phone/core/` y `mobile-app/core/` son paquetes diferentes sin solapamiento de nombres.

## Reglas

1. **`phone/` no es paquete Python**: se importa porque `sys.path` incluye `daniela-os/` (ver `tests/conftest.py`), lo que da `phone.*` (p. ej. `phone.agents.*`).
2. **Los boot scripts de Termux** referencian módulos en `daniela-os/phone/services/` con rutas absolutas `<repo>/daniela-os/phone/services/`.
3. **`phone/core/` y `mobile-app/core/` coexisten**: si un módulo necesita ambos, debe explicitar cuál usa (`from phone.core.X import Y` vs `from mobile_app.core.X import Y`).
4. **Los stubs en `phone/services/`** (`daniela_sensor_guard.py`, `daniela_voice.py`, etc.) son marcadores de posición para módulos pendientes de migrar. Lanzan `NotImplementedError` con mensaje descriptivo.

## Consecuencias

- El repo tiene dos árboles de cliente: `mobile-app/` (Android) y `phone/` (Termux). Esto es intencional y documentado.
- Los boot scripts pueden referenciar módulos en `phone/services/` sin riesgo de colisión con `mobile-app/`.
- La auditoría de integridad (`tests/test_paths_integrity.py`) verifica que `phone/` no cree ficheros fuera de `phone/core/`.

## Alternativas consideradas

1. **Fusionar `phone/` en `mobile-app/`**: descartado. Las estructuras son incompatibles (`phone/core` vs `mobile_app.core`) y los ciclos de vida son diferentes.
2. **Mover `phone/` a `daniela-os/`**: descartado en 2026-09-30, pero **hecho el 2026-10-03** en `4d0bf8b1` por la unificación home -> repo; ver Actualización arriba.
3. **Eliminar `phone/` y usar solo `mobile-app/`**: descartado. `mobile-app/` no tiene los módulos de Daniela (`daniela_brain`, `daniela_master`, etc.) y migrarlos rompería el árbol de cliente.
