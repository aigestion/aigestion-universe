## What / Why

<!-- One paragraph: what changes and why. Link issue if any. -->

## Type

- [ ] fix
- [ ] feat
- [ ] refactor / chore
- [ ] docs / tests only

## Risk & scope

- Size: <!-- XS/S/M/L/XL per docs/CODE-REVIEW.md §5 -->
- Risk areas: <!-- auth / migrations / prod compose / secrets / none -->
- [ ] Single concern (no drive-by refactors)

## Test evidence

<!-- Paste or describe: pytest result, manual verification, endpoints hit.
For bugfixes: how do we know the regression test fails without the fix? -->

```
# paste relevant output
```

## Author checklist (docs/CODE-REVIEW.md §3)

- [ ] New behavior covered by tests (bugfix has regression test)
- [ ] No secrets, `.env` dumps, `.db`, or PII in diff
- [ ] Local gates green: `ruff check` + `ruff format --check` (changed files),
      `pytest tests/`
- [ ] Ratchet not worsened (`.quality-baseline/ruff-count.txt`)
- [ ] Service/port/env changes reflected in `config/docker-compose*.yml`,
      `nginx.conf`, docs (if applicable)

## Self-review notes (solo-dev: fill per §9)

<!-- Risky change? Reviewed with 24h gap? Anything you want a future
reviewer (or future-you) to double-check? -->
