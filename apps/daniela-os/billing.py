#!/usr/bin/env python3
"""
gev.billing — Facturacion real expuesta por HTTP
===============================================================
Conecta `scripts/core/billing_system.py` con el visor de Daniela. La pieza clave es el
webhook de Stripe, que antes era un stub: decia "processed" y no tocaba la
base de datos. Ahora persiste de verdad y **falla cerrado** si no hay secreto.

Rutas:
  GET  /api/billing/planes           -> catalogo de planes (publico)
  GET  /api/billing/mrr              -> MRR y suscripciones (solo admin)
  POST /api/billing/stripe/webhook   -> eventos de Stripe (firma obligatoria)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_DIR = os.path.dirname(os.path.abspath(__file__))


def _raiz_repo() -> str:
    """Raíz por marcador.

    Este fichero vivía en `<repo>/aig/gev/`, donde dos `..` daban
    la raíz. Al mudarse a `<repo>/gev/`, los dos `..` dan el PADRE de la
    raíz: se metía en `sys.path` un directorio fuera del proyecto y
    `<repo>/../core` no existía.
    """
    aqui = Path(_DIR)
    for c in (aqui, *aqui.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return str(c)
    return os.path.dirname(_DIR)


_RAIZ = _raiz_repo()
for _p in (
    _RAIZ,
    os.path.join(_RAIZ, "core"),
    os.path.join(_RAIZ, "aig", "core"),
    os.path.join(_RAIZ, "scripts", "core"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _gestor():
    """Importa BillingManager de forma perezosa.

    `scripts.core.billing_system` ejecuta `init_billing_db()` al importarse, asi que
    no se importa a nivel de modulo para no crear la base de datos solo por
    arrancar el visor. El duplicado `daniela-os/billing_system.py` se borro en la
    ola de dedup: el canonico vive en `scripts/core/`.
    """
    from billing_system import STRIPE_WEBHOOK_SECRET, TIERS, BillingManager

    return BillingManager(), STRIPE_WEBHOOK_SECRET, TIERS


def planes() -> dict[str, Any]:
    """Catalogo de planes, sin filtrar secretos."""
    try:
        _, _, TIERS = _gestor()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"billing_system no importable: {e}"}
    return {
        "ok": True,
        "planes": [
            {
                "clave": k,
                "nombre": v.get("name", k),
                "precio_mes": v.get("price_monthly", 0),
                "precio_ano": v.get("price_yearly", 0),
                "peticiones_dia": v.get("daily_requests", 0),
                "concurrentes": v.get("concurrent_requests", 0),
                "caracteristicas": v.get("features", []),
            }
            for k, v in TIERS.items()
        ],
    }


def registrar_billing(app) -> None:
    """Registra las rutas de facturacion en `app`."""
    from flask import jsonify, request

    @app.route("/api/billing/planes")
    def billing_planes():
        d = planes()
        return jsonify(d), (200 if d.get("ok") else 503)

    @app.route("/api/billing/mrr")
    def billing_mrr():
        # Solo el admin ve los ingresos.
        try:
            # Se prefiere `core.access` para no cargar una segunda
            # copia del modulo (ver el mismo razonamiento en server.py). El
            # respaldo cubre el modo autonomo del visor Y el modulo aplanado
            # a la raiz (2026-09-29: `core/access.py` -> `access.py`).
            try:
                from core import access as acc
            except ModuleNotFoundError as e:
                falta = (e.name or "").split(".")
                if falta[0] != "aig" and not (
                    falta[0] == "core" and ".".join(falta) in ("core.access", "core")
                ):
                    raise
                import access as acc
            s = acc.sujeto_desde_request(request)
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": f"control de acceso no disponible: {e}"}), 500
        if not s.es_admin:
            return jsonify(
                acc.AccesoDenegado(
                    "solo el administrador ve la facturacion", f"rol={s.rol.value}"
                ).to_dict()
            ), 403

        try:
            gestor, _, _ = _gestor()
            return jsonify({"ok": True, **gestor.get_mrr()})
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)[:200]}), 503

    @app.route("/api/billing/stripe/webhook", methods=["POST"])
    def billing_stripe_webhook():
        try:
            gestor, secreto, _ = _gestor()
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": f"billing_system no importable: {e}"}), 503

        # Falla cerrado: sin secreto no se procesa NADA.
        if not secreto:
            return jsonify(
                {
                    "ok": False,
                    "error": "STRIPE_WEBHOOK_SECRET no configurado",
                    "nota": (
                        "Configura el secreto del endpoint de Stripe antes de "
                        "apuntar webhooks aqui. No se procesa nada sin firma."
                    ),
                }
            ), 503

        cuerpo = request.get_data() or b""
        firma = request.headers.get("Stripe-Signature", "")
        veredicto = gestor.verificar_firma_stripe(cuerpo, firma, secreto)
        if not veredicto.get("ok"):
            return jsonify(
                {"ok": False, "error": "firma_invalida", "motivo": veredicto.get("motivo")}
            ), 400

        try:
            evento = request.get_json(silent=True) or {}
        except Exception:  # noqa: BLE001
            return jsonify({"ok": False, "error": "cuerpo no es JSON"}), 400

        try:
            res = gestor.handle_stripe_webhook(evento)
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)[:200]}), 500
        return jsonify({"ok": True, **res})

    print("[Billing] rutas registradas en /api/billing/* (webhook Stripe con firma obligatoria)")
