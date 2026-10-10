# ADR-020 - `iot_hub/`: dominio IoT unificado (`/api/iot/*`)

**Estado:** aceptado (2026-10-02)

## Contexto

La superficie de domótica estaba dispersa en cinco sitios con solape:

| Sitio | Papel | Problema |
|---|---|---|
| `daniela-os/iot_real_integration.py` | Lógica real (HA + MQTT) | Copiado **4 veces** (`daniela-os/`, `danielaos/`, `mobile-app/`, `phone_deploy/`) |
| `api/homeassistant_api.py` | Cliente HA | Módulo API de 1 línea; el 95% era la clase `HomeAssistantAPI` |
| `connectors/homeassistant_connector.py` | Segundo cliente HA | **0 consumidores**, duplicado puro |
| `skills/iot_controller.py` | Voz → dispositivo | Stub simulado, sin backend real |
| `IA-SERVICES/hermes/skills/smart_home_hub.py` | Hub de vista | Todo mock, sin fuente real |

Y **el servidor real (`gev/daniela-os/server.py`) no tenía ninguna ruta de domótica**: 0 rutas `/api/iot/*` en el snapshot.

## Decisión

1. **`iot_hub/` como paquete en la raíz** (raíz = contratos, ADR-REPO-LAYOUT; `snake_case` + `__init__.py` para paquetes; `tests/test_organization.py` lo valida):
   - `config.py` — env a nivel de módulo (`HA_URL`, `HA_TOKEN`, `MQTT_*`, `ESPHOME_URL`, `IOT_*`), monkeypatchable en tests.
   - `service.py` — `IoTService` (estado, aliases, control, voz), singleton `get_service()` perezoso sin efectos en import; `parse_voice_command()` canónico.
   - `backends/` — `homeassistant.py` (clase movida de `api/homeassistant_api.py`), `mqtt.py`, `esphome.py`; todos import-safe (paho/requests lazy).
   - `discovery.py` — `nmap` si existe, si no ping-sweep stdlib (`ThreadPoolExecutor`, `/16` tope); inventario en `data/iot/inventory.json`.
   - `api.py` — blueprint `iot_bp` (`/api/iot/status|devices|sync|control|scene|voice|alias|inventory|discovery|mqtt-publish|aliases`), **11 rutas**.
2. **Registro como fase `iot`** en `gev/daniela-os/server.py` con el patrón `_safe_register` existente: si `iot_hub` no importa, `/api/status` sigue vivo.
3. **Home Assistant es externo y va por `.env`** (vars añadidas a `.env.example` local — ignorado por git vía `.env.*`); nunca credenciales en repo. MQTT/ESPHome: backends locales opcionales (`status()` degradado a "no alcanzable", nunca 500).
4. **Estado runtime en `data/iot/`** (`device_map.json` con 10 aliases por defecto, `inventory.json`) — cubierto por la regla `/data/` de `.gitignore`, sin cambios de `.gitignore`.
5. **`api/homeassistant_api.py` queda como shim** (`from iot_hub.backends.homeassistant import HomeAssistantAPI` + `import requests  # noqa: F401`): los tests parchean `requests.get` ahí siguen funcionando.
6. **`connectors/homeassistant_connector.py` eliminado** (`git rm`, 0 consumidores verificados con grep).
7. **Skills delegan en el hub con fallback simulado**: `skills/iot_controller.py` (contrato `process_iot_command(command) -> str` intacto) y `IA-SERVICES/hermes/skills/smart_home_hub.py` (hub en `127.0.0.1:9200`, mock si no responde). Dos bugs heredados de voz corregidos en el paso: matching por tokens («luz del salon») e intención de temperatura antes que `turn_on` («pon el termostato a 22»).
8. **Copias legacy `*_integration.py` NO se tocan** (runtime del teléfono); su consolidación con shims al estilo ADR-001 queda **diferida**.

## Motivos

1. **Un solo canónico por operación**: sync/control/voz/descubrimiento viven en `iot_hub`; los shims apuntan ahí.
2. **Nunca romper el servidor**: fase `iot` aislada; un import roto degrada a "sin domótica", no a 500 general.
3. **Verificable**: snapshot de rutas (493 → 503, solo inserciones), 58 tests nuevos (`tests/iot/`), suite oficial en verde.
4. **Reversible**: shims conservan los nombres públicos históricos (`api.homeassistant_api.HomeAssistantAPI`).

## Consecuencias

- +11 rutas `/api/iot/*` en `tests/fixtures/api_routes.snapshot.json`.
- `paho-mqtt 2.1.0`: `mqtt.Client()` sigue funcionando (DeprecationWarning; sin cambio de código).
- El panel IoT (`unified-dashboard/src/lib/IoTPanel.svelte`) depende de la fase `iot` activa en :9200.

## Pendientes (fuera de este ADR)

1. **Consolidar las 4 copias legacy** de `iot_real_integration.py` → shims hacia `iot_hub.service` (fase posterior, ADR-001).
2. **Twin `*_engine/` en raíz ↔ `engine/`** (21 pares) — separado, también diferido.
3. **Build del SPA `unified-dashboard/`**: fragmento sin `package.json`/`index.html`/`dist` (preexistente; `server.py` sirve `../dist` inexistente). El proxy de `vite.config.js` ya no se auto-buclea (puerto 5173, `/api/iot` → 9200).
