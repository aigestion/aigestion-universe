"""MCPs: Model Context Protocol para exponer tools a agentes.

Unificacion 2026-10-03: aqui conviven los 6 MCP servers (antes `mcps/` en la
raiz, luego `skills/mcps/`) y el RAG (antes paquete `mcp.rag`, luego `rag/`).
Namespace unico: `mcps.ai_mcp`, `mcps.rag`, ... El antiguo `mcp/tool_*.py`
(7 ficheros) quedo obsoleto y se elimino en la reestructura.
"""
