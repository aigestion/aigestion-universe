#!/usr/bin/env python3
"""
Auto-Sanitizer — Refactor de os.system() a safe_exec (E-02 / Fase 5)
=====================================================================
Convierte automaticamente las 109 llamadas inseguras del repo en llamadas
seguras a safe_exec.run_code() / run_out().

Transformaciones:
    os.system(X)          ->  run_code(X)         (mismo retorno: int)
    os.popen(X).read()    ->  run_out(X)          (mismo retorno: str)
    shell=True            ->  REPORTE (requiere revision manual)

Uso:
    python auto_sanitizer.py                 — informe sin tocar nada
    python auto_sanitizer.py --apply         — aplica los cambios (con .bak)
    python auto_sanitizer.py --verify        — verifica que no queda nada
    python auto_sanitizer.py --file tools.py — solo un archivo
    python auto_sanitizer.py --apply --rollback  — restaura desde .bak

Seguridad:
    - Crea copia .bak de cada archivo antes de modificarlo
    - Verifica con AST que el resultado sigue siendo Python valido
    - No toca nada si el AST no cuadra

Coste: $0 — Python stdlib.
"""

from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

# Raiz del repo (este modulo vive en core/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKUP_SUFFIX = ".bak"

# Directorios que nunca se tocan
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".workbuddy-ai", "data", "backup_patches", "tests",
}

SKIP_FILES = {"auto_sanitizer.py", "safe_exec.py"}

C = {
    "r": "\033[91m", "g": "\033[92m", "y": "\033[93m",
    "c": "\033[96m", "b": "\033[1m", "e": "\033[0m",
}


class Hit(NamedTuple):
    file: str
    line: int
    kind: str            # os_system / os_popen / shell_true
    old: str
    new: Optional[str]   # None = requiere revision manual
    offset_start: int
    offset_end: int


# =============================================================================
# ANALISIS
# =============================================================================

def _line_offsets(src: str) -> List[int]:
    """Offset de inicio de cada linea."""
    offs = [0]
    for ln in src.splitlines(keepends=True):
        offs.append(offs[-1] + len(ln))
    return offs


def _offset(offs: List[int], line: int, col: int) -> int:
    return offs[line - 1] + col


def _segment(src: str, node: ast.AST) -> str:
    """Fuente original de un nodo."""
    try:
        return ast.get_source_segment(src, node) or ""
    except Exception:
        return ""


# Metacaracteres de shell: si aparecen, shlex.split() no basta
SHELL_META = ("|", ">", "<", "&", ";", "$", "`", "\n", "*", "?")


def _has_shell_meta(arg_src: str) -> bool:
    """True si el comando depende del shell (pipes, redirecciones, vars)."""
    return any(m in arg_src for m in SHELL_META)


def analyze(path: Path) -> List[Hit]:
    """Encuentra las llamadas inseguras de un archivo."""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception:
        return []

    rel = str(path.relative_to(PROJECT_ROOT))
    offs = _line_offsets(src)
    hits: List[Hit] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        # os.system(X) / os.popen(X)
        if isinstance(node.func, ast.Attribute) and \
           isinstance(node.func.value, ast.Name) and \
           node.func.value.id == "os" and node.func.attr in ("system", "popen"):
            if not node.args:
                continue
            arg_src = _segment(src, node.args[0])
            if not arg_src:
                continue
            # Si usa pipes/redirecciones, shlex.split() no reproduce el
            # comportamiento -> se deja para revision manual.
            safe = not _has_shell_meta(arg_src)
            if node.func.attr == "system":
                new = f"run_code({arg_src})" if safe else None
                kind = "os_system" if safe else "os_system_shell"
            else:
                new = f"run_out({arg_src})" if safe else None
                kind = "os_popen" if safe else "os_popen_shell"
            hits.append(Hit(
                file=rel, line=node.lineno, kind=kind,
                old=_segment(src, node) or f"os.{node.func.attr}(...)",
                new=new,
                offset_start=_offset(offs, node.lineno, node.col_offset),
                offset_end=_offset(offs, node.end_lineno, node.end_col_offset),
            ))

        # subprocess.<fn>(X, shell=True, ...) -> run_cmd / run_code / run_out
        if isinstance(node.func, ast.Attribute) and \
           isinstance(node.func.value, ast.Name) and \
           node.func.value.id == "subprocess":
            fn = node.func.attr
            has_shell = any(
                kw.arg == "shell" and isinstance(kw.value, ast.Constant)
                and kw.value.value is True for kw in node.keywords)
            has_check = any(
                kw.arg == "check" and isinstance(kw.value, ast.Constant)
                and kw.value.value is True for kw in node.keywords)

            if has_shell and node.args:
                arg_src = _segment(src, node.args[0])
                timeout = None
                for kw in node.keywords:
                    if kw.arg == "timeout" and isinstance(kw.value, ast.Constant):
                        timeout = kw.value.value
                tpart = f", timeout={timeout}" if timeout else ""

                new = None
                if arg_src and not _has_shell_meta(arg_src) and not has_check:
                    if fn == "run":
                        new = f"run_cmd({arg_src}{tpart})"
                    elif fn in ("call", "check_call"):
                        new = f"run_code({arg_src}{tpart})"
                    elif fn in ("check_output", "getoutput", "getstatusoutput"):
                        new = f"run_out({arg_src}{tpart})"

                hits.append(Hit(
                    file=rel, line=node.lineno,
                    kind="shell_true" if new is None else f"subprocess_{fn}",
                    old=(_segment(src, node) or f"subprocess.{fn}(shell=True)")[:90],
                    new=new,
                    offset_start=_offset(offs, node.lineno, node.col_offset),
                    offset_end=_offset(offs, node.end_lineno, node.end_col_offset),
                ))
    return hits


def iter_py_files(only: Optional[str] = None) -> List[Path]:
    """Archivos .py del proyecto (solo raiz por defecto)."""
    if only:
        return [PROJECT_ROOT / only]
    out = []
    for p in sorted(PROJECT_ROOT.glob("*.py")):
        if p.name in SKIP_FILES:
            continue
        out.append(p)
    return out


# =============================================================================
# APLICACION
# =============================================================================

def _needs_import(src: str) -> bool:
    return "from safe_exec import" not in src and "import safe_exec" not in src


def _add_import(src: str, names: List[str]) -> str:
    """Inserta 'from safe_exec import ...' despues de los imports iniciales."""
    lines = src.splitlines(keepends=True)
    imp = f"from safe_exec import {', '.join(sorted(set(names)))}\n"
    last_import = 0
    in_docstring = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"""') or s.startswith("'''"):
            in_docstring = not in_docstring or s.count('"""') == 2
        if in_docstring:
            continue
        if s.startswith("import ") or s.startswith("from "):
            last_import = i
        elif s and not s.startswith("#") and last_import:
            break
    if last_import:
        lines.insert(last_import + 1, imp)
    else:
        lines.insert(0, imp)
    return "".join(lines)


def apply_to(path: Path, hits: List[Hit]) -> int:
    """Aplica los reemplazos. Devuelve el numero de cambios."""
    usable = [h for h in hits if h.new]
    if not usable:
        return 0

    src = path.read_text(encoding="utf-8", errors="replace")

    # Backup
    bak = path.with_suffix(path.suffix + BACKUP_SUFFIX)
    shutil.copy2(path, bak)

    # Reemplazar de atras hacia adelante para no desplazar offsets
    out = src
    for h in sorted(usable, key=lambda x: x.offset_start, reverse=True):
        out = out[:h.offset_start] + h.new + out[h.offset_end:]

    # Import
    names = []
    if any(h.kind in ("os_system", "subprocess_call", "subprocess_check_call")
           for h in usable):
        names.append("run_code")
    if any(h.kind in ("os_popen", "subprocess_check_output",
                      "subprocess_getoutput", "subprocess_getstatusoutput")
           for h in usable):
        names.append("run_out")
    if any(h.kind == "subprocess_run" for h in usable):
        names.append("run_cmd")
    if names and _needs_import(out):
        out = _add_import(out, names)

    # Validar antes de escribir
    try:
        ast.parse(out)
    except SyntaxError as e:
        print(f"  {C['r']}ERROR de sintaxis en {path.name}:{e.lineno} "
              f"— se restaura backup{C['e']}")
        shutil.copy2(bak, path)
        return 0

    path.write_text(out, encoding="utf-8")
    return len(usable)


def rollback() -> int:
    """Restaura todos los .bak."""
    n = 0
    for bak in PROJECT_ROOT.glob(f"*{BACKUP_SUFFIX}"):
        if not bak.name.endswith(".py" + BACKUP_SUFFIX):
            continue
        target = bak.with_suffix("")
        target = Path(str(bak)[:-len(BACKUP_SUFFIX)])
        shutil.copy2(bak, target)
        bak.unlink()
        n += 1
    return n


# =============================================================================
# CLI
# =============================================================================

def verify() -> int:
    """Verifica que no queden os.system/popen (shell=True aparte)."""
    remaining: List[Hit] = []
    for p in iter_py_files():
        remaining.extend([h for h in analyze(p) if h.kind in ("os_system", "os_popen")])
    total_shell = sum(
        1 for p in iter_py_files() for h in analyze(p) if h.kind == "shell_true")

    print(f"\n{C['b']}{C['c']}{'=' * 68}\n  VERIFICACION\n{'=' * 68}{C['e']}")
    if not remaining:
        print(f"  {C['g']}0 os.system() / os.popen() restantes{C['e']}")
    else:
        print(f"  {C['r']}{len(remaining)} restantes:{C['e']}")
        for h in remaining[:20]:
            print(f"    {h.file}:{h.line}  {h.kind}")
    print(f"  {C['y']}{total_shell} shell=True (revision manual){C['e']}")
    return 1 if remaining else 0


def main() -> int:
    args = sys.argv[1:]
    only = None
    if "--file" in args:
        i = args.index("--file")
        only = args[i + 1] if i + 1 < len(args) else None

    if "--rollback" in args:
        n = rollback()
        print(f"{C['y']}Restaurados {n} archivos desde .bak{C['e']}")
        return 0

    if "--verify" in args:
        return verify()

    apply_mode = "--apply" in args

    print(f"\n{C['b']}{C['c']}{'=' * 68}\n  AUTO-SANITIZER — "
          f"{'APLICANDO' if apply_mode else 'INFORME (dry-run)'}\n{'=' * 68}{C['e']}")

    files = iter_py_files(only)
    all_hits: Dict[str, List[Hit]] = {}
    for p in files:
        hits = analyze(p)
        if hits:
            all_hits[p.name] = hits

    total_auto = sum(len([h for h in v if h.new]) for v in all_hits.values())
    total_manual = sum(len([h for h in v if not h.new]) for v in all_hits.values())

    changed = 0
    fixed = 0
    for name in sorted(all_hits):
        hits = all_hits[name]
        auto = [h for h in hits if h.new]
        manual = [h for h in hits if not h.new]
        print(f"\n  {C['b']}{name}{C['e']}  "
              f"{len(auto)} auto · {len(manual)} manual")
        for h in hits[:4]:
            tag = C["g"] if h.new else C["y"]
            print(f"    L{h.line:<4} {tag}{h.kind}{C['e']}  {h.old[:66]}")
            if h.new:
                print(f"           {C['c']}->{C['e']} {h.new[:66]}")
        if len(hits) > 4:
            print(f"    ... y {len(hits) - 4} mas")

        if apply_mode and auto:
            n = apply_to(PROJECT_ROOT / name, hits)
            if n:
                changed += 1
                fixed += n
                print(f"    {C['g']}aplicado ({n} cambios, .bak creado){C['e']}")

    print(f"\n  {C['b']}RESUMEN{C['e']}")
    print(f"    convertibles automaticamente : {total_auto}")
    print(f"    requieren revision manual    : {total_manual} (shell=True)")
    if apply_mode:
        print(f"    {C['g']}archivos modificados: {changed} · llamadas: {fixed}{C['e']}")
        print(f"    backups en *.py{C['g']}{BACKUP_SUFFIX}{C['e']} — "
              f"revierte con --rollback")
    else:
        print(f"\n  Ejecuta con {C['b']}--apply{C['e']} para convertir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())