# SIL Weekly Job — self-improvement como rutina semanal

El motor SIL (`sil_engine.py`: review → dispatch → verify → learn →
dashboard) ya existía como clases + CLI. Este documento convierte el
loop en un **job programado**: qué corre, cuándo, dónde deja el reporte
y qué riesgos tiene cada modo.

## Qué ejecuta

`python scripts/sil_weekly.py` (por defecto, **local y seguro**):

| Paso | Comando | Efectos |
|------|---------|---------|
| review | `sil_engine.py review` | Lee el repo, genera findings (solo lectura + `data/sil/`) |
| lessons-export | `sil_engine.py lessons-export` | Escribe `data/sil/learning_log.md` |
| dashboard | `sil_engine.py dashboard` | Escribe `static/health_dashboard.html` |
| scoreboard | snapshot en memoria | Solo lectura (`core.health()` + exec log) |

Reporte: `data/sil/weekly_report_<fecha>.json` (ignorado por git).
Salida 0 = todo rc 0; 1 = algún paso falló (el reporte dice cuál).

Con `--full` añade `dispatch` + `verify`: **abren PRs vía Jules**,
escriben `dispatch_log` y hacen commits. Solo con claves configuradas
y aceptación consciente (ver Seguridad).

## Programarlo

**Linux cron** (lunes 9:00):

```cron
0 9 * * 1 cd /ruta/a/aig && /ruta/a/.venv/bin/python scripts/sil_weekly.py >> data/sil/weekly_cron.log 2>&1
```

**Windows Task Scheduler** (lunes 9:00, semanal):

```powershell
schtasks /create /tn "Daniela SIL semanal" /tr "C:\ruta\aig\.venv\Scripts\python.exe C:\ruta\aig\scripts\sil_weekly.py" /sc weekly /d MON /st 09:00
```

**systemd timer** (ver `infra/` si se añade; el script ya es idempotente
y no requiere terminal).

**Termux**: `termux-job-scheduler` o Termux:Boot con el mismo comando;
el modo local no necesita red (el review no llama a LLMs).

## Probar sin programar nada

```bash
python scripts/sil_weekly.py --check   # qué correría
python scripts/sil_weekly.py           # ejecución local real
```

## Seguridad

- Modo local: sin red saliente salvo la que ya haga `review`
  (analiza código en disco; no envía nada).
- Modo `--full`: `dispatch` contacta con Jules y puede abrir PRs;
  `verify` lee el estado de esos PRs. Requiere las claves de
  automatización y revisión humana de `dispatch_log` después.
- Los reportes y la Knowledge Base viven en `data/sil/` (ignorado
  por git, nunca se versionan secretos ni estado local).

## Troubleshooting

| Síntoma | Causa probable |
|---------|----------------|
| `review` tarda mucho | Repo grande; timeout 900 s, el reporte lo marca rc=124 |
| `dispatch` rc != 0 sin `--full` | Normal: no corre en modo local |
| Dashboard desactualizado | `dashboard` falló: ver `tail` del paso en el reporte |
| Scoreboard `ok: false` | Core no cargó: ver `scoreboard.error` en el reporte |
