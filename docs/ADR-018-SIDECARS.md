# ADR-018 — Sidecars: procesos ajenos, nunca dependencias nuestras (2026-09-30)

**Estado:** aceptado (criterio de arquitectura derivado de ADR-016/ADR-017).

**Regla.** *Todo runtime de terceros que adoptemos entra como **sidecar**
(proceso lateral o servidor MCP), nunca como dependencia pip del monorepo.*

> Nota de fichero: los ADR-001…017 viven todos en `docs/ADR-REPO-LAYOUT.md`.
> Este se escribe aparte porque nace mientras hay una migración en vuelo
> (absorción ADR-017#2); en la Fase 1 de higiene se enlaza desde ese fichero
> y se le asigna su posición definitiva.

## Contexto

Tres candidatos OSS evaluados en la misma semana, tres stacks distintos al
nuestro:

| Candidato | Stack | Fricción con el repo |
|---|---|---|
| visor Vite (`--base=/gods-eye/pro/`) | Node | ya vive como sidecar en `:4173` |
| `google/artemis` (Apache-2.0) | Python **≥3.12** + `adbutils`/`uiautomator2` | repo en **3.11**; sin SDK de Android en Termux |
| OpenClaw (MIT, fundación 501(c)(3)) | **Node/pnpm**, gateway `:18789` | duplicaría gateway, memoria y browser control |

El repo es Python 3.11 + Docker, con mandato de coste cero y sin GitHub
Actions. Meter cualquiera de los tres en `pyproject.toml` no es solo
instalable: es adoptar su ciclo de vida, sus CVEs y su superficie.

## Decisión

1. **Sidecar, no dependencia.** Se ejecutan fuera del árbol de dependencias:
   proceso aparte, contenedor aparte o servidor MCP. El repo solo habla con
   ellos por HTTP/WS/MCP.
2. **Puente nuestro.** Si un sidecar necesita tocar Daniela, lo hace por la
   puerta que ya existe: **Hermes (`:9900`)** o el registrador canónico
   `daniela.registrar()`. Nunca importando nuestros módulos ni nosotros los
   suyos.
3. **Fase 0 obligatoria antes de nada.** Evaluación sin instalar (licencia,
   `requires-python`, telemetría, dependencias nativas). Solo si pasa →
   piloto de 1 unidad; si no → se borra el sidecar y no queda deuda.
4. **Los sidecars no entran en el health gate de 13 servicios.** Se vigilan
   aparte: no deben poder tumbar el arranque de Daniela OS.
5. **Registro único de candidatos**: `.opencode/oss-queue.md` (orden, fase
   y veredicto de cada uno).

## Consecuencias

- **+**: cero inflación de `pyproject.toml`; un lado cae sin arrastrar al
  otro; los forks/patches de terceros no viven en nuestro historial.
- **−**: hay que mantener el puente (wrapper HTTP/MCP) y su contract test.
- **−**: el sidecar puede morirse sin que el gate lo note → el health gate
  propio debe seguir siendo el criterio de verdad, no el estado del sidecar.
- **Seguridad**: todo sidecar con `exec`/browser/canal de mensajería entra
  con política de allow-list estricta y sin credenciales del repo
  (ver lección de los PATs, sesión 2026-09-30).

## Candidatos y estado

| OSS | Fase | Nota |
|---|---|---|
| Vite (`gev`) | **en producción** | sidecar de referencia del repo |
| `google/artemis` | Fase 0 ✅ / Fase 1 ✅ | ADB validado 2026-10-04 en Pixel 8a físico; E2E `tests/mobile/test_artemis_e2e.py` |
| OpenClaw | encolado (Fase 0 propuesta) | 1 canal (Telegram) → wrapper → Hermes `:9900` |
