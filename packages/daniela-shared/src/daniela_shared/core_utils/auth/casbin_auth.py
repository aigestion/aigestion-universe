"""
Casbin Integration for AIG - Fine-grained Authorization
RBAC, ABAC, and custom models for multi-engine access control.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import casbin
from casbin import Enforcer


class ResourceType(StrEnum):
    """AIG resource types."""
    ENGINE = "engine"
    SERVICE = "service"
    API = "api"
    DASHBOARD = "dashboard"
    DATA = "data"
    CONFIG = "config"
    DEPLOYMENT = "deployment"
    AGENT = "agent"
    MEMORY = "memory"
    MODEL = "model"


class Action(StrEnum):
    """Standard actions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    DEPLOY = "deploy"
    MONITOR = "monitor"
    DEBUG = "debug"


@dataclass
class PolicyRule:
    """A single policy rule."""
    subject: str  # user, role, or group
    resource: str  # resource type or specific resource
    action: str   # action
    effect: str = "allow"  # allow or deny
    conditions: dict[str, Any] = field(default_factory=dict)


class AIGEnforcer:
    """
    Casbin enforcer for AIG with support for:
    - RBAC (Role-Based Access Control)
    - ABAC (Attribute-Based Access Control)
    - Custom models per engine/service
    - Domain/tenancy support
    """

    def __init__(
        self,
        model_path: str | None = None,
        policy_path: str | None = None,
        adapter: Any | None = None
    ):
        self.model_path = model_path or self._get_default_model()
        self.policy_path = policy_path
        self.adapter = adapter
        self.enforcer: Enforcer | None = None
        self._init_enforcer()

    def _get_default_model(self) -> str:
        """Get default model configuration."""
        model_dir = Path(__file__).parent / "models"
        model_dir.mkdir(exist_ok=True)
        model_file = model_dir / "aig_model.conf"

        if not model_file.exists():
            self._create_default_model(model_file)

        return str(model_file)

    def _create_default_model(self, path: Path) -> None:
        """Create default RBAC + ABAC model.

        `p` lleva 5 tokens (sub, dom, obj, act, eft): las politicas default
        se anaden con 5 valores (["engine:daniela:admin", "*", "engine:
        daniela", "*", "allow"], efecto implícito `allow` en la ultima
        posicion). El token de efecto se llama `eft` porque el `policy_effect`
        de casbin usa `p.eft == allow`; declararlo como `effect` genera
        `NameNotDefined: p_eft` y produce HTTP 500 en CADA peticion (bug
        2026-10-09).
        """
        model_text = """
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act, eft

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && keyMatch(r.dom, p.dom) && keyMatch(r.obj, p.obj) && regexMatch(r.act, p.act)
"""
        path.write_text(model_text)

    def _init_enforcer(self) -> None:
        """Initialize Casbin enforcer."""
        try:
            if self.adapter:
                self.enforcer = casbin.Enforcer(self.model_path, self.adapter)
            elif self.policy_path:
                self.enforcer = casbin.Enforcer(self.model_path, self.policy_path)
            else:
                self.enforcer = casbin.Enforcer(self.model_path)
                self._load_default_policies()

            # Enable auto-save
            self.enforcer.enable_auto_save(True)
        except Exception as e:
            print(f"[Casbin] Failed to initialize: {e}")
            self.enforcer = None

    def _load_default_policies(self) -> None:
        """Load default AIG policies."""
        if not self.enforcer:
            return

        default_policies = [
            # 2026-10-04 (S14): ELIMINADA la politica wildcard
            # ["admin", "*", "*", "*", "allow"] — cualquier usuario llamado
            # "admin" tenia acceso TOTAL a todo. Ahora admin se concede por
            # engine explicitamente (engine:<name>:admin).

            # Engine-specific roles
            ["engine:daniela:admin", "*", "engine:daniela", "*", "allow"],
            ["engine:hermes:admin", "*", "engine:hermes", "*", "allow"],
            ["engine:infra:admin", "*", "engine:infra", "*", "allow"],
            ["engine:security:admin", "*", "engine:security", "*", "allow"],
            ["engine:perf:admin", "*", "engine:perf", "*", "allow"],
            ["engine:orchestrator:admin", "*", "engine:orchestrator", "*", "allow"],

            # Developer role - read/write on assigned engines
            ["role:developer", "*", "engine:*", "read", "allow"],
            ["role:developer", "*", "engine:*", "write", "allow"],
            ["role:developer", "*", "api:*", "read", "allow"],
            ["role:developer", "*", "dashboard:*", "read", "allow"],

            # Operator role - deploy and monitor
            ["role:operator", "*", "deployment:*", "deploy", "allow"],
            ["role:operator", "*", "service:*", "monitor", "allow"],
            ["role:operator", "*", "dashboard:*", "read", "allow"],

            # Viewer role - read only
            ["role:viewer", "*", "*", "read", "allow"],

            # App de escritorio Daniela (Tauri, siempre localhost): la
            # ventana y el Vision Menu leen y escriben en la superficie
            # que usan (globo, memoria, capas, estado). Identidad fija
            # que el desktop manda en `X-User-ID` (ver `pedir()` en
            # apps/daniela-desktop/resources/js/menu.js).
            ["daniela-desktop", "*", "/api/*", "read", "allow"],
            ["daniela-desktop", "*", "/api/*", "write", "allow"],
            ["daniela-desktop", "*", "/api/*", "delete", "allow"],
            ["daniela-desktop", "*", "/gods-eye/*", "read", "allow"],

            # Agent roles
            ["agent:orchestrator", "*", "agent:*", "execute", "allow"],
            ["agent:security", "*", "engine:security", "*", "allow"],
            ["agent:perf", "*", "engine:perf", "*", "allow"],
            ["agent:android", "*", "engine:android", "*", "allow"],
            ["agent:observability", "*", "engine:observability", "*", "allow"],
            ["agent:deploy", "*", "deployment:*", "deploy", "allow"],

            # Memory access
            ["role:developer", "*", "memory:*", "read", "allow"],
            ["role:developer", "*", "memory:*", "write", "allow"],
            ["agent:*", "*", "memory:*", "read", "allow"],
            ["agent:*", "*", "memory:*", "write", "allow"],

            # Model access
            ["role:developer", "*", "model:*", "read", "allow"],
            ["role:developer", "*", "model:*", "execute", "allow"],
            ["agent:*", "*", "model:*", "execute", "allow"],
        ]

        for policy in default_policies:
            self.enforcer.add_policy(*policy)

    def enforce(
        self,
        subject: str,
        domain: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if subject has permission for action on resource in domain.

        Args:
            subject: User, role, or agent identifier
            domain: Domain/tenant (e.g., "prod", "staging", "*")
            resource: Resource identifier (e.g., "engine:daniela", "api:chat")
            action: Action to perform (e.g., "read", "write", "deploy")

        Returns:
            True if allowed, False otherwise
        """
        if not self.enforcer:
            return False
        return self.enforcer.enforce(subject, domain, resource, action)

    def enforce_with_context(
        self,
        subject: str,
        domain: str,
        resource: str,
        action: str,
        context: dict[str, Any]
    ) -> bool:
        """
        Enforce with additional context for ABAC.

        Context can include: time, IP, resource attributes, etc.
        """
        if not self.enforcer:
            return False

        # Add context to enforcer if model supports it
        # For now, use basic enforce
        return self.enforce(subject, domain, resource, action)

    # Role management
    def add_role_for_user(self, user: str, role: str, domain: str = "*") -> bool:
        """Assign role to user in domain."""
        if not self.enforcer:
            return False
        return self.enforcer.add_role_for_user(user, role, domain)

    def delete_role_for_user(self, user: str, role: str, domain: str = "*") -> bool:
        """Remove role from user in domain."""
        if not self.enforcer:
            return False
        return self.enforcer.delete_role_for_user(user, role, domain)

    def get_roles_for_user(self, user: str, domain: str = "*") -> list[str]:
        """Get roles for user in domain."""
        if not self.enforcer:
            return []
        return self.enforcer.get_roles_for_user(user, domain)

    def get_users_for_role(self, role: str, domain: str = "*") -> list[str]:
        """Get users for role in domain."""
        if not self.enforcer:
            return []
        return self.enforcer.get_users_for_role(role, domain)

    def has_role_for_user(self, user: str, role: str, domain: str = "*") -> bool:
        """Check if user has role in domain."""
        if not self.enforcer:
            return False
        return self.enforcer.has_role_for_user(user, role, domain)

    # Policy management
    def add_policy(self, rule: PolicyRule, domain: str = "*") -> bool:
        """Add a policy rule."""
        if not self.enforcer:
            return False
        return self.enforcer.add_policy(rule.subject, domain, rule.resource, rule.action, rule.effect)

    def remove_policy(self, rule: PolicyRule, domain: str = "*") -> bool:
        """Remove a policy rule."""
        if not self.enforcer:
            return False
        return self.enforcer.remove_policy(rule.subject, domain, rule.resource, rule.action, rule.effect)

    def get_all_policies(self) -> list[list[str]]:
        """Get all policies."""
        if not self.enforcer:
            return []
        return self.enforcer.get_policy()

    def get_filtered_policies(self, field_index: int, *field_values: str) -> list[list[str]]:
        """Get policies matching filter."""
        if not self.enforcer:
            return []
        return self.enforcer.get_filtered_policy(field_index, *field_values)

    # Domain management
    def add_domain(self, domain: str) -> bool:
        """Add a new domain."""
        if not self.enforcer:
            return False
        # Add default policies for new domain
        self.enforcer.add_policy("admin", domain, "*", "*", "allow")
        return True

    def delete_domain(self, domain: str) -> bool:
        """Delete a domain and its policies."""
        if not self.enforcer:
            return False
        # Remove all policies for domain
        policies = self.get_filtered_policies(1, domain)
        for policy in policies:
            self.enforcer.remove_policy(*policy)
        return True

    # Engine-specific helpers
    def can_access_engine(self, subject: str, engine: str, action: Action, domain: str = "*") -> bool:
        """Check if subject can access engine."""
        return self.enforce(subject, domain, f"engine:{engine}", action.value)

    def can_access_api(self, subject: str, api: str, action: Action, domain: str = "*") -> bool:
        """Check if subject can access API."""
        return self.enforce(subject, domain, f"api:{api}", action.value)

    def can_deploy(self, subject: str, environment: str, domain: str = "*") -> bool:
        """Check if subject can deploy to environment."""
        return self.enforce(subject, domain, f"deployment:{environment}", Action.DEPLOY.value)

    def can_access_memory(self, subject: str, memory_namespace: str, action: Action, domain: str = "*") -> bool:
        """Check if subject can access memory namespace."""
        return self.enforce(subject, domain, f"memory:{memory_namespace}", action.value)

    def can_use_model(self, subject: str, model: str, domain: str = "*") -> bool:
        """Check if subject can use model."""
        return self.enforce(subject, domain, f"model:{model}", Action.EXECUTE.value)

    # Bulk operations
    def get_permissions_for_user(self, user: str, domain: str = "*") -> list[PolicyRule]:
        """Get all effective permissions for a user."""
        if not self.enforcer:
            return []

        roles = self.get_roles_for_user(user, domain)
        all_subjects = [user] + roles

        permissions = []
        for subject in all_subjects:
            policies = self.get_filtered_policies(0, subject)
            for policy in policies:
                permissions.append(PolicyRule(
                    subject=policy[0],
                    resource=policy[2],
                    action=policy[3],
                    effect=policy[4]
                ))
        return permissions

    def audit_access(self, subject: str, domain: str = "*") -> dict[str, list[str]]:
        """Audit all access for a subject."""
        permissions = self.get_permissions_for_user(subject, domain)

        audit = {
            "engines": [],
            "apis": [],
            "dashboards": [],
            "deployments": [],
            "memory": [],
            "models": [],
            "admin": []
        }

        for perm in permissions:
            if perm.resource.startswith("engine:"):
                audit["engines"].append(f"{perm.action}:{perm.resource}")
            elif perm.resource.startswith("api:"):
                audit["apis"].append(f"{perm.action}:{perm.resource}")
            elif perm.resource.startswith("dashboard:"):
                audit["dashboards"].append(f"{perm.action}:{perm.resource}")
            elif perm.resource.startswith("deployment:"):
                audit["deployments"].append(f"{perm.action}:{perm.resource}")
            elif perm.resource.startswith("memory:"):
                audit["memory"].append(f"{perm.action}:{perm.resource}")
            elif perm.resource.startswith("model:"):
                audit["models"].append(f"{perm.action}:{perm.resource}")
            elif perm.resource == "*":
                audit["admin"].append(f"{perm.action}:{perm.resource}")

        return audit


# Global enforcer instance
_default_enforcer: AIGEnforcer | None = None


def get_enforcer() -> AIGEnforcer:
    """Get global enforcer instance."""
    global _default_enforcer
    if _default_enforcer is None:
        _default_enforcer = AIGEnforcer()
    return _default_enforcer


# Convenience functions
def check_permission(
    subject: str,
    resource: str,
    action: Action,
    domain: str = "*"
) -> bool:
    """Check permission using global enforcer."""
    return get_enforcer().enforce(subject, domain, resource, action.value)


def check_engine_access(subject: str, engine: str, action: Action, domain: str = "*") -> bool:
    """Check engine access using global enforcer."""
    return get_enforcer().can_access_engine(subject, engine, action, domain)


def check_deploy_permission(subject: str, environment: str, domain: str = "*") -> bool:
    """Check deploy permission using global enforcer."""
    return get_enforcer().can_deploy(subject, environment, domain)


def assign_role(user: str, role: str, domain: str = "*") -> bool:
    """Assign role to user."""
    return get_enforcer().add_role_for_user(user, role, domain)


def audit_user(subject: str, domain: str = "*") -> dict[str, list[str]]:
    """Audit user permissions."""
    return get_enforcer().audit_access(subject, domain)


# Decorator for protecting functions
def require_permission(resource: str, action: Action, domain: str = "*"):
    """Decorator to enforce permission on function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract subject from context (first arg or kwargs)
            subject = kwargs.get("subject") or (args[0] if args else "anonymous")

            if not check_permission(subject, resource, action, domain):
                raise PermissionError(
                    f"Subject '{subject}' lacks permission '{action.value}' "
                    f"on resource '{resource}' in domain '{domain}'"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Flask middleware for Casbin authentication
def create_auth_middleware(app, public_paths: set | None = None):
    """Create Flask middleware for Casbin-based authentication."""
    from flask import g, jsonify, request

    enforcer = get_enforcer()
    public_paths = public_paths or {"/api/status", "/health"}

    @app.before_request
    def auth_check():
        # Skip auth for health checks and static files
        if request.path in public_paths:
            return None
        if request.path.startswith('/static/') or request.path.startswith('/web/'):
            return None

        # Get subject from header or default
        subject = request.headers.get('X-User-ID', 'anonymous')
        domain = request.headers.get('X-Domain', '*')
        resource = request.path
        action = request.method.lower()

        # Map HTTP methods to actions
        action_map = {
            'get': 'read',
            'post': 'write',
            'put': 'write',
            'patch': 'write',
            'delete': 'delete',
        }
        action = action_map.get(action, 'read')

        # Check permission
        if not enforcer.enforce(subject, domain, resource, action):
            return jsonify({"error": "Forbidden", "message": f"Permission denied: {action} {resource}"}), 403

        g.subject = subject
        g.domain = domain
        return None

    return app
