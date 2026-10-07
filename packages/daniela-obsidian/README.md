# daniela-obsidian

Two-way sync between Daniela OS memory and an Obsidian vault.

Memories become Obsidian notes (with YAML frontmatter for
id/tier/importance/tags). Edits in Obsidian flow back.

```python
from daniela_obsidian import VaultSync, MemoryDoc
from datetime import datetime

sync = VaultSync("~/Documents/ObsidianVault/Daniela")

memories = [
    MemoryDoc(id="abc123", tier="semantic",
              content="Daniela runs on port 9200",
              tags=["daniela", "core"],
              created_at=datetime.utcnow()),
]

await sync.sync(memories)          # memory -> vault
docs = sync.scan_vault()           # vault -> memory
```

Notes are plain Markdown, so they stay portable and
human-editable.
