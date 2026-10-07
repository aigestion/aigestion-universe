"""Convert between Daniela memories and Obsidian markdown."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
import re


@dataclass
class MemoryDoc:
    id: str
    tier: str
    content: str
    importance: float = 0.5
    tags: list[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []


def memory_to_markdown(mem: MemoryDoc) -> str:
    """Render a memory as an Obsidian note with YAML frontmatter."""
    created = mem.created_at.isoformat() if mem.created_at else datetime.utcnow().isoformat()
    tags = " ".join(f"#{t}" for t in mem.tags)
    frontmatter = (
        "---\n"
        f"id: {mem.id}\n"
        f"tier: {mem.tier}\n"
        f"importance: {mem.importance}\n"
        f"created: {created}\n"
        f"tags: [{tags}]\n"
        "---\n\n"
    )
    return frontmatter + mem.content


def markdown_to_memory(md: str) -> MemoryDoc:
    """Parse an Obsidian note back into a MemoryDoc."""
    fm_match = re.match(r"^---\n(.*?)\n---\n\n?(.*)$", md, re.DOTALL)
    meta: Dict[str, Any] = {}
    body = md
    if fm_match:
        fm, body = fm_match.group(1), fm_match.group(2)
        for line in fm.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    tags = re.findall(r"#(\w+)", meta.get("tags", ""))
    return MemoryDoc(
        id=meta.get("id", ""),
        tier=meta.get("tier", "episodic"),
        content=body.strip(),
        importance=float(meta.get("importance", 0.5)),
        tags=tags,
    )
