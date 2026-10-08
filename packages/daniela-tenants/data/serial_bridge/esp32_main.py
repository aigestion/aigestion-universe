# main.py — Daniela Node para ESP32 (MicroPython)
# Generado por serial_bridge.py (aig / DanielaOS)
#
# Flasheo:
#   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
#   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32.bin
#   ampy --port /dev/ttyUSB0 put main.py
#
# Protocolo: una linea JSON por comando, una linea JSON por respuesta.

import json
import time
from machine import Pin, ADC

try:
    import dht

    HAS_DHT = True
except ImportError:
    HAS_DHT = False

# ---- Configuracion: ajusta los pines a tu cableado --------------
DHT_PIN = 4
PIR_PIN = 5
ADC_PIN = 34  # entrada analogica (0-3.3V max!)
RELAYS = (12, 13, 14)  # pines de rele activos en alto
LED = 2  # LED integrado

_dht = None
if HAS_DHT:
    import machine

    _dht = dht.DHT22(machine.Pin(DHT_PIN))

_pir = Pin(PIR_PIN, Pin.IN)
_adc = ADC(Pin(ADC_PIN))
_adc.atten(ADC.ATTN_11DB)  # rango completo 0-3.3 V
_relays = {p: Pin(p, Pin.OUT, value=0) for p in RELAYS}
_led = Pin(LED, Pin.OUT)


def read_sensors():
    s = {}
    if _dht is not None:
        try:
            _dht.measure()
            s["temp"] = round(_dht.temperature(), 1)
            s["hum"] = round(_dht.humidity(), 1)
        except Exception:
            pass
    s["motion"] = _pir.value()
    s["adc"] = _adc.read()
    s["uptime"] = time.ticks_ms() // 1000
    return s


def handle(cmd):
    c = cmd.get("c")

    if c == "ping":
        return {"ok": True, "pong": True}

    if c == "read":
        return {"ok": True, "s": read_sensors()}

    if c == "set":
        pin = int(cmd.get("pin", -1))
        val = int(cmd.get("v", 0))
        # Solo se permite tocar los pines declarados arriba: nunca uno libre
        if pin in _relays:
            _relays[pin].value(1 if val else 0)
            return {"ok": True, "pin": pin, "v": _relays[pin].value()}
        if pin == LED:
            _led.value(1 if val else 0)
            return {"ok": True, "pin": pin, "v": _led.value()}
        return {"ok": False, "msg": "pin no permitido: %d" % pin}

    if c == "state":
        return {"ok": True, "relays": {p: _relays[p].value() for p in RELAYS}}

    if c == "info":
        return {
            "ok": True,
            "node": "daniela-esp32",
            "dht": HAS_DHT,
            "relays": list(RELAYS),
            "version": 1,
        }

    return {"ok": False, "msg": "comando desconocido: %s" % c}


def main():
    import sys

    print(json.dumps({"ok": True, "boot": True, "node": "daniela-esp32"}))
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                time.sleep(0.05)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                cmd = json.loads(line)
            except ValueError:
                print(json.dumps({"ok": False, "msg": "JSON invalido"}))
                continue
            print(json.dumps(handle(cmd)))
        except Exception as e:
            print(json.dumps({"ok": False, "msg": str(e)[:60]}))
            time.sleep(0.1)


main()
