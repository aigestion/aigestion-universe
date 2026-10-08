"""Bilingual (Spanish/English) domain lexicon.

The corpus is written in Spanish while much of the original vocabulary is
English, and users query in whichever language they think in. Neither BM25 nor
TF-IDF can bridge that: "cuellos de botella" and "bottleneck" share no token, so
one of them always returns nothing.

Rather than force the corpus into a single language, queries are expanded with
the other side of every term they contain. This keeps the corpus readable in
whichever language it was authored in and makes retrieval work in both.

Scope is deliberately the project's own domain vocabulary, not general
translation. A general bilingual lexicon would need stemming across two
languages and would add far more noise than signal.
"""

from __future__ import annotations

from .text import stem, tokenize

__all__ = ["PHRASES", "TOKEN_EQUIVALENTS", "expand_bilingual", "apply_phrases"]

# Multi-word terms, applied to the normalised string before tokenisation.
# Both directions are listed so the map stays symmetric.
PHRASES: tuple[tuple[str, str], ...] = (
    ("cuello de botella", "bottleneck"),
    ("cuellos de botella", "bottleneck"),
    ("datos", "data"),
    ("seguridad", "security"),
    ("monitoreo", "monitoring"),
    ("despliegue", "deployment"),
    ("aprendizaje", "learning"),
    ("coordinacion", "coordination"),
    ("coordinador central", "central coordinator"),
    ("procesamiento de datos", "data processing"),
    ("interaccion con usuario", "user interaction"),
    ("memoria", "memory"),
    ("concurrencia", "concurrency"),
    ("eficiencia", "efficiency"),
    ("capacidad", "capacity"),
    ("carga", "load"),
    ("cola", "queue"),
    ("cache", "cache"),
    ("escalado", "scaling"),
    ("orquestacion", "orchestration"),
    ("sincronizacion", "synchronization"),
    ("dependencia", "dependency"),
    ("metricas", "metrics"),
    ("configuracion", "configuration"),
    ("interfaz", "interface"),
    ("conector", "connector"),
    ("proveedor", "provider"),
    ("eventos", "events"),
)

# Single-token equivalences, keyed by stemmed form, in both directions.
_EQUIVALENT_GROUPS: tuple[tuple[str, ...], ...] = (
    ("agent", "agente"),
    ("subagent", "subagente"),
    ("coordinador", "coordinator", "coordinar", "coordinate"),
    ("orquestar", "orchestrate", "orquesta", "orchestrator"),
    ("dato", "data"),
    ("procesar", "process", "procesamiento", "processing"),
    ("transformar", "transform", "transformacion", "transformation"),
    ("limpiar", "clean", "limpieza", "cleaning"),
    ("validar", "validate", "validacion", "validation"),
    ("interaccion", "interaction", "interactuar", "interact"),
    ("usuario", "user"),
    ("respuesta", "response", "responder", "respond"),
    ("analisis", "analysis", "analizar", "analyze", "analyzing", "analytics"),
    ("patron", "pattern"),
    ("deteccion", "detection", "detectar", "detect", "detector"),
    ("seguridad", "security"),
    ("amenaza", "threat"),
    ("acceso", "access"),
    ("autorizado", "authorized", "unauthorized"),
    ("comunicacion", "communication"),
    ("mensaje", "message"),
    ("enrutamiento", "routing", "enrutar", "route", "router"),
    ("aprendizaje", "learning", "aprender", "learn"),
    ("entrenar", "train", "entrenamiento", "training"),
    ("modelo", "model"),
    ("rendimiento", "performance"),
    ("despliegue", "deployment", "deploy", "desplegar"),
    (
        "monitoreo",
        "monitoring",
        "monitorizar",
        "monitor",
        "monitorear",
        "supervisar",
        "monitorizacion",
        "monitorización",
        "monitorizar",
        "monitoriza",
        "monitorea",
        "supervision",
        "observabilidad",
    ),
    ("metrica", "metric", "medir", "measure"),
    ("tarea", "task", "tareas", "task"),
    ("dependencia", "dependency"),
    ("ciclo", "cycle"),
    ("conflicto", "conflict"),
    ("cuello", "bottleneck"),
    ("botella", "bottleneck"),
    ("latencia", "latency"),
    ("caudal", "throughput"),
    ("memoria", "memory"),
    ("concurrencia", "concurrency", "concurrente", "concurrent"),
    ("cola", "queue", "encolar", "queue"),
    ("cache", "cache", "cachear"),
    ("cargar", "load", "carga", "load"),
    ("balancear", "balance", "balanceador", "balancer", "balanced"),
    ("escalar", "scale", "escalado", "scaling", "escalamiento", "scale"),
    ("capacidad", "capacity"),
    ("planificador", "planner", "planificar", "plan"),
    ("pronosticar", "forecast", "pronostico", "forecast"),
    ("optimizar", "optimize", "optimizacion", "optimization", "optimizer"),
    ("eficiencia", "efficiency", "eficiente", "efficiency"),
    ("alerta", "alert"),
    ("formato", "format", "formatear", "format"),
    ("predecir", "predict", "prediccion", "prediction"),
    ("contenedor", "container"),
    ("persistente", "persistent"),
    ("emoción", "emotion", "emocion"),
    ("reforzamiento", "reinforcement"),
    ("estado", "state"),
    ("registro", "log", "registrar", "log"),
    ("proveedor", "provider", "provide"),
    ("interfaz", "interface", "adapter", "adaptador"),
    ("conector", "connector", "connect", "conectar"),
    ("flujo", "stream", "streaming"),
    ("centralizado", "centralized", "central"),
    ("distribuido", "distributed"),
    ("restricción", "constraint", "restriccion", "limitar", "limit"),
    ("operación", "operation", "operacion"),
    ("etapa", "stage"),
    ("umbral", "threshold"),
    ("reducir", "reduce", "reduccion", "reduction"),
    ("impulso", "boost", "impulsar", "booster"),
    ("asignar", "allocate", "asignacion", "allocation", "allocator"),
    ("recurso", "resource"),
    ("saturacion", "saturation"),
    ("porcentaje", "percentage"),
)


def _build_equivalents() -> dict[str, list[str]]:
    """Expand each group into token -> [equivalents], stemmed both ways."""
    table: dict[str, set] = {}
    for group in _EQUIVALENT_GROUPS:
        stems = {stem(word) for word in group}
        for word in stems:
            table.setdefault(word, set()).update(stems - {word})
    return {token: sorted(others) for token, others in table.items()}


TOKEN_EQUIVALENTS: dict[str, list[str]] = _build_equivalents()


def apply_phrases(text: str, normalize_fn=None) -> list[str]:
    """Return the alternate-language renderings of any known phrase in ``text``.

    Works on the raw string so multi-word terms survive tokenisation.
    """
    from .text import normalize

    normalize_fn = normalize_fn or normalize
    lowered = normalize_fn(text)
    found: list[str] = []
    for source, target in PHRASES:
        if source in lowered and target not in found:
            found.append(target)
        if target in lowered and source not in found:
            found.append(source)
    return found


def expand_bilingual(query: str) -> list[str]:
    """Tokens to add to ``query`` so it matches the other language.

    Handles both multi-word phrases and single tokens. Original tokens are not
    repeated: the caller keeps them, this returns only the additions.
    """
    # Preserve first-seen order: BM25 is bag-of-words, but the expansion is
    # also surfaced to callers and tests, where noise is visible.
    additions: list[str] = []
    seen: set[str] = set()

    def add(tokens: list[str]) -> None:
        for token in tokens:
            if token not in seen:
                seen.add(token)
                additions.append(token)

    for phrase in apply_phrases(query):
        add(tokenize(phrase))

    for token in tokenize(query):
        for equivalent in TOKEN_EQUIVALENTS.get(token, ()):
            add([equivalent])

    return additions
