"""Code analysis tools (11-20)."""

import ast
import hashlib
import os
import re
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class ComplexityResult:
    function: str
    file: str
    line: int
    cyclomatic: int
    cognitive: int
    rank: str


@dataclass
class DuplicateBlock:
    content_hash: str
    files: list
    line_ranges: list
    lines_count: int


@dataclass
class DeadCodeItem:
    file: str
    name: str
    line: int
    kind: str
    confidence: float


@dataclass
class ImportNode:
    module: str
    source_file: str
    imported_names: list
    is_local: bool


@dataclass
class EndpointInfo:
    method: str
    path: str
    file: str
    line: int
    handler: str
    decorators: list


@dataclass
class QueryInfo:
    query: str
    file: str
    line: int
    has_index: bool
    has_limit: bool
    has_where: bool


@dataclass
class SecurityIssue:
    file: str
    line: int
    issue_type: str
    severity: str
    description: str
    suggestion: str


@dataclass
class CodeSmell:
    file: str
    line: int
    smell_type: str
    severity: str
    description: str


class CyclomaticComplexityAnalyzer:
    """11. Complexity analyzer (cyclomatic)."""

    def __init__(self):
        self._results: list[ComplexityResult] = []

    def analyze_file(self, filepath: str) -> list[ComplexityResult]:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return []

        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = self._cyclomatic_complexity(node)
                cog = self._cognitive_complexity(node, 0)
                rank = self._get_rank(cc)
                results.append(
                    ComplexityResult(
                        function=node.name,
                        file=filepath,
                        line=node.lineno,
                        cyclomatic=cc,
                        cognitive=cog,
                        rank=rank,
                    )
                )
        self._results.extend(results)
        return results

    def _cyclomatic_complexity(self, node: ast.AST) -> int:
        cc = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                cc += 1
            elif isinstance(child, ast.BoolOp):
                cc += len(child.values) - 1
            elif isinstance(child, (ast.ExceptHandler,)):
                cc += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                cc += 1
        return cc

    def _cognitive_complexity(self, node: ast.AST, nesting: int) -> int:
        total = 0
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                total += 1 + nesting
                total += self._cognitive_complexity(child, nesting + 1)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += 1 + nesting
                total += self._cognitive_complexity(child, nesting + 1)
            elif isinstance(child, ast.BoolOp):
                total += len(child.values) - 1
            else:
                total += self._cognitive_complexity(child, nesting)
        return total

    @staticmethod
    def _get_rank(cc: int) -> str:
        if cc <= 5:
            return "A"
        elif cc <= 10:
            return "B"
        elif cc <= 20:
            return "C"
        elif cc <= 30:
            return "D"
        return "F"

    def get_summary(self) -> dict:
        if not self._results:
            return {"total_functions": 0, "avg_complexity": 0, "rank_distribution": {}}
        ranks = defaultdict(int)
        for r in self._results:
            ranks[r.rank] += 1
        avg_cc = sum(r.cyclomatic for r in self._results) / len(self._results)
        return {
            "total_functions": len(self._results),
            "avg_complexity": round(avg_cc, 2),
            "rank_distribution": dict(ranks),
        }


class CodeDuplicationDetector:
    """12. Code duplication detector."""

    def __init__(self, min_lines: int = 5, window_size: int = 4):
        self._min_lines = min_lines
        self._window_size = window_size

    def analyze_directory(self, directory: str) -> list[DuplicateBlock]:
        files = {}
        for root, _, filenames in os.walk(directory):
            for fn in filenames:
                if fn.endswith(".py"):
                    fp = os.path.join(root, fn)
                    try:
                        with open(fp, encoding="utf-8") as f:
                            files[fp] = self._normalize(f.readlines())
                    except (OSError, UnicodeDecodeError):
                        continue
        return self._find_duplicates(files)

    def _normalize(self, lines: list[str]) -> list[str]:
        normalized = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                normalized.append(stripped)
        return normalized

    def _find_duplicates(self, files: dict[str, list[str]]) -> list[DuplicateBlock]:
        windows: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for filepath, lines in files.items():
            for i in range(len(lines) - self._window_size + 1):
                window = "\n".join(lines[i : i + self._window_size])
                h = hashlib.md5(window.encode()).hexdigest()
                windows[h].append((filepath, i))

        duplicates = []
        seen = set()
        for h, occurrences in windows.items():
            if len(occurrences) < 2:
                continue
            file_groups: dict[str, list[int]] = defaultdict(list)
            for fp, line_idx in occurrences:
                file_groups[fp].append(line_idx)

            if len(file_groups) < 2:
                continue

            key = tuple(sorted(file_groups.keys()))
            if key in seen:
                continue
            seen.add(key)

            all_files = list(file_groups.keys())
            line_ranges = []
            for fp in all_files:
                start = min(file_groups[fp])
                line_ranges.append(f"{fp}:{start}-{start + self._window_size}")

            duplicates.append(
                DuplicateBlock(
                    content_hash=h,
                    files=all_files,
                    line_ranges=line_ranges,
                    lines_count=self._window_size,
                )
            )
        return duplicates

    def get_results(self) -> list[dict]:
        blocks = self.analyze_directory(".")
        return [
            {
                "hash": d.content_hash,
                "files": d.files,
                "line_ranges": d.line_ranges,
                "lines": d.lines_count,
            }
            for d in blocks
        ]


class DeadCodeDetector:
    """13. Dead code detector."""

    def __init__(self):
        self._results: list[DeadCodeItem] = []

    def analyze_file(self, filepath: str) -> list[DeadCodeItem]:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return []

        defined_names = {}
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_names[node.name] = ("function", node.lineno)
            elif isinstance(node, ast.AsyncFunctionDef):
                defined_names[node.name] = ("async_function", node.lineno)
            elif isinstance(node, ast.ClassDef):
                defined_names[node.name] = ("class", node.lineno)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)

        results = []
        for name, (kind, lineno) in defined_names.items():
            if name.startswith("_") and name != "__init__":
                continue
            if name not in used_names:
                results.append(
                    DeadCodeItem(
                        file=filepath,
                        name=name,
                        line=lineno,
                        kind=kind,
                        confidence=0.7,
                    )
                )
        self._results.extend(results)
        return results

    def get_results(self) -> list[dict]:
        return [
            {
                "file": d.file,
                "name": d.name,
                "line": d.line,
                "kind": d.kind,
                "confidence": d.confidence,
            }
            for d in self._results
        ]


class ImportDependencyGraph:
    """14. Import dependency graph."""

    def __init__(self):
        self._nodes: dict[str, ImportNode] = {}
        self._edges: dict[str, set[str]] = defaultdict(set)

    def analyze_file(self, filepath: str) -> list[ImportNode]:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return []

        nodes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    n = ImportNode(
                        module=alias.name,
                        source_file=filepath,
                        imported_names=[alias.asname or alias.name],
                        is_local=not alias.name.startswith(("os", "sys", "json")),
                    )
                    self._nodes[f"{filepath}:{alias.name}"] = n
                    nodes.append(n)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [a.name for a in node.names]
                n = ImportNode(
                    module=module,
                    source_file=filepath,
                    imported_names=names,
                    is_local=module.startswith("."),
                )
                self._nodes[f"{filepath}:{module}"] = n
                nodes.append(n)
                self._edges[filepath].add(module)
        return nodes

    def get_graph(self) -> dict:
        return {
            "nodes": [
                {
                    "module": n.module,
                    "source": n.source_file,
                    "imports": n.imported_names,
                }
                for n in self._nodes.values()
            ],
            "edges": {k: list(v) for k, v in self._edges.items()},
        }

    def get_reverse_deps(self, module: str) -> list[str]:
        dependents = []
        for source, deps in self._edges.items():
            if module in deps:
                dependents.append(source)
        return dependents


class APIEndpointMapper:
    """15. API endpoint mapper."""

    def __init__(self):
        self._endpoints: list[EndpointInfo] = []
        self._frameworks = {
            "flask": [r'@(?:app|blueprint)\.(route|get|post|put|delete|patch)\('],
            "fastapi": [r'@(?:app|router)\.(get|post|put|delete|patch)\('],
            "django": [r'path\(', r'url\('],
        }

    def analyze_file(self, filepath: str) -> list[EndpointInfo]:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        endpoints = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            for _framework, patterns in self._frameworks.items():
                for pattern in patterns:
                    if re.search(pattern, stripped):
                        method = self._extract_method(stripped)
                        path = self._extract_path(stripped)
                        handler = self._extract_handler(lines, i)
                        endpoints.append(
                            EndpointInfo(
                                method=method.upper(),
                                path=path,
                                file=filepath,
                                line=i + 1,
                                handler=handler,
                                decorators=[stripped],
                            )
                        )
        self._endpoints.extend(endpoints)
        return endpoints

    @staticmethod
    def _extract_method(decorator: str) -> str:
        for method in ["get", "post", "put", "delete", "patch"]:
            if method in decorator.lower():
                return method
        return "GET"

    @staticmethod
    def _extract_path(decorator: str) -> str:
        match = re.search(r"['\"]([^'\"]+)['\"]", decorator)
        return match.group(1) if match else "/"

    @staticmethod
    def _extract_handler(lines: list[str], decorator_line: int) -> str:
        for i in range(decorator_line + 1, min(decorator_line + 3, len(lines))):
            line = lines[i].strip()
            if line.startswith(("def ", "async def ")):
                name = line.split("(")[0].replace("def ", "").replace("async ", "")
                return name
        return "unknown"

    def get_endpoints(self) -> list[dict]:
        return [
            {
                "method": e.method,
                "path": e.path,
                "handler": e.handler,
                "file": e.file,
                "line": e.line,
            }
            for e in self._endpoints
        ]


class DatabaseQueryAnalyzer:
    """16. Database query analyzer."""

    def __init__(self):
        self._queries: list[QueryInfo] = []
        self._patterns = {
            "select": r"(?:SELECT|select)\s+",
            "insert": r"(?:INSERT|insert)\s+INTO",
            "update": r"(?:UPDATE|update)\s+\w+\s+SET",
            "delete": r"(?:DELETE|delete)\s+FROM",
        }

    def analyze_string(self, query: str, source: str = "unknown", line: int = 0) -> QueryInfo:
        qi = QueryInfo(
            query=query.strip(),
            file=source,
            line=line,
            has_index=False,
            has_limit="LIMIT" in query.upper() or "limit" in query.lower(),
            has_where="WHERE" in query.upper() or "where" in query.lower(),
        )
        self._queries.append(qi)
        return qi

    def analyze_file(self, filepath: str) -> list[QueryInfo]:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        query_pattern = r"""(?:""" + "|".join(self._patterns.values()) + r""")[^"']*?['"]"""
        results = []
        for match in re.finditer(query_pattern, content, re.DOTALL):
            line_num = content[: match.start()].count("\n") + 1
            qi = self.analyze_string(match.group(), filepath, line_num)
            results.append(qi)
        return results

    def get_issues(self) -> list[dict]:
        issues = []
        for q in self._queries:
            if not q.has_where and ("SELECT" in q.query.upper() or "DELETE" in q.query.upper()):
                issues.append({"type": "missing_where", "query": q.query[:80], "file": q.file})
            if not q.has_limit and "SELECT" in q.query.upper():
                issues.append({"type": "missing_limit", "query": q.query[:80], "file": q.file})
        return issues


class SecurityCodeScanner:
    """17. Security code scanner."""

    def __init__(self):
        self._rules: list[dict] = [
            {
                "pattern": r"(?:password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
                "type": "hardcoded_secret",
                "severity": "high",
                "suggestion": "Use environment variables instead of hardcoded secrets",
            },
            {
                "pattern": r"eval\s*\(",
                "type": "eval_usage",
                "severity": "high",
                "suggestion": "Avoid eval(), use ast.literal_eval() or safer alternatives",
            },
            {
                "pattern": r"exec\s*\(",
                "type": "exec_usage",
                "severity": "high",
                "suggestion": "Avoid exec(), refactor to use functions directly",
            },
            {
                "pattern": r"subprocess\.(?:call|run)\([^)]*shell\s*=\s*True",
                "type": "shell_injection",
                "severity": "high",
                "suggestion": "Use shell=False with argument list instead",
            },
            {
                "pattern": r"(?:pickle\.loads?|yaml\.load)\(",
                "type": "unsafe_deserialization",
                "severity": "medium",
                "suggestion": "Use safe loading methods (yaml.safe_load, json.loads)",
            },
            {
                "pattern": r"SQL\s*=\s*['\"].*%s|\.format\(",
                "type": "sql_injection",
                "severity": "high",
                "suggestion": "Use parameterized queries instead of string formatting",
            },
            {
                "pattern": r"chmod\s+777|0o777",
                "type": "insecure_permissions",
                "severity": "medium",
                "suggestion": "Use more restrictive file permissions",
            },
        ]
        self._issues: list[SecurityIssue] = []

    def scan_file(self, filepath: str) -> list[SecurityIssue]:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        issues = []
        for i, line in enumerate(lines):
            for rule in self._rules:
                if re.search(rule["pattern"], line, re.IGNORECASE):
                    issue = SecurityIssue(
                        file=filepath,
                        line=i + 1,
                        issue_type=rule["type"],
                        severity=rule["severity"],
                        description=f"Found: {rule['type']}",
                        suggestion=rule["suggestion"],
                    )
                    issues.append(issue)
        self._issues.extend(issues)
        return issues

    def scan_directory(self, directory: str) -> list[SecurityIssue]:
        all_issues = []
        for root, _, files in os.walk(directory):
            for fn in files:
                if fn.endswith(".py"):
                    fp = os.path.join(root, fn)
                    all_issues.extend(self.scan_file(fp))
        return all_issues

    def get_summary(self) -> dict:
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        for issue in self._issues:
            by_severity[issue.severity] += 1
            by_type[issue.issue_type] += 1
        return {
            "total_issues": len(self._issues),
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
        }


class PerformanceCodeAnalyzer:
    """18. Performance code analyzer."""

    def __init__(self):
        self._issues: list[dict] = []
        self._rules = [
            {
                "pattern": r"for\s+\w+\s+in\s+range\(.+len\(",
                "type": "inefficient_iteration",
                "suggestion": "Use enumerate() or direct iteration",
            },
            {
                "pattern": r"\+=\s*['\"].*['\"]|=\s*\w+\s*\+\s*['\"]",
                "type": "string_concatenation",
                "suggestion": "Use f-strings or str.join() for better performance",
            },
            {
                "pattern": r"import\s+.*\*",
                "type": "wildcard_import",
                "suggestion": "Use explicit imports to avoid namespace pollution",
            },
            {
                "pattern": r"(?:try|except)\s*:",
                "type": "bare_except",
                "suggestion": "Catch specific exceptions instead of using bare except",
            },
        ]

    def analyze_file(self, filepath: str) -> list[dict]:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        issues = []
        for i, line in enumerate(lines):
            for rule in self._rules:
                if re.search(rule["pattern"], line):
                    issues.append(
                        {
                            "file": filepath,
                            "line": i + 1,
                            "type": rule["type"],
                            "suggestion": rule["suggestion"],
                        }
                    )
        self._issues.extend(issues)
        return issues

    def get_results(self) -> list[dict]:
        return self._issues


class CodeSmellDetector:
    """19. Code smell detector."""

    def __init__(self):
        self._smells: list[CodeSmell] = []

    def analyze_file(self, filepath: str) -> list[CodeSmell]:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return []

        lines = source.split("\n")
        smells = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = self._get_function_length(node)
                if func_lines > 50:
                    smells.append(
                        CodeSmell(
                            file=filepath,
                            line=node.lineno,
                            smell_type="long_method",
                            severity="medium",
                            description=f"Function '{node.name}' is {func_lines} lines long",
                        )
                    )
                if len(node.args.args) > 5:
                    smells.append(
                        CodeSmell(
                            file=filepath,
                            line=node.lineno,
                            smell_type="too_many_parameters",
                            severity="low",
                            description=f"Function '{node.name}' has {len(node.args.args)} parameters",
                        )
                    )

            elif isinstance(node, ast.ClassDef):
                methods = [
                    n
                    for n in ast.iter_child_nodes(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                if len(methods) > 20:
                    smells.append(
                        CodeSmell(
                            file=filepath,
                            line=node.lineno,
                            smell_type="god_class",
                            severity="high",
                            description=f"Class '{node.name}' has {len(methods)} methods",
                        )
                    )

        for i, line in enumerate(lines):
            if len(line) > 120:
                smells.append(
                    CodeSmell(
                        file=filepath,
                        line=i + 1,
                        smell_type="long_line",
                        severity="low",
                        description=f"Line {i+1} is {len(line)} characters",
                    )
                )

        self._smells.extend(smells)
        return smells

    @staticmethod
    def _get_function_length(node: ast.FunctionDef) -> int:
        if not node.body:
            return 0
        start = node.body[0].lineno
        end = node.body[-1].end_lineno or node.body[-1].lineno
        return end - start + 1

    def get_summary(self) -> dict:
        by_type = defaultdict(int)
        for s in self._smells:
            by_type[s.smell_type] += 1
        return {"total_smells": len(self._smells), "by_type": dict(by_type)}


class ArchitectureFitnessFunctions:
    """20. Architecture fitness functions."""

    def __init__(self):
        self._rules: list[dict] = []
        self._results: list[dict] = []

    def add_rule(
        self, name: str, check: str, description: str, severity: str = "medium"
    ) -> None:
        self._rules.append(
            {
                "name": name,
                "check": check,
                "description": description,
                "severity": severity,
            }
        )

    def check_no_circular_imports(self, directory: str) -> dict:
        graph = ImportDependencyGraph()
        for root, _, files in os.walk(directory):
            for fn in files:
                if fn.endswith(".py"):
                    graph.analyze_file(os.path.join(root, fn))
        g = graph.get_graph()
        edges = g["edges"]
        cycles = []
        for source in edges:
            for dep in edges[source]:
                if source in edges.get(dep, []):
                    cycles.append([source, dep])
        result = {
            "rule": "no_circular_imports",
            "passed": len(cycles) == 0,
            "violations": len(cycles),
            "details": cycles[:10],
        }
        self._results.append(result)
        return result

    def check_max_function_length(self, filepath: str, max_lines: int = 50) -> dict:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return {"rule": "max_function_length", "passed": False, "error": "syntax error"}

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.body:
                    length = (node.body[-1].end_lineno or node.body[-1].lineno) - node.body[0].lineno + 1
                    if length > max_lines:
                        violations.append({"function": node.name, "lines": length})
        result = {
            "rule": "max_function_length",
            "passed": len(violations) == 0,
            "violations": len(violations),
            "details": violations,
        }
        self._results.append(result)
        return result

    def check_max_file_length(self, filepath: str, max_lines: int = 500) -> dict:
        with open(filepath, encoding="utf-8") as f:
            line_count = sum(1 for _ in f)
        result = {
            "rule": "max_file_length",
            "passed": line_count <= max_lines,
            "actual_lines": line_count,
            "max_lines": max_lines,
        }
        self._results.append(result)
        return result

    def get_all_results(self) -> list[dict]:
        return self._results

    def get_pass_rate(self) -> float:
        if not self._results:
            return 0.0
        passed = sum(1 for r in self._results if r.get("passed", False))
        return passed / len(self._results)
