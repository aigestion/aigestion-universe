# Invoice Truth Graph (idea #4) — alerta proactiva antes de pagar

El auditor (`smart_invoice_auditor`, reglas locales) hace el primer
cribado; el grafo (`agents/agent_invoice_graph.py`) añade
proveedores, duplicados probables y fraude. `puedo_pagar()` es la
puerta: **pagar | revisar | bloquear** con motivos.

## Reglas de fraude (constantes en el módulo, sin ML)

| Señal | Condición | Efecto |
|-------|-----------|--------|
| DUPLICADO_EXACTO | mismo proveedor + número (+hash auditor) | **bloquear** |
| DUPLICADO_PROBABLE | mismo proveedor, importe ±1 EUR, <30 días, distinto número | revisar |
| REDONDO_ALTO | total ≥ 1000 y múltiplo de 100 | revisar |
| PROVEEDOR_NUEVO_ALTO | primera factura y total > 500 | revisar |
| RACHA | >3 facturas del proveedor en 7 días | revisar |
| FIN_SEMANA | emitida sáb/dom | nota (no bloquea) |

El auditor aporta además: anómalo vs promedio ×2, proveedor
desconocido, fecha futura. Todo queda en `data/invoice/ledger.jsonl`
(ignorado por git); bloquear/revisar se registra en el vault
(`invoice/alertas`).

## Lo que NO hace (honesto)

- **No lee facturas reales**: la entrada son dicts
  `{proveedor, numero, total, fecha, concepto}` (CLI/API). El OCR
  (`extraer_datos_texto`) existe en el auditor pero sin pipeline
  de ingesta conectado.
- **No paga ni bloquea pagos de verdad**: el veredicto es una
  propuesta registrada. La ejecución bancaria es trabajo futuro.
- Fechas aceptadas: `YYYY-MM-DD` (y `DD/MM/YYYY` por tolerancia).

## Superficies

- CLI: `registrar '<json>' | veredicto '<json>' | red [proveedor] | stats`
- Rutas: `/api/invoice/registrar`, `/api/invoice/veredicto`,
  `/api/invoice/red`, `/api/invoice/stats` (252 → 256 reglas).
- Core: alias `SmartInvoiceAuditor.audit()` (el adapter lo esperaba y
  explotaba con `AttributeError`); `do_default` audita dicts.
- Auditor escribe `invoice_database.json` en cwd (preexistente);
  añadido a `.gitignore`.
