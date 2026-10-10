# Engine template (canonical skeleton)

New engines start here — never copy-paste an existing engine.

```
python engine/_template/new_engine.py <slug> <port>
# e.g. python engine/_template/new_engine.py billing 9920
```

It scaffolds `engine/<slug>/` (`__init__.py`, `server.py`, `Dockerfile`,
`requirements.txt`) with `{{slug}}`/`{{PORT}}` replaced. Then:

1. Implement domain modules next to `server.py`.
2. Add the service to `config/docker-compose.prod.yml` (copy the
   `intel-engine` block: build from repo root, `SERVICE_PORT`, healthcheck
   on `/api/<slug>/status`, memory limit).
3. Add the nginx `location /engine/<slug>/` block (variable + rewrite pattern).
4. Register the port in `scripts/core/ci_health_gate.py` if it must be probed.

Conventions (enforced by review, see `docs/CODE-REVIEW.md`):
- PORT only from `SERVICE_PORT` env. No `app.run(debug=True)`.
- `/api/<slug>/status` returns `{"status","service","version"}`.
- No `.db`/`.sqlite` files inside the engine dir (state goes to volumes).
- No `sys.path.insert` hacks: the image sets `PYTHONPATH=/app`.
