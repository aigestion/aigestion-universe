---
name: gate
description: Quality gate for aig - run suite, compare failures by name vs baseline, GO/NO-GO verdict
version: 1.0.0
author: aig Team
tags: [testing, pytest, quality-gate, regression]
---

# aig Gate Skill

## Purpose
Single quality gate for every change: run the suite, compare failures **by test
name** (never by raw counts alone) against the vigente baseline in `handoff.md`,
and emit GO / NO-GO. For delegated runs use the `gatekeeper` agent.

## Gate Command
```bash
python3 -m pytest tests/ -q --tb=no \
  -p no:cacheprovider --continue-on-collection-errors
```

## Verdict Rules
| Condition | Verdict |
|---|---|
| 0 new FAILED/ERROR by name | **GO** |
| Any new failure by name | **NO-GO** — list names, do not commit |
| Fewer failures, rest identical | **GO (+bonus)** — name the fixed tests |
| skipped ±1 or error↔failed moves, same names | **GO** — report delta + cause |

## Traps
- Counts lie: collection errors shift totals. Always diff failure NAMES.
- `xfail(strict=False)` never fails the suite; an XPASS signals a rule got implemented.
- Missing optional deps (`daniela_os`, `piper-tts`, `sqlite-vec`) skip, they don't fail.
- `conftest.py` purges ambiguous modules (`server`, `analytics`); a test passing
  solo but failing in-suite smells like a `sys.modules` collision, not a regression.
