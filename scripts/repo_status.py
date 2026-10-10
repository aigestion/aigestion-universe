"""Estado real del repositorio, sin fiarse de `git status -sb`.

¿Por que existe este script?
----------------------------
En este repo `git fetch` NO persiste los refs remotos: `.git/refs/remotes/origin/`
esta VACIO y ni siquiera `git update-ref` consigue crear entradas (falla en
silencio, sin error y con codigo de salida 0). La consecuencia es que cualquier
comando que compare con `origin/...` MIENTE:

    git status -sb   ->  "## universo-v1...origin/universo-v1"  (falso: no lo sabe)
    git branch -vv   ->  "[origin/universo-v1: gone]"           (falso: la rama existe)

Este script pregunta directamente al remoto con `git ls-remote`, que si es fiable,
y compara con el estado local. Sin sorpresas.

Uso:
    ./.venv/Scripts/python.exe scripts/repo_status.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    r = subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return r.stdout.strip()


def refs_remotos() -> dict[str, str]:
    """Lee las ramas del remoto de verdad (ls-remote, no la cache local)."""
    salida = git("ls-remote", "--heads", "origin")
    ramas: dict[str, str] = {}
    for linea in salida.splitlines():
        if not linea.strip():
            continue
        sha, _, ref = linea.partition("\t")
        if ref.startswith("refs/heads/"):
            ramas[ref.removeprefix("refs/heads/")] = sha.strip()
    return ramas


def main() -> int:
    print("=" * 68)
    print("ESTADO REAL DEL REPOSITORIO  (consultado con git ls-remote)")
    print("=" * 68)

    head = git("rev-parse", "HEAD")
    rama = git("rev-parse", "--abbrev-ref", "HEAD")
    print(f"\nRama actual : {rama}")
    print(f"Commit      : {head[:12]}")

    # ¿Hay algo sin commitear?
    pendiente = git("status", "--porcelain")
    n_pendiente = len([line for line in pendiente.splitlines() if line.strip()])
    print(f"Sin commitear: {n_pendiente} fichero(s)")
    if n_pendiente:
        for line in pendiente.splitlines()[:10]:
            print(f"    {line}")
        if n_pendiente > 10:
            print(f"    ... y {n_pendiente - 10} mas")

    remoto = refs_remotos()
    print(f"\nRamas en el remoto ({len(remoto)}):")
    for nombre, sha in sorted(remoto.items()):
        marcas = []
        if sha == head:
            marcas.append("== tu HEAD")
        print(f"  {nombre:34} {sha[:12]} {' '.join(marcas)}")

    # ¿Esta la rama actual empujada?
    print()
    if rama in remoto:
        if remoto[rama] == head:
            print(f"[OK] '{rama}' esta empujada: local y remoto coinciden.")
        else:
            adelante = git("rev-list", "--count", f"{remoto[rama]}..{head}")
            atras = git("rev-list", "--count", f"{head}..{remoto[rama]}")
            print(f"[!] '{rama}' DIVERGE del remoto: {adelante} local sin empujar, "
                  f"{atras} en el remoto sin bajar.")
    else:
        print(f"[!] La rama '{rama}' no existe en el remoto (nunca se ha empujado).")

    # ¿Se puede promocionar a main?
    if "main" in remoto:
        print()
        r = subprocess.run(
            ["git", "merge-base", "--is-ancestor", remoto["main"], head], cwd=RAIZ
        )
        if r.returncode == 0:
            n = git("rev-list", "--count", f"{remoto['main']}..{head}")
            if n == "0":
                print("[OK] main y HEAD estan al dia.")
            else:
                print(f"[i] Promocionable a main con FAST-FORWARD (sin --force): "
                      f"faltan {n} commits.")
                print("    -> git push origin HEAD:main")
        else:
            print("[!] main NO se puede promocionar por fast-forward. No usar --force.")

    # Aviso de la trampa
    print()
    print("-" * 68)
    print("Recordatorio: 'git status -sb' y 'git branch -vv' NO son fiables en este")
    print("repo (no hay refs remotos cacheados). Usa este script o 'git ls-remote'.")
    print("-" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
