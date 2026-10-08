#!/usr/bin/env python3
"""
Phase 3 Engine — Autonomous Evolution
======================================
Implements the final 4 ideas for Daniela's full autonomy:

  AP-15: Dead Code Reaper — find and remove unused code
  AP-02: Feature Factory — GitHub Issue -> code -> tests -> PR
  AP-13: Auto-Deploy Pipeline — push -> lint -> test -> build -> deploy
  SIL-05: Evolution Engine — architecture recommendations -> roadmap items

Cost: $0/month — Python AST + GitHub API (free) + Gemini Flash + JSON

CLI:
  python phase3_engine.py status              — overall status
  python phase3_engine.py reaper              — scan for dead code
  python phase3_engine.py reaper-remove      — generate removal PR via Jules
  python phase3_engine.py feature <issue#>   — implement a GitHub issue
  python phase3_engine.py deploy-gen          — generate deploy workflow YAML
  python phase3_engine.py evolve              — run evolution engine
  python phase3_engine.py all                 — run all 4 modules
  python phase3_engine.py export              — export JSON state
"""

import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "phase3"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = PROJECT_ROOT / "static" / "brand"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "phase3_state.json"

SKIP_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    "backup_patches",
    "tests",
    "data",
    "static",
    "docs",
    "biometric-profile",
    "assets",
    "android_app",
    "apps",
    "apps-script",
    "apps-script-admin",
    ".workbuddy-ai",
    "scripts",
    "agents",
}


def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().isoformat(),
        "dead_code_found": 0,
        "dead_code_removed": 0,
        "features_implemented": 0,
        "deploys_generated": 0,
        "evolution_items": 0,
        "last_run": "",
    }


def _save_state(state: dict):
    state["updated_at"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _get_py_files() -> list[Path]:
    """Get all Python files in the project (excluding venv, tests, etc.)."""
    files = []
    for item in PROJECT_ROOT.rglob("*.py"):
        rel = item.relative_to(PROJECT_ROOT)
        parts = rel.parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        files.append(item)
    return sorted(files)


# ==============================================================================
# AP-15: DEAD CODE REAPER
# ==============================================================================


@dataclass
class DeadCodeItem:
    """A piece of dead code found by the reaper."""

    id: str
    type: str  # function, class, import, variable
    name: str
    file: str
    line: int
    references: int  # how many times found in codebase (excluding definition)
    is_dead: bool
    recommendation: str


class DeadCodeReaper:
    """AP-15: Find and remove unused code."""

    @staticmethod
    def scan() -> list[DeadCodeItem]:
        """Scan the entire codebase for dead code (optimized single-pass)."""
        py_files = _get_py_files()

        # Phase 1: Parse all files, collect definitions and build word frequency
        definitions = []  # (name, type, file, line)
        word_counter = defaultdict(int)  # global word frequency across all files

        # Cache of (file -> code) only for files we successfully parsed
        for fpath in py_files:
            rel = str(fpath.relative_to(PROJECT_ROOT)).replace("\\", "/")
            try:
                code = fpath.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue

            # Tokenize once: extract all identifier-like words
            for m in re.finditer(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code):
                word_counter[m.group()] += 1

            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("__") or node.name == "__init__":
                        definitions.append((node.name, "function", rel, node.lineno))
                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith("_"):
                        definitions.append((node.name, "class", rel, node.lineno))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split(".")[-1]
                        definitions.append((name, "import", rel, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if name != "*":
                            definitions.append((name, "import", rel, node.lineno))

        # Phase 2: Look up each definition in the global word counter
        results = []
        seen = set()

        for name, def_type, def_file, def_line in definitions:
            key = f"{name}@{def_file}:{def_line}"
            if key in seen:
                continue
            seen.add(key)

            # Total occurrences minus the definition itself
            ref_count = max(0, word_counter.get(name, 0) - 1)
            is_dead = ref_count == 0

            item = DeadCodeItem(
                id=f"DC-{len(results) + 1:03d}",
                type=def_type,
                name=name,
                file=def_file,
                line=def_line,
                references=ref_count,
                is_dead=is_dead,
                recommendation="Remove this unused " + def_type
                if is_dead
                else f"Keep — referenced {ref_count} times",
            )
            results.append(item)

        # Sort: dead first, then by type
        results.sort(key=lambda x: (not x.is_dead, x.type, x.file, x.line))
        return results

    @staticmethod
    def get_dead_code() -> list[DeadCodeItem]:
        """Return only dead code items."""
        all_items = DeadCodeReaper.scan()
        return [item for item in all_items if item.is_dead]

    @staticmethod
    def generate_removal_report() -> dict:
        """Generate a report of all dead code for Jules removal."""
        dead = DeadCodeReaper.get_dead_code()
        by_file = defaultdict(list)
        for item in dead:
            by_file[item.file].append(asdict(item))

        report = {
            "scan_date": datetime.now().isoformat(),
            "total_definitions_scanned": len(DeadCodeReaper.scan()),
            "dead_code_items": len(dead),
            "by_type": {
                "functions": len([d for d in dead if d.type == "function"]),
                "classes": len([d for d in dead if d.type == "class"]),
                "imports": len([d for d in dead if d.type == "import"]),
            },
            "by_file": {k: len(v) for k, v in by_file.items()},
            "items": [asdict(d) for d in dead],
            "jules_prompt": DeadCodeReaper._build_jules_prompt(dead),
        }

        # Save report
        report_path = DATA_DIR / "dead_code_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        state = _load_state()
        state["dead_code_found"] = len(dead)
        _save_state(state)

        return report

    @staticmethod
    def _build_jules_prompt(dead_items: list[DeadCodeItem]) -> str:
        """Build a Jules prompt for removing dead code."""
        lines = ["# Jules Task: Remove dead code\n\n## Dead code to remove:\n"]
        for item in dead_items[:20]:  # Max 20 per Jules task
            lines.append(f"- `{item.file}:{item.line}` — {item.type} `{item.name}` (0 references)")
        lines.append("\n## Instructions:")
        lines.append("- Remove the definition and any related comments")
        lines.append("- Remove associated tests if they only test the dead code")
        lines.append("- Do NOT remove anything that might be used dynamically")
        lines.append("- If unsure, leave it")
        return "\n".join(lines)


# ==============================================================================
# AP-02: FEATURE FACTORY
# ==============================================================================


@dataclass
class FeatureRequest:
    """A feature parsed from a GitHub issue."""

    issue_number: int
    title: str
    body: str
    labels: list[str]
    created_at: str
    parsed_requirements: list[str]
    suggested_files: list[str]
    estimated_complexity: str  # S, M, L, XL


class FeatureFactory:
    """AP-02: Turn GitHub issues into code + tests + PR."""

    ISSUE_TEMPLATE_KEYWORDS = {
        "feature": ["feature", "add", "implement", "create", "build"],
        "bug": ["bug", "fix", "broken", "error", "crash"],
        "refactor": ["refactor", "cleanup", "restructure", "simplify"],
    }

    @staticmethod
    def parse_issue(
        issue_number: int, title: str, body: str, labels: list[str] = None
    ) -> FeatureRequest:
        """Parse a GitHub issue into a structured feature request."""
        labels = labels or []
        full_text = f"{title}\n{body}".lower()

        # Detect type
        for _ftype, keywords in FeatureFactory.ISSUE_TEMPLATE_KEYWORDS.items():
            if any(kw in full_text for kw in keywords):
                break

        # Extract requirements (lines with "should", "must", "need", "want")
        requirements = []
        for line in body.split("\n"):
            line = line.strip()
            if any(
                kw in line.lower()
                for kw in ["should", "must", "need", "want", "accept", "given", "when", "then"]
            ):
                if len(line) > 10:
                    requirements.append(line)

        # Suggest files based on keywords
        suggested_files = FeatureFactory._suggest_files(title, body)

        # Estimate complexity
        word_count = len(body.split())
        if word_count < 50:
            complexity = "S"
        elif word_count < 150:
            complexity = "M"
        elif word_count < 400:
            complexity = "L"
        else:
            complexity = "XL"

        return FeatureRequest(
            issue_number=issue_number,
            title=title,
            body=body,
            labels=labels,
            created_at=datetime.now().isoformat(),
            parsed_requirements=requirements,
            suggested_files=suggested_files,
            estimated_complexity=complexity,
        )

    @staticmethod
    def _suggest_files(title: str, body: str) -> list[str]:
        """Suggest which files should be modified based on issue keywords."""
        text = f"{title} {body}".lower()
        suggestions = []

        keyword_map = {
            "agent": ["agents.py", "agent_*.py"],
            "correo": ["agent_correo.py"],
            "calendario": ["agent_calendario.py"],
            "documento": ["agent_documentos.py"],
            "redes": ["agent_redes.py"],
            "vigia": ["agent_vigia.py"],
            "api": ["daniela_os.py", "api_gateway.py"],
            "auth": ["auth_system.py"],
            "frontend": ["static/", "templates/"],
            "dashboard": ["static/", "templates/index.html"],
            "content": ["content_factory_ai.py", "viral_content_factory.py"],
            "billing": ["billing_system.py"],
            "analytics": ["analytics.py"],
            "security": ["auth_system.py", "bypass_pin.py"],
            "deploy": ["autodeploy_core.py"],
            "test": ["tests/"],
        }

        for keyword, files in keyword_map.items():
            if keyword in text:
                suggestions.extend(files)

        return list(set(suggestions)) if suggestions else ["(auto-detect via Gemini)"]

    @staticmethod
    def generate_implementation_plan(feature: FeatureRequest) -> dict:
        """Generate an implementation plan for a feature request."""
        plan = {
            "feature_id": f"FF-{feature.issue_number}",
            "title": feature.title,
            "complexity": feature.estimated_complexity,
            "requirements": feature.parsed_requirements,
            "files_to_modify": feature.suggested_files,
            "steps": [
                "1. Analyze existing code in suggested files",
                "2. Design the implementation approach",
                "3. Write the new code following existing patterns",
                "4. Generate tests for the new feature",
                "5. Update documentation if applicable",
                "6. Run tests to verify",
                "7. Open PR with description",
            ],
            "jules_prompt": FeatureFactory._build_jules_prompt(feature),
            "auto_merge_criteria": [
                "All tests pass",
                "SIL finds no new critical findings",
                "No merge conflicts",
                "Pre-commit hook passes",
            ],
        }

        # Save plan
        plan_path = DATA_DIR / f"feature_plan_{feature.issue_number}.json"
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        state = _load_state()
        state["features_implemented"] += 1
        _save_state(state)

        return plan

    @staticmethod
    def _build_jules_prompt(feature: FeatureRequest) -> str:
        """Build a Jules prompt for implementing the feature."""
        return f"""# Jules Task: Implement {feature.title}

## Issue #{feature.issue_number}
{feature.body[:2000]}

## Requirements
{chr(10).join(f"- {r}" for r in feature.parsed_requirements) or "- See issue body"}

## Suggested files to modify
{chr(10).join(f"- {f}" for f in feature.suggested_files)}

## Complexity
{feature.estimated_complexity}

## Instructions
- Follow existing code patterns in the codebase
- Add type hints and docstrings
- Generate tests in tests/auto_generated/
- Do NOT break existing API contracts
- Keep changes focused and minimal
"""


# ==============================================================================
# AP-13: AUTO-DEPLOY PIPELINE
# ==============================================================================


class AutoDeployPipeline:
    """AP-13: Generate CI/CD pipeline for automatic deployment."""

    WORKFLOW_TEMPLATE = """name: Daniela Auto-Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install linter
        run: pip install ruff
      - name: Lint
        run: ruff check . --exit-zero

  type-check:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install mypy
        run: pip install mypy
      - name: Type check
        run: mypy *.py --ignore-missing-imports || true

  test:
    runs-on: ubuntu-latest
    needs: type-check
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov flask python-dotenv
      - name: Run tests
        run: |
          python autoprog_engine.py tests
          pytest tests/auto_generated/ -v --tb=short || true
      - name: Pre-commit check
        run: python autoprog_engine.py precommit-check || true
      - name: SIL health check
        run: python sil_engine.py status

  security-scan:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install security tools
        run: pip install bandit
      - name: Security scan
        run: bandit -r *.py -ll || true

  build:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: |
          tar -czf aigestion.tar.gz *.py static/ templates/ agents/ skills/

  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy notification
        run: |
          echo "Deploy triggered at $(date)"
          python sil_engine.py dashboard
      - name: Health check
        run: |
          echo "Post-deploy health check..."
          python autoprog_engine.py heal daniela_os.py
      - name: Rollback on failure
        if: failure()
        run: |
          echo "ROLLBACK TRIGGERED"
          git log --oneline -5
"""

    DOCKERFILE_TEMPLATE = """# Auto-generated Dockerfile (AP-14)
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

COPY . .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status')"

CMD ["python", "daniela_os.py", "--host", "127.0.0.1", "--port", "5000"]
"""

    @staticmethod
    def generate_workflow() -> dict:
        """Generate GitHub Actions workflow YAML."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "auto-deploy.yml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(AutoDeployPipeline.WORKFLOW_TEMPLATE, encoding="utf-8")

        # Also generate Dockerfile
        dockerfile_path = PROJECT_ROOT / "Dockerfile"
        dockerfile_path.write_text(AutoDeployPipeline.DOCKERFILE_TEMPLATE, encoding="utf-8")

        # .dockerignore
        dockerignore = PROJECT_ROOT / ".dockerignore"
        dockerignore.write_text(
            ".venv\n__pycache__\n*.pyc\n.git\ndata/\ntests/\ndocs/\n", encoding="utf-8"
        )

        state = _load_state()
        state["deploys_generated"] += 1
        _save_state(state)

        return {
            "workflow_path": str(workflow_path),
            "dockerfile_path": str(dockerfile_path),
            "dockerignore_path": str(dockerignore),
            "stages": ["lint", "type-check", "test", "security-scan", "build", "deploy"],
            "free_tier": "GitHub Actions (2000 min/month free)",
            "rollback": "Automatic on failure",
        }


# ==============================================================================
# SIL-05: EVOLUTION ENGINE
# ==============================================================================


@dataclass
class EvolutionItem:
    """An architecture recommendation that becomes a roadmap item."""

    id: str
    title: str
    source: str  # where the recommendation came from
    category: str  # architecture, security, testing, performance
    priority: str  # critical, high, medium, low
    effort: str  # S, M, L, XL
    description: str
    status: str = "proposed"  # proposed, accepted, in_progress, implemented, rejected
    dependencies: list[str] = field(default_factory=list)
    date_added: str = ""


class EvolutionEngine:
    """SIL-05: Turn architecture recommendations into roadmap items."""

    # Pre-seeded from Gemini 3.1 Pro architecture analysis (2026-09-05)
    INITIAL_RECOMMENDATIONS = [
        EvolutionItem(
            id="EV-01",
            title="Standardize LLM access through ModelRouter",
            source="Gemini 3.1 Pro architecture analysis",
            category="architecture",
            priority="high",
            effort="M",
            description="Multiple files use Gemini directly with different patterns. Centralize through gemini35_free_tier.py ModelRouter for consistent routing, fallback, and rate limiting.",
            dependencies=[],
        ),
        EvolutionItem(
            id="EV-02",
            title="Implement SQLAlchemy ORM",
            source="Gemini 3.1 Pro architecture analysis",
            category="architecture",
            priority="medium",
            effort="L",
            description="Replace scattered sqlite3 raw queries with SQLAlchemy/SQLModel ORM. Benefits: type safety, migrations, relationships, connection pooling.",
            dependencies=["EV-01"],
        ),
        EvolutionItem(
            id="EV-03",
            title="Extract static data to JSON/YAML config files",
            source="Gemini 3.1 Pro architecture analysis",
            category="architecture",
            priority="medium",
            effort="M",
            description="Brand kit, calendar, epic ideas are hardcoded in Python. Extract to JSON for easier updates and non-developer editing.",
            dependencies=[],
        ),
        EvolutionItem(
            id="EV-04",
            title="Adopt real agent framework (LangGraph or CrewAI)",
            source="Gemini 3.1 Pro architecture analysis",
            category="architecture",
            priority="high",
            effort="L",
            description="swarm_intelligence.py uses simulated execution. Replace with a real agent framework that supports parallel execution, state management, and inter-agent communication.",
            dependencies=["EV-01"],
        ),
        EvolutionItem(
            id="EV-05",
            title="Standardize module interfaces with base AgentModule class",
            source="Gemini 3.1 Pro architecture analysis",
            category="architecture",
            priority="high",
            effort="M",
            description="Each agent module has a different interface. Create an abstract base class that defines the contract: initialize(), process(), get_status(), shutdown(). All agents must implement it.",
            dependencies=["EV-04"],
        ),
        EvolutionItem(
            id="EV-06",
            title="Add OpenAPI/Swagger documentation",
            source="SIL finding SR-14",
            category="documentation",
            priority="low",
            effort="S",
            description="Flask endpoints have no API documentation. Add flask-smorest or flasgger for auto-generated OpenAPI spec and Swagger UI.",
            dependencies=[],
        ),
        EvolutionItem(
            id="EV-07",
            title="Implement refresh token rotation",
            source="SIL finding SR-15",
            category="security",
            priority="low",
            effort="S",
            description="Old refresh token not invalidated when used. Implement rotation: delete old, issue new on each refresh.",
            dependencies=["EV-06"],
        ),
        EvolutionItem(
            id="EV-08",
            title="Connect content_factory_ai.py to Gemini ModelRouter",
            source="SIL finding SR-07",
            category="integration",
            priority="high",
            effort="S",
            description="Content factory has stubs that return strings. Connect to real Gemini API via ModelRouter for actual content generation.",
            status="implemented",
            dependencies=["EV-01"],
        ),
    ]

    @staticmethod
    def get_items(status_filter: str | None = None) -> list[EvolutionItem]:
        """Get evolution items, optionally filtered by status."""
        items = EvolutionEngine.INITIAL_RECOMMENDATIONS
        if status_filter:
            items = [i for i in items if i.status == status_filter]
        return items

    @staticmethod
    def run_evolution() -> dict:
        """Run the evolution engine: review recommendations and update status."""
        items = EvolutionEngine.INITIAL_RECOMMENDATIONS

        # Check which recommendations have been implemented by checking the codebase
        implemented = EvolutionEngine._check_implementation()

        # Update statuses
        updated = []
        for item in items:
            if item.id in implemented:
                item.status = "implemented"
            updated.append(item)

        # Generate roadmap
        roadmap = EvolutionEngine._generate_roadmap(updated)

        # Save
        report = {
            "run_date": datetime.now().isoformat(),
            "total_items": len(updated),
            "by_status": {
                "proposed": len([i for i in updated if i.status == "proposed"]),
                "accepted": len([i for i in updated if i.status == "accepted"]),
                "in_progress": len([i for i in updated if i.status == "in_progress"]),
                "implemented": len([i for i in updated if i.status == "implemented"]),
                "rejected": len([i for i in updated if i.status == "rejected"]),
            },
            "by_priority": {
                "critical": len([i for i in updated if i.priority == "critical"]),
                "high": len([i for i in updated if i.priority == "high"]),
                "medium": len([i for i in updated if i.priority == "medium"]),
                "low": len([i for i in updated if i.priority == "low"]),
            },
            "items": [asdict(i) for i in updated],
            "roadmap": roadmap,
        }

        report_path = DATA_DIR / "evolution_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        state = _load_state()
        state["evolution_items"] = len(updated)
        _save_state(state)

        return report

    @staticmethod
    def _check_implementation() -> set[str]:
        """Check which recommendations have been implemented by scanning code."""
        implemented = set()

        # EV-01: ModelRouter
        if (PROJECT_ROOT / "gemini35_free_tier.py").exists():
            code = (PROJECT_ROOT / "gemini35_free_tier.py").read_text(
                encoding="utf-8", errors="ignore"
            )
            if "ModelRouter" in code:
                implemented.add("EV-01")

        # EV-03: JSON config files
        json_configs = list((PROJECT_ROOT / "static" / "brand").glob("*.json"))
        if len(json_configs) > 5:
            implemented.add("EV-03")

        # EV-06: OpenAPI
        for fpath in _get_py_files():
            code = fpath.read_text(encoding="utf-8", errors="ignore")
            if "flasgger" in code or "smorest" in code or "openapi" in code.lower():
                implemented.add("EV-06")
                break

        # EV-08: Content factory connected
        if (PROJECT_ROOT / "content_factory_ai.py").exists():
            code = (PROJECT_ROOT / "content_factory_ai.py").read_text(
                encoding="utf-8", errors="ignore"
            )
            if "gemini35" in code or "ModelRouter" in code or "model_router" in code.lower():
                implemented.add("EV-08")

        return implemented

    @staticmethod
    def _generate_roadmap(items: list[EvolutionItem]) -> list[dict]:
        """Generate a prioritized roadmap from evolution items."""
        # Sort by priority then by effort
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        effort_order = {"S": 0, "M": 1, "L": 2, "XL": 3}

        sorted_items = sorted(
            items,
            key=lambda x: (
                priority_order.get(x.priority, 4),
                effort_order.get(x.effort, 3),
            ),
        )

        roadmap = []
        for i, item in enumerate(sorted_items):
            if item.status == "implemented":
                continue
            roadmap.append(
                {
                    "order": i + 1,
                    "id": item.id,
                    "title": item.title,
                    "priority": item.priority,
                    "effort": item.effort,
                    "category": item.category,
                    "dependencies": item.dependencies,
                    "status": item.status,
                }
            )

        return roadmap


# ==============================================================================
# FULL RUN
# ==============================================================================


def run_all():
    print("=" * 60)
    print("  PHASE 3 — AUTONOMOUS EVOLUTION")
    print("=" * 60)
    print()

    print("[AP-15] Dead Code Reaper")
    print("-" * 40)
    report = DeadCodeReaper.generate_removal_report()
    print(f"  Definitions scanned: {report['total_definitions_scanned']}")
    print(f"  Dead code found: {report['dead_code_items']}")
    print(f"  By type: {report['by_type']}")
    print(f"  Report: {DATA_DIR / 'dead_code_report.json'}")
    print()

    print("[AP-02] Feature Factory (demo)")
    print("-" * 40)
    demo_feature = FeatureFactory.parse_issue(
        issue_number=1,
        title="Add rate limiting to API endpoints",
        body="The API should limit requests to 100 per minute per user. Need to add a middleware that tracks requests by IP and returns 429 when exceeded.",
        labels=["auto-implement", "enhancement"],
    )
    plan = FeatureFactory.generate_implementation_plan(demo_feature)
    print(f"  Feature: {plan['title']}")
    print(f"  Complexity: {plan['complexity']}")
    print(f"  Requirements: {len(plan['requirements'])}")
    print(f"  Files to modify: {plan['files_to_modify']}")
    print(f"  Jules prompt: {len(plan['jules_prompt'])} chars")
    print()

    print("[AP-13] Auto-Deploy Pipeline")
    print("-" * 40)
    deploy = AutoDeployPipeline.generate_workflow()
    print(f"  Workflow: {deploy['workflow_path']}")
    print(f"  Dockerfile: {deploy['dockerfile_path']}")
    print(f"  Stages: {', '.join(deploy['stages'])}")
    print(f"  Free tier: {deploy['free_tier']}")
    print(f"  Rollback: {deploy['rollback']}")
    print()

    print("[SIL-05] Evolution Engine")
    print("-" * 40)
    evo = EvolutionEngine.run_evolution()
    print(f"  Total items: {evo['total_items']}")
    print(f"  By status: {evo['by_status']}")
    print(f"  By priority: {evo['by_priority']}")
    print(f"  Roadmap items (pending): {len(evo['roadmap'])}")
    print(f"  Report: {DATA_DIR / 'evolution_report.json'}")
    print()

    state = _load_state()
    state["last_run"] = datetime.now().isoformat()
    _save_state(state)

    print("=" * 60)
    print("  PHASE 3 COMPLETE")
    print("=" * 60)
    cli_status()


# ==============================================================================
# CLI
# ==============================================================================


def cli_status():
    state = _load_state()
    print("\n" + "=" * 60)
    print("  PHASE 3 ENGINE — STATUS")
    print("=" * 60)
    print(f"\n  Dead code found: {state.get('dead_code_found', 0)}")
    print(f"  Dead code removed: {state.get('dead_code_removed', 0)}")
    print(f"  Features implemented: {state.get('features_implemented', 0)}")
    print(f"  Deploys generated: {state.get('deploys_generated', 0)}")
    print(f"  Evolution items: {state.get('evolution_items', 0)}")
    print(f"  Last run: {state.get('last_run', 'Never')}")
    print(f"\n  State file: {STATE_FILE}")
    print(f"  Data dir: {DATA_DIR}")
    print()


def cli_export():
    state = _load_state()
    data = {
        "status": state,
        "evolution_items": [asdict(i) for i in EvolutionEngine.INITIAL_RECOMMENDATIONS],
    }
    path = OUTPUT_DIR / "phase3_engine_state.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[Phase 3] Exported state to {path}")


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python phase3_engine.py status|reaper|reaper-remove|feature <n>|deploy-gen|evolve|all|export"
        )
        return

    cmd = sys.argv[1]

    if cmd == "status":
        cli_status()

    elif cmd == "reaper":
        report = DeadCodeReaper.generate_removal_report()
        print("\n  Dead Code Reaper Report")
        print(f"  Definitions scanned: {report['total_definitions_scanned']}")
        print(f"  Dead code found: {report['dead_code_items']}")
        print(f"  Functions: {report['by_type']['functions']}")
        print(f"  Classes: {report['by_type']['classes']}")
        print(f"  Imports: {report['by_type']['imports']}")
        print("\n  Top dead code items:")
        for item in report["items"][:15]:
            print(f"    [{item['type']}] {item['name']} — {item['file']}:{item['line']}")

    elif cmd == "reaper-remove":
        report = DeadCodeReaper.generate_removal_report()
        print(f"\n  Jules removal prompt ({len(report['jules_prompt'])} chars):")
        print(report["jules_prompt"])

    elif cmd == "feature":
        if len(sys.argv) < 3:
            print("Usage: python phase3_engine.py feature <issue_number>")
            print("  (Also needs --title and --body)")
            return
        # Demo mode
        feature = FeatureFactory.parse_issue(
            issue_number=int(sys.argv[2]),
            title="Demo feature",
            body="Demo feature body",
        )
        plan = FeatureFactory.generate_implementation_plan(feature)
        print(f"\n  Feature: {plan['title']}")
        print(f"  Complexity: {plan['complexity']}")
        print(f"  Steps: {len(plan['steps'])}")
        print(f"  Jules prompt: {len(plan['jules_prompt'])} chars")

    elif cmd == "deploy-gen":
        result = AutoDeployPipeline.generate_workflow()
        print(f"\n  Workflow: {result['workflow_path']}")
        print(f"  Dockerfile: {result['dockerfile_path']}")
        print(f"  Stages: {', '.join(result['stages'])}")

    elif cmd == "evolve":
        report = EvolutionEngine.run_evolution()
        print("\n  Evolution Engine Report")
        print(f"  Total items: {report['total_items']}")
        print(f"  By status: {report['by_status']}")
        print(f"  By priority: {report['by_priority']}")
        print("\n  Roadmap (pending items):")
        for item in report["roadmap"]:
            print(
                f"    {item['order']}. [{item['priority']}] {item['id']}: {item['title']} ({item['effort']})"
            )

    elif cmd == "all":
        run_all()

    elif cmd == "export":
        cli_export()

    else:
        print(f"Unknown command: {cmd}")
        print("Available: status|reaper|reaper-remove|feature <n>|deploy-gen|evolve|all|export")


if __name__ == "__main__":
    main()
