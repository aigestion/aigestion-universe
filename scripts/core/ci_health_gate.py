"""Health gate for the deployed AIG services. Stdlib only.

Checks each service's status endpoint and reports the percent healthy.
Exit 0 when percent >= --fail-under, else exit 1.

Usage:
    python scripts/core/ci_health_gate.py --base-url http://localhost --fail-under 95
    python scripts/core/ci_health_gate.py http://localhost --fail-under 100 --only intel_engine,auto_engine
    python scripts/core/ci_health_gate.py --base-url http://localhost --json
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

# Services that docker-compose.prod.yml REALLY deploys: (name, port, path).
# 2026-09-23: fuera epic_pc/optimization/frontend/dashboard (retirados por
# diseno) y regions (multi-region es simulacion, no se despliega). Dentro
# gateway + orchestrator (cross_engine en :8080/:9900) y chaos_engine
# (anadido a prod el mismo dia).
ENGINES = [
    {"name": "daniela", "port": 9200, "path": "/api/status"},
    {"name": "hermes", "port": 9300, "path": "/api/status"},
    {"name": "infra_opt", "port": 9700, "path": "/api/infra/status"},
    {"name": "agent_mobile", "port": 9800, "path": "/api/agent/status"},
    {"name": "security", "port": 9999, "path": "/api/secure/status"},
    {"name": "perf", "port": 9998, "path": "/api/perf/status"},
    # cross responde 200 con mapa (health_score/engines) pero sin campo
    # `status`: el mecanismo status_key=None lo declara (200+dict = vivo).
    {"name": "gateway", "port": 8080, "path": "/api/cross/status", "status_key": None},
    {
        "name": "orchestrator",
        "port": 9900,
        "path": "/api/cross/status",
        "status_key": None,
    },
    {"name": "intel_engine", "port": 9850, "path": "/api/intel/status"},
    {"name": "auto_engine", "port": 9860, "path": "/api/auto/status"},
    {"name": "data_engine", "port": 9870, "path": "/api/data/status"},
    {"name": "secure_engine", "port": 9880, "path": "/api/secure_engine/status"},
    {"name": "devtools_engine", "port": 9890, "path": "/api/devtools/status"},
    {"name": "ecosystem_engine", "port": 9840, "path": "/api/ecosystem/status"},
    {"name": "ux_engine", "port": 9830, "path": "/api/ux/status"},
    {"name": "scale_engine", "port": 9820, "path": "/api/scale/status"},
    {"name": "chaos_engine", "port": 9910, "path": "/api/chaos/status"},
    {"name": "brand_studio", "port": 9920, "path": "/api/brand/status"},
]

HEALTHY_STATUSES = {
    # 🔴 Vocabulario MEDIDO el 2026-09-18 contra los motores reales:
    #    alive x10, ok x3, running x5, active x1, operational x1.
    # La lista anterior era {"alive","online","active"}: dejaba fuera
    # `running` (5 motores) y `operational` (1) -> **6 motores sanos
    # reportados como CAIDOS**. Un gate que miente no sirve para decidir.
    "alive",
    "online",
    "active",
    "ok",
    "running",
    "operational",
    "ready",
    "healthy",
    "up",
}

# Hosts que son "esta misma maquina" -> nunca deben pasar por un proxy.
_HOSTS_LOCALES = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "[::1]"}


def es_base_local(base_url):
    """True si `base_url` apunta a la propia maquina."""
    try:
        host = urllib.parse.urlsplit(str(base_url)).hostname or ""
    except ValueError:
        return False
    host = host.lower()
    return host in _HOSTS_LOCALES or host.endswith((".localhost", ".local"))


def instalar_opener_sin_proxy():
    """Hace que `urlopen()` ignore `HTTP_PROXY`/`HTTPS_PROXY`.

    🔴 Por que existe esto (medido el 2026-09-18). En este PC hay
    `HTTP_PROXY=http://127.0.0.1:15765` puesto en el entorno, y `urllib` respeta
    esas variables. Consecuencia medida sobre el puerto 8082:

        con proxy -> HTTP 502   |   sin proxy -> 000 (conexion rechazada)

    Es decir: **el proxy convierte "no hay nadie escuchando" en un 502**, que
    parece un fallo del gateway en vez de un servicio caido. Ocultar la causa
    real es exactamente lo que este gate existe para evitar. Para una URL local
    el proxy no aporta nada, asi que se desactiva.
    """
    urllib.request.install_opener(
        urllib.request.build_opener(urllib.request.ProxyHandler({}))
    )


def build_url(base_url, engine):
    """Build the full status URL for an engine.

    base_url is normally a host like http://localhost; the engine port
    and path are appended. If base_url already ends with an explicit
    port (e.g. http://host:5020), the path is appended directly.
    """
    base = base_url.rstrip("/")
    tail = base.rsplit(":", 1)[-1].split("/", 1)[0]
    if tail.isdigit():
        return "{}{}".format(base, engine["path"])
    return "{}:{}{}".format(base, engine["port"], engine["path"])


def check_engine(base_url, engine, timeout=4):
    """GET one engine status endpoint. Return a result dict."""
    url = build_url(base_url, engine)
    result = {
        "name": engine["name"],
        "port": engine["port"],
        "path": engine["path"],
        "url": url,
        "healthy": False,
        "status_code": None,
        "status": None,
        "error": None,
    }
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["status_code"] = getattr(resp, "status", 200)
            raw = resp.read()
            try:
                payload = json.loads(
                    raw.decode("utf-8") if isinstance(raw, bytes) else raw
                )
            except (ValueError, UnicodeDecodeError) as exc:
                result["error"] = f"invalid-json: {exc}"
                return result
            clave = engine.get("status_key", "status")
            if clave is None:
                # Motor sin campo `status` (reserva para respuestas tipo
                # failover/matrix). Un 200 con objeto JSON cuenta como vivo.
                result["status"] = "n/a"
                if (
                    result["status_code"] == 200
                    and isinstance(payload, dict)
                    and payload
                ):
                    result["healthy"] = True
                else:
                    result["error"] = "respuesta-sin-estado: http {}".format(
                        result["status_code"]
                    )
                return result
            status_value = payload.get(clave) if isinstance(payload, dict) else None
            result["status"] = status_value
            if (
                result["status_code"] == 200
                and str(status_value).lower() in HEALTHY_STATUSES
            ):
                result["healthy"] = True
            else:
                result["error"] = "unexpected-status: {!r} (http {})".format(
                    status_value, result["status_code"]
                )
    except urllib.error.HTTPError as exc:
        result["status_code"] = exc.code
        result["error"] = f"http-error: {exc.code}"
    except Exception as exc:  # noqa: BLE001 - timeouts, connection refused, DNS, etc.
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def check(base_url, timeout=4, only=None, noproxy=None):
    """Check all (or a subset of) engines. Returns a list of result dicts.

    `noproxy`: None (por defecto) = decidir solo; True = ignorar el proxy del
    entorno; False = usarlo. Con `base_url` local se desactiva automaticamente
    (ver `instalar_opener_sin_proxy`).
    """
    if noproxy is None:
        noproxy = es_base_local(base_url)
    if noproxy:
        instalar_opener_sin_proxy()
    selected = ENGINES
    if only:
        wanted = {name.strip() for name in only if name.strip()}
        selected = [e for e in ENGINES if e["name"] in wanted]
    return [check_engine(base_url, engine, timeout=timeout) for engine in selected]


def summarize(results, fail_under=95.0, base_url=None):
    """Build the JSON-serializable summary dict."""
    total = len(results)
    healthy = sum(1 for r in results if r.get("healthy"))
    unhealthy = total - healthy
    percent = round((healthy / total * 100.0) if total else 0.0, 2)
    passed = percent >= fail_under
    return {
        "base_url": base_url,
        "total": total,
        "healthy": healthy,
        "unhealthy": unhealthy,
        "percent": percent,
        "fail_under": fail_under,
        "passed": passed,
        "results": results,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="AIG 21-engine health gate (stdlib only)."
    )
    parser.add_argument("base_url", nargs="?", default="http://localhost")
    parser.add_argument("--base-url", dest="base_url_opt", default=None)
    parser.add_argument("--fail-under", dest="fail_under", type=float, default=95.0)
    parser.add_argument("--timeout", type=float, default=4.0)
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated engine names to check (default: all 21).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON summary (default output is already JSON).",
    )
    proxy = parser.add_mutually_exclusive_group()
    proxy.add_argument(
        "--noproxy",
        dest="noproxy",
        action="store_true",
        default=None,
        help="Ignore HTTP_PROXY/HTTPS_PROXY (default: auto for localhost).",
    )
    proxy.add_argument(
        "--proxy",
        dest="noproxy",
        action="store_false",
        help="Force use of the environment proxy.",
    )
    args = parser.parse_args(argv)
    base_url = args.base_url_opt or args.base_url
    only = [n.strip() for n in args.only.split(",")] if args.only else None
    return base_url, args.fail_under, args.timeout, only, args.noproxy


def main(
    argv=None, base_url=None, fail_under=95.0, timeout=4.0, only=None, noproxy=None
):
    """Entry point. Prints JSON summary, returns exit code (0 pass / 1 fail).

    Dos formas de llamada:

    * **CLI real** (argv=None): se parsea `sys.argv`. Los valores de la linea de
      comandos MANDAN, incluidos `--only` y `--fail-under`.
    * **Programatica**: se pasa `base_url` (y opcionalmente fail_under/timeout/only);
      en ese caso no se toca `sys.argv`.

    🔴 BUG ARREGLADO EL 2026-09-17 (causa del CD en rojo). La version anterior era:

        if argv is not None or base_url is None:
            parsed_base, parsed_fail, parsed_timeout, parsed_only = parse_args(argv)
            base_url = parsed_base if base_url is None else base_url
        else:
            ...
        if argv is None and base_url is not None:      # <-- SIEMPRE cierto por CLI
            parsed_fail, parsed_timeout, parsed_only = fail_under, timeout, only
            parsed_base = base_url

    En el camino CLI, `argv` es None y la primera rama ya habia dejado `base_url`
    con valor -> la segunda condicion tambien se cumplia -> **machacaba lo que se
    acababa de parsear con los DEFAULTS**. Resultado: `--only` se descartaba
    (se comprobaban los 21 engines en vez del smoke subset) y `--fail-under 100`
    volvia a 95.0. Por eso `cd-21.yml` fallaba con "Connection refused" en
    ux_engine/scale_engine/chaos_engine/regions: servicios que el paso de deploy
    nunca arranca. Medido con un repro antes de tocar nada.

    Nota de cobertura: los tests 8 y 15 pasaban `argv=[...]` EXPLICITAMENTE, y con
    argv explicito la condicion `argv is None` era False -> el bug no se disparaba
    y la suite salia verde. Ver `test_cli_path_honors_only_and_fail_under`.
    """
    if base_url is None:
        # Camino CLI: parsear sys.argv (o el argv explicito si lo hay).
        base_url, fail_under, timeout, only, noproxy = parse_args(argv)
    results = check(base_url, timeout=timeout, only=only, noproxy=noproxy)
    summary = summarize(results, fail_under=fail_under, base_url=base_url)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
