# Comprueba que el entorno de DanielaOS esta completo ANTES de arrancar nada.
#
# ¿Por que existe este script?
# Durante dias el `.env` de la raiz se quedo con 12 claves (solo Supabase)
# mientras que la configuracion buena vivia en `config/.env`. Como `load_dotenv()`
# solo leia el de la raiz, DANIELA_PIN, GEMINI_API_KEY (la usan ~75 modulos),
# GROQ_API_KEY, PIXEL_IP y PIXEL_TOKEN llegaban VACIAS y sin ningun error:
# el sintoma aparecia mucho despues, en otro modulo y como un "no reconoce la clave"
# misterioso. Esto paso DOS veces.
#
# HISTORIA (2026-10-03): la duplicacion se resolvio archivando config/env/ en
# storage/archives/env-consolidacion-2026-10-03/. Fuente unica = .env de la raiz.
# Este script sigue comprobando claves criticas y su --restore fusiona desde el
# archivo (por si hay que resucitar el fichero antiguo).
#
# Uso:
#   ./.venv/Scripts/python.exe scripts/check_env.py            # solo comprobar
#   ./.venv/Scripts/python.exe scripts/check_env.py --restore  # restaurar del archivo
#
# No imprime NUNCA el valor de un secreto: solo si esta, y cuantos caracteres tiene.

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ENV_RAIZ = RAIZ / ".env"
# Copia de seguridad del fichero que vivia en config/.env (archivado 2026-10-03).
ENV_CONFIG = RAIZ / "storage" / "archives" / "env-consolidacion-2026-10-03" / ".env"

# Claves sin las cuales DanielaOS arranca "bien" pero no funciona.
# (nombre, para que sirve, cuantos modulos lo usan aprox.)
CRITICAS = [
    ("DANIELA_PIN", "acceso por PIN al panel", "1"),
    ("GEMINI_API_KEY", "motor de IA principal", "~75"),
    ("GROQ_API_KEY", "IA de respaldo / rapida", "~20"),
    ("OPENROUTER_API_KEY", "IA de respaldo", "~10"),
    ("PIXEL_IP", "direccion del movil", "~30"),
    ("PIXEL_TOKEN", "auth contra el movil", "~30"),
]

# Claves que, si estan, se avisa pero no es un fallo.
OPCIONALES = [
    ("SUPABASE_URL", "cloud / RAG"),
    ("SUPABASE_SERVICE_KEY", "cloud / RAG"),
    ("TELEGRAM_BOT_TOKEN", "bot de Telegram"),
]


def leer_env(ruta: Path) -> dict[str, str]:
    """Lee un .env sin depender de python-dotenv (asi funciona en Termux)."""
    valores: dict[str, str] = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", clave):
            continue
        valores[clave] = valor.strip().strip("\"'")
    return valores


def claves_utiles(ruta: Path) -> dict[str, str]:
    """Como leer_env, pero descarta las claves sin valor y los comentarios.

    Hace falta para el --restore: en el .env roto hay lineas del tipo
    `GEMINI_API_KEY=` (existen pero vacias). Si se copian encima de las buenas,
    load_dotenv las deja VACIAS y no se arregla nada. Solo se conserva lo que
    tiene valor de verdad.
    """
    return {k: v for k, v in leer_env(ruta).items() if v}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--restore",
        action="store_true",
        help="fusiona la copia archivada (storage/archives/env-consolidacion-2026-10-03/) en el .env de la raiz (copia de seguridad antes)",
    )
    args = ap.parse_args()

    raiz = leer_env(ENV_RAIZ)
    config = leer_env(ENV_CONFIG)

    print(
        f"Raiz    {ENV_RAIZ.name:12} -> {len(raiz):4} claves "
        f"({ENV_RAIZ.stat().st_size if ENV_RAIZ.exists() else 0} bytes)"
    )
    print(
        f"Archivo {ENV_CONFIG.parent.name}/{ENV_CONFIG.name} -> {len(config):4} claves "
        f"({ENV_CONFIG.stat().st_size if ENV_CONFIG.exists() else 0} bytes)"
    )
    print()

    # Si el de la raiz esta casi vacio pero la copia archivada no, es
    # exactamente el sintoma del incidente: restaurar.
    roto = len(raiz) < 50 and len(config) > 50

    faltan_criticas = [
        (k, uso, n) for k, uso, n in CRITICAS if not raiz.get(k) and not config.get(k)
    ]
    solo_en_config = [
        (k, uso, n) for k, uso, n in CRITICAS if not raiz.get(k) and config.get(k)
    ]

    if roto:
        print("*** EL .env DE LA RAIZ ESTA CASI VACIO ***")
        print(f"    Tiene {len(raiz)} claves y la copia archivada tiene {len(config)}.")
        print("    Esto es el sintoma del incidente del 2026-09-14. Arreglo:")
        print("      ./.venv/Scripts/python.exe scripts/check_env.py --restore")
        print()

    if solo_en_config:
        print(
            "Claves CRITICAS que solo estan en la copia archivada (DanielaOS lee la raiz):"
        )
        for k, uso, n in solo_en_config:
            print(f"  [!] {k:22} {uso} ({n} modulos)")
        print()

    if faltan_criticas:
        print("Claves CRITICAS que NO estan en ningun sitio:")
        for k, uso, n in faltan_criticas:
            print(f"  [X] {k:22} {uso} ({n} modulos)")
        print()

    if args.restore:
        if not ENV_CONFIG.exists():
            print("No hay copia archivada de la que restaurar. Nada que hacer.")
            return 1
        respaldo = RAIZ / ".env.bak-antes-de-restaurar"
        if ENV_RAIZ.exists():
            shutil.copy2(ENV_RAIZ, respaldo)
            print(f"Copia del .env actual -> {respaldo.name}")

        # Fusion a nivel de CLAVE, quedando la raiz por delante.
        # No se concatenan ficheros a lo bruto porque el .env roto tiene lineas
        # del tipo `GEMINI_API_KEY=` sin valor: si van despues, pisan la buena.
        # Tampoco sirve poner la copia detras: la ULTIMA linea gana en dotenv.
        fusion: dict[str, str] = {}
        for clave, valor in leer_env(ENV_CONFIG).items():
            if valor:
                fusion[clave] = valor
        for clave, valor in leer_env(ENV_RAIZ).items():
            if valor:  # solo lo que aporta un valor real
                fusion[clave] = valor

        lineas = [
            "# Restaurado por scripts/check_env.py --restore",
            "# Orden: copia archivada como base + los valores del .env de la raiz encima.",
            "# Las claves sin valor se ignoran a proposito.",
            "",
        ]
        lineas += [f"{k}={v}" for k, v in sorted(fusion.items())]
        ENV_RAIZ.write_text("\n".join(lineas) + "\n", encoding="utf-8")

        print(f"Restaurado. {ENV_RAIZ.name} -> {len(fusion)} claves con valor.")
        print("Vuelve a ejecutar sin --restore para verificarlo.")
        return 0

    if not faltan_criticas and not solo_en_config:
        print("Todo correcto: las claves criticas estan en el entorno.")
        return 0

    print("Ejecuta con --restore para arreglarlo (hace copia antes).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
