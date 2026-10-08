#!/usr/bin/env python3
"""
gev.memoria — la memoria de Daniela, en los DOS sentidos
=============================================================
`/api/globe/memoria` es la puerta de la memoria de Daniela vista desde el
visor. No es una base nueva: es **`agents/memory_vault.py`** (SQLite + grafo),
la misma que usa el Command Center (`/api/cc/astra`) y la que el chat escribe
con la herramienta `memoria_guardar`. Una sola memoria, tres bocas.

Por que HTTP y no solo el chat: God's Eye es una PANTALLA de Daniela, y una
pantalla que solo cuenta lo que hay no es integracion. Desde aqui el visor
PUEDE leer (¿que recuerdas de esto?) y PUEDE escribir (apuntalo), y las dos
direcciones pasan por la misma autorizacion.

  GET    /api/globe/memoria[?q=...]  stats + recuerdos (por consulta o recientes)
  POST   /api/globe/memoria          guardar un recuerdo        (solo admin)
  DELETE /api/globe/memoria/<id>     olvidar un recuerdo        (solo admin)

Autorizacion (igual que el resto del visor: rol REAL del request, nunca lo
que el cuerpo diga ser):

  La memoria es GLOBAL: no hay tenant en `rag_docs`, asi que un recuerdo puede
  mezclar datos de varios clientes. Leeria y escribiria datos ajenos quien no
  sea el dueno, asi que **lectura y escritura son solo-administrador** mientras
  la memoria no lleve `tenant`. Si un dia se etiqueta por tenant, la lectura se
  abre al cliente *con su filtro puesto*; hasta entonces, decir que no.

Registro (convencion del visor, en `server.register_gev_routes`):

    from gev.memoria import registrar_memoria
    registrar_memoria(app)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent


def _raiz_repo() -> Path:
    """Raíz por marcador (mismo criterio que `billing.py` y `command_center.py`).

    Con `_DIR.parent` basta: `gev/` esta en la raiz. El bucle sobre
    padres aguanta que el paquete se mude dentro de `aig/` otra vez.
    """
    for c in (_DIR, *_DIR.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return c
    return _DIR.parent


_RAIZ = _raiz_repo()
for _p in (str(_RAIZ), str(_RAIZ / "core"), str(_RAIZ / "aig")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# El modulo de acceso es el MISMO que usa el resto de aig (`core.access`
# si existe el paquete, `access.py` aplanado a la raiz si no).
try:
    import core.access as acc  # type: ignore
except ModuleNotFoundError:
    import access as acc  # type: ignore


# ── La memoria ───────────────────────────────────────────────

_VAULT: Any = None


def vault():
    """`MemoryVault` unico del visor. Perezooso: no abre la base al importar.

    `fijar_vault()` lo sustituye en los tests (base en `tmp_path`): un test que
    tocase `memory_rag.db` de produccion estaria escribiendo memoria real.
    """
    global _VAULT
    if _VAULT is None:
        from agents.memory.memory_vault import MemoryVault

        _VAULT = MemoryVault()
    return _VAULT


def fijar_vault(v: Any) -> Any:
    """Cambia el vault (devuelve el anterior). Para tests y para CLI."""
    global _VAULT
    anterior, _VAULT = _VAULT, v
    return anterior


_LIMITE_CONTENIDO = 4000  # un recuerdo es una nota, no un archivo
_LIMITE_FUENTE = 80


def _rol(s) -> str:
    return getattr(getattr(s, "rol", None), "value", str(getattr(s, "rol", "?")))


def registrar_memoria(app) -> None:
    """Registra `/api/globe/memoria` en una app Flask de Daniela."""
    from flask import jsonify, request

    def _solo_admin():
        """El sujeto real de la peticion, o `None` si no puede.

        Devuelve la respuesta ya montada como tupla `(json, 403)`: si se
        devuelve suelta, Flask la responderia con 200 y el cliente creeria
        que lo denegado habia salido bien.
        """
        s = acc.sujeto_desde_request(request)
        if not s.es_admin:
            return None, (
                jsonify(
                    acc.AccesoDenegado(
                        "la memoria de Daniela es global (sin filtro por tenant): "
                        "solo el administrador puede leerla o escribirla",
                        f"rol={_rol(s)}",
                    ).to_dict()
                ),
                403,
            )
        return s, None

    @app.route("/api/globe/memoria", methods=["GET"])
    def globe_memoria_leer():
        """Recuerdos: los que coinciden con `q`, o los ultimos si no hay `q`."""
        s, denegada = _solo_admin()
        if s is None:
            return denegada
        try:
            q = (request.args.get("q") or "").strip()
            try:
                top = int(request.args.get("top", 10))
            except (TypeError, ValueError):
                top = 10
            top = max(1, min(top, 50))

            v = vault()
            st = v.stats()
            recuerdos = v.recall(q, top_k=top) if q else v.recientes(limite=top)
            return jsonify(
                {
                    "ok": True,
                    "q": q,
                    "rol": _rol(s),
                    "n": len(recuerdos),
                    "recuerdos": recuerdos,
                    "stats": st,
                    "nota": "" if q else "sin consulta: los ultimos recuerdos",
                }
            )
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)[:200]}), 500

    @app.route("/api/globe/memoria", methods=["POST"])
    def globe_memoria_guardar():
        """Guarda un recuerdo. Solo admin. El id devuelto sirve para olvidarlo."""
        s, denegada = _solo_admin()
        if s is None:
            return denegada

        cuerpo = request.get_json(silent=True) or {}
        contenido = str(cuerpo.get("content") or cuerpo.get("contenido") or "").strip()
        if not contenido:
            return jsonify({"ok": False, "error": "falta 'content'"}), 400
        if len(contenido) > _LIMITE_CONTENIDO:
            return jsonify(
                {
                    "ok": False,
                    "error": (f"recuerdo demasiado largo ({len(contenido)} > {_LIMITE_CONTENIDO})"),
                }
            ), 400

        fuente = (
            str(cuerpo.get("source") or cuerpo.get("fuente") or "visor").strip()[:_LIMITE_FUENTE]
            or "visor"
        )
        try:
            doc_id = vault().record(fuente, contenido)
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)[:200]}), 500
        return jsonify({"ok": True, "id": doc_id, "source": fuente, "rol": _rol(s)}), 201

    @app.route("/api/globe/memoria/<int:doc_id>", methods=["DELETE"])
    def globe_memoria_olvidar(doc_id: int):
        """Olvida un recuerdo y sus enlaces. Solo admin."""
        s, denegada = _solo_admin()
        if s is None:
            return denegada
        try:
            r = vault().olvidar(doc_id)
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)[:200]}), 500
        if not r.get("docs"):
            return jsonify(
                {"ok": False, "error": f"no existe el recuerdo {doc_id}", "id": doc_id}
            ), 404
        return jsonify({"ok": True, "id": doc_id, **r})

    print("[God's Eye] memoria bidireccional en /api/globe/memoria (agents/memory_vault.py)")


# ── Auto-test ────────────────────────────────────────────────


def _selftest() -> int:
    """Prueba la memoria contra una base TEMPORAL: nunca contra la real."""
    import tempfile

    from agents.memory.memory_vault import MemoryVault

    with tempfile.TemporaryDirectory() as tmp:
        fijar_vault(MemoryVault(Path(tmp) / "memoria.db"))
        v = vault()
        v.record("selftest", "el proveedor Garcia cambio de tarifa en marzo")
        v.record("selftest", "Garcia pide factura mensual desde marzo")
        print("== stats ==")
        print(" ", v.stats()["docs"], "docs")
        print("== recientes ==")
        for r in v.recientes(5):
            print(f"  #{r['id']} {r['content'][:60]}")
        print("== recall 'tarifa de Garcia' ==")
        for r in v.recall("tarifa de Garcia", top_k=3):
            print(f"  [{r['score']:.2f}] {r['content'][:60]}")
        print("== olvidar ==")
        print(" ", v.olvidar(1))
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())
