import json
import os

GRAPH_FILE = os.path.expanduser("~/daniela-os/graph_memory.json")

def load_graph():
    if not os.path.exists(GRAPH_FILE):
        default_graph = {
            "nodes": [
                {"id": "Daniela_OS", "type": "Core"},
                {"id": "Pixel_Termux", "type": "Host"},
                {"id": "server-ai", "type": "RemoteNode"}
            ],
            "edges": [
                {"source": "Daniela_OS", "target": "Pixel_Termux", "relation": "runs_on"},
                {"source": "Daniela_OS", "target": "server-ai", "relation": "delegates_to"}
            ]
        }
        with open(GRAPH_FILE, "w") as f:
            json.dump(default_graph, f, indent=2)
        return default_graph
    with open(GRAPH_FILE) as f:
        return json.load(f)

def add_relation(source, target, relation):
    """
    Skill #32C: Sovereign Knowledge Graph.
    Añade nodos y relaciones al grafo de memoria.
    """
    graph = load_graph()

    # Asegurar nodos
    node_ids = [n["id"] for n in graph["nodes"]]
    if source not in node_ids:
        graph["nodes"].append({"id": source, "type": "Entity"})
    if target not in node_ids:
        graph["nodes"].append({"id": target, "type": "Entity"})

    # Añadir arista
    graph["edges"].append({"source": source, "target": target, "relation": relation})

    with open(GRAPH_FILE, "w") as f:
        json.dump(graph, f, indent=2)

    return f"🕸️ [KNOWLEDGE GRAPH]: Relación registrada: ({source}) --[{relation}]--> ({target})."

def query_graph():
    graph = load_graph()
    n_count = len(graph["nodes"])
    e_count = len(graph["edges"])
    return f"🕸️ [KNOWLEDGE GRAPH]: Grafo activo con {n_count} Nodos y {e_count} Relaciones registradas."
