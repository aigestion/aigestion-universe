# Daniela Continuum — cerebro nocturno (idea #1)

Un solo repaso compone lo construido: **memoria + personajes + SIL +
scoreboard**. Cada noche: resume el día, propone 3 acciones y — solo
con `--auto` — abre autofix/Jules ante fallos recurrentes.

## Qué hace `repaso_nocturno()`

1. **Personajes**: `briefing_diario()` fresco (5 agentes, acciones de
   solo lectura) + registro en vault (`squad/*`).
2. **Memoria**: recall `pendiente/ayer` del vault (continuidad).
3. **SIL** (lectura): `sil_state.json`, `health_trend.json`,
   `dispatch_log.json` + findings abiertos via `AutoFixPipeline`.
4. **Scoreboard**: `summary()` (SLO por módulo, live-ratio del swarm).
5. **3 acciones por reglas** (cada una documenta su `porque`):
   recurrente → deterioro de salud → personaje fallido →
   módulo degradado → pendiente del vault → rutina.
6. **Recurrente** = abierto hoy + en `dispatch_log` sin verificar,
   o salud cayendo 2 lecturas seguidas.
7. Persiste `static/brand/continuum_<fecha>.json|.md` (ignorados
   por git) + record en vault (`continuum/resumen`).

## Modos

```bash
python agent_continuum.py            # lectura (recomendado en cron)
python agent_continuum.py --auto     # + dispatch autofix real
python agent_continuum.py --json     # digest máquina (ojo: el stdout
                                     # mezcla logs de core; el JSON
                                     # canónico está en el fichero)
```

Sin `--auto` nada externo se toca. Con `--auto`,
`AutoFixPipeline.dispatch_auto_fixes()` encola: **sin credenciales
Jules las tareas quedan en `dispatch_log.json` con estado `queued`**
(cola local, nada sale a la red); con credenciales, sigue el flujo
Jules existente. El digest registra `despachadas` + evidencias.

## Programarlo (cada noche 23:30)

```cron
30 23 * * * cd /ruta/a/aig && /ruta/a/.venv/bin/python agent_continuum.py >> data/sil/continuum_cron.log 2>&1
```

```powershell
schtasks /create /tn "Daniela Continuum" /tr "C:\ruta\aig\.venv\Scripts\python.exe C:\ruta\aig\agent_continuum.py" /sc daily /st 23:30
```

Termux: mismo comando vía `termux-job-scheduler` (los 5 agentes del
briefing corren en local; el LLM solo se usa si hay claves).

## Señales vistas en producción (2026-09-11)

- SR-05 (secret fallbacks) detectado recurrente dos días seguidos.
- Salud SIL 72→25 tras un review (15 findings): el digest lo marcó
  como deterioro con la serie del trend como evidencia.
- Scoreboard real: `swarm_live_ratio` 0.077 (1 live Ollama de 68 s
  + 12 simuladas), tokens estimados etiquetados.
