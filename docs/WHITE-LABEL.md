# White-Label in a Box (idea #12) — enterprise sin tocar su código

Un tenant = marca + auth + billing + stack compose propio, generado
por `scripts/deploy/tenant_bootstrap.py` sobre piezas existentes
(`white_label`, `auth_system`, `billing_system`, brand kit). Cero
cambios en el código del tenant: solo mounts + env.

## Alta (2 min)

```bash
python scripts/deploy/tenant_bootstrap.py crear --slug mi-gestoria \
  --brand-name "Mi Gestoria" --domain gestoria.example.com \
  --primary "#0ea5e9" --admin-email admin@example.com
# Imprime password y PIN UNA VEZ (aleatorios). Guárdalos fuera del repo.
python scripts/deploy/tenant_bootstrap.py estado --slug mi-gestoria
```

Crea `tenants/<slug>/` (DBs inicializadas, config, `.env`) +
`static/tenants/<slug>/` (brand.css + preview.html). Todo bajo
`tenants/` y `static/tenants/` va **ignorado por git**.

## Arrancar el stack del tenant

```powershell
$env:TENANT_SLUG="mi-gestoria"
$env:DANIELA_PIN="<pin del alta>"   # el PIN efectivo sale del shell:
                                    # compose prioriza environment: sobre env_file
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml config  # valida
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml -p mi-gestoria up -d --build
```

Las claves LLM salen del shell (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`);
el compose base ya las mapea.

## Qué monta el profile (`docker-compose.enterprise.yml`)

- `env_file: tenants/<slug>.env` + `TENANT_SLUG` en environment.
- Aislamiento por **ficheros pre-creados** (bind a path existente;
  nunca a paths que no existen): `daniela_vault.db`,
  `config.json` (copia la del repo), `memory_rag.db`,
  `auth.db`, `billing.db`, `whitelabel.db`,
  dirs `data/` y `content_output/`, marca en
  `static/tenants/<slug>/` (solo lectura).
- Redis compartido a propósito (caché volátil, sin datos en reposo).

## Límites honestos

- **Un tenant por stack** (`-p <slug>`). Multi-tenant en un stack
  exigiría rutas de DB configurables en el código (futuro).
- `static/` se comparte salvo `static/tenants/<slug>/`; los previews
  llevan el slug en el nombre.
- Sin `TENANT_SLUG` el `config` falla (`:?` en los mounts).
- El `version: 3.8` obsoleto del base lo advierte compose (ignorado,
  preexistente).
