"""CLI: python -m secops [rapido|completo] [--raiz .]"""
from __future__ import annotations

import sys

from secops.runner import ejecutar, guardar, resumen_para_daniela


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    perfil = args[0] if args and args[0] in ("rapido", "completo") else "rapido"
    raiz = "."
    if "--raiz" in args:
        raiz = args[args.index("--raiz") + 1]
    informe = ejecutar(perfil=perfil, raiz=raiz)
    ruta = guardar(informe)
    print(resumen_para_daniela(informe))
    print(f"\nInforme: {ruta}")
    crit = informe["totales"]["critica"] + informe["totales"]["alta"]
    return 2 if crit else 0


if __name__ == "__main__":
    raise SystemExit(main())
