# Meeting → Expediente (idea #6) — cierre del loop

Transcripción → `MeetingIntelligence` → `DocumentosAgent` (acta) →
`CalendarioAgent` (seguimiento por action item) → vault + ledger.

## Cableado real (módulo `agents/agent_expediente.py`)

| Paso | Qué usa | Sale |
|------|---------|------|
| Intel | `extraer_participantes/action_items/decisiones`, `generar_resumen` (regex ES, local) | participantes, acciones `{person, task, deadline, status}`, decisiones, resumen |
| Acta | `generate_meeting_minutes` → `data/documents/acta_*.md` | fichero, palabras, método (template/gemini) |
| Eventos | `add_event` por acción, 09:00, 30 min, tipo seguimiento | evento por action item en `calendar_events.json` |
| Memoria | vault `expediente` + `data/expedientes.jsonl` | trazabilidad |

## Fechas en lenguaje natural (reglas, sin LLM)

Explícita `12 de septiembre` → ese día (año siguiente si pasó);
`mañana` → +1; `próxima semana` → +7; `fin de semana` → sábado;
día de semana → **próxima ocurrencia estrictamente futura**
("el viernes" dicho en viernes = el siguiente); sin fecha → +7
etiquetado. El evento cita la regla (`[proximo viernes]`).

## Bugs del camino (reales, corregidos aquí)

1. **Adapter roto doble**: `MeetingIntelligence(transcript)` +
   métodos ingleses (`extract_participants()`) que no existen → la
   API real es `MeetingIntelligence()` + `extraer_*(transcript)`.
   Reescrito + `do_default` (texto pegado) + `do_expediente`.
2. **Acta fantasma en Windows**: `generate_report` titulaba
   `Acta: ...` y el `:` creaba un ADS invisible (`data/documents/acta`)
   en vez de fichero (todas las actas colisionaban). Saneado de
   nombre en `agent_documentos.py`.
3. Regex de deadlines no casaba `manana` sin ñ (solo `mañana`):
   añadida la variante ASCII.

## Lo que NO hace

- Sin diarización real (quién habla sale de patrones `Nombre: ...`).
- Sin NLP de fechas con LLM (reglas documentadas arriba).
- `calendar_events.json` y `meeting_history.json` fuera de git
  (estado runtime, como las DBs de Fase 0).

## Superficies

- CLI: `python agent_expediente.py "<transcripcion>" [--titulo T]`
- Rutas: `/api/expediente/procesar`, `/api/expediente/stats`
  (256 → 258 reglas).
