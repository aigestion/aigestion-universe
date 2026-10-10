# Zero-Inbox Court (idea #5) — confirmación humana solo en zona gris

El motor (`email_zero_inbox`, reglas locales, sin red) clasifica; el
tribunal (`agents/agent_court.py`) decide qué hacer.

## Zonas (calibración v1 por reglas, no ML)

| Categoría | Confianza | Zona | Qué pasa |
|-----------|-----------|------|----------|
| spam | 0.93 | auto | propuesta de archivado |
| newsletter | 0.90 | auto | propuesta de archivado |
| urgent | 0.82 | **gris** | cola humana + borrador (lo urgente siempre lo ve un humano) |
| important | 0.68 | **gris** | cola humana + borrador |
| delegable | 0.55 | **gris** | cola humana + borrador delegación |
| info | 0.45 | **gris** | cola humana, sin borrador |

Umbral auto: 0.85. Las confianzas se calibrarán con
`tasa_aprobacion` del feedback (hoy: loop registrado, sin auto-ajuste).

## Lo que NO hace (honesto)

- **No envía emails.** Los borradores quedan en
  `data/court/borradores/<id>.json` con estado
  pendiente/aprobado/rechazado. El envío Gmail API requiere OAuth
  y es trabajo futuro.
- **No lee tu inbox.** La entrada son dicts `{id, subject, sender,
  body, date}` (CLI/API/dispatch). `fetch_unread` IMAP existe en
  `agent_correo` pero pide credenciales que no hay.
- Spam ambiguo (p. ej. sin keywords en reglas) cae a **gris** en vez
  de auto: fallar hacia el humano es el diseño, no un bug.

## Loop de calibración

Cada `decidir` escribe en `feedback.jsonl` (categoría, confianza,
decisión). `stats` expone `tasa_aprobacion` global: si una categoría
se rechaza mucho, sus confianzas están infladas → ajuste manual
documentado aquí. Sin este loop (gap auditado) los umbrales serían
fe ciega.

## Superficies

- CLI: `triage '<json>' | cola | decidir <id> aprobar|rechazar | stats`
- Rutas: `/api/court/triage`, `/api/court/cola`, `/api/court/decidir`,
  `/api/court/stats` (248 → 252 reglas con este módulo).
- Core: `EmailAdapter.do_default` clasifica queries pegadas como
  email (sender "chat"); `classify_email`/`generate_reply` a nivel
  de módulo activaron el adapter (era stub por firma fantasma).
- Vault: decisiones en `court/decisiones` (trazabilidad).
