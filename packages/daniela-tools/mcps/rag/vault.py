"""Generate the Obsidian vault from the indexed knowledge base.

The vault layout has been documented since the first revision but the note
directories never existed. This builds them from the live index, so the notes
cannot drift from the corpus the retriever actually serves.

Run as a module::

    python3 -m mcp.rag.vault
"""

from __future__ import annotations

import pathlib
import re
import sys
from collections.abc import Sequence

from .store import DocumentStore

__all__ = ["VAULT_CATEGORIES", "generate_vault", "main"]

# category -> directory name inside the vault
VAULT_CATEGORIES: dict[str, str] = {
    "agents": "agents",
    "subagents": "subagents",
    "docs": "agents",  # documentation lives alongside the agents it describes
    "mcps": "mcps",
    "dashboards": "dashboards",
}

DEFAULT_VAULT = pathlib.Path("/root/obsidian_vault")


def _safe_name(name: str) -> str:
    """Turn an identifier into a readable, filesystem-safe note name."""
    stem = pathlib.Path(name).stem
    # agent_7 -> Agent 7
    match = re.fullmatch(r"(agent|subagent)_(\d+)", stem, re.IGNORECASE)
    if match:
        return f"{match.group(1).title()} {match.group(2)}"
    return stem.replace("_", " ").replace("-", " ").strip() or "Untitled"


def _source_line(document: dict) -> str:
    source = str(document.get("source") or "")
    if not source:
        return ""
    try:
        return f"`{pathlib.Path(source).relative_to('/root')}`"
    except ValueError:
        return f"`{source}`"


# Lines that are obviously source code rather than prose.
_CODE_PATTERNS = (
    re.compile(r"^[\w.\[\]]+\s*[:=]\s"),  # assignments and bare dict entries
    re.compile(r"^[\w.\[\]]+\s*=\s*$"),  # bare assignments
    re.compile(r'^["\'][\w\s.-]*["\']\s*:'),  # quoted keys of a dict literal
    re.compile(r"^[\[\{\(].*[\]\}\)]\s*,?$"),  # list / dict / tuple literals
    re.compile(r"^(return|yield|pass|raise|assert|print|break|continue)\b"),
    re.compile(r"^(if|elif|else|for|while|try|except|finally|with)\b"),
    re.compile(r"^[)\]}]+[,:]?\s*$"),  # closing brackets
    re.compile(r"^(self|cls)\."),
    re.compile(r"^\w+\(.*\)[,:]?\s*$"),  # calls
    re.compile(r"^(True|False|None)\b"),
)


def _is_code_line(line: str) -> bool:
    """Whether a line is source code rather than prose."""
    return any(pattern.match(line) for pattern in _CODE_PATTERNS)


def _summarise(content: str, max_lines: int = 12) -> str:
    """First meaningful prose of a document, ignoring code structure.

    Agent sources are Python files, so the note would otherwise duplicate the
    whole file, which makes the vault useless for reading. Module and class
    docstrings are what actually describe a component, so those are kept and
    the implementation is dropped.
    """
    lines: list[str] = []
    in_docstring = False

    for raw in content.splitlines():
        stripped = raw.strip()
        if not stripped:
            if in_docstring:
                lines.append("")
            continue

        if in_docstring:
            if stripped.endswith(('"""', "'''")):
                in_docstring = False
                lines.append(stripped.rstrip('"').rstrip("'").strip())
            else:
                lines.append(stripped)
            continue

        if stripped.startswith(('"""', "'''")):
            quote = stripped[:3]
            remainder = stripped[3:]
            # A docstring that opens and closes on one line is self-contained.
            # Otherwise it continues on the following lines, and whatever sits
            # after the opening quote is its first sentence.
            trailing = remainder.rstrip()
            if trailing.endswith(quote) and trailing != quote:
                lines.append(trailing[:-3].strip())
            elif remainder.strip():
                lines.append(remainder.strip())
                in_docstring = True
            else:
                in_docstring = True
            continue

        # Skip implementation: imports, decorators, signatures, assignments,
        # literals and comments. Only prose survives into the note.
        if stripped.startswith(("import ", "from ", "@", "def ", "class ", "#")):
            continue
        if _is_code_line(stripped):
            continue

        lines.append(stripped)

    prose = [line for line in lines if line]
    if not prose:
        return ""
    if len(prose) > max_lines:
        prose = prose[:max_lines] + ["_..._"]
    return "\n".join(prose)


def _render_note(document: dict, related: Sequence[dict], db: DocumentStore) -> str:
    """Render one note: frontmatter, summary, content and backlinks."""
    title = str(document.get("title") or _safe_name(str(document.get("doc_id"))))
    category = str(document.get("category") or "general")
    doc_id = str(document.get("doc_id"))

    lines: list[str] = []
    lines.append("---")
    lines.append(f'title: "{title}"')
    lines.append(f"category: {category}")
    lines.append(f"doc_id: {doc_id}")
    updated = str(document.get("updated_at") or "")
    if updated:
        lines.append(f"updated: {updated}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")

    source = _source_line(document)
    if source:
        lines.append(f"**Fuente:** {source}")
        lines.append("")

    chunks = [c for c in db.load_chunks() if c["doc_id"] == doc_id]
    lines.append(f"**Fragmentos indexados:** {len(chunks)}")
    lines.append("")

    body = _summarise(str(document.get("content") or ""))
    lines.append("## Descripción")
    lines.append("")
    lines.append(body if body else "_(sin descripcion)_")
    lines.append("")

    if related:
        lines.append("## Relacionado")
        lines.append("")
        for other in related:
            other_title = str(other.get("title") or _safe_name(str(other.get("doc_id"))))
            VAULT_CATEGORIES.get(str(other.get("category")), "agents")
            lines.append(f"- [[{_safe_name(other_title)}]] ({other.get('category')})")
        lines.append("")

    return "\n".join(lines)


def _related_documents(document: dict, all_documents: Sequence[dict], limit: int = 5) -> list[dict]:
    """Nearest neighbours by shared distinctive tokens.

    Uses the store's own vocabulary rather than a separate graph so the vault
    reflects what retrieval actually considers similar.
    """
    from .text import tokenize

    doc_tokens = set(tokenize(str(document.get("content") or "")))
    if not doc_tokens:
        return []

    scored = []
    for other in all_documents:
        if other["doc_id"] == document["doc_id"]:
            continue
        other_tokens = set(tokenize(str(other.get("content") or "")))
        if not other_tokens:
            continue
        intersection = len(doc_tokens & other_tokens)
        if intersection < 2:
            continue
        union = len(doc_tokens | other_tokens)
        scored.append((intersection / union, other))

    scored.sort(key=lambda item: -item[0])
    return [other for _, other in scored[:limit]]


def generate_vault(
    root: str = "/root",
    vault: str | None = None,
    db_path: str | None = None,
) -> dict[str, int]:
    """Write one note per indexed document.

    Returns:
        Counts of notes written and directories created.
    """
    root_path = pathlib.Path(root)
    vault_path = pathlib.Path(vault) if vault else root_path / "obsidian_vault"

    db = DocumentStore(db_path) if db_path else DocumentStore()
    documents = db.load_documents()
    if not documents:
        raise SystemExit(
            "La base de conocimiento esta vacia. Ejecute primero: python3 -m mcp.rag.seed"
        )

    written = 0
    directories = 0
    used_dirs = {VAULT_CATEGORIES.get("agents", "agents")}

    for document in documents:
        category = str(document.get("category") or "general")
        directory_name = VAULT_CATEGORIES.get(category, "agents")
        directory = vault_path / directory_name
        directory.mkdir(parents=True, exist_ok=True)
        used_dirs.add(directory_name)

        title = str(document.get("title") or _safe_name(str(document.get("doc_id"))))
        note_path = directory / f"{_safe_name(title)}.md"
        related = _related_documents(document, documents)
        note_path.write_text(_render_note(document, related, db), encoding="utf-8")
        written += 1

    for name in used_dirs:
        if not (vault_path / name).exists():
            directories += 1
        (vault_path / name).mkdir(parents=True, exist_ok=True)

    return {"notes": written, "directories": len(used_dirs)}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = argv[0] if argv else "/root"
    stats = generate_vault(root=root)
    print(f"Notas generadas: {stats['notes']}")
    print(f"Directorios:     {stats['directories']}")
    print(f"Vault:           {root}/obsidian_vault")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
