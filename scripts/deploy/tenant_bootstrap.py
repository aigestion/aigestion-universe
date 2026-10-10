#!/usr/bin/env python3
"""White-Label in a Box (idea #12) — alta de tenant sin tocar su codigo.

Crea todo lo que el profile enterprise espera bajo tenants/<slug>/:
  brand (CSS+preview) + white-label config + admin auth (enterprise,
  admin) + suscripcion enterprise + .env + DBs inicializadas +
  config.json + dirs data/content_output.

Todo es local (SQLite) y reversible (borrar tenants/<slug>/).
tenants/ esta en .gitignore: aqui viven secretos (PIN, password).

Uso:
  python scripts/deploy/tenant_bootstrap.py crear --slug mi-gestoria --brand-name "Mi Gestoria" --domain gestoria.example.com --admin-email admin@example.com
  python scripts/deploy/tenant_bootstrap.py estado --slug mi-gestoria
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
# `white_label` (core/white_label.py) se importa con nombre pelado mas abajo.
# Sin esta ruta el script fallaba con ModuleNotFoundError en `estado` y en
# `crear`: nunca habia funcionado.
sys.path.insert(0, str(REPO_ROOT / "core"))
TENANTS_DIR = REPO_ROOT / "tenants"

# El calculo de arriba tiene que coincidir con la fuente de verdad del repo
# (core/paths.py). Antes era parents[1], que resolvia a <repo>/scripts:
# los tenants se habrian creado en scripts/tenants y los imports del core
# habrian fallado. Se comprueba en vez de confiar.
try:
    from paths import REPO_ROOT as _RAIZ_CANONICA
    # En Windows `Path` distingue mayusculas y formas de normalizar, asi que se
    # comparan rutas normalizadas (normcase) en vez de objetos Path.
    if os.path.normcase(str(_RAIZ_CANONICA)) != os.path.normcase(str(REPO_ROOT)):
        raise RuntimeError(
            f"REPO_ROOT incoherente: este script dice {REPO_ROOT}, "
            f"core/paths.py dice {_RAIZ_CANONICA}"
        )
except ImportError:
    pass   # aig no importable: seguimos con el calculo local

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$")

DB_FILES = ("daniela_vault.db", "memory_rag.db", "aig_auth.db",
            "billing.db", "aig_whitelabel.db")


@contextmanager
def _en_tenant(tdir: Path):
    """Los modulos abren DBs por nombre relativo: todo lo que toque
    SQLite del tenant corre con cwd=tenant. Restaura al salir."""
    cwd = Path.cwd()
    os.chdir(tdir)
    try:
        yield
    finally:
        os.chdir(cwd)


def _slug_valido(slug: str) -> bool:
    return bool(SLUG_RE.match(slug or ""))


def _tenant_dir(slug: str) -> Path:
    return TENANTS_DIR / slug


def crear(args: argparse.Namespace) -> int:
    import auth_system
    import billing_system
    import white_label

    slug = args.slug
    if not _slug_valido(slug):
        print("slug invalido: minusculas, numeros y guiones (3-32)")
        return 1
    tdir = _tenant_dir(slug)
    if tdir.exists():
        print(f"el tenant {slug} ya existe ({tdir})")
        return 1
    tdir.mkdir(parents=True)
    (tdir / "data").mkdir()
    (tdir / "content_output").mkdir()

    user_id = f"tenant-{slug}"
    config = {
        "brand_name": args.brand_name, "domain": args.domain,
        "primary_color": args.primary, "secondary_color": args.secondary,
        "ai_name": args.ai_name,
        "logo_url": args.logo or "",
    }

    # 1. Marca: CSS + preview HTML del tenant (tras crear su config,
    # porque generate_branded_* espera el objeto WhiteLabelConfig).
    marca_dir = REPO_ROOT / "static" / "tenants" / slug
    marca_dir.mkdir(parents=True, exist_ok=True)

    # 2-5. Todo SQLite del tenant con cwd=tenant (los modulos usan
    # nombres relativos): inits + config + admin + suscripcion.
    for db in DB_FILES:
        (tdir / db).touch(exist_ok=True)
    with _en_tenant(tdir):
        auth_system.init_auth_db()
        billing_system.init_billing_db()
        white_label.init_db()

        wl = white_label.WhiteLabelManager()
        wl_cfg = wl.create_config(user_id, config)
        cfg_obj = wl.get_config(user_id)
        css = wl.generate_branded_css(cfg_obj)
        html = wl.generate_branded_html(cfg_obj)

        password = secrets.token_urlsafe(12)
        auth = auth_system.AuthManager()
        reg = auth.register_local(args.admin_email, password, args.brand_name)
        if not reg.get("success"):
            print(f"auth fallo: {reg.get('error')}")
            return 1
        uid = reg.get("user_id") or ""
        try:
            auth.update_user_tier(uid, "enterprise")
        except Exception as e:
            print(f"aviso: tier no actualizado ({e})")
        if uid:
            con = sqlite3.connect("aig_auth.db")
            try:
                con.execute("UPDATE users SET role = 'admin' WHERE id = ?", (uid,))
                con.commit()
            finally:
                con.close()

        sub = billing_system.BillingManager().create_subscription(
            uid, "enterprise", "monthly", "stripe")

    (marca_dir / "brand.css").write_text(css, encoding="utf-8")
    (marca_dir / "preview.html").write_text(html, encoding="utf-8")

    pin = f"{secrets.randbelow(900000) + 100000}"
    # NOTE: compose da prioridad a `environment:` sobre env_file, y a .env
    # sobre nada: el PIN efectivo al lanzar sale del SHELL. Este fichero
    # es el registro (ignorado por git); exportalo al arrancar:
    #   $env:DANIELA_PIN="<pin>"; $env:TENANT_SLUG="<slug>"
    (TENANTS_DIR / f"{slug}.env").write_text(
        f"# Tenant {slug} — generado {datetime.now():%Y-%m-%d %H:%M} (NO versionar)\n"
        f"TENANT_SLUG={slug}\nTENANT_DOMAIN={args.domain}\n"
        f"DANIELA_PIN={pin}  # exportar al shell al lanzar (ver docs/WHITE-LABEL.md)\n",
        encoding="utf-8")

    # La base canonica es `daniela-os/config.json`. Antes se buscaba un
    # `aig_config.json` en la RAIZ, que no existe en ningun checkout: todos
    # los tenants recien creados se quedan con un {"version": "1.0.0"} sin
    # ningun modulo activated.
    base_cfg = REPO_ROOT / "daniela-os" / "config.json"
    destino_cfg = tdir / "config.json"
    if base_cfg.exists():
        shutil.copy(base_cfg, destino_cfg)
    else:
        destino_cfg.write_text('{"version": "1.0.0"}', encoding="utf-8")

    print(json.dumps({
        "ok": True, "slug": slug, "dir": str(tdir),
        "whitelabel_config": wl_cfg.get("config_id") if isinstance(wl_cfg, dict) else wl_cfg,
        "admin": {"email": args.admin_email, "user_id": uid,
                  "password_UNA_VEZ": password, "tier": "enterprise", "role": "admin"},
        "pin_UNA_VEZ": pin,
        "subscription": sub.get("subscription_id") if isinstance(sub, dict) else sub,
        "marca": [str(marca_dir / "brand.css"), str(marca_dir / "preview.html")],
        "siguiente": (f"TENANT_SLUG={slug} docker-compose --project-directory . "
                      f"-f config/docker-compose.yml "
                      f"-f config/docker-compose.enterprise.yml config"),
    }, indent=2, ensure_ascii=False))
    return 0


def estado(args: argparse.Namespace) -> int:
    import white_label

    slug = args.slug
    tdir = _tenant_dir(slug)
    if not tdir.exists():
        print(f"no existe tenants/{slug}")
        return 1
    with _en_tenant(tdir):
        cfg = white_label.WhiteLabelManager().get_config(f"tenant-{slug}")
    print(json.dumps({
        "slug": slug, "dir": str(tdir),
        "ficheros": sorted(p.name for p in tdir.iterdir()),
        "whitelabel": bool(cfg),
        "env": (TENANTS_DIR / f"{slug}.env").exists(),
    }, indent=2, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="White-Label in a Box")
    sub = parser.add_subparsers(dest="cmd")

    p_c = sub.add_parser("crear", help="Alta de tenant")
    p_c.add_argument("--slug", required=True)
    p_c.add_argument("--brand-name", default="Mi Gestoria")
    p_c.add_argument("--domain", default="")
    p_c.add_argument("--primary", default="#0ea5e9")
    p_c.add_argument("--secondary", default="#8b5cf6")
    p_c.add_argument("--ai-name", default="Daniela")
    p_c.add_argument("--logo", default="")
    p_c.add_argument("--admin-email", required=True)

    p_e = sub.add_parser("estado", help="Estado de un tenant")
    p_e.add_argument("--slug", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "crear":
        return crear(args)
    if args.cmd == "estado":
        return estado(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

