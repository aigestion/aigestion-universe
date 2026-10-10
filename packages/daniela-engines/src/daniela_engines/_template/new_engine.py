"""Scaffold a new engine from the canonical template.

Usage (from repo root):
    python engine/_template/new_engine.py <slug> <port>

Creates engine/<slug>/ with placeholders replaced. Refuses to overwrite.
"""
import re
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent
ENGINE_DIR = TEMPLATE_DIR.parent


def main() -> int:
    if len(sys.argv) != 3 or not re.fullmatch(r"[a-z][a-z0-9_]*", sys.argv[1] or ""):
        print("usage: python engine/_template/new_engine.py <slug> <port>")
        return 2
    slug, port = sys.argv[1], sys.argv[2]
    if not port.isdigit() or not (1024 <= int(port) <= 65535):
        print("port must be 1024-65535")
        return 2
    dest = ENGINE_DIR / slug
    if dest.exists():
        print(f"refusing: {dest} already exists")
        return 1
    dest.mkdir()
    for src in TEMPLATE_DIR.iterdir():
        if src.name in ("new_engine.py", "README.md") or not src.is_file():
            continue
        text = src.read_text(encoding="utf-8")
        text = text.replace("{{slug}}", slug).replace("{{SLUG}}", slug)
        text = text.replace("{{NAME}}", slug.replace("_", " ").title())
        text = text.replace("{{PORT}}", port)
        (dest / src.name).write_text(text, encoding="utf-8")
    print(f"scaffolded {dest} ({len(list(dest.iterdir()))} files)")
    print("next: implement modules, add compose block + nginx location (see README)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
