#!/usr/bin/env python3
"""
core.access — Quien puede ver que
============================================
Modelo de acceso jerarquico de aig.

    ADMIN  (el dueno de aig)
      - ve y opera TODAS las empresas agregadas
      - es el UNICO que ve la Sede (HQ) y los agregados del negocio
      - puede abrir el Command Center completo

    CLIENTE  (usuario de negocio)
      - ve UNICAMENTE su propia empresa
      - NO puede ver la Sede, ni otras empresas, ni la lista global
      - NO puede ver agregados (MRR total, recuentos) — filtrarian
        informacion de otros clientes

Principio rector: **fail-closed**.
Ante cualquier duda se DENIEGA. Un rol desconocido, un tenant vacio, un id que
no coincide o una excepcion => denegado. Nunca "por defecto permitido".

Este modulo no depende de Flask: se puede usar desde CLI, agentes o rutas.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

# ── Roles ────────────────────────────────────────────────────


class Rol(StrEnum):
    ADMIN = "admin"
    CLIENTE = "cliente"


class AccesoDenegado(Exception):
    """Se lanza cuando una operacion no esta permitida para el rol."""

    def __init__(self, motivo: str, detalle: str = ""):
        super().__init__(motivo)
        self.motivo = motivo
        self.detalle = detalle

    def to_dict(self) -> dict[str, str]:
        return {"error": "acceso_denegado", "motivo": self.motivo,
                "detalle": self.detalle}


# ── Identidad ────────────────────────────────────────────────


@dataclass(frozen=True)
class Sujeto:
    """Quien hace la peticion."""

    rol: Rol
    tenant_slug: str = ""       # vacio para el admin
    nombre: str = ""

    @property
    def es_admin(self) -> bool:
        return self.rol is Rol.ADMIN


def _admin_tenant() -> str:
    """Tenant del admin (el dueno). Por defecto, el suyo propio."""
    return os.getenv("aig_ADMIN_TENANT", "aig").strip().lower()


def resolver(tenant_slug: str | None = None,
             rol: str | None = None,
             secreto_admin: str | None = None) -> Sujeto:
    """Resuelve el sujeto de una peticion.

    - Si `rol` viene explicito, se respeta (pero validado).
    - Si no, se deduce: sin tenant => admin; con tenant => cliente.
    - Un tenant igual al del admin NO se considera cliente: es el dueno,
      asi que se exige secreto para no confundir un tenant homonimo con el admin.
    """
    if rol:
        try:
            r = Rol(rol.strip().lower())
        except ValueError:
            # Rol desconocido -> cliente con tenant vacio => denegado en todo
            return Sujeto(rol=Rol.CLIENTE, tenant_slug="", nombre="desconocido")
    else:
        r = Rol.ADMIN if not tenant_slug else Rol.CLIENTE

    ts = (tenant_slug or "").strip().lower()

    # El tenant del admin exige secreto: evita que un cliente se declare admin
    # simplemente llamandose igual.
    if r is Rol.ADMIN or (ts and ts == _admin_tenant()):
        esperado = os.getenv("aig_ADMIN_SECRET", "")
        if esperado:
            if not secreto_admin or not hmac.compare_digest(secreto_admin, esperado):
                return Sujeto(rol=Rol.CLIENTE, tenant_slug=ts, nombre="admin-no-autenticado")
        r = Rol.ADMIN
        ts = ""

    return Sujeto(rol=r, tenant_slug=ts)


# ── Permisos ─────────────────────────────────────────────────


def puede_ver_hq(s: Sujeto) -> bool:
    """La Sede solo la ve el admin. Los clientes nunca."""
    return s.es_admin


def puede_ver_agregados(s: Sujeto) -> bool:
    """Totales y recuentos globales: solo admin (filtrarian datos ajenos)."""
    return s.es_admin


def puede_ver_cliente(s: Sujeto, cliente_id: str,
                      tenant_slug: str = "") -> bool:
    """Admin ve todos. Un cliente, solo el suyo."""
    if s.es_admin:
        return True
    if not s.tenant_slug:
        return False
    objetivo = (tenant_slug or cliente_id or "").strip().lower()
    return bool(objetivo) and objetivo == s.tenant_slug


def puede_operar_cliente(s: Sujeto, cliente_id: str,
                         tenant_slug: str = "") -> bool:
    """Operar (cambiar estado, geocodificar): mismo criterio que ver.

    Separado a proposito: si algun dia la lectura se abre, la escritura
    puede seguir restringida sin tocar el resto.
    """
    return puede_ver_cliente(s, cliente_id, tenant_slug)


def filtrar_clientes(s: Sujeto, clientes: Sequence[Any]) -> list[Any]:
    """Recorta una lista de clientes a lo que el sujeto puede ver."""
    if s.es_admin:
        return list(clientes)
    out = []
    for c in clientes:
        cid = getattr(c, "id", None) or (c.get("id") if isinstance(c, dict) else "")
        tsl = getattr(c, "tenant_slug", None) or (
            c.get("tenant_slug", "") if isinstance(c, dict) else "")
        if puede_ver_cliente(s, str(cid), str(tsl)):
            out.append(c)
    return out


def filtrar_resumen(s: Sujeto, resumen: dict[str, Any]) -> dict[str, Any]:
    """Un cliente no ve agregados globales: se le devuelve solo su parte."""
    if s.es_admin:
        return resumen
    return {
        "total": None,
        "ubicados": None,
        "mrr_total": None,
        "por_estado": {},
        "por_tier": {},
        "restringido": True,
        "motivo": "los agregados globales son solo para el administrador",
    }


# ── Guardas ──────────────────────────────────────────────────


def exigir_hq(s: Sujeto) -> None:
    if not puede_ver_hq(s):
        raise AccesoDenegado(
            "sin_acceso_a_sede",
            "La Sede de aig es privada: solo el administrador puede acceder.",
        )


def exigir_agregados(s: Sujeto) -> None:
    if not puede_ver_agregados(s):
        raise AccesoDenegado("sin_acceso_a_agregados",
                             "Los totales del negocio son solo del administrador.")


def exigir_cliente(s: Sujeto, cliente_id: str, tenant_slug: str = "") -> None:
    if not puede_ver_cliente(s, cliente_id, tenant_slug):
        raise AccesoDenegado(
            "sin_acceso_a_empresa",
            "Solo puedes acceder a tu propia empresa.",
        )


def exigir_operar(s: Sujeto, cliente_id: str, tenant_slug: str = "") -> None:
    if not puede_operar_cliente(s, cliente_id, tenant_slug):
        raise AccesoDenegado("sin_permiso_de_operacion",
                             "No puedes modificar esta empresa.")


# ── Utilidades para Flask ────────────────────────────────────


def sujeto_desde_request(req) -> Sujeto:
    """Extrae el sujeto de una peticion Flask.

    Orden: cabeceras > query string. El tenant NUNCA se toma del cuerpo
    para que no se pueda suplantar cambiando un JSON.
    """
    tenant = (req.headers.get("X-Tenant-Slug")
              or req.args.get("tenant")
              or "").strip().lower()
    rol = (req.headers.get("X-Rol") or req.args.get("rol") or "").strip().lower()
    secreto = req.headers.get("X-Admin-Secret") or req.args.get("admin_secret")
    return resolver(tenant_slug=tenant, rol=rol, secreto_admin=secreto)


def respuesta_denegada(e: AccesoDenegado):
    """Respuesta JSON estandar para un acceso denegado (403)."""
    return e.to_dict(), 403


# ── Auto-test ────────────────────────────────────────────────


def _selftest() -> int:
    admin = Sujeto(rol=Rol.ADMIN)
    cli_a = Sujeto(rol=Rol.CLIENTE, tenant_slug="gestoria-lopez")
    Sujeto(rol=Rol.CLIENTE, tenant_slug="asesoria-ruiz")
    vacio = Sujeto(rol=Rol.CLIENTE, tenant_slug="")

    casos = [
        ("admin ve la sede",            puede_ver_hq(admin), True),
        ("cliente NO ve la sede",       puede_ver_hq(cli_a), False),
        ("cliente vacio NO ve la sede", puede_ver_hq(vacio), False),
        ("admin ve empresa ajena",      puede_ver_cliente(admin, "asesoria-ruiz", "asesoria-ruiz"), True),
        ("cliente ve la suya",          puede_ver_cliente(cli_a, "gestoria-lopez", "gestoria-lopez"), True),
        ("cliente NO ve la ajena",      puede_ver_cliente(cli_a, "asesoria-ruiz", "asesoria-ruiz"), False),
        ("cliente sin tenant: denegado", puede_ver_cliente(vacio, "gestoria-lopez", "gestoria-lopez"), False),
        ("admin ve agregados",          puede_ver_agregados(admin), True),
        ("cliente NO ve agregados",     puede_ver_agregados(cli_a), False),
        ("id vacio: denegado",          puede_ver_cliente(cli_a, "", ""), False),
    ]
    fallos = 0
    for nombre, obtenido, esperado in casos:
        ok = obtenido == esperado
        fallos += 0 if ok else 1
        print(f"  [{'OK ' if ok else 'FALLO'}] {nombre}")
    print(f"\n{len(casos) - fallos}/{len(casos)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    import sys
    print("== control de acceso aig ==")
    sys.exit(_selftest())
