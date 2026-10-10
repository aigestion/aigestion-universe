# Mesh Offline-First (idea #3) — cola cifrada para mala red

`aig/pixel/mesh_outbox.py`: al encolar se aplica en local YA
(offline-first) y se guarda cifrado; con WiFi se drena a peers y se
entregan documentos. Rutas `/api/mesh/outbox/*` (262 → 265).

## Ops

`mesh_set` / `mesh_add` / `mesh_counter` (al CRDT local + push vía
`node.sincronizar()`, idempotente por `fusionar`) y `documento`
({nombre, b64, sha256 opcional}; ≤2 MB; entrega a
`data/pixel_sync/received/` con verificación sha).

## Cifrado (fail-closed)

Backend: Silicon Vault (`MESH_VAULT_PIN` o `DANIELA_PIN`; el PIN
nunca se guarda). Sin desbloqueo no se encola; PIN mal → error
honesto. Payloads troceados a 6000 chars (límite del vault).
El log solo guarda metadatos (verificado: sin plaintext).

## Red

Orden: fichero `forzar_online` (tests/dev) → `termux-wifi-*` en
Pixel → probe TCP al primer peer. Sin peers = offline (nada con
quien sincronizar). Lease/TTL los pone el mesh; el outbox marca
`drenado` por op y sigue ante fallos parciales (cada fallo se
reporta, no tumba el drain).

## Verificado en smoke

- Encolar offline → lectura local inmediata + log sin plaintext +
  rechazo sin vault.
- Un vault distinto por proceso no descifra otro (fallo por op,
  honesto).
- Drain completo vía HTTP: 2/2, documento con bytes exactos,
  pendientes a 0.
- Lease vencido → pending; 3 fallos → dead (unit del fold).

## Límites

- Documentos >2 MB se rechazan (v1); el vault manda en tamaños.
- El vault es por proceso: el PIN del operador real no se prueba
  aquí (sus 2 secretos preexistentes no se tocan).
- `forzar_online` es solo para tests; en prod manda WiFi/peer.
