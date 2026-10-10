# Pixel Edge Node (idea #2) — el teléfono como worker del swarm

El Pixel ejecuta tareas (OCR, voz, geofence, cámara) en vez de solo
mostrar espejos. Dos piezas: **servidor** (`aig/pixel/edge_node.py`,
en el PC) y **worker** (`edge_worker.py`, en Termux).

## Protocolo

| Paso | Endpoint | Notas |
|------|----------|-------|
| Encolar | `POST /api/edge/dispatch` {tipo, payload, prioridad} | tipos: `ocr_factura`, `transcribir_voz`, `foto_camara`, `chequeo_geofence`, `estado_nodo` |
| Pedir trabajo | `GET /api/edge/tasks/next?node_id=&bateria=&cargando=` | lease con TTL (300 s, 900 s pesadas) |
| Reportar | `POST /api/edge/tasks/<id>/result` {node_id, resultado} | cierra la tarea |
| Ver cola | `GET /api/edge/status` | conteos, nodos, backend redis/local |

Prioridad 0 = urgente, 2 = normal. Sin auth (mismo modelo de
confianza que el resto de rutas pixel: red local/Tailscale).

## Política de batería (vía `battery_aware_scheduler`)

| Modo | Batería | Qué se le da al worker |
|------|---------|------------------------|
| full | ≥50% o cargando | todo |
| normal | 20–49% (o sin dato: conservador) | todo menos pesadas (`ocr_factura`, `transcribir_voz` en espera) |
| save | <20% | solo prioridad 0 |

Si el worker muere sin reportar, el lease vence y la tarea vuelve a
pending (3 intentos → dead). Cola en `data/edge/edge_log.jsonl`
(ignorado por git); Redis solo como aviso best-effort si hay
`REDIS_URL` (si no, `redis: no_configurado` honesto).

## Capability matrix del worker (v1)

| Tarea | En Pixel con Termux:API | En PC |
|-------|-------------------------|-------|
| `estado_nodo` | real (más batería) | real (plataforma) |
| `chequeo_geofence` | real (`termux-location` + haversine) | `no_soportado` |
| `foto_camara` | real (`termux-camera-photo`) | `no_soportado` |
| `transcribir_voz` | **parcial honesto**: graba (`grabado_sin_stt`, fichero real), sin STT | `no_soportado` |
| `ocr_factura` | real si hay `tesseract`, si no `no_soportado` con requisito | `no_soportado` |

`no_soportado` es un resultado válido (capability discovery), no un
fallo: el lease se libera y la tarea queda para un nodo capaz.

## Puesta en marcha (Pixel)

```bash
# En Termux (con Termux:API instalado):
pkg install python termux-api
pip install requests
python edge_worker.py --server http://100.111.139.106:5000 --interval 15
```

El worker llega al teléfono vía `scripts/sync_phone_deploy.py`
(`edge_worker.py` en la lista). Probar en PC:

```bash
python edge_node.py dispatch chequeo_geofence '{"lat":40.4,"lon":-3.7,"radio_m":100}'
python edge_node.py next nodo-pc --bateria 80
python edge_worker.py --server http://localhost:5000 --once
python edge_node.py status
```
