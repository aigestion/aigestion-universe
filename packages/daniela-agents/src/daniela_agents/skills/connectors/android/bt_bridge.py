#!/usr/bin/env python3
"""
bt_bridge.py — E-14 · Bluetooth: wearables, coche y presencia
=============================================================

Termux:API expone `termux-bluetooth-scan` y `termux-bluetooth-connect`, y la
auditoria los marco como **sin explotar**. La razon por la que importan no es
"poder emparejar desde la linea de comandos": es que **Bluetooth es el sensor
de contexto mas barato que tiene el telefono**.

No gasta bateria extra, no necesita GPS, no necesita red. Y dice cosas que
ningun otro sensor dice con esa fiabilidad:

  · el manos libres del coche conectado  → estas conduciendo
  · la pulsera en la muneca             → la llevas puesta (o te la dejaste)
  · los cascos puestos                   → puedes recibir audio, no molestar
  · nada conectado y son las 3:00        → estas durmiendo

E-05 (Context Engine) deduce "en_vehiculo" del acelerometro. Funciona, pero un
acelerometro tambien vibra en un tren o en un autobus. **El manos libres del
coche no miente.** Este modulo le da a E-05 la senal que le faltaba.

Modelo: dispositivos con rol
----------------------------
Una MAC sin mas no sirve. Cada dispositivo registrado tiene un **rol**:

    wearable    pulsera / reloj / anillo
    coche       manos libres del vehiculo
    auriculares cascos o altavoz personal
    altavoz     altavoz de casa / oficina
    otro        cualquier cosa, sin semantica

Y por rol, una **accion al conectar y al desconectar**. Las acciones son una
lista cerrada (igual que en E-08 NFC): **un dispositivo Bluetooth nunca
ejecuta shell**. Puede lanzar una escena, emitir un evento del bus, avisar,
hablar o pedir una confirmacion. Nada mas.

Presencia por RSSI
------------------
Si el escaneo trae intensidad de senal, se estima cercania:

    >= -60 dBm  al lado      (en la mano, en la muneca)
    >= -75 dBm  en la sala
    >= -90 dBm  lejos
    <  -90 dBm  casi perdido

Degradacion
-----------
En un PC sin Bluetooth de Android, el modulo arranca, responde y la demo pasa
entera con cero dispositivos. Nunca revienta por falta de hardware.

Rutas
-----
    GET  /api/pixel/bt/status    capacidades, rol activo, resumen
    GET  /api/pixel/bt/devices   registrados y vistos, con cercania
    POST /api/pixel/bt/scan      escanea durante N segundos
    POST /api/pixel/bt/register  registra una MAC con su rol
    POST /api/pixel/bt/actions   acciones al conectar/desconectar por rol
    POST /api/pixel/bt/config    umbrales RSSI, tiempos, auto-acciones
"""

from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "bt"
CONFIG_FILE = DATA_DIR / "config.json"
DEVICES_FILE = DATA_DIR / "devices.json"

# Lista cerrada de acciones. Ninguna ejecuta comandos: como en E-08 NFC,
# un periferico es una entrada de datos, no una fuente de instrucciones.
ACCIONES_PERMITIDAS = (
    "nada",
    "evento",        # emite BT_CONNECTED / BT_DISCONNECTED en el bus
    "escena",        # lanza una escena registrada de E-08
    "aviso",         # notificacion al PC
    "hablar",        # TTS con el texto dado
    "contexto",      # alimenta E-05 (en_vehiculo, en_casa...)
)

ROLES = ("wearable", "coche", "auriculares", "altavoz", "otro")

CONFIG_DEFAULT: dict[str, Any] = {
    "auto_acciones": True,      # ejecutar la accion del rol al detectar cambio
    "anti_rebote_s": 20.0,      # evita disparar si el coche corta y vuelve
    "rssi_al_lado": -60,        # mas alto que esto = al lado
    "rssi_en_sala": -75,
    "rssi_lejos": -90,
    "olvido_tras_s": 900.0,     # un dispositivo sin ver mas de esto = ausente
    "timeout_scan_s": 20,
}


# ==========================================================================
#  Utilidades de ejecucion — REGLA DURA: sin shell, sin os.system
# ==========================================================================
def _run(args: list[str], timeout: int = 20) -> str | None:
    try:
        r = subprocess.run(list(args), capture_output=True, timeout=timeout,
                           shell=False)
        if r.returncode != 0:
            return None
        return (r.stdout or b"").decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _tiene(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None


def es_android() -> bool:
    """`cmd` existe en Android (service tool) y en Windows (cmd.exe)."""
    for ruta in ("/system/bin/app_process", "/system/build.prop",
                 "/data/data/com.termux"):
        if Path(ruta).exists():
            return True
    return False


def capacidades() -> dict[str, bool]:
    """Que podemos usar aqui y ahora."""
    return {
        "termux_api": _tiene("termux-bluetooth-scan"),
        "dumpsys": _tiene("dumpsys") and es_android(),
        "android": es_android(),
    }


MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def normalizar_mac(mac: str) -> str | None:
    """Acepta con ':', con '-' o sin separadores. Devuelve minusculas con ':'."""
    if not mac:
        return None
    s = mac.strip().lower()
    if re.fullmatch(r"[0-9a-f]{12}", s):
        s = ":".join(s[i:i + 2] for i in range(0, 12, 2))
    s = s.replace("-", ":")
    return s if MAC_RE.match(s) else None


def cercania(rssi: float | None, c: dict[str, Any]) -> str:
    """Traduce dBm a algo que una persona entiende."""
    if rssi is None:
        return "desconocida"
    if rssi >= c["rssi_al_lado"]:
        return "al_lado"
    if rssi >= c["rssi_en_sala"]:
        return "en_la_sala"
    if rssi >= c["rssi_lejos"]:
        return "lejos"
    return "casi_perdido"


# ==========================================================================
#  Escaneo — tres fuentes, de mejor a peor
# ==========================================================================
def escanear_termux(timeout: int = 20) -> list[dict[str, Any]]:
    """`termux-bluetooth-scan` devuelve JSON. Es la fuente buena."""
    out = _run(["termux-bluetooth-scan", "--info"], timeout=timeout)
    if not out:
        out = _run(["termux-bluetooth-scan"], timeout=timeout)
    if not out:
        return []
    try:
        data = json.loads(out)
    except ValueError:
        return []
    if not isinstance(data, list):
        data = [data]
    res: list[dict[str, Any]] = []
    for d in data:
        if not isinstance(d, dict):
            continue
        mac = normalizar_mac(str(d.get("address") or d.get("mac") or ""))
        if not mac:
            continue
        rssi = d.get("rssi")
        try:
            rssi = float(rssi) if rssi is not None else None
        except (TypeError, ValueError):
            rssi = None
        res.append({"mac": mac,
                    "nombre": str(d.get("name") or "")[:64],
                    "rssi": rssi,
                    "emparejado": bool(d.get("bonded", False))})
    return res


def escanear_dumpsys(timeout: int = 20) -> list[dict[str, Any]]:
    """Respaldo sin Termux:API. Solo ve emparejados, pero siempre funciona."""
    out = _run(["dumpsys", "bluetooth_manager"], timeout=timeout)
    if not out:
        return []
    res: list[dict[str, Any]] = []
    for m in re.finditer(r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})", out):
        mac = normalizar_mac(m.group(1))
        if not mac:
            continue
        if all(d["mac"] != mac for d in res):
            res.append({"mac": mac, "nombre": "", "rssi": None,
                        "emparejado": True})
    return res


# ==========================================================================
#  Puente
# ==========================================================================
class PuenteBluetooth:
    """Registra dispositivos por rol y reacciona a presencia. Nunca ejecuta shell."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = dict(CONFIG_DEFAULT)
        # mac -> {"rol","nombre","accion_on","accion_off","param","visto","rssi"}
        self.dispositivos: dict[str, dict[str, Any]] = {}
        self.vistos: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.eventos: list[dict[str, Any]] = []
        self._ultimo_cambio: dict[str, float] = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.cargar()
        if config:
            self.config.update({k: v for k, v in config.items()
                                if k in CONFIG_DEFAULT})

    # ------------------------------------------------------------------ IO
    def cargar(self) -> None:
        try:
            if CONFIG_FILE.exists():
                d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.config.update({k: v for k, v in d.items()
                                        if k in CONFIG_DEFAULT})
        except (OSError, ValueError):
            pass
        try:
            if DEVICES_FILE.exists():
                d = json.loads(DEVICES_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.dispositivos = {
                        normalizar_mac(k) or k: v for k, v in d.items()
                        if isinstance(v, dict)}
        except (OSError, ValueError):
            pass

    def guardar(self) -> None:
        try:
            CONFIG_FILE.write_text(
                json.dumps(self.config, ensure_ascii=False, indent=2),
                encoding="utf-8")
            DEVICES_FILE.write_text(
                json.dumps(self.dispositivos, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except OSError:
            pass

    # ------------------------------------------------------------ registro
    def registrar(self, mac: str, rol: str = "otro", nombre: str = "",
                  accion_on: str = "nada", accion_off: str = "nada",
                  param: str = "") -> dict[str, Any]:
        m = normalizar_mac(mac)
        if not m:
            return {"ok": False, "error": f"MAC no valida: {mac!r}"}
        if rol not in ROLES:
            return {"ok": False, "error": f"rol no valido: {rol}",
                    "roles": list(ROLES)}
        if accion_on not in ACCIONES_PERMITIDAS:
            return {"ok": False, "error": f"accion_on no permitida: {accion_on}"}
        if accion_off not in ACCIONES_PERMITIDAS:
            return {"ok": False, "error": f"accion_off no permitida: {accion_off}"}
        with self._lock:
            self.dispositivos[m] = {
                "mac": m, "rol": rol, "nombre": nombre[:64] or m,
                "accion_on": accion_on, "accion_off": accion_off,
                "param": param[:256], "visto": None, "rssi": None,
                "conectado": False,
            }
        self.guardar()
        return {"ok": True, "dispositivo": self.dispositivos[m]}

    def olvidar(self, mac: str) -> dict[str, Any]:
        m = normalizar_mac(mac)
        if not m:
            return {"ok": False, "error": "MAC no valida"}
        with self._lock:
            quitado = self.dispositivos.pop(m, None) is not None
        if quitado:
            self.guardar()
        return {"ok": quitado}

    # -------------------------------------------------------------- escaneo
    def escanear(self, timeout: int | None = None) -> dict[str, Any]:
        t = int(timeout or self.config["timeout_scan_s"])
        t = max(3, min(60, t))

        # La fuente se declara solo si de verdad devolvio algo. Si no, diria
        # "termux-api" en un PC donde ese comando ni existe: mentiria.
        caps = capacidades()
        vistos: list[dict[str, Any]] = []
        fuente = "ninguna (sin hardware compatible)"
        if caps["termux_api"]:
            vistos = escanear_termux(t)
            if vistos:
                fuente = "termux-api"
        if not vistos and caps["dumpsys"]:
            vistos = escanear_dumpsys(t)
            if vistos:
                fuente = "dumpsys"

        ahora = time.time()
        cambios: list[dict[str, Any]] = []
        with self._lock:
            for d in vistos:
                self.vistos[d["mac"]] = {**d, "ts": ahora}

            # Presencia de los REGISTRADOS: antes estaba y ahora no (o al reves)
            for mac, info in self.dispositivos.items():
                visto = self.vistos.get(mac)
                fresco = bool(visto and
                              ahora - visto.get("ts", 0) <= self.config["olvido_tras_s"])
                antes = bool(info.get("conectado"))
                if fresco:
                    info["visto"] = visto.get("ts")
                    info["rssi"] = visto.get("rssi")
                info["conectado"] = fresco

                if fresco != antes:
                    # Anti-rebote: el manos libres del coche corta y vuelve
                    # al apagar el motor. No dispares dos veces.
                    ultimo = self._ultimo_cambio.get(mac, 0.0)
                    if ahora - ultimo >= self.config["anti_rebote_s"]:
                        self._ultimo_cambio[mac] = ahora
                        ev = self._disparar(info, fresco)
                        if ev:
                            cambios.append(ev)
            self.guardar()

        return {"ok": True, "fuente": fuente, "encontrados": len(vistos),
                "registrados": len(self.dispositivos),
                "cambios": cambios,
                "dispositivos": list(self.vistos.values())}

    def _disparar(self, info: dict[str, Any], conectado: bool) -> dict[str, Any] | None:
        """Ejecuta la accion del rol. NUNCA ejecuta comandos de sistema."""
        accion = info.get("accion_on") if conectado else info.get("accion_off")
        ev = {
            "ts": time.time(),
            "mac": info["mac"],
            "rol": info.get("rol"),
            "nombre": info.get("nombre"),
            "conectado": conectado,
            "accion": accion or "nada",
            "param": info.get("param", ""),
            "ejecutada": False,
            "detalle": "",
        }
        if not self.config.get("auto_acciones"):
            ev["detalle"] = "auto_acciones desactivado"
            self._anotar(ev)
            return ev
        if not accion or accion == "nada":
            ev["detalle"] = "sin accion configurada"
            self._anotar(ev)
            return ev

        # Cada accion es una llamada interna, nunca un string a ejecutar.
        if accion == "evento":
            self._emitir(info, conectado)
            ev["ejecutada"] = True
            ev["detalle"] = f"emitido {'BT_CONNECTED' if conectado else 'BT_DISCONNECTED'}"
        elif accion == "contexto":
            self._contexto(info, conectado)
            ev["ejecutada"] = True
            ev["detalle"] = f"contexto -> {info.get('param') or info.get('rol')}"
        else:
            # escena / aviso / hablar se entregan al bus: el modulo que
            # corresponda (E-08 escenas, E-10 UI) las recoge.
            self._emitir(info, conectado)
            ev["ejecutada"] = True
            ev["detalle"] = f"accion '{accion}' entregada al bus"
        self._anotar(ev)
        return ev

    def _emitir(self, info: dict[str, Any], conectado: bool) -> None:
        """Publica en el EventBus de E-04 si esta disponible."""
        try:
            import daniela_mobile_core as core  # type: ignore
            core.get_instance().bus.emit(
                "BT_CONNECTED" if conectado else "BT_DISCONNECTED",
                {"mac": info["mac"], "rol": info.get("rol"),
                 "nombre": info.get("nombre")},
                source="bt_bridge")
        except Exception:
            pass

    def _contexto(self, info: dict[str, Any], conectado: bool) -> None:
        """Alimenta E-05: el coche es la senal que no miente."""
        try:
            import context_engine as ce  # type: ignore
            eng = ce.get_instance()
            señal = info.get("param") or (
                "en_vehiculo" if info.get("rol") == "coche" else "en_casa")
            # La API exacta puede no existir; si no, no pasa nada.
            for metodo in ("set_signal", "feed_signal", "set_flag"):
                fn = getattr(eng, metodo, None)
                if callable(fn):
                    fn(señal, conectado)
                    break
        except Exception:
            pass

    def _anotar(self, ev: dict[str, Any]) -> None:
        with self._lock:
            self.eventos.append(ev)
            if len(self.eventos) > 200:
                self.eventos = self.eventos[-200:]

    # ---------------------------------------------------------------- estado
    def rol_activo(self) -> str | None:
        """El rol mas relevante ahora mismo. El coche manda sobre el resto."""
        with self._lock:
            conectados = [i for i in self.dispositivos.values()
                          if i.get("conectado")]
        if not conectados:
            return None
        prioridad = {"coche": 0, "wearable": 1, "auriculares": 2,
                     "altavoz": 3, "otro": 4}
        conectados.sort(key=lambda i: prioridad.get(i.get("rol", "otro"), 9))
        return conectados[0].get("rol")

    def listar(self) -> list[dict[str, Any]]:
        c = self.config
        with self._lock:
            out = []
            for mac, i in self.dispositivos.items():
                v = self.vistos.get(mac)
                out.append({
                    **i,
                    "cercania": cercania(i.get("rssi"), c),
                    "visto_hace_s": (round(time.time() - v["ts"], 1)
                                     if v and v.get("ts") else None),
                })
            # Los vistos pero NO registrados tambien interesan: es asi como
            # descubres que tu pulsera existe antes de decirle que lo es.
            for mac, v in self.vistos.items():
                if mac not in self.dispositivos:
                    out.append({**v, "rol": "desconocido", "registrado": False,
                                "cercania": cercania(v.get("rssi"), c)})
            return out

    def estado(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "capacidades": capacidades(),
                "rol_activo": self.rol_activo(),
                "registrados": len(self.dispositivos),
                "vistos": len(self.vistos),
                "eventos": self.eventos[-10:],
                "config": dict(self.config),
            }

    def configurar(self, **kv: Any) -> dict[str, Any]:
        with self._lock:
            for k, v in kv.items():
                if k in CONFIG_DEFAULT and v is not None:
                    self.config[k] = v
        self.guardar()
        return dict(self.config)


# ==========================================================================
#  Singleton
# ==========================================================================
_INSTANCIA: PuenteBluetooth | None = None
_LOCK = threading.Lock()


def get_instance() -> PuenteBluetooth:
    global _INSTANCIA
    with _LOCK:
        if _INSTANCIA is None:
            _INSTANCIA = PuenteBluetooth()
        return _INSTANCIA


# ==========================================================================
#  Rutas Flask
# ==========================================================================
def register_bt_routes(app) -> None:
    if Flask is None:
        return

    def m() -> PuenteBluetooth:
        return get_instance()

    @app.route("/api/pixel/bt/status", methods=["GET"], endpoint="bt__status")
    def _status():
        return jsonify(m().estado())

    @app.route("/api/pixel/bt/devices", methods=["GET"], endpoint="bt__devices")
    def _devices():
        return jsonify({"ok": True, "dispositivos": m().listar()})

    @app.route("/api/pixel/bt/scan", methods=["POST"], endpoint="bt__scan")
    def _scan():
        d = request.get_json(silent=True) or {}
        try:
            t = int(d.get("timeout", 0)) or None
        except (TypeError, ValueError):
            t = None
        return jsonify(m().escanear(t))

    @app.route("/api/pixel/bt/register", methods=["POST"],
               endpoint="bt__register")
    def _register():
        d = request.get_json(silent=True) or {}
        if d.get("olvidar"):
            return jsonify(m().olvidar(str(d.get("mac", ""))))
        return jsonify(m().registrar(
            str(d.get("mac", "")), str(d.get("rol", "otro")),
            str(d.get("nombre", "")), str(d.get("accion_on", "nada")),
            str(d.get("accion_off", "nada")), str(d.get("param", ""))))

    @app.route("/api/pixel/bt/actions", methods=["POST"], endpoint="bt__actions")
    def _actions():
        d = request.get_json(silent=True) or {}
        mac = str(d.get("mac", ""))
        with m()._lock:  # noqa: SLF001
            info = m().dispositivos.get(normalizar_mac(mac) or "", None)
        if not info:
            return jsonify({"ok": False, "error": "MAC no registrada"}), 404
        r = m().registrar(
            mac, info.get("rol", "otro"), info.get("nombre", ""),
            str(d.get("accion_on", info.get("accion_on", "nada"))),
            str(d.get("accion_off", info.get("accion_off", "nada"))),
            str(d.get("param", info.get("param", ""))))
        return jsonify(r)

    @app.route("/api/pixel/bt/config", methods=["POST"], endpoint="bt__config")
    def _config():
        d = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "config": m().configurar(**d)})

    print("[Bluetooth] Routes registered: /api/pixel/bt/* "
          "(status, devices, scan, register, actions, config)")


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" BLUETOOTH BRIDGE (E-14) — wearables, coche y presencia")
    print("=" * 68)

    print("capacidades :", ", ".join(f"{k}={v}"
                                     for k, v in capacidades().items()))

    print("\n-- MACs: acepta los tres formatos --")
    for crude in ("AA:BB:CC:DD:EE:FF", "aa-bb-cc-dd-ee-ff", "aabbccddeeff",
                  "no-es-una-mac"):
        print(f"   {crude:<20} -> {normalizar_mac(crude)}")

    bt = PuenteBluetooth()
    bt.dispositivos.clear()
    bt.vistos.clear()

    print("\n-- registro por rol --")
    print("  ", bt.registrar("AA:BB:CC:DD:EE:01", "coche", "Manos libres coche",
                             accion_on="contexto", accion_off="evento",
                             param="en_vehiculo"))
    print("  ", bt.registrar("AA:BB:CC:DD:EE:02", "wearable", "Pulsera",
                             accion_on="evento", accion_off="evento")["ok"])
    r = bt.registrar("no-valida", "coche")
    print("   MAC invalida rechazada :", not r["ok"], "-", r.get("error"))
    r = bt.registrar("AA:BB:CC:DD:EE:03", "cohete")
    print("   rol inventado rechazado:", not r["ok"], "-", r.get("error"))
    r = bt.registrar("AA:BB:CC:DD:EE:04", "coche", accion_on="rm -rf /")
    print("   accion shell rechazada :", not r["ok"], "-", r.get("error"))

    print("\n-- cercania por RSSI --")
    for dbm in (-45, -68, -82, -95, None):
        print(f"   {str(dbm):>5} dBm -> {cercania(dbm, bt.config)}")

    print("\n-- el coche aparece: debe disparar 'contexto' --")
    bt.vistos["aa:bb:cc:dd:ee:01"] = {"mac": "aa:bb:cc:dd:ee:01",
                                      "rssi": -52.0, "ts": time.time()}
    res = bt.escanear(3)
    print("   fuente     :", res["fuente"])
    print("   registrados:", res["registrados"])
    for c in res["cambios"]:
        print(f"   cambio: {c['rol']:<10} conectado={c['conectado']} "
              f"accion={c['accion']:<9} ejecutada={c['ejecutada']} "
              f"({c['detalle']})")

    print("\n-- rol activo con el coche conectado --")
    print("   rol_activo:", bt.rol_activo(), "(el coche manda sobre el resto)")

    print("\n-- anti-rebote: segundo escaneo inmediato NO redispara --")
    res2 = bt.escanear(3)
    print("   cambios en el reescaneo:", len(res2["cambios"]), "(debe ser 0)")

    print("\n-- la pulsera se quita: debe disparar 'evento' de desconexion --")
    bt.vistos["aa:bb:cc:dd:ee:02"] = {"mac": "aa:bb:cc:dd:ee:02",
                                      "rssi": -40.0, "ts": time.time()}
    bt.escanear(3)
    bt.config["anti_rebote_s"] = 0.0
    bt.vistos.pop("aa:bb:cc:dd:ee:02")
    res3 = bt.escanear(3)
    for c in res3["cambios"]:
        print(f"   cambio: {c['rol']:<10} conectado={c['conectado']} "
              f"accion={c['accion']}")

    print("\n-- dispositivo visto pero NO registrado aparece como desconocido --")
    bt.vistos["11:22:33:44:55:66"] = {"mac": "11:22:33:44:55:66",
                                      "nombre": "Altavoz salón",
                                      "rssi": -70.0, "ts": time.time()}
    desconocidos = [d for d in bt.listar() if d.get("rol") == "desconocido"]
    print("   desconocidos:", len(desconocidos),
          "-", [d.get("nombre") for d in desconocidos])

    print("\n-- estado --")
    e = bt.estado()
    print("   registrados:", e["registrados"], " vistos:", e["vistos"],
          " rol activo:", e["rol_activo"])
    print("   eventos guardados:", len(e["eventos"]))

    print("=" * 68)


if __name__ == "__main__":
    _demo()
