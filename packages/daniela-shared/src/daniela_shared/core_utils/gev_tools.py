"""Herramientas con las que Daniela GESTIONA el visor God's Eye.

El visor es una PANTALLA de Daniela, no un vecino: el chat no solo puede
CONTAR lo que hay en el globo, puede OPERARLO. Este modulo expone el catalogo
completo de lo que Daniela puede hacer con el visor y el dispatch seguro.

Diseño (y por qué asi):

* **Sin function calling nativo.** El conector usado por `/api/ai/chat`
  (`FreeLLMAPIConnector`) devuelve solo `content`. Asi que el contrato con el
  modelo es un bloque con formato:

      ```tool
      {"name": "geocercas_listar", "args": {}}
      ```

  `detectar()` lo lee y `ejecutar()` lo ejecuta; `ai_bridge` hace la segunda
  pasada con el resultado para que Daniela lo cuente con datos reales.
  Si el modelo no pide nada, `detectar` devuelve `None` y la respuesta se
  devuelve tal cual.

* **Autorización por el sujeto de la peticion, no por el modelo.** Las
  herramientas de escritura exigen `es_admin()`. El rol sale del request real
  (`access.sujeto_desde_request`), nunca de lo que el modelo diga ser.

* **Todo se ejecuta dentro de `try`**: una herramienta que revienta devuelve
  `{"ok": False, "error": ...}` y no mata el chat.

Rutas relacionadas (todas en la misma app Flask): `/api/ai/chat`,
`/api/gev/*`, `/api/globe/*`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ── Raíz del repo (por marcador, ver nota en `shared/ai_bridge.py`) ──────

def _repo_root() -> str:
    aqui = Path(os.path.abspath(__file__))
    for c in (aqui.parent, *aqui.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return str(c)
    return os.path.dirname(os.path.dirname(os.path.dirname(str(aqui))))


RAIZ = _repo_root()


def _en_path() -> None:
    """`gev_*` viven en la raiz del repo y `gev` es el paquete de ahi."""
    if RAIZ not in sys.path:
        sys.path.insert(0, RAIZ)


# ── Sujeto (rol real de quien hace la peticion) ─────────────────────────

def sujeto_por_defecto():
    """Rol de quien habla con el chat: el del request si lo hay, si no cliente."""
    try:
        from flask import has_request_context, request

        if has_request_context():
            import access
            return access.sujeto_desde_request(request)
    except Exception:  # noqa: BLE001  fuera de Flask (CLI, tests)
        pass
    import access
    return access.Sujeto(rol=access.Rol.CLIENTE, tenant_slug="", nombre="daniela")


def _es_admin(sujeto) -> bool:
    """`Sujeto.es_admin` es una PROPIEDAD, no un método.

    Llamarla (`s.es_admin()`) revienta con `TypeError: 'bool' object is not
    callable`, que es justo el error que escondía el fallo de permisos como
    un error de herramienta. Se aceptan las dos formas por si aparece una
    variante sin `@property`.
    """
    if sujeto is None:
        return False
    v = getattr(sujeto, "es_admin", False)
    if callable(v) and not isinstance(v, bool):
        try:
            v = v()
        except Exception:  # noqa: BLE001
            return False
    return bool(v)


def _exigir_admin(sujeto) -> None:
    if not _es_admin(sujeto):
        permiso = getattr(sujeto, "rol", None)
        raise PermissionError(f"operacion de escritura solo para admin (rol: {permiso})")


def _exigir_sujeto(sujeto):
    return sujeto if sujeto is not None else sujeto_por_defecto()


# ── Validación de argumentos ────────────────────────────────────────────

def _num(args: dict, clave: str, defecto: float) -> float:
    try:
        return float(args.get(clave, defecto))
    except (TypeError, ValueError):
        return float(defecto)


def _texto(args: dict, clave: str, defecto: str = "", max_len: int = 80) -> str:
    v = args.get(clave, defecto)
    if not isinstance(v, str):
        v = defecto
    return v.strip()[:max_len]


def _lista_textos(v: Any, limite: int = 5) -> list[str]:
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        return []
    return [str(x)[:40] for x in v[:limite]]


def _acotar(items: Any, limite: int = 50) -> Any:
    if isinstance(items, list) and len(items) > limite:
        return items[:limite] + [f"… (+{len(items) - limite} más)"]
    return items


# ── Cada herramienta: catálogo ──────────────────────────────────────────

@dataclass(frozen=True)
class Herramienta:
    nombre: str
    descripcion: str
    parametros: dict[str, Any]
    handler: Callable[..., dict]
    solo_lectura: bool = True


def _h(
    nombre: str,
    descripcion: str,
    propiedades: dict[str, Any],
    handler: Callable[..., dict],
    requeridos: tuple[str, ...] = (),
    solo_lectura: bool = True,
) -> tuple[str, Herramienta]:
    esquema: dict[str, Any] = {
        "type": "object",
        "properties": propiedades,
        "additionalProperties": False,
    }
    if requeridos:
        esquema["required"] = list(requeridos)
    return nombre, Herramienta(
        nombre=nombre,
        descripcion=descripcion,
        parametros=esquema,
        handler=handler,
        solo_lectura=solo_lectura,
    )


# ── Lectura: estado, capas y nodos ──────────────────────────────────────

def _visor_estado(_args: dict, _sujeto) -> dict:
    """Salud del visor propio, del API puente y del visor completo."""
    _en_path()
    from gev import gev_proxy

    out: dict[str, Any] = {"ok": True}
    try:
        out["visor"] = {
            "titulo": __import__("gev.server", fromlist=["x"]).TITULO,
            "base": "/gods-eye",
        }
    except Exception as e:  # noqa: BLE001
        out["visor"] = {"ok": False, "error": str(e)[:200]}
    try:
        out["visor_completo"] = gev_proxy.estado()
    except Exception as e:  # noqa: BLE001
        out["visor_completo"] = {"ok": False, "error": str(e)[:200]}
    try:
        import gev_integration
        out["api_puente"] = {
            "estado": gev_integration.estado(),
        }
    except Exception as e:  # noqa: BLE001
        out["api_puente"] = {"ok": False, "error": str(e)[:200]}
    return out


def _visor_capas(_args: dict, _sujeto) -> dict:
    """Que capas hay: las del sidecar original y las de las geocercas."""
    _en_path()
    import gev_integration
    from gev import gev_proxy
    return {
        "ok": True,
        "proveedores_original": list(gev_proxy.PREFIJOS_API),
        "n_proveedores": len(gev_proxy.PREFIJOS_API),
        "capas_geocerca": list(gev_integration.CAPAS_VALIDAS),
        "estilos": list(gev_integration.ESTILOS),
        "montaje": gev_proxy.BASE_URL,
    }


def _globo_nodos(args: dict, sujeto) -> dict:
    """Nodos del globo visibles para el rol real de quien pregunta."""
    _en_path()
    # P1 2026-10-04: el modulo visor era `gev/server.py`; el aplanado lo dejo
    # en `daniela-os/gev_server.py` (el shim `gev/__init__.py` lo re-exporta).
    from gev.gev_server import datos_globo

    s = _exigir_sujeto(sujeto)
    datos = datos_globo(s)
    for k, v in list(datos.items()):
        if isinstance(v, list):
            datos[k] = _acotar(v, 50)
    return {"ok": True, "rol": s.rol.value, **datos}


def _globo_enlace(args: dict, _sujeto) -> dict:
    """Enlace profundo al globo, ya enfocado, con el estilo del contexto."""
    _en_path()
    import gev_integration

    lat, lon = _num(args, "lat", 0.0), _num(args, "lon", 0.0)
    contexto = _texto(args, "contexto", "")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return {"ok": False, "error": f"lat/lon fuera de rango: {lat}, {lon}"}
    try:
        url = gev_integration.gev_link(
            lat, lon,
            alt=_num(args, "alt", 1500),
            pitch=_num(args, "pitch", -35),
            style=gev_integration.estilo_para(contexto),
        )
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "url": url, "lat": lat, "lon": lon,
            "estilo": gev_integration.estilo_para(contexto)}


# ── Geocercas (lectura y escritura) ─────────────────────────────────────

def _geocercas_listar(_args: dict, _sujeto) -> dict:
    _en_path()
    import gev_integration

    zonas = gev_integration.cargar_zonas()
    return {"ok": True, "n": len(zonas), "zonas": [z.__dict__ for z in zonas]}


def _geocercas_guardar(args: dict, sujeto) -> dict:
    """Crea o actualiza una geocerca. Solo admin."""
    _en_path()
    import gev_integration

    _exigir_admin(sujeto)
    key = _texto(args, "key", "")
    if not key:
        return {"ok": False, "error": "falta 'key'"}
    lat, lon = _num(args, "lat", 0.0), _num(args, "lon", 0.0)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return {"ok": False, "error": "lat/lon fuera de rango"}
    capas = [c for c in _lista_textos(args.get("capas"))
             if c in gev_integration.CAPAS_VALIDAS] or ["vuelos", "sismos"]
    zonas = [z for z in gev_integration.cargar_zonas() if z.key != key]
    zonas.append(gev_integration.Zona(
        key=key,
        nombre=_texto(args, "nombre", key),
        lat=lat,
        lon=lon,
        radio_km=_num(args, "radio_km", 25.0),
        capas=capas,
        min_mag=_num(args, "min_mag", 4.0),
    ))
    gev_integration.guardar_zonas(zonas)
    return {"ok": True, "key": key, "n": len(zonas), "capas": capas}


def _geocercas_borrar(args: dict, sujeto) -> dict:
    """Elimina una geocerca por su clave. Solo admin."""
    _en_path()
    import gev_integration

    _exigir_admin(sujeto)
    key = _texto(args, "key", "")
    zonas = gev_integration.cargar_zonas()
    resto = [z for z in zonas if z.key != key]
    if len(resto) == len(zonas):
        return {"ok": False, "error": f"no existe la geocerca '{key}'"}
    gev_integration.guardar_zonas(resto)
    return {"ok": True, "key": key, "n": len(resto)}


# ── Feeds en vivo ───────────────────────────────────────────────────────

def _capas_vuelos(args: dict, _sujeto) -> dict:
    _en_path()
    import gev_integration

    filas = gev_integration.GevClient().vuelos_cerca(
        _num(args, "lat", 0.0),
        _num(args, "lon", 0.0),
        _num(args, "radio", 50),
        int(_num(args, "limite", 25)),
    )
    return {"ok": True, "n": len(filas), "vuelos": _acotar(filas, 30)}


def _capas_sismos(args: dict, _sujeto) -> dict:
    _en_path()
    import gev_integration

    filas = gev_integration.GevClient.sismos(
        min_mag=_num(args, "min_mag", 4.0),
        limite=int(_num(args, "limite", 25)),
    )
    return {"ok": True, "n": len(filas), "sismos": _acotar(filas, 30)}


# ── Memoria de Daniela (la MISMA base que el visor y Astra) ─────────────

def _vault_memoria():
    """`MemoryVault` compartido.

    Se coge el del visor (`gev.memoria`) para que chat, pantalla y
    Command Center lean y escriban en UNA sola instancia/base; si ese modulo
    no se puede importar, se cae a una propia sobre el mismo fichero
    (`agents/memory_vault.py`). No hay "memoria del chat" aparte.
    """
    _en_path()
    try:
        from gev import memoria as memoria_visor
        return memoria_visor.vault()
    except Exception:  # noqa: BLE001  modulo no importable: vault directo
        from agents.memory.memory_vault import MemoryVault
        return MemoryVault()


def _memoria_recordar(args: dict, sujeto) -> dict:
    """Recuerdos de Daniela: por consulta, o los ultimos si no la hay.

    Solo administrador: la memoria es global y aun no lleva tenant, asi que
    filtrarla para un cliente seria inventar. Mismo criterio que
    `GET /api/globe/memoria`.
    """
    _exigir_admin(sujeto)
    v = _vault_memoria()
    consulta = _texto(args, "consulta", "", max_len=200)
    top = int(_num(args, "top", 5)) or 5
    recuerdos = (v.recall(consulta, top_k=max(1, min(top, 20)))
                 if consulta else v.recientes(limite=max(1, min(top, 20))))
    return {
        "ok": True,
        "consulta": consulta,
        "n": len(recuerdos),
        "recuerdos": _acotar(recuerdos, 20),
        "stats": v.stats(),
    }


def _memoria_guardar(args: dict, sujeto) -> dict:
    """Guarda un recuerdo para siempre. Solo admin."""
    _exigir_admin(sujeto)
    contenido = (_texto(args, "content", "", max_len=4000)
                 or _texto(args, "contenido", "", max_len=4000))
    if not contenido:
        return {"ok": False, "error": "falta 'content'"}
    fuente = _texto(args, "source", "chat", max_len=80) or "chat"
    doc_id = _vault_memoria().record(fuente, contenido)
    return {"ok": True, "id": doc_id, "source": fuente,
            "nota": "guardado en la memoria de Daniela"}


# ── Ciclo de vida del visor completo (sidecar :4173) ────────────────────

def _visor_arrancar(_args: dict, sujeto) -> dict:
    """Arranca el God's Eye View original completo. Solo admin."""
    _en_path()
    from gev import gev_proxy

    _exigir_admin(sujeto)
    ok, motivo = gev_proxy.disponible()
    if not ok:
        return {"ok": False, "motivo": motivo}
    return gev_proxy.arrancar(espera=25.0)


def _visor_parar(_args: dict, sujeto) -> dict:
    """Para el sidecar del visor completo. Solo admin."""
    _en_path()
    from gev import gev_proxy

    _exigir_admin(sujeto)
    return gev_proxy.parar()


# ── Catálogo ────────────────────────────────────────────────────────────

_REGISTRO = dict([
    _h(
        "visor_estado",
        "Estado del visor God's Eye: visor propio, visor completo "
        "(sidecar :4173) y API puente.",
        {},
        _visor_estado,
    ),
    _h(
        "visor_capas",
        "Lista las capas y proveedores disponibles en el visor.",
        {},
        _visor_capas,
    ),
    _h(
        "globo_nodos",
        "Nodos visibles en el globo (sede y empresas) segun el rol del usuario.",
        {"limitar_a_empresa": {"type": "string",
                               "description": "id de empresa a mirar (opcional)"}},
        _globo_nodos,
    ),
    _h(
        "globo_enlace",
        "Enlace profundo al globo ya enfocado a unas coordenadas.",
        {
            "lat": {"type": "number"}, "lon": {"type": "number"},
            "contexto": {"type": "string", "description": "sede|cliente|alerta|osint"},
            "alt": {"type": "number"}, "pitch": {"type": "number"},
        },
        _globo_enlace,
        requeridos=("lat", "lon"),
    ),
    _h(
        "geocercas_listar",
        "Geocercas configuradas con las capas que vigilan.",
        {},
        _geocercas_listar,
    ),
    _h(
        "geocercas_guardar",
        "Crea o actualiza una geocerca (solo admin).",
        {
            "key": {"type": "string"},
            "nombre": {"type": "string"},
            "lat": {"type": "number"}, "lon": {"type": "number"},
            "radio_km": {"type": "number"},
            "capas": {"type": "array", "items": {"type": "string"},
                      "description": "vuelos|militares|sismos|incendios|barcos"},
            "min_mag": {"type": "number"},
        },
        _geocercas_guardar,
        requeridos=("key", "lat", "lon"),
        solo_lectura=False,
    ),
    _h(
        "geocercas_borrar",
        "Elimina una geocerca por su clave (solo admin).",
        {"key": {"type": "string"}},
        _geocercas_borrar,
        requeridos=("key",),
        solo_lectura=False,
    ),
    _h(
        "capas_vuelos",
        "Aeronaves en vuelo cerca de un punto.",
        {"lat": {"type": "number"}, "lon": {"type": "number"},
         "radio": {"type": "number"}, "limite": {"type": "number"}},
        _capas_vuelos,
        requeridos=("lat", "lon"),
    ),
    _h(
        "capas_sismos",
        "Sismos recientes por magnitud.",
        {"min_mag": {"type": "number"}, "limite": {"type": "number"}},
        _capas_sismos,
    ),
    _h(
        "memoria_recordar",
        "Recuerdos de Daniela (memoria a largo plazo, RAG + grafo). "
        "Solo el administrador: la memoria es global. Sin 'consulta' "
        "devuelve los ultimos recuerdos.",
        {
            "consulta": {"type": "string",
                         "description": "que recordar (opcional)"},
            "top": {"type": "number", "description": "maximo de recuerdos"},
        },
        _memoria_recordar,
    ),
    _h(
        "memoria_guardar",
        "Guarda un recuerdo en la memoria de Daniela para siempre "
        "(solo admin).",
        {
            "content": {"type": "string", "description": "texto del recuerdo"},
            "source": {"type": "string",
                       "description": "quien o que lo origina (chat, visor…)"},
        },
        _memoria_guardar,
        requeridos=("content",),
        solo_lectura=False,
    ),
    _h(
        "visor_arrancar",
        "Arranca el visor completo (God's Eye View original, solo admin).",
        {},
        _visor_arrancar,
        solo_lectura=False,
    ),
    _h(
        "visor_parar",
        "Para el sidecar del visor completo (solo admin).",
        {},
        _visor_parar,
        solo_lectura=False,
    ),
])

HERRAMIENTAS: dict[str, Herramienta] = _REGISTRO


# ── Expuesta al modelo ──────────────────────────────────────────────────

def nombres() -> list[str]:
    return sorted(HERRAMIENTAS)


def esquemas() -> list[dict[str, Any]]:
    """Formato estándar `tools` (OpenAI) por si el conector aprende function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": h.nombre,
                "description": h.descripcion,
                "parameters": h.parametros,
            },
        }
        for h in (HERRAMIENTAS[n] for n in nombres())
    ]


def describir() -> str:
    """Bloque de sistema: el mismo catalogo, pero para un modelo sin tools."""
    lineas = [
        "Tienes herramientas para GESTIONAR el visor God's Eye de Daniela.",
        "Si necesitas datos o una accion, responde EXCLUSIVAMENTE con:",
        '```tool\n{"name": "<nombre>", "args": {...}}\n```',
        "Sin texto fuera del bloque. Si no necesitas ninguna, responde normal.",
        "",
        "Herramientas:",
    ]
    for n in nombres():
        h = HERRAMIENTAS[n]
        props = ", ".join(h.parametros.get("properties", {})) or "ninguno"
        lectura = "lectura" if h.solo_lectura else "ESCRITURA (admin)"
        lineas.append(f"- {n}: {h.descripcion} [args: {props}] ({lectura})")
    return "\n".join(lineas)


# ── Llamada desde la respuesta del modelo ───────────────────────────────

_BLOQUE = re.compile(r"```(?:tool|json)?\s*\n(\{.*?\})\s*```", re.S)


def _parse_bloque(candidato: Any) -> tuple[str, dict] | None:
    if not isinstance(candidato, dict):
        return None
    nombre = candidato.get("name") or candidato.get("tool") or candidato.get("nombre")
    if not isinstance(nombre, str) or nombre not in HERRAMIENTAS:
        return None
    args = candidato.get("args", candidato.get("arguments", {}))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except (ValueError, TypeError):
            args = {}
    if not isinstance(args, dict):
        args = {}
    return nombre, args


def detectar(texto: str) -> tuple[str, dict] | None:
    """Extrae la llamada a herramienta de la respuesta del modelo, si la hay.

    Primero se miran los bloques cercados (el contrato oficial). Si no, se
    barre el texto buscando el primer objeto JSON con una herramienta valida:
    algunos modelos se salen del formato pero mandan el JSON entero.
    """
    if not texto:
        return None
    for m in _BLOQUE.finditer(texto):
        try:
            parsed = json.loads(m.group(1))
        except (ValueError, TypeError):
            continue
        hallada = _parse_bloque(parsed)
        if hallada:
            return hallada

    dec = json.JSONDecoder()
    for i, ch in enumerate(texto):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(texto[i:])
        except (ValueError, TypeError):
            continue
        hallada = _parse_bloque(obj)
        if hallada:
            return hallada
    return None


def ejecutar(
    nombre: str,
    args: dict | None = None,
    sujeto=None,
) -> dict[str, Any]:
    """Ejecuta una herramienta. Nunca lanza: siempre devuelve `{ok, ...}`."""
    if nombre not in HERRAMIENTAS:
        return {"ok": False, "error": f"herramienta desconocida: {nombre}",
                "disponibles": nombres()}
    args = args if isinstance(args, dict) else {}
    if not isinstance(args, dict):
        return {"ok": False, "error": "args debe ser un objeto"}
    try:
        resultado = HERRAMIENTAS[nombre].handler(args, _exigir_sujeto(sujeto))
    except PermissionError as e:
        return {"ok": False, "error": str(e), "permiso": "denegado"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"}
    if not isinstance(resultado, dict):
        resultado = {"ok": True, "resultado": resultado}
    return {**resultado, "herramienta": nombre}


def procesar(
    texto: str,
    sujeto=None,
) -> dict[str, Any] | None:
    """Detecta una llamada en `texto` y la ejecuta.

    Devuelve `None` si el modelo no pidió nada (respuesta normal).
    """
    llamada = detectar(texto)
    if llamada is None:
        return None
    nombre, args = llamada
    return {"peticion": {"name": nombre, "args": args},
            "resultado": ejecutar(nombre, args, sujeto=sujeto)}
