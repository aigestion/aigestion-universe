# /aig-audit - Auditoría completa del monorepo

Ejecuta health checks, dependencias, seguridad, performance.

## Pasos
1. **Lint**: `python scripts/utils/ratchet_ruff.py` (techo 0)
2. **Tests**: `uv run pytest tests/ -q --tb=no -p no:cacheprovider --continue-on-collection-errors` vs baseline
3. **Deps**: `uv pip list --outdated` + `uv pip audit`
4. **Secrets**: `gitleaks detect --source . --verbose`
5. **Docker**: `docker compose -f config/docker/docker-compose.yml config --quiet`
6. **Android**: `cd daniela-os/android-app && ./gradlew :app:lintDebug` (si Gradle dispo)
7. **Config**: `opencode debug config`

## Veredicto
- **GO**: 0 fallos nuevos vs baseline, ruff 0, sin secretos, docker config OK
- **NO-GO**: cualquier fallo nuevo, ruff > 0, secretos, docker broken

## Output
Reporte en consola + `audit-$(date +%Y%m%d).md` en docs/