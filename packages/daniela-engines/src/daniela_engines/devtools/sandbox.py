"""Code sandbox tools (21-30)."""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str | None = None
    duration_ms: float = 0
    exit_code: int = 0


@dataclass
class TestResult:
    name: str
    passed: bool
    output: str
    error: str | None = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list
    warnings: list


class PythonCodeExecutor:
    """21. Python code executor (sandboxed)."""

    def __init__(self, timeout: float = 10.0, max_output: int = 10000):
        self._timeout = timeout
        self._max_output = max_output
        self._restricted_builtins = {"exec", "eval", "compile", "__import__"}

    def execute(self, code: str, globals_dict: dict | None = None) -> ExecutionResult:
        start = time.time()
        stdout_capture = []
        stderr_capture = []
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            sys.stdout = type("Capturer", (), {"write": lambda self, x: stdout_capture.append(x), "flush": lambda self: None})()
            sys.stderr = type("Capturer", (), {"write": lambda self, x: stderr_capture.append(x), "flush": lambda self: None})()

            safe_globals = {"__builtins__": {}}
            import builtins
            safe_globals["__builtins__"] = {
                k: v
                for k, v in vars(builtins).items()
                if k not in self._restricted_builtins
            }

            if globals_dict:
                safe_globals.update(globals_dict)

            compiled = compile(code, "<sandbox>", "exec")
            exec(compiled, safe_globals)

            output = "".join(stdout_capture)[: self._max_output]
            duration = (time.time() - start) * 1000
            return ExecutionResult(success=True, output=output, duration_ms=round(duration, 2))

        except Exception as e:
            output = "".join(stdout_capture)[: self._max_output]
            error = "".join(stderr_capture) or str(e)
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                success=False,
                output=output,
                error=error[: self._max_output],
                duration_ms=round(duration, 2),
                exit_code=1,
            )
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def execute_with_capture(self, code: str) -> dict:
        result = self.execute(code)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
        }


class JavaScriptCodeExecutor:
    """22. JavaScript code executor (sandboxed)."""

    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout
        self._node_path = self._find_node()

    @staticmethod
    def _find_node() -> str | None:
        import shutil

        return shutil.which("node")

    def execute(self, code: str) -> ExecutionResult:
        if not self._node_path:
            return ExecutionResult(
                success=False,
                output="",
                error="Node.js not found. Install Node.js to use JS executor.",
                exit_code=1,
            )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            start = time.time()
            proc = subprocess.run(
                [self._node_path, tmp_path],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                success=proc.returncode == 0,
                output=proc.stdout,
                error=proc.stderr if proc.returncode != 0 else None,
                duration_ms=round(duration, 2),
                exit_code=proc.returncode,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False, output="", error="Execution timed out", exit_code=1
            )
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e), exit_code=1)
        finally:
            os.unlink(tmp_path)


class SQLQueryTester:
    """23. SQL query tester - tests queries against in-memory SQLite."""

    def __init__(self):
        self._conn = None
        self._setup_db()

    def _setup_db(self) -> None:
        import sqlite3

        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row

    def execute_schema(self, schema: str) -> ExecutionResult:
        try:
            self._conn.executescript(schema)
            self._conn.commit()
            return ExecutionResult(success=True, output="Schema created successfully")
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def execute_query(self, query: str) -> ExecutionResult:
        start = time.time()
        try:
            cursor = self._conn.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result_data = [dict(row) for row in rows[:100]]
            duration = (time.time() - start) * 1000
            output = json.dumps({"columns": columns, "rows": result_data, "row_count": len(rows)}, indent=2)
            return ExecutionResult(success=True, output=output, duration_ms=round(duration, 2))
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                success=False, output="", error=str(e), duration_ms=round(duration, 2)
            )

    def explain_query(self, query: str) -> ExecutionResult:
        return self.execute_query(f"EXPLAIN QUERY PLAN {query}")

    def close(self) -> None:
        if self._conn:
            self._conn.close()


class APIEndpointTester:
    """24. API endpoint tester."""

    def __init__(self):
        self._results: list[dict] = []

    def test_endpoint(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        body: Any | None = None,
        expected_status: int | None = None,
        timeout: float = 10.0,
    ) -> ExecutionResult:
        try:
            import urllib.error
            import urllib.request

            data = json.dumps(body).encode() if body else None
            req = urllib.request.Request(url, data=data, method=method.upper())
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            if body:
                req.add_header("Content-Type", "application/json")

            start = time.time()
            try:
                resp = urllib.request.urlopen(req, timeout=timeout)
                status = resp.status
                resp_body = resp.read().decode()
                duration = (time.time() - start) * 1000
            except urllib.error.HTTPError as e:
                status = e.code
                resp_body = e.read().decode()
                duration = (time.time() - start) * 1000

            passed = expected_status is None or status == expected_status
            result = {
                "method": method,
                "url": url,
                "status": status,
                "expected_status": expected_status,
                "passed": passed,
                "duration_ms": round(duration, 2),
                "response_preview": resp_body[:500],
            }
            self._results.append(result)
            return ExecutionResult(
                success=passed,
                output=json.dumps(result, indent=2),
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def get_results(self) -> list[dict]:
        return self._results


class WebSocketClientTester:
    """25. WebSocket client tester."""

    def __init__(self):
        self._messages: list[dict] = []

    def test_connection(self, url: str, timeout: float = 5.0) -> ExecutionResult:
        try:
            import websocket

            ws = websocket.create_connection(url, timeout=timeout)
            ws.close()
            return ExecutionResult(success=True, output=f"Connected to {url}")
        except ImportError:
            return ExecutionResult(
                success=False,
                output="",
                error="websocket-client not installed. pip install websocket-client",
            )
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def send_and_receive(
        self, url: str, message: str, timeout: float = 5.0
    ) -> ExecutionResult:
        try:
            import websocket

            ws = websocket.create_connection(url, timeout=timeout)
            ws.send(message)
            response = ws.recv()
            ws.close()
            self._messages.append({"sent": message, "received": response})
            return ExecutionResult(
                success=True,
                output=json.dumps({"sent": message, "received": response}, indent=2),
            )
        except ImportError:
            return ExecutionResult(
                success=False, output="", error="websocket-client not installed"
            )
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def get_messages(self) -> list[dict]:
        return self._messages


class RegexTester:
    """26. Regex tester."""

    def __init__(self):
        self._history: list[dict] = []

    def test(self, pattern: str, test_string: str, flags: list[str] | None = None) -> ExecutionResult:
        flag_map = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE}
        re_flags = 0
        if flags:
            for f in flags:
                re_flags |= flag_map.get(f.lower(), 0)

        try:
            compiled = re.compile(pattern, re_flags)
            matches = list(compiled.finditer(test_string))
            match_data = [
                {
                    "match": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "groups": m.groups(),
                    "groupdict": m.groupdict(),
                }
                for m in matches
            ]
            result = {
                "pattern": pattern,
                "test_string": test_string,
                "match_count": len(matches),
                "matches": match_data,
            }
            self._history.append(result)
            return ExecutionResult(success=True, output=json.dumps(result, indent=2))
        except re.error as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def find_all(self, pattern: str, text: str) -> list[str]:
        try:
            return re.findall(pattern, text)
        except re.error:
            return []

    def split(self, pattern: str, text: str) -> list[str]:
        try:
            return re.split(pattern, text)
        except re.error:
            return []

    def substitute(self, pattern: str, replacement: str, text: str) -> str:
        try:
            return re.sub(pattern, replacement, text)
        except re.error:
            return text

    def get_history(self) -> list[dict]:
        return self._history


class JSONPathTester:
    """27. JSON path tester."""

    def __init__(self):
        self._history: list[dict] = []

    def query(self, json_data: Any, path: str) -> ExecutionResult:
        try:
            if isinstance(json_data, str):
                json_data = json.loads(json_data)

            result = self._navigate(json_data, path)
            output = json.dumps({"path": path, "result": result}, indent=2, default=str)
            self._history.append({"path": path, "result_count": len(result) if isinstance(result, list) else 1})
            return ExecutionResult(success=True, output=output)
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))

    @staticmethod
    def _navigate(data: Any, path: str) -> Any:
        parts = [p for p in re.split(r"\.(?!\.)", path) if p]
        current = data
        for part in parts:
            if part == "$":
                continue
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                if part.isdigit():
                    current = current[int(part)]
                elif part == "*":
                    current = current
                else:
                    current = [item.get(part) if isinstance(item, dict) else None for item in current]
            else:
                return None
        return current

    def get_schema(self, json_data: Any) -> dict:
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        return self._infer_schema(json_data)

    @staticmethod
    def _infer_schema(data: Any) -> dict:
        if isinstance(data, dict):
            return {k: JSONPathTester._infer_schema(v) for k, v in data.items()}
        elif isinstance(data, list):
            if data:
                return {"_array_of": JSONPathTester._infer_schema(data[0])}
            return {"_array_of": "unknown"}
        else:
            return {"_type": type(data).__name__}

    def get_history(self) -> list[dict]:
        return self._history


class CronExpressionTester:
    """28. Cron expression tester."""

    def __init__(self):
        self._history: list[dict] = []

    def parse(self, expression: str) -> ExecutionResult:
        parts = expression.strip().split()
        if len(parts) != 5:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Expected 5 fields, got {len(parts)}. Format: minute hour day month weekday",
            )

        field_names = ["minute", "hour", "day", "month", "weekday"]
        parsed = {}
        errors = []

        for _i, (name, part) in enumerate(zip(field_names, parts)):
            result = self._parse_field(name, part)
            if "error" in result:
                errors.append(f"{name}: {result['error']}")
            else:
                parsed[name] = result.get("values", [])

        if errors:
            return ExecutionResult(success=False, output="", error="; ".join(errors))

        next_runs = self._calculate_next_runs(parsed, count=5)
        output = json.dumps(
            {"expression": expression, "parsed": parsed, "next_runs": next_runs},
            indent=2,
        )
        self._history.append({"expression": expression, "valid": True})
        return ExecutionResult(success=True, output=output)

    @staticmethod
    def _parse_field(name: str, value: str) -> dict:
        ranges = {
            "minute": (0, 59),
            "hour": (0, 23),
            "day": (1, 31),
            "month": (1, 12),
            "weekday": (0, 7),
        }
        low, high = ranges[name]

        if value == "*":
            return {"values": list(range(low, high + 1))}

        values = set()
        for part in value.split(","):
            if "/" in part:
                base, step = part.split("/", 1)
                step = int(step)
                if base == "*":
                    values.update(range(low, high + 1, step))
                else:
                    start = int(base)
                    values.update(range(start, high + 1, step))
            elif "-" in part:
                start, end = part.split("-", 1)
                values.update(range(int(start), int(end) + 1))
            else:
                values.add(int(part))

        return {"values": sorted(v for v in values if low <= v <= high)}

    @staticmethod
    def _calculate_next_runs(parsed: dict, count: int = 5) -> list[str]:
        import datetime

        runs = []
        now = datetime.datetime.now()
        candidate = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
        attempts = 0
        while len(runs) < count and attempts < 10000:
            if (
                candidate.minute in parsed.get("minute", [candidate.minute])
                and candidate.hour in parsed.get("hour", [candidate.hour])
                and candidate.day in parsed.get("day", [candidate.day])
                and candidate.month in parsed.get("month", [candidate.month])
                and candidate.weekday() in parsed.get("weekday", [candidate.weekday()])
            ):
                runs.append(candidate.strftime("%Y-%m-%d %H:%M"))
            candidate += datetime.timedelta(minutes=1)
            attempts += 1
        return runs

    def describe(self, expression: str) -> ExecutionResult:
        parts = expression.strip().split()
        field_names = ["minute", "hour", "day", "month", "weekday"]
        descriptions = []
        for name, part in zip(field_names, parts):
            if part == "*":
                descriptions.append(f"{name}: every {name}")
            elif "/" in part:
                descriptions.append(f"{name}: every {part.split('/')[1]} {name}s")
            elif "-" in part:
                descriptions.append(f"{name}: from {part}")
            elif "," in part:
                descriptions.append(f"{name}: at {part}")
            else:
                descriptions.append(f"{name}: at {part}")
        return ExecutionResult(success=True, output="\n".join(descriptions))

    def get_history(self) -> list[dict]:
        return self._history


class DockerComposeValidator:
    """29. Docker compose validator."""

    def __init__(self):
        self._required_fields = ["version", "services"]
        self._valid_versions = ["2", "2.0", "2.1", "2.2", "2.3", "2.4", "3", "3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"]

    def validate(self, content: str) -> ValidationResult:
        errors = []
        warnings = []

        try:
            _yaml = sys.modules.get("yaml")
            data = _yaml.safe_load(content) if _yaml else json.loads(content)
        except Exception as e:
            return ValidationResult(valid=False, errors=[f"Parse error: {e}"], warnings=[])

        if not isinstance(data, dict):
            return ValidationResult(valid=False, errors=["Root must be a mapping"], warnings=[])

        for field in self._required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "services" in data and isinstance(data["services"], dict):
            for svc_name, svc_config in data["services"].items():
                if not isinstance(svc_config, dict):
                    errors.append(f"Service '{svc_name}' must be a mapping")
                    continue
                if "image" not in svc_config and "build" not in svc_config:
                    warnings.append(f"Service '{svc_name}' has neither 'image' nor 'build'")
                if "ports" in svc_config:
                    for port in svc_config["ports"]:
                        if isinstance(port, str) and ":" in port:
                            host_port = port.split(":")[0]
                            if host_port.isdigit() and int(host_port) > 65535:
                                errors.append(f"Invalid host port: {host_port}")

        if "version" in data and str(data["version"]) not in self._valid_versions:
            warnings.append(f"Unusual version: {data.get('version')}")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_file(self, filepath: str) -> ValidationResult:
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            return self.validate(content)
        except Exception as e:
            return ValidationResult(valid=False, errors=[f"File error: {e}"], warnings=[])


class YAMLJSONValidator:
    """30. YAML/JSON validator."""

    def __init__(self):
        self._history: list[dict] = []

    def validate_json(self, content: str) -> ValidationResult:
        errors = []
        warnings = []
        try:
            data = json.loads(content)
            if isinstance(data, dict) and len(data) == 0:
                warnings.append("Empty JSON object")
            elif isinstance(data, list) and len(data) == 0:
                warnings.append("Empty JSON array")
        except json.JSONDecodeError as e:
            errors.append(f"JSON error at line {e.lineno}, col {e.colno}: {e.msg}")

        result = ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
        self._history.append({"type": "json", "valid": result.valid})
        return result

    def validate_yaml(self, content: str) -> ValidationResult:
        errors = []
        warnings = []
        try:
            import yaml

            data = yaml.safe_load(content)
            if data is None:
                warnings.append("Empty YAML document")
        except ImportError:
            return ValidationResult(
                valid=False,
                errors=["PyYAML not installed. pip install pyyaml"],
                warnings=[],
            )
        except yaml.YAMLError as e:
            errors.append(f"YAML error: {e}")

        result = ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
        self._history.append({"type": "yaml", "valid": result.valid})
        return result

    def detect_format(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith(("{", "[")):
            return "json"
        elif stripped.startswith("---") or ":" in stripped:
            return "yaml"
        return "unknown"

    def auto_validate(self, content: str) -> ValidationResult:
        fmt = self.detect_format(content)
        if fmt == "json":
            return self.validate_json(content)
        elif fmt == "yaml":
            return self.validate_yaml(content)
        return ValidationResult(valid=False, errors=["Unknown format"], warnings=[])

    def format_json(self, content: str, indent: int = 2) -> ExecutionResult:
        try:
            data = json.loads(content)
            formatted = json.dumps(data, indent=indent, ensure_ascii=False)
            return ExecutionResult(success=True, output=formatted)
        except json.JSONDecodeError as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def minify_json(self, content: str) -> ExecutionResult:
        try:
            data = json.loads(content)
            minified = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
            return ExecutionResult(success=True, output=minified)
        except json.JSONDecodeError as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def get_history(self) -> list[dict]:
        return self._history
