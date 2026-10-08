"""Standard cross-engine event types and validation."""

# --- Service Health ---
SERVICE_HEALTH = "service.health"
SERVICE_STARTUP = "service.startup"
SERVICE_SHUTDOWN = "service.shutdown"
SERVICE_ERROR = "service.error"

# --- Data ---
DATA_PROCESSED = "data.processed"
DATA_VALIDATED = "data.validated"
DATA_ENRICHED = "data.enriched"
DATA_ALERT = "data.alert"

# --- Security ---
SECURITY_THREAT = "security.threat_detected"
SECURITY_VULNERABILITY = "security.vulnerability_found"
SECURITY_ACCESS_DENIED = "security.access_denied"

# --- Workflow ---
WORKFLOW_STARTED = "workflow.started"
WORKFLOW_COMPLETED = "workflow.completed"
WORKFLOW_FAILED = "workflow.failed"

# --- AI ---
AI_MODEL_SELECTED = "ai.model.selected"
AI_PREDICTION = "ai.prediction.made"
AI_CACHE_HIT = "ai.cache.hit"

# --- Scale ---
SCALE_CACHE_INVALIDATED = "scale.cacheinvalidated"
SCALE_CIRCUIT_OPENED = "scale.circuit_opened"
SCALE_AUTO_SCALED = "scale.auto_scaled"

# --- UX ---
UX_THEME_CHANGED = "ux.theme.changed"
UX_ACCESSIBILITY_ISSUE = "ux.accessibility.issue"
UX_TRANSLATION_LOADED = "ux.translation.loaded"

# --- Integration ---
INTEGRATION_WEBHOOK = "integration.webhook.received"
INTEGRATION_SYNC_COMPLETED = "integration.sync.completed"

# --- DevTools ---
DEVTOOLS_ANALYSIS_COMPLETE = "devtools.analysis.complete"
DEVTOOLS_PROFILE_COMPLETE = "devtools.profile.complete"

EVENT_TYPES = {
    "service": [SERVICE_HEALTH, SERVICE_STARTUP, SERVICE_SHUTDOWN, SERVICE_ERROR],
    "data": [DATA_PROCESSED, DATA_VALIDATED, DATA_ENRICHED, DATA_ALERT],
    "security": [SECURITY_THREAT, SECURITY_VULNERABILITY, SECURITY_ACCESS_DENIED],
    "workflow": [WORKFLOW_STARTED, WORKFLOW_COMPLETED, WORKFLOW_FAILED],
    "ai": [AI_MODEL_SELECTED, AI_PREDICTION, AI_CACHE_HIT],
    "scale": [SCALE_CACHE_INVALIDATED, SCALE_CIRCUIT_OPENED, SCALE_AUTO_SCALED],
    "ux": [UX_THEME_CHANGED, UX_ACCESSIBILITY_ISSUE, UX_TRANSLATION_LOADED],
    "integration": [INTEGRATION_WEBHOOK, INTEGRATION_SYNC_COMPLETED],
    "devtools": [DEVTOOLS_ANALYSIS_COMPLETE, DEVTOOLS_PROFILE_COMPLETE],
}

ALL_EVENT_TYPES = set()
for types in EVENT_TYPES.values():
    ALL_EVENT_TYPES.update(types)


def validate_event_type(event_type: str) -> bool:
    """Check if an event type string is valid."""
    if event_type in ALL_EVENT_TYPES:
        return True
    if "*" in event_type:
        prefix = event_type.rstrip("*").rstrip(".")
        return prefix in EVENT_TYPES
    return False


def get_event_category(event_type: str) -> str:
    """Return the category of an event type, or empty string if invalid."""
    for category, types in EVENT_TYPES.items():
        if event_type in types:
            return category
    if "*" in event_type:
        prefix = event_type.rstrip("*").rstrip(".")
        if prefix in EVENT_TYPES:
            return prefix
    return ""


ENGINE_PORTS = {
    "epic_pc": 5020,
    "daniela": 9200,
    "hermes": 9300,
    "optimization": 9400,
    "frontend": 9500,
    "infra_opt": 9700,
    "agent_mobile": 9800,
    "security": 9999,
    "perf": 9998,
    "dashboard": 9997,
    "intel_engine": 9850,
    "auto_engine": 9860,
    "data_engine": 9870,
    "secure_engine": 9880,
    "devtools_engine": 9890,
    "ecosystem_engine": 9840,
    "ux_engine": 9830,
    "scale_engine": 9820,
}

ENGINE_PATHS = {
    "epic_pc": "/api/epic-pc",
    "daniela": "/api/daniela",
    "hermes": "/api/hermes",
    "optimization": "/api/optimization",
    "frontend": "/api/frontend",
    "infra_opt": "/api/infra",
    "agent_mobile": "/api/agent",
    "security": "/api/security",
    "perf": "/api/perf",
    "dashboard": "/api/dashboard",
    "intel_engine": "/api/intel",
    "auto_engine": "/api/auto",
    "data_engine": "/api/data",
    "secure_engine": "/api/secure-engine",
    "devtools_engine": "/api/devtools",
    "ecosystem_engine": "/api/ecosystem",
    "ux_engine": "/api/ux",
    "scale_engine": "/api/scale",
}

ALL_ENGINES = list(ENGINE_PORTS.keys())

