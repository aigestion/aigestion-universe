#!/usr/bin/env python3
"""
Secret Guard — Escudo Anti-Secretos para AIGestion / DanielaOS
===============================================================
Bloquea commits que contengan API keys, private keys, seed phrases o
credenciales. Es la respuesta al hallazgo P0 del 2026-09-10: .env estuvo
commiteado en HEAD con una Gemini API key real.

Uso:
    python scripts/secret_guard.py              — escanea el staging area
    python scripts/secret_guard.py --all        — escanea todo el working tree
    python scripts/secret_guard.py --history    — escanea todo el historial git
    python scripts/secret_guard.py --install    — instala el pre-commit hook
    python scripts/secret_guard.py --uninstall  — desinstala el hook

El hook se instala en .githooks/pre-commit y se activa con:
    git config core.hooksPath .githooks

Coste: $0 — Python stdlib puro, sin dependencias.
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOOK_DIR = PROJECT_ROOT / ".githooks"
HOOK_FILE = HOOK_DIR / "pre-commit"
ALLOW_FILE = PROJECT_ROOT / ".secretguard-allow"

# Archivos que nunca se escanean (binarios, lockfiles, etc.)
NEVER_SCAN = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp3",
    ".mp4",
    ".wav",
    ".webm",
    ".pyc",
    ".so",
    ".dll",
    ".exe",
}

# Rutas ignoradas
IGNORED_PATHS = {
    "scripts/secret_guard.py",
    ".githooks/pre-commit",
}

C = {
    "r": "\033[91m",
    "g": "\033[92m",
    "y": "\033[93m",
    "c": "\033[96m",
    "b": "\033[1m",
    "e": "\033[0m",
}


class Finding(NamedTuple):
    file: str
    line: int
    rule: str
    severity: str  # P0 / P1 / P2
    snippet: str
    advice: str


# =============================================================================
# REGLAS DE DETECCION
# =============================================================================

RULES: list[dict] = [
    {
        "id": "GOOGLE_API_KEY",
        "severity": "P0",
        "regex": r"AIza[0-9A-Za-z_\-]{35}",
        "advice": "Key de Google/Gemini. Revocala en console.cloud.google.com.",
    },
    {
        "id": "OPENAI_KEY",
        "severity": "P0",
        "regex": r"\bsk-[A-Za-z0-9]{20,}",
        "advice": "Key de OpenAI. Revocala en platform.openai.com/api-keys.",
    },
    {
        "id": "ANTHROPIC_KEY",
        "severity": "P0",
        "regex": r"\bsk-ant-[A-Za-z0-9_\-]{20,}",
        "advice": "Key de Anthropic. Revocala en console.anthropic.com.",
    },
    {
        "id": "AWS_ACCESS_KEY",
        "severity": "P0",
        "regex": r"\bAKIA[0-9A-Z]{16}\b",
        "advice": "Access key de AWS. Desactivala en IAM.",
    },
    {
        "id": "GITHUB_TOKEN",
        "severity": "P0",
        "regex": r"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
        "advice": "Token de GitHub. Revocalo en Settings > Developer settings.",
    },
    {
        "id": "SLACK_TOKEN",
        "severity": "P1",
        "regex": r"\bxox[baprs]-[A-Za-z0-9\-]{10,}",
        "advice": "Token de Slack. Revocalo en api.slack.com.",
    },
    {
        "id": "PRIVATE_KEY",
        "severity": "P0",
        "regex": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----",
        "advice": "Clave privada. Comprometida: regenerala por completo.",
    },
    {
        "id": "JWT_SECRET",
        "severity": "P1",
        "regex": r"(?:JWT_SECRET|SECRET_KEY|SESSION_SECRET)\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{24,}",
        "advice": "Secreto de sesion. Rotalo y muevelo a variable de entorno.",
    },
    {
        "id": "DATABASE_URL",
        "severity": "P1",
        "regex": r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:@]+:[^\s@]{4,}@",
        "advice": "URL de BD con password embebido. Muevela a variable de entorno.",
    },
    {
        "id": "TELEGRAM_TOKEN",
        "severity": "P1",
        "regex": r"\b\d{8,10}:AA[A-Za-z0-9_\-]{33}\b",
        "advice": "Token de bot de Telegram. Regeneralo con @BotFather.",
    },
    {
        "id": "SEED_PHRASE_LABEL",
        "severity": "P0",
        "regex": r"(?i)(?:seed|mnemonic|frase[_ ]?semilla|recovery[_ ]?phrase)\s*[=:]\s*"
        r"[\"']?((?:[a-z]{3,10}\s+){11,23}[a-z]{3,10})",
        "advice": "SEED PHRASE DE CRIPTO. Mueve los fondos a una wallet nueva YA.",
    },
]

# Palabras que indican que la linea es un placeholder / ejemplo
PLACEHOLDER_HINTS = (
    "your_",
    "your-",
    "xxx",
    "placeholder",
    "example",
    "ejemplo",
    "changeme",
    "change_me",
    "todo",
    "fixme",
    "<",
    "insert",
    "replace",
    "xxxxxxx",
    "000000",
    "aaaaaa",
    "sample",
    "dummy",
    "fake",
    "test_key",
)


def _is_placeholder(line: str, match: str) -> bool:
    """Descarta falsos positivos evidentes."""
    low = line.lower()
    if any(h in low for h in PLACEHOLDER_HINTS):
        return True
    # secuencias repetidas tipo AAAA... o 1234...
    val = match.strip("\"'")
    if re.fullmatch(r"(.)\1{7,}", val):
        return True
    if re.fullmatch(r"(?:0123|1234|1234567890|abcdefgh)\w*", val, re.I):
        return True
    return False


def _shannon(s: str) -> float:
    """Entropia de Shannon — detecta strings aleatorios."""
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def _check_entropy(file: str, line_no: int, line: str) -> Finding | None:
    """Detecta asignaciones tipo KEY=valor con alta entropia (posible secreto)."""
    m = re.search(
        r"(?i)\b(\w*(?:key|token|secret|password|passwd|pwd|credential)\w*)\s*[=:]\s*"
        r"[\"']([A-Za-z0-9_\-/+]{28,})[\"']",
        line,
    )
    if not m:
        return None
    name, value = m.group(1), m.group(2)
    if _is_placeholder(line, value):
        return None
    if _shannon(value) < 3.6:  # no es aleatorio -> no es secreto
        return None
    return Finding(
        file=file,
        line=line_no,
        rule="HIGH_ENTROPY",
        severity="P2",
        snippet=f"{name}={value[:12]}... ({len(value)} chars)",
        advice=f"Valor aleatorio de alta entropia en '{name}'. "
        f"Muevelo a .env si es un secreto real.",
    )


def scan_text(file: str, text: str) -> list[Finding]:
    """Escanea un texto y devuelve los hallazgos."""
    findings: list[Finding] = []
    if not text:
        return findings
    for i, line in enumerate(text.splitlines(), 1):
        if len(line) > 4000:  # linea gigante (minificado) -> saltar
            continue
        for rule in RULES:
            for m in re.finditer(rule["regex"], line):
                if _is_placeholder(line, m.group(0)):
                    continue
                snippet = m.group(0)
                if len(snippet) > 60:
                    snippet = snippet[:57] + "..."
                findings.append(
                    Finding(
                        file=file,
                        line=i,
                        rule=rule["id"],
                        severity=rule["severity"],
                        snippet=snippet,
                        advice=rule["advice"],
                    )
                )
        f = _check_entropy(file, i, line)
        if f:
            findings.append(f)
    return findings


def _is_scannable(path: str) -> bool:
    if path in IGNORED_PATHS:
        return False
    return Path(path).suffix.lower() not in NEVER_SCAN


def _load_allowlist() -> set:
    if not ALLOW_FILE.exists():
        return set()
    out = set()
    for ln in ALLOW_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            out.add(ln)
    return out


def scan_staged() -> list[Finding]:
    """Escanea los archivos en el staging area."""
    allow = _load_allowlist()
    findings: list[Finding] = []
    try:
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
        ).stdout.splitlines()
    except Exception as e:
        print(f"{C['r']}No se pudo leer el staging area: {e}{C['e']}")
        return []
    for path in staged:
        path = path.strip()
        if not path or not _is_scannable(path):
            continue
        try:
            content = subprocess.run(
                ["git", "show", f":{path}"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            ).stdout
        except Exception:
            continue
        for f in scan_text(path, content):
            if f"{f.file}:{f.line}" in allow or f.file in allow:
                continue
            findings.append(f)
    return findings


def scan_worktree() -> list[Finding]:
    """Escanea todo el working tree (respetando .gitignore via git ls-files)."""
    allow = _load_allowlist()
    findings: list[Finding] = []
    try:
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
        ).stdout.splitlines()
    except Exception:
        tracked = []
    for path in tracked:
        path = path.strip()
        if not path or not _is_scannable(path) or path in IGNORED_PATHS:
            continue
        p = PROJECT_ROOT / path
        if not p.exists():
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for f in scan_text(path, content):
            if f"{f.file}:{f.line}" in allow or f.file in allow:
                continue
            findings.append(f)
    return findings


def scan_history() -> list[Finding]:
    """Escanea TODO el historial git — revela secretos ya commiteados."""
    findings: list[Finding] = []
    seen = set()
    try:
        revs = subprocess.run(
            ["git", "rev-list", "--all"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=60,
        ).stdout.split()
    except Exception as e:
        print(f"{C['r']}No se pudo leer el historial: {e}{C['e']}")
        return []
    for rev in revs:
        try:
            files = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", rev],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            ).stdout.splitlines()
        except Exception:
            continue
        for path in files:
            path = path.strip()
            if not path or not _is_scannable(path) or path in IGNORED_PATHS:
                continue
            key = (rev[:8], path)
            if key in seen:
                continue
            seen.add(key)
            try:
                content = subprocess.run(
                    ["git", "show", f"{rev}:{path}"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=30,
                ).stdout
            except Exception:
                continue
            for f in scan_text(f"{rev[:8]}:{path}", content):
                findings.append(f)
    return findings


# =============================================================================
# HOOK
# =============================================================================

HOOK_SCRIPT = """#!/bin/sh
# Secret Guard — bloquea commits con credenciales
# Instalado por: python scripts/secret_guard.py --install
python scripts/secret_guard.py || exit 1
"""


def install_hook() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    HOOK_FILE.write_text(HOOK_SCRIPT, encoding="utf-8")
    try:
        subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            cwd=PROJECT_ROOT,
            check=True,
            timeout=15,
        )
    except Exception as e:
        print(f"{C['r']}No se pudo configurar core.hooksPath: {e}{C['e']}")
        return 1
    print(f"{C['g']}Hook instalado{C['e']}: {HOOK_FILE}")
    print(f"{C['g']}core.hooksPath{C['e']} = .githooks")
    return 0


def uninstall_hook() -> int:
    try:
        subprocess.run(
            ["git", "config", "--unset", "core.hooksPath"],
            cwd=PROJECT_ROOT,
            timeout=15,
        )
    except Exception:
        pass
    if HOOK_FILE.exists():
        HOOK_FILE.unlink()
    print(f"{C['y']}Hook desinstalado{C['e']}")
    return 0


# =============================================================================
# CLI
# =============================================================================


def _report(findings: list[Finding], title: str) -> int:
    order = {"P0": 0, "P1": 1, "P2": 2}
    findings.sort(key=lambda f: (order[f.severity], f.file, f.line))
    print(f"\n{C['b']}{C['c']}{'=' * 72}\n  {title}\n{'=' * 72}{C['e']}")
    if not findings:
        print(f"  {C['g']}Sin secretos detectados.{C['e']}\n")
        return 0
    counts = {s: sum(1 for f in findings if f.severity == s) for s in ("P0", "P1", "P2")}
    print(
        f"  {C['r']}{counts['P0']} P0{C['e']} · "
        f"{C['y']}{counts['P1']} P1{C['e']} · "
        f"{C['c']}{counts['P2']} P2{C['e']} · {len(findings)} total\n"
    )
    for f in findings:
        col = {"P0": C["r"], "P1": C["y"], "P2": C["c"]}[f.severity]
        print(f"  {col}[{f.severity}]{C['e']} {f.rule}")
        print(f"      {f.file}:{f.line}")
        print(f"      {f.snippet}")
        print(f"      {C['y']}→{C['e']} {f.advice}")
    print(
        f"\n  {C['b']}Para permitir una excepcion, anade "
        f"'<archivo>:<linea>' a .secretguard-allow{C['e']}\n"
    )
    return 1 if counts["P0"] else 0


def main() -> int:
    args = sys.argv[1:]
    if "--install" in args:
        return install_hook()
    if "--uninstall" in args:
        return uninstall_hook()
    if "--history" in args:
        return _report(scan_history(), "SECRET GUARD — HISTORIAL COMPLETO")
    if "--all" in args:
        return _report(scan_worktree(), "SECRET GUARD — WORKING TREE")
    return _report(scan_staged(), "SECRET GUARD — STAGING AREA")


if __name__ == "__main__":
    sys.exit(main())
