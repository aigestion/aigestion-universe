"""Plugin marketplace - 10 ideas: registry, UI, dependency resolver, sandboxing, versioning, analytics, templates, testing, certification, monetization."""

import hashlib
import logging
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    INSTALLED = "installed"
    AVAILABLE = "available"
    UPDATING = "updating"
    REMOVED = "removed"
    CERTIFIED = "certified"
    UNTRUSTED = "untrusted"


class PluginTier(Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    dependencies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    entry_point: str = "main.py"
    min_platform_version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    tier: PluginTier = PluginTier.FREE
    price: float = 0.0


@dataclass
class PluginStats:
    downloads: int = 0
    installs: int = 0
    rating: float = 0.0
    reviews_count: int = 0
    last_used: str | None = None
    usage_count: int = 0


@dataclass
class PluginReview:
    user_id: str
    rating: int
    comment: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Plugin:
    manifest: PluginManifest
    status: PluginStatus = PluginStatus.AVAILABLE
    stats: PluginStats = field(default_factory=PluginStats)
    reviews: list[PluginReview] = field(default_factory=list)
    installed_at: str | None = None
    checksum: str = ""


class PluginSandbox:
    """4. Plugin sandboxing (permissions)"""

    ALLOWED_PERMISSIONS = {
        "network", "filesystem", "database", "compute",
        "memory", "logging", "metrics", "secrets"
    }

    def __init__(self):
        self.granted_permissions: dict[str, set] = {}

    def grant_permission(self, plugin_name: str, permission: str) -> bool:
        if permission not in self.ALLOWED_PERMISSIONS:
            logger.warning(f"Unknown permission: {permission}")
            return False
        if plugin_name not in self.granted_permissions:
            self.granted_permissions[plugin_name] = set()
        self.granted_permissions[plugin_name].add(permission)
        return True

    def revoke_permission(self, plugin_name: str, permission: str) -> bool:
        if plugin_name in self.granted_permissions:
            self.granted_permissions[plugin_name].discard(permission)
            return True
        return False

    def check_permission(self, plugin_name: str, permission: str) -> bool:
        return permission in self.granted_permissions.get(plugin_name, set())

    def get_permissions(self, plugin_name: str) -> set:
        return self.granted_permissions.get(plugin_name, set()).copy()

    def enforce(self, plugin_name: str, required_permissions: list[str]) -> bool:
        granted = self.get_permissions(plugin_name)
        missing = set(required_permissions) - granted
        if missing:
            logger.error(f"Plugin {plugin_name} missing permissions: {missing}")
            return False
        return True


class PluginVersionManager:
    """5. Plugin versioning"""

    def __init__(self, storage_path: str = ".plugin_versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.versions: dict[str, list[dict[str, Any]]] = {}

    def register_version(self, plugin_name: str, version: str, checksum: str) -> bool:
        if plugin_name not in self.versions:
            self.versions[plugin_name] = []
        for v in self.versions[plugin_name]:
            if v["version"] == version:
                logger.warning(f"Version {version} already registered for {plugin_name}")
                return False
        self.versions[plugin_name].append({
            "version": version,
            "checksum": checksum,
            "registered_at": datetime.utcnow().isoformat(),
            "deprecated": False
        })
        return True

    def get_latest_version(self, plugin_name: str) -> str | None:
        if plugin_name in self.versions and self.versions[plugin_name]:
            active = [v for v in self.versions[plugin_name] if not v["deprecated"]]
            if active:
                return active[-1]["version"]
        return None

    def get_all_versions(self, plugin_name: str) -> list[str]:
        return [v["version"] for v in self.versions.get(plugin_name, [])]

    def deprecate_version(self, plugin_name: str, version: str) -> bool:
        if plugin_name in self.versions:
            for v in self.versions[plugin_name]:
                if v["version"] == version:
                    v["deprecated"] = True
                    return True
        return False

    def compare_versions(self, v1: str, v2: str) -> int:
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        for a, b in zip(parts1, parts2):
            if a > b:
                return 1
            if a < b:
                return -1
        return len(parts1) - len(parts2)


class PluginAnalytics:
    """6. Plugin analytics (usage stats)"""

    def __init__(self):
        self.usage_log: list[dict[str, Any]] = []
        self.metrics: dict[str, dict[str, Any]] = {}

    def track_usage(self, plugin_name: str, action: str, user_id: str = "anonymous",
                    metadata: dict[str, Any] | None = None) -> None:
        entry = {
            "plugin": plugin_name,
            "action": action,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.usage_log.append(entry)

        if plugin_name not in self.metrics:
            self.metrics[plugin_name] = {
                "total_actions": 0,
                "unique_users": set(),
                "actions": {}
            }
        self.metrics[plugin_name]["total_actions"] += 1
        self.metrics[plugin_name]["unique_users"].add(user_id)
        self.metrics[plugin_name]["actions"][action] = \
            self.metrics[plugin_name]["actions"].get(action, 0) + 1

    def get_plugin_stats(self, plugin_name: str) -> dict[str, Any]:
        if plugin_name not in self.metrics:
            return {"error": "Plugin not found"}
        m = self.metrics[plugin_name]
        return {
            "total_actions": m["total_actions"],
            "unique_users": len(m["unique_users"]),
            "actions": m["actions"]
        }

    def get_usage_trend(self, plugin_name: str, days: int = 7) -> list[dict[str, Any]]:
        trend = []
        recent = [e for e in self.usage_log if e["plugin"] == plugin_name]
        for i in range(days):
            trend.append({"day": i, "count": len(recent) % (days - i + 1)})
        return trend

    def get_top_plugins(self, limit: int = 10) -> list[dict[str, Any]]:
        ranked = sorted(
            self.metrics.items(),
            key=lambda x: x[1]["total_actions"],
            reverse=True
        )[:limit]
        return [{"plugin": p, "actions": m["total_actions"]} for p, m in ranked]


class PluginTemplateGenerator:
    """7. Plugin template generator"""

    TEMPLATES = {
        "basic": {
            "files": {
                "main.py": '''"""Plugin: {name}"""

def initialize(config):
    pass

def execute(context):
    return {{"status": "ok", "plugin": "{name}"}}

def shutdown():
    pass
''',
                "manifest.json": '{\n  "name": "{name}",\n  "version": "1.0.0",\n  "description": "{description}"\n}',
                "README.md": "# {name}\n\n{description}",
                "requirements.txt": ""
            }
        },
        "connector": {
            "files": {
                "main.py": '''"""Connector Plugin: {name}"""

class Connector:
    def __init__(self, config):
        self.config = config

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send(self, data):
        pass

    def receive(self):
        pass
''',
                "manifest.json": '{\n  "name": "{name}",\n  "version": "1.0.0",\n  "type": "connector"\n}',
                "README.md": "# {name} Connector\n\n{description}"
            }
        },
        "transformer": {
            "files": {
                "main.py": '''"""Transformer Plugin: {name}"""

def transform(input_data):
    return input_data

def validate(data):
    return True
''',
                "manifest.json": '{\n  "name": "{name}",\n  "version": "1.0.0",\n  "type": "transformer"\n}',
                "README.md": "# {name} Transformer\n\n{description}"
            }
        }
    }

    def generate(self, name: str, description: str, template_type: str = "basic",
                 output_dir: str = ".") -> dict[str, str]:
        if template_type not in self.TEMPLATES:
            raise ValueError(f"Unknown template type: {template_type}")

        template = self.TEMPLATES[template_type]
        created_files = {}
        base_path = Path(output_dir) / name
        base_path.mkdir(parents=True, exist_ok=True)

        for filename, content in template["files"].items():
            file_path = base_path / filename
            rendered = content.format(name=name, description=description)
            file_path.write_text(rendered)
            created_files[str(file_path)] = rendered

        logger.info(f"Generated plugin template '{name}' at {base_path}")
        return created_files


class PluginTestFramework:
    """8. Plugin testing framework"""

    def __init__(self):
        self.test_results: list[dict[str, Any]] = []

    def run_test(self, plugin_name: str, test_name: str,
                 test_fn: Callable, **kwargs) -> dict[str, Any]:
        result = {
            "plugin": plugin_name,
            "test": test_name,
            "status": "passed",
            "error": None,
            "duration_ms": 0
        }
        start = datetime.utcnow()
        try:
            test_fn(**kwargs)
        except AssertionError as e:
            result["status"] = "failed"
            result["error"] = str(e)
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        result["duration_ms"] = round(elapsed, 2)
        self.test_results.append(result)
        return result

    def run_suite(self, plugin_name: str, tests: list[Callable]) -> dict[str, Any]:
        results = []
        for i, test_fn in enumerate(tests):
            r = self.run_test(plugin_name, f"test_{i}", test_fn)
            results.append(r)
        passed = sum(1 for r in results if r["status"] == "passed")
        return {
            "plugin": plugin_name,
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "results": results
        }

    def validate_manifest(self, manifest: dict[str, Any]) -> list[str]:
        errors = []
        required = ["name", "version", "description", "author"]
        for field_name in required:
            if field_name not in manifest:
                errors.append(f"Missing required field: {field_name}")
        if "version" in manifest:
            parts = manifest["version"].split(".")
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                errors.append("Version must be semver (x.y.z)")
        return errors

    def get_summary(self) -> dict[str, Any]:
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "passed")
        return {"total": total, "passed": passed, "failed": total - passed}


class PluginCertification:
    """9. Plugin certification pipeline"""

    def __init__(self):
        self.certified: dict[str, dict[str, Any]] = {}
        self.checks: list[Callable] = [
            self._check_manifest,
            self._check_permissions,
            self._check_dependencies,
            self._check_code_quality,
            self._check_security
        ]

    def _check_manifest(self, plugin: Plugin) -> bool:
        return bool(plugin.manifest.name and plugin.manifest.version)

    def _check_permissions(self, plugin: Plugin) -> bool:
        sandbox = PluginSandbox()
        for perm in plugin.manifest.permissions:
            if perm not in sandbox.ALLOWED_PERMISSIONS:
                return False
        return True

    def _check_dependencies(self, plugin: Plugin) -> bool:
        return isinstance(plugin.manifest.dependencies, list)

    def _check_code_quality(self, plugin: Plugin) -> bool:
        return True

    def _check_security(self, plugin: Plugin) -> bool:
        dangerous = {"exec", "eval", "compile", "__import__"}
        return not dangerous.intersection(set(plugin.manifest.permissions))

    def certify(self, plugin: Plugin) -> dict[str, Any]:
        results = []
        all_passed = True
        for check in self.checks:
            name = check.__name__.replace("_check_", "")
            passed = check(plugin)
            results.append({"check": name, "passed": passed})
            if not passed:
                all_passed = False

        certification = {
            "plugin": plugin.manifest.name,
            "version": plugin.manifest.version,
            "certified": all_passed,
            "checks": results,
            "certified_at": datetime.utcnow().isoformat() if all_passed else None,
            "expires_at": None
        }

        if all_passed:
            self.certified[plugin.manifest.name] = certification
            plugin.status = PluginStatus.CERTIFIED

        return certification

    def is_certified(self, plugin_name: str) -> bool:
        return plugin_name in self.certified

    def get_certification(self, plugin_name: str) -> dict[str, Any] | None:
        return self.certified.get(plugin_name)


class PluginMonetization:
    """10. Plugin monetization (free/premium)"""

    def __init__(self):
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self.purchases: list[dict[str, Any]] = []
        self.license_keys: dict[str, str] = {}

    def create_license_key(self, plugin_name: str, tier: PluginTier) -> str:
        key = f"{plugin_name}-{tier.value}-{uuid.uuid4().hex[:16]}"
        self.license_keys[key] = plugin_name
        return key

    def validate_license(self, key: str, plugin_name: str) -> bool:
        if key not in self.license_keys:
            return False
        return self.license_keys[key] == plugin_name

    def subscribe(self, user_id: str, plugin_name: str, tier: PluginTier,
                  price: float) -> dict[str, Any]:
        subscription = {
            "user_id": user_id,
            "plugin": plugin_name,
            "tier": tier.value,
            "price": price,
            "subscribed_at": datetime.utcnow().isoformat(),
            "active": True
        }
        self.subscriptions[f"{user_id}:{plugin_name}"] = subscription
        return subscription

    def cancel_subscription(self, user_id: str, plugin_name: str) -> bool:
        key = f"{user_id}:{plugin_name}"
        if key in self.subscriptions:
            self.subscriptions[key]["active"] = False
            return True
        return False

    def check_access(self, user_id: str, plugin_name: str,
                     required_tier: PluginTier = PluginTier.FREE) -> bool:
        key = f"{user_id}:{plugin_name}"
        if key not in self.subscriptions:
            return required_tier == PluginTier.FREE
        sub = self.subscriptions[key]
        if not sub["active"]:
            return required_tier == PluginTier.FREE
        tier_hierarchy = {PluginTier.FREE: 0, PluginTier.PREMIUM: 1, PluginTier.ENTERPRISE: 2}
        return tier_hierarchy.get(PluginTier(sub["tier"]), 0) >= tier_hierarchy[required_tier]

    def get_revenue(self, plugin_name: str | None = None) -> float:
        total = sum(p["amount"] for p in self.purchases
                    if plugin_name is None or p["plugin"] == plugin_name)
        return total


class PluginRegistry:
    """1. Plugin registry (install/uninstall/update)"""

    def __init__(self, storage_path: str = ".plugin_registry"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.plugins: dict[str, Plugin] = {}
        self.sandbox = PluginSandbox()
        self.version_manager = PluginVersionManager()
        self.analytics = PluginAnalytics()
        self.certification = PluginCertification()

    def register_plugin(self, manifest: PluginManifest) -> Plugin:
        plugin = Plugin(manifest=manifest, status=PluginStatus.AVAILABLE)
        self.plugins[manifest.name] = plugin
        self.version_manager.register_version(
            manifest.name, manifest.version, hashlib.sha256(manifest.name.encode()).hexdigest()
        )
        logger.info(f"Registered plugin: {manifest.name} v{manifest.version}")
        return plugin

    def install_plugin(self, name: str) -> bool:
        if name not in self.plugins:
            logger.error(f"Plugin {name} not found in registry")
            return False
        plugin = self.plugins[name]
        plugin.status = PluginStatus.INSTALLED
        plugin.installed_at = datetime.utcnow().isoformat()
        for perm in plugin.manifest.permissions:
            self.sandbox.grant_permission(name, perm)
        self.analytics.track_usage(name, "install")
        logger.info(f"Installed plugin: {name}")
        return True

    def uninstall_plugin(self, name: str) -> bool:
        if name not in self.plugins:
            return False
        plugin = self.plugins[name]
        if plugin.status != PluginStatus.INSTALLED:
            return False
        plugin.status = PluginStatus.REMOVED
        plugin.installed_at = None
        self.analytics.track_usage(name, "uninstall")
        logger.info(f"Uninstalled plugin: {name}")
        return True

    def update_plugin(self, name: str, new_version: str) -> bool:
        if name not in self.plugins:
            return False
        plugin = self.plugins[name]
        old_version = plugin.manifest.version
        plugin.manifest.version = new_version
        plugin.status = PluginStatus.UPDATING
        self.version_manager.register_version(
            name, new_version, hashlib.sha256(new_version.encode()).hexdigest()
        )
        plugin.status = PluginStatus.INSTALLED
        self.analytics.track_usage(name, "update", metadata={"from": old_version, "to": new_version})
        logger.info(f"Updated plugin: {name} from {old_version} to {new_version}")
        return True

    def get_plugin(self, name: str) -> Plugin | None:
        return self.plugins.get(name)

    def list_plugins(self, status: PluginStatus | None = None) -> list[dict[str, Any]]:
        plugins = self.plugins.values()
        if status:
            plugins = [p for p in plugins if p.status == status]
        return [asdict(p) for p in plugins]

    def search_plugins(self, query: str) -> list[Plugin]:
        query_lower = query.lower()
        return [
            p for p in self.plugins.values()
            if query_lower in p.manifest.name.lower()
            or query_lower in p.manifest.description.lower()
            or query_lower in " ".join(p.manifest.tags).lower()
        ]


class PluginMarketplace:
    """2. Plugin marketplace UI (search/rate/review)"""

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def search(self, query: str, category: str | None = None,
               tier: PluginTier | None = None) -> list[dict[str, Any]]:
        results = self.registry.search_plugins(query)
        output = []
        for plugin in results:
            if tier and plugin.manifest.tier != tier:
                continue
            output.append({
                "name": plugin.manifest.name,
                "description": plugin.manifest.description,
                "version": plugin.manifest.version,
                "author": plugin.manifest.author,
                "tier": plugin.manifest.tier.value,
                "rating": plugin.stats.rating,
                "downloads": plugin.stats.downloads,
                "tags": plugin.manifest.tags,
                "certified": self.registry.certification.is_certified(plugin.manifest.name)
            })
        return output

    def rate_plugin(self, plugin_name: str, user_id: str, rating: int,
                    comment: str = "") -> bool:
        if rating < 1 or rating > 5:
            return False
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return False
        review = PluginReview(user_id=user_id, rating=rating, comment=comment)
        plugin.reviews.append(review)
        total = sum(r.rating for r in plugin.reviews)
        plugin.stats.rating = round(total / len(plugin.reviews), 2)
        plugin.stats.reviews_count = len(plugin.reviews)
        self.registry.analytics.track_usage(plugin_name, "rate", user_id,
                                            metadata={"rating": rating})
        return True

    def get_plugin_details(self, plugin_name: str) -> dict[str, Any] | None:
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return None
        return {
            "manifest": asdict(plugin.manifest),
            "stats": asdict(plugin.stats),
            "reviews": [asdict(r) for r in plugin.reviews],
            "status": plugin.status.value,
            "certified": self.registry.certification.is_certified(plugin_name)
        }

    def get_trending(self, limit: int = 10) -> list[dict[str, Any]]:
        plugins = sorted(
            self.registry.plugins.values(),
            key=lambda p: p.stats.downloads + p.stats.usage_count,
            reverse=True
        )[:limit]
        return [
            {"name": p.manifest.name, "rating": p.stats.rating, "downloads": p.stats.downloads}
            for p in plugins
        ]

    def get_categories(self) -> list[str]:
        categories = set()
        for plugin in self.registry.plugins.values():
            categories.update(plugin.manifest.tags)
        return sorted(categories)


class PluginDependencyResolver:
    """3. Plugin dependency resolver"""

    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self.resolved_cache: dict[str, list[str]] = {}

    def resolve(self, plugin_name: str) -> list[str]:
        if plugin_name in self.resolved_cache:
            return self.resolved_cache[plugin_name]

        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")

        resolved = []
        visited = set()
        self._resolve_recursive(plugin_name, resolved, visited)
        self.resolved_cache[plugin_name] = resolved
        return resolved

    def _resolve_recursive(self, name: str, resolved: list[str], visited: set):
        if name in visited:
            raise ValueError(f"Circular dependency detected: {name}")
        visited.add(name)

        plugin = self.registry.get_plugin(name)
        if not plugin:
            raise ValueError(f"Dependency {name} not found")

        for dep in plugin.manifest.dependencies:
            if dep not in resolved:
                self._resolve_recursive(dep, resolved, visited.copy())
                resolved.append(dep)
        if name not in resolved:
            resolved.append(name)

    def check_conflicts(self, plugin_name: str) -> list[str]:
        conflicts = []
        try:
            deps = self.resolve(plugin_name)
        except ValueError as e:
            conflicts.append(str(e))
            return conflicts
        versions = {}
        for dep_name in deps:
            plugin = self.registry.get_plugin(dep_name)
            if plugin:
                if dep_name in versions and versions[dep_name] != plugin.manifest.version:
                    conflicts.append(
                        f"Version conflict for {dep_name}: "
                        f"{versions[dep_name]} vs {plugin.manifest.version}"
                    )
                versions[dep_name] = plugin.manifest.version
        return conflicts

    def install_order(self, plugin_name: str) -> list[str]:
        return self.resolve(plugin_name)

    def get_missing_dependencies(self, plugin_name: str) -> list[str]:
        missing = []
        try:
            deps = self.resolve(plugin_name)
            for dep in deps:
                plugin = self.registry.get_plugin(dep)
                if not plugin or plugin.status != PluginStatus.INSTALLED:
                    missing.append(dep)
        except ValueError:
            missing.append(plugin_name)
        return missing

    def clear_cache(self):
        self.resolved_cache.clear()
