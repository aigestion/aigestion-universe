"""Seed the knowledge base from the project's own documentation.

Run as a module::

    python3 -m mcp.rag.seed

Ingesting the repository's own markdown gives the retrieval stack real Spanish
prose to rank against, instead of three hardcoded English fragments.
"""

from __future__ import annotations

import pathlib
import sys

from .engine import RAGConfig, RAGEngine

__all__ = ["SOURCES", "seed", "main"]

# (path, category) relative to the repository root.
SOURCES: tuple[tuple[str, str], ...] = (
    ("README.md", "docs"),
    ("summary.md", "docs"),
    ("obsidian_vault/README.md", "docs"),
    ("aig-shared/README.md", "docs"),
)

AGENT_DOCS: tuple[tuple[str, str], ...] = tuple(
    (f"phone/agents/agent_{i}.py", "agents") for i in range(1, 10)
) + tuple((f"phone/agents/subagent_{i}.py", "subagents") for i in range(1, 25))


def _collect(root: pathlib.Path) -> list[dict]:
    documents: list[dict] = []
    for relative, category in SOURCES + AGENT_DOCS:
        path = root / relative
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        documents.append(
            {
                "doc_id": relative,
                "title": path.stem.replace("_", " ").title(),
                "content": content,
                "category": category,
                "source": str(path),
            }
        )
    return documents


def seed(root: str | pathlib.Path = "/root", db_path: str | None = None, rebuild: bool = True) -> int:
    """Ingest project documentation into the knowledge base.

    Returns the number of chunks indexed.
    """
    root_path = pathlib.Path(root)
    config = RAGConfig(db_path=db_path) if db_path else RAGConfig()
    engine = RAGEngine(config)
    documents = _collect(root_path)
    engine.ingest_many(documents, rebuild=rebuild)
    return len(documents)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = argv[0] if argv else "/root"
    documents = _collect(pathlib.Path(root))
    engine = RAGEngine(RAGConfig())
    engine.ingest_many(documents)
    stats = engine.stats()
    print(f"Documentos ingeridos: {len(documents)}")
    print(f"Fragmentos indexados:  {stats['indexed_chunks']}")
    print(f"Embedding backend:    {stats['embedding_backend']} (dim={stats['embedding_dim']})")
    print(f"Almacenamiento:        {stats['path']} (persistente={stats['persistent']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
