# `docs/archive/` — archivado versionado

Directorio versionado **a proposito**. `.gitignore` tiene un patron
`archive/` (sin barra inicial, pensado para `<raiz>/archives/`, que guarda
`.env` de backup y `credentials.json`): ese patron casa con **cualquier**
directorio llamado `archive`, incluido este. La negacion `!docs/archive/`
(va DESPUES del patron `archive/`) es lo que permite que git lo siga
versionando.

Guardias que lo vigilan:

- `tests/core/test_punto_de_entrada.py::test_el_archivado_de_workflows_no_esta_ignorado_por_git`
- `tests/core/test_punto_de_entrada.py::test_archives_sigue_ignorado_para_no_filtrar_credenciales`

## `workflows/`

Los cuatro workflows de GitHub Actions que traia `origin/main` (2026-09-29).
Se archivan —no se borran— por una decision del dueno ya vigente en el repo
desde el 2026-09-23: **Actions esta desactivado a nivel de repo y no se
facturan minutos de GitHub**. La decision es ejecutable y esta tutelada por
`tests/core/test_deploy_honesto.py::test_no_quedan_workflows`, que exige que
`.github/workflows/` este vacio.

Tenian un conflicto ademas con el propio repositorio: `ci.yml` ejecutaba
`pytest` + `ruff` en cada push, mientras `tests/core/test_deploy_honesto.py`
prohibia que existiera ningun workflow. Las dos reglas no pueden cumplirse a
la vez; gana la mas reciente y la del dueno (2026-09-23).

Si un dia se reactivan Actions, hay que:
1. moverlos de vuelta a `.github/workflows/`,
2. adaptar `test_no_quedan_workflows` (ver su historial),
3. comprobar `tests/core/test_referencias_integridad.py::test_rutas_de_workflow_existen`
   (hoy `free-model-ci.yml` cita `config/docker-compose.observability.yml`,
   que no existe: esta en la raiz, `docker-compose.observability.yml`).
