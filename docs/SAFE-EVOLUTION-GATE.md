# Safe Evolution Gate (idea #9) — main solo en verde

Ningún cambio de autofix/SIL toca `main` sin pasar por rama + gate.
Tres piezas: el gate, el autofix en rama y el hook pre-push.

## El gate (`aig/sil/safe_gate.py`)

Reutiliza los trabajos **cerrados** de `ci_runner` (nada externo):

| Nivel | Trabajos | Uso | Coste |
|-------|----------|-----|-------|
| quick | sintaxis, seguridad, ruff | pre-push, ramas autofix | ~5 s |
| full | + arranque, mypy, pytest | fusión a main | minutos |

```bash
python safe_gate.py check [--full]      # evalúa el checkout actual
python safe_gate.py fusionar <rama>     # fusiona a main SOLO en verde
```

`fusionar_si_verde`: exige árbol limpio, checkout de la rama, gate,
vuelta a main y `merge --no-ff`. Cualquier fallo aborta **sin
fusionar** (conflicto → `merge --abort` + vuelta a la rama origen).
Nunca lanza excepción: devuelve dict honesto.

Sin rutas HTTP a propósito: el gate opera sobre estado git
(ramas, diffs); dispararlo por red al repo de producción sería un
footgun. Se ejecuta donde está el código: hooks y autofix.

## Autofix en rama (`autofix_engine.test_and_apply_fix`)

Antes: parche + `git add/commit` **en la rama actual** (main en
producción). Ahora:

1. Árbol sucio → revertir parche, nada commiteado.
2. `checkout -b autofix/<fich>-<ts>` → parche → commit **ahí**.
3. Gate quick sobre la rama → vuelta a la rama original.
4. Verde + `merge_if_green=True` → fusión; si no, la rama queda
   para revisión con el reporte (`safe_gate.py fusionar <rama>`).

Firma compatible: `test_and_apply_fix(fich, codigo,
rama_auto=True, merge_if_green=False)`.

## Hook pre-push (`githooks/`)

```bash
git config core.hooksPath githooks   # config LOCAL del repo
```

El hook corre el gate quick y bloquea el push en rojo. Sin `python`
en PATH avisa y permite (fail-open documentado: el hook nunca debe
dejar un equipo sin pushear por toolchain).

## Limpieza de seguridad previa (gate en verde hoy)

El gate estaba en rojo por 4 llamadas reales (no tests):

| Fichero | Hallazgo | Fix |
|---------|----------|-----|
| `server.py:88` | **RCE por chat** (`cmd:` → `check_output(shell=True)` en Flask 0.0.0.0:8082) | rama neutralizada: registra intento y niega |
| `server.py:73` | `Popen("sync", shell=True)` (no-op en Windows) | línea eliminada |
| `swarm_planner.py:47` | shell con comandos de SQLite elegidos por LLM (RCE en cadena) | `safe_exec.run_cmd` sin shell |
| `nightly_maintenance.py:4` | `os.system(powershell...)` | `run_cmd` por lista |

Excluidos a propósito (documentados, no olvidados): `platform.system()`
(falso positivo conocido, el job lo filtra), probes `zeroconf` con
`noqa`, imports con `try/except` de disponibilidad.
