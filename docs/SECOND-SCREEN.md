# Second Screen Command (idea #11) — HUD con aprobar/rechazar

El Pixel como HUD de gestoría: `/pixel-dashboard` muestra salud,
agentes y una sección **Pendientes de tap** alimentada por:

| Origen | Qué sale | Tap | Efecto real |
|--------|----------|-----|-------------|
| court | grises sin decidir | aprobar/rechazar | `decidir` (feedback incluido) |
| invoice | veredictos revisar/bloquear no vistos | visto | evento `revision` (el grafo no cambia) |
| edge | tareas muertas | reencolar | `dispatch_task` nuevo con mismo tipo/payload |

Rutas: `GET /api/pixel/hud/pendientes`, `POST /api/pixel/hud/accion`
(260 → 262 reglas). El template trae botones por acción (verdes los
seguros, rojos rechazar) con `fetch` + recarga.

## Decisiones y bugs

- **Invoice `visto` no altera el grafo**: el veredicto queda; solo se
  registra el acuse. Cambiar veredictos a posteriori falsearía la
  auditoría.
- **`_leer_ledger` filtraba `ev==factura`**: el HUD no veía
  veredictos ni revisiones → parámetro `solo_facturas` (default
  preserva `red()`/`stats()`).
- **Bonus**: `/api/pixel/dashboard/data` devolvía 500 siempre
  (`app.jsonify` no existe; es `flask.jsonify`). Corregido al tocar
  el registro de rutas.
- Sin decisiones pendientes la sección muestra "Sin pendientes";
  todo fallo de una fuente deja a las demás (try/except por bloque).
