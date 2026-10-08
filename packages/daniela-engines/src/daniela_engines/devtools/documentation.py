"""Auto-documentation tools (31-40)."""

import ast
import json
import os
import re
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class APISchema:
    title: str
    version: str
    description: str
    endpoints: list
    models: dict


@dataclass
class DocStringInfo:
    name: str
    type: str
    docstring: str | None
    args: list
    returns: str | None
    line: int


@dataclass
class ChangelogEntry:
    version: str
    date: str
    changes: dict
    hash: str


@dataclass
class SchemaTable:
    name: str
    columns: list
    primary_key: str | None
    foreign_keys: list
    indexes: list


class APIDocumentationGenerator:
    """31. API documentation generator (OpenAPI/Swagger)."""

    def __init__(self):
        self._paths: dict[str, dict] = {}
        self._models: dict[str, dict] = {}

    def add_endpoint(
        self,
        method: str,
        path: str,
        summary: str = "",
        description: str = "",
        parameters: list | None = None,
        request_body: dict | None = None,
        responses: dict | None = None,
        tags: list | None = None,
    ) -> None:
        if path not in self._paths:
            self._paths[path] = {}
        self._paths[path][method.lower()] = {
            "summary": summary,
            "description": description,
            "parameters": parameters or [],
            "requestBody": request_body,
            "responses": responses or {"200": {"description": "Success"}},
            "tags": tags or [],
        }

    def add_model(self, name: str, properties: dict, required: list | None = None) -> None:
        self._models[name] = {
            "type": "object",
            "properties": properties,
            "required": required or [],
        }

    def generate_openapi(self, title: str = "API", version: str = "1.0.0") -> dict:
        return {
            "openapi": "3.0.0",
            "info": {"title": title, "version": version, "description": ""},
            "paths": self._paths,
            "components": {"schemas": self._models} if self._models else {},
        }

    def generate_swagger(self, title: str = "API", version: str = "1.0.0") -> dict:
        return {
            "swagger": "2.0",
            "info": {"title": title, "version": version},
            "host": "localhost",
            "basePath": "/",
            "paths": self._paths,
            "definitions": self._models,
        }

    def generate_markdown(self, title: str = "API") -> str:
        lines = [f"# {title}\n"]
        for path, methods in sorted(self._paths.items()):
            for method, details in methods.items():
                lines.append(f"\n## {method.upper()} `{path}`\n")
                if details.get("summary"):
                    lines.append(f"{details['summary']}\n")
                if details.get("description"):
                    lines.append(f"{details['description']}\n")
                if details.get("parameters"):
                    lines.append("\n**Parameters:**\n")
                    lines.append("| Name | In | Type | Required | Description |")
                    lines.append("|------|-----|------|----------|-------------|")
                    for param in details["parameters"]:
                        lines.append(
                            f"| {param.get('name', '')} | {param.get('in', '')} "
                            f"| {param.get('type', '')} | {param.get('required', False)} "
                            f"| {param.get('description', '')} |"
                        )
        return "\n".join(lines)

    def from_flask_app(self, app: Any) -> None:
        try:
            for rule in app.url_map.iter_rules():
                if rule.endpoint == "static":
                    continue
                methods = [m for m in rule.methods if m not in ("HEAD", "OPTIONS")]
                for method in methods:
                    view_func = app.view_functions.get(rule.endpoint)
                    docstring = ""
                    if view_func and hasattr(view_func, "__doc__"):
                        docstring = view_func.__doc__ or ""
                    self.add_endpoint(
                        method=method,
                        path=rule.rule,
                        summary=docstring.split("\n")[0] if docstring else "",
                        description=docstring,
                    )
        except Exception:
            pass

    def export_json(self) -> str:
        return json.dumps(self.generate_openapi(), indent=2)


class CodeDocumentationGenerator:
    """32. Code documentation generator (docstrings)."""

    def __init__(self):
        self._docs: list[DocStringInfo] = []

    def extract_docstrings(self, filepath: str) -> list[DocStringInfo]:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return []

        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                args = []
                for arg in node.args.args:
                    ann = None
                    if arg.annotation:
                        if isinstance(arg.annotation, ast.Name):
                            ann = arg.annotation.id
                        elif isinstance(arg.annotation, ast.Constant):
                            ann = str(arg.annotation.value)
                    args.append({"name": arg.arg, "type": ann})

                returns = None
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        returns = node.returns.id

                results.append(
                    DocStringInfo(
                        name=node.name,
                        type="function",
                        docstring=docstring,
                        args=args,
                        returns=returns,
                        line=node.lineno,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                results.append(
                    DocStringInfo(
                        name=node.name,
                        type="class",
                        docstring=docstring,
                        args=[],
                        returns=None,
                        line=node.lineno,
                    )
                )
        self._docs.extend(results)
        return results

    def generate_docstring(self, info: DocStringInfo) -> str:
        lines = []
        if info.docstring:
            lines.append(info.docstring)
        else:
            lines.append(f"{'Class' if info.type == 'class' else 'Function'} {info.name}.")

        if info.args:
            lines.append("")
            lines.append("Args:")
            for arg in info.args:
                type_str = f" ({arg['type']})" if arg["type"] else ""
                lines.append(f"    {arg['name']}{type_str}: Description.")

        if info.returns:
            lines.append("")
            lines.append("Returns:")
            lines.append(f"    {info.returns}: Description.")

        return "\n".join(lines)

    def generate_module_doc(self, filepath: str) -> str:
        docs = self.extract_docstrings(filepath)
        lines = [f"# Documentation for {os.path.basename(filepath)}\n"]
        for doc in docs:
            lines.append(f"\n## {doc.name}\n")
            lines.append(self.generate_docstring(doc))
        return "\n".join(lines)

    def get_missing_docs(self) -> list[dict]:
        return [
            {"name": d.name, "type": d.type, "line": d.line}
            for d in self._docs
            if not d.docstring
        ]


class READMEGenerator:
    """33. README generator."""

    def __init__(self):
        self._sections: list[dict] = []

    def add_section(self, title: str, content: str, order: int = 0) -> None:
        self._sections.append({"title": title, "content": content, "order": order})

    def from_project(self, directory: str) -> str:
        self._sections.clear()
        name = os.path.basename(directory)
        self.add_section(name, f"Project: {name}", 0)
        self.add_section("Installation", self._detect_install(directory), 1)
        self.add_section("Usage", self._detect_usage(directory), 2)
        self.add_section("Structure", self._detect_structure(directory), 3)
        return self.generate()

    @staticmethod
    def _detect_install(directory: str) -> str:
        if os.path.exists(os.path.join(directory, "requirements.txt")):
            return "```bash\npip install -r requirements.txt\n```"
        if os.path.exists(os.path.join(directory, "pyproject.toml")):
            return "```bash\npip install -e .\n```"
        if os.path.exists(os.path.join(directory, "package.json")):
            return "```bash\nnpm install\n```"
        return "# Add installation instructions"

    @staticmethod
    def _detect_usage(directory: str) -> str:
        py_files = [f for f in os.listdir(directory) if f.endswith(".py")]
        if py_files:
            main = "main.py" if "main.py" in py_files else py_files[0]
            return f"```bash\npython {main}\n```"
        return "# Add usage instructions"

    @staticmethod
    def _detect_structure(directory: str) -> str:
        items = []
        for item in sorted(os.listdir(directory)):
            if item.startswith(".") or item in ("__pycache__", "node_modules"):
                continue
            items.append(f"- {item}")
        return "\n".join(items[:20])

    def generate(self) -> str:
        sections = sorted(self._sections, key=lambda s: s["order"])
        parts = []
        for s in sections:
            parts.append(f"## {s['title']}\n\n{s['content']}")
        return "\n\n".join(parts)

    def generate_with_badges(self, project_name: str) -> str:
        badges = f"""# {project_name}

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
"""
        content = self.generate()
        return badges + "\n" + content


class ChangelogGenerator:
    """34. Changelog generator from git."""

    def __init__(self):
        self._entries: list[ChangelogEntry] = []

    def from_git_log(self, directory: str = ".", count: int = 50) -> list[ChangelogEntry]:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", f"-{count}", "--format=%H|%s|%ai"],
                capture_output=True,
                text=True,
                cwd=directory,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            entries = []
            current_version = "Unreleased"
            changes = defaultdict(list)

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 2)
                if len(parts) < 3:
                    continue
                commit_hash, message, date = parts

                tag_match = re.match(r"^(v?\d+\.\d+\.\d+)", message)
                if tag_match:
                    if changes:
                        entries.append(
                            ChangelogEntry(
                                version=current_version,
                                date=date[:10],
                                changes=dict(changes),
                                hash=commit_hash[:8],
                            )
                        )
                    current_version = tag_match.group(1)
                    changes.clear()

                if any(kw in message.lower() for kw in ["feat", "add", "new"]):
                    changes["Added"].append(message)
                elif any(kw in message.lower() for kw in ["fix", "bug", "patch"]):
                    changes["Fixed"].append(message)
                elif any(kw in message.lower() for kw in ["refactor", "clean", "improve"]):
                    changes["Changed"].append(message)
                elif any(kw in message.lower() for kw in ["remove", "delete", "drop"]):
                    changes["Removed"].append(message)
                else:
                    changes["Changed"].append(message)

            if changes:
                entries.append(
                    ChangelogEntry(
                        version=current_version,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        changes=dict(changes),
                        hash="",
                    )
                )
            self._entries = entries
            return entries
        except Exception:
            return []

    def generate_markdown(self) -> str:
        lines = ["# Changelog\n"]
        for entry in self._entries:
            lines.append(f"## [{entry.version}] - {entry.date}\n")
            for change_type, items in entry.changes.items():
                lines.append(f"### {change_type}\n")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")
        return "\n".join(lines)

    def get_entries(self) -> list[dict]:
        return [
            {
                "version": e.version,
                "date": e.date,
                "changes": e.changes,
                "hash": e.hash,
            }
            for e in self._entries
        ]


class ArchitectureDiagramGenerator:
    """35. Architecture diagram generator (text-based)."""

    def __init__(self):
        self._nodes: dict[str, dict] = {}
        self._edges: list[tuple[str, str, str]] = []

    def add_node(self, name: str, node_type: str = "component", description: str = "") -> None:
        self._nodes[name] = {"type": node_type, "description": description}

    def add_edge(self, source: str, target: str, label: str = "") -> None:
        self._edges.append((source, target, label))

    def from_directory(self, directory: str) -> None:
        for item in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, item)) and not item.startswith("."):
                self.add_node(item, "module")
                sub = os.path.join(directory, item)
                for subitem in os.listdir(sub):
                    if subitem.endswith(".py"):
                        subname = f"{item}/{subitem[:-3]}"
                        self.add_node(subname, "file")
                        self.add_edge(item, subname, "contains")

    def generate_ascii(self) -> str:
        lines = ["Architecture Diagram", "=" * 40, ""]
        for name, info in sorted(self._nodes.items()):
            icon = {"module": "[M]", "file": "[F]", "component": "[C]", "service": "[S]"}.get(
                info["type"], "[?]"
            )
            desc = f" - {info['description']}" if info["description"] else ""
            lines.append(f"  {icon} {name}{desc}")

        lines.append("")
        lines.append("Connections:")
        for src, tgt, label in self._edges:
            lbl = f" ({label})" if label else ""
            lines.append(f"  {src} --> {tgt}{lbl}")

        return "\n".join(lines)

    def generate_mermaid(self) -> str:
        lines = ["graph TD"]
        for name in self._nodes:
            safe_name = re.sub(r"[^a-zA-Z0-9]", "_", name)
            lines.append(f"    {safe_name}[\"{name}\"]")
        for src, tgt, label in self._edges:
            safe_src = re.sub(r"[^a-zA-Z0-9]", "_", src)
            safe_tgt = re.sub(r"[^a-zA-Z0-9]", "_", tgt)
            if label:
                lines.append(f"    {safe_src} -->|{label}| {safe_tgt}")
            else:
                lines.append(f"    {safe_src} --> {safe_tgt}")
        return "\n".join(lines)


class DatabaseSchemaDocumentation:
    """36. Database schema documentation."""

    def __init__(self):
        self._tables: list[SchemaTable] = []

    def from_sqlite(self, db_path: str) -> list[SchemaTable]:
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [
                {"name": row[1], "type": row[2], "not_null": bool(row[3]), "default": row[4]}
                for row in cursor.fetchall()
            ]

            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = [
                {"from": row[3], "table": row[2], "to": row[4]}
                for row in cursor.fetchall()
            ]

            pk = None
            for col in columns:
                if col["name"] in [r[1] for r in cursor.execute(f"PRAGMA index_info(PRAGMA table_info('{table_name}'))").fetchall()]:
                    pk = col["name"]

            self._tables.append(
                SchemaTable(
                    name=table_name,
                    columns=columns,
                    primary_key=pk,
                    foreign_keys=foreign_keys,
                    indexes=[],
                )
            )
        conn.close()
        return self._tables

    def from_dict(self, schema: dict) -> None:
        for table_name, cols in schema.items():
            columns = [
                {"name": col, "type": "text", "not_null": False, "default": None}
                for col in cols
            ]
            self._tables.append(
                SchemaTable(
                    name=table_name,
                    columns=columns,
                    primary_key=cols[0] if cols else None,
                    foreign_keys=[],
                    indexes=[],
                )
            )

    def generate_markdown(self) -> str:
        lines = ["# Database Schema\n"]
        for table in self._tables:
            lines.append(f"## {table.name}\n")
            lines.append("| Column | Type | Not Null | Default |")
            lines.append("|--------|------|----------|---------|")
            for col in table.columns:
                lines.append(
                    f"| {col['name']} | {col['type']} | {col['not_null']} | {col.get('default', '')} |"
                )
            if table.foreign_keys:
                lines.append("\n**Foreign Keys:**\n")
                for fk in table.foreign_keys:
                    lines.append(f"- `{fk['from']}` -> `{fk['table']}.{fk['to']}`")
            lines.append("")
        return "\n".join(lines)

    def get_tables(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "columns": [c["name"] for c in t.columns],
                "primary_key": t.primary_key,
                "foreign_keys": t.foreign_keys,
            }
            for t in self._tables
        ]


class EnvironmentVariableDocumentation:
    """37. Environment variable documentation."""

    def __init__(self):
        self._vars: dict[str, dict] = {}

    def scan_file(self, filepath: str) -> dict:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        patterns = [
            r"os\.environ\.get\(['\"](\w+)['\"]",
            r"os\.environ\[['\"](\w+)['\"]\]",
            r"os\.getenv\(['\"](\w+)['\"]",
            r"env\(['\"](\w+)['\"]",
            r"settings\.(\w+)",
        ]
        found = set()
        for pattern in patterns:
            found.update(re.findall(pattern, content))

        env_vars = {}
        for var in found:
            if var.isupper() and len(var) > 2:
                env_vars[var] = {
                    "description": f"Environment variable {var}",
                    "used_in": filepath,
                    "has_default": f"getenv('{var}'," in content or f"get('{var}'," in content,
                }
        self._vars.update(env_vars)
        return env_vars

    def scan_directory(self, directory: str) -> dict:
        for root, _, files in os.walk(directory):
            for fn in files:
                if fn.endswith((".py", ".env", ".yaml", ".yml", ".toml")):
                    self.scan_file(os.path.join(root, fn))
        return self._vars

    def scan_dotenv(self, filepath: str) -> dict:
        env_vars = {}
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    env_vars[key] = {
                        "description": f"Configured in {filepath}",
                        "has_value": bool(value),
                        "is_secret": any(kw in key.lower() for kw in ["key", "secret", "password", "token"]),
                    }
        self._vars.update(env_vars)
        return env_vars

    def generate_docs(self) -> str:
        lines = ["# Environment Variables\n"]
        for name, info in sorted(self._vars.items()):
            secret = " [SECRET]" if info.get("is_secret") else ""
            lines.append(f"## `{name}`{secret}\n")
            lines.append(f"- **Description:** {info.get('description', 'N/A')}")
            if info.get("has_default"):
                lines.append("- **Has default:** Yes")
            lines.append("")
        return "\n".join(lines)

    def get_vars(self) -> dict:
        return self._vars


class DeploymentGuideGenerator:
    """38. Deployment guide generator."""

    def __init__(self):
        self._config: dict = {}

    def configure(
        self,
        project_name: str,
        platform: str = "docker",
        port: int = 8000,
        env_vars: list[str] | None = None,
        health_check: str = "/health",
    ) -> None:
        self._config = {
            "project_name": project_name,
            "platform": platform,
            "port": port,
            "env_vars": env_vars or [],
            "health_check": health_check,
        }

    def generate_docker(self) -> str:
        return f"""# Docker Deployment Guide

## Build
```bash
docker build -t {self._config['project_name']} .
```

## Run
```bash
docker run -d -p {self._config['port']}:{self._config['port']} \\
  --name {self._config['project_name']} \\
  {self._config['project_name']}
```

## Health Check
```bash
curl http://localhost:{self._config['port']}{self._config['health_check']}
```
"""

    def generate_kubernetes(self) -> str:
        name = self._config["project_name"]
        return f"""# Kubernetes Deployment

## Deploy
```bash
kubectl apply -f k8s/
```

## Check Status
```bash
kubectl get pods -l app={name}
kubectl logs -l app={name}
```

## Scale
```bash
kubectl scale deployment/{name} --replicas=3
```
"""

    def generate_systemd(self) -> str:
        name = self._config["project_name"]
        return f"""# Systemd Service

## Install
```bash
sudo cp {name}.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable {name}
sudo systemctl start {name}
```

## Status
```bash
sudo systemctl status {name}
sudo journalctl -u {name} -f
```
"""

    def generate(self) -> str:
        platform = self._config.get("platform", "docker")
        generators = {
            "docker": self.generate_docker,
            "kubernetes": self.generate_kubernetes,
            "k8s": self.generate_kubernetes,
            "systemd": self.generate_systemd,
        }
        gen = generators.get(platform, self.generate_docker)
        return gen()


class RunbookGenerator:
    """39. Runbook generator."""

    def __init__(self):
        self._procedures: list[dict] = []

    def add_procedure(
        self,
        title: str,
        steps: list[str],
        description: str = "",
        severity: str = "medium",
        estimated_time: str = "5 min",
    ) -> None:
        self._procedures.append(
            {
                "title": title,
                "description": description,
                "steps": steps,
                "severity": severity,
                "estimated_time": estimated_time,
            }
        )

    def generate_common_runbooks(self) -> None:
        self.add_procedure(
            "Service Restart",
            ["Identify the failing service", "Check recent logs", "Restart the service", "Verify health check"],
            "How to restart a service",
        )
        self.add_procedure(
            "Database Failover",
            ["Check primary database status", "Promote replica to primary", "Update connection strings", "Verify data consistency"],
            "Database failover procedure",
            severity="high",
            estimated_time="15 min",
        )
        self.add_procedure(
            "Scale Up",
            ["Check current resource usage", "Determine required capacity", "Update scaling configuration", "Monitor during scaling"],
            "Scale up infrastructure",
        )

    def generate_markdown(self) -> str:
        lines = ["# Runbook\n"]
        for i, proc in enumerate(self._procedures, 1):
            lines.append(f"## {i}. {proc['title']}\n")
            if proc["description"]:
                lines.append(f"**Description:** {proc['description']}\n")
            lines.append(f"**Severity:** {proc['severity']} | **Est. Time:** {proc['estimated_time']}\n")
            lines.append("**Steps:**\n")
            for j, step in enumerate(proc["steps"], 1):
                lines.append(f"{j}. {step}")
            lines.append("")
        return "\n".join(lines)

    def get_procedures(self) -> list[dict]:
        return self._procedures


class KnowledgeBaseBuilder:
    """40. Knowledge base builder."""

    def __init__(self):
        self._entries: dict[str, dict] = {}

    def add_entry(
        self,
        key: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
        category: str = "general",
    ) -> None:
        self._entries[key] = {
            "title": title,
            "content": content,
            "tags": tags or [],
            "category": category,
            "created_at": time.time(),
            "updated_at": time.time(),
        }

    def search(self, query: str) -> list[dict]:
        query_lower = query.lower()
        results = []
        for key, entry in self._entries.items():
            score = 0
            if query_lower in entry["title"].lower():
                score += 3
            if query_lower in entry["content"].lower():
                score += 1
            if any(query_lower in tag.lower() for tag in entry["tags"]):
                score += 2
            if score > 0:
                results.append({"key": key, "score": score, **entry})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_by_category(self, category: str) -> list[dict]:
        return [
            {"key": k, **v}
            for k, v in self._entries.items()
            if v["category"] == category
        ]

    def get_by_tag(self, tag: str) -> list[dict]:
        return [
            {"key": k, **v}
            for k, v in self._entries.items()
            if tag in v["tags"]
        ]

    def generate_markdown(self) -> str:
        by_category = defaultdict(list)
        for key, entry in self._entries.items():
            by_category[entry["category"]].append({"key": key, **entry})

        lines = ["# Knowledge Base\n"]
        for category, entries in sorted(by_category.items()):
            lines.append(f"## {category.title()}\n")
            for entry in sorted(entries, key=lambda e: e["title"]):
                lines.append(f"### {entry['title']}\n")
                lines.append(f"{entry['content']}\n")
                if entry["tags"]:
                    lines.append(f"**Tags:** {', '.join(entry['tags'])}\n")
                lines.append("")
        return "\n".join(lines)

    def get_stats(self) -> dict:
        categories = defaultdict(int)
        all_tags = defaultdict(int)
        for entry in self._entries.values():
            categories[entry["category"]] += 1
            for tag in entry["tags"]:
                all_tags[tag] += 1
        return {
            "total_entries": len(self._entries),
            "categories": dict(categories),
            "top_tags": dict(sorted(all_tags.items(), key=lambda x: -x[1])[:10]),
        }

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2, default=str)
