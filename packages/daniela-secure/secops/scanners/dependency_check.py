#!/usr/bin/env python3
"""
Dependency Audit Scanner for aig Monorepo
Checks Python packages for known vulnerabilities using pip-audit
Output: report with fix versions
"""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Vulnerability:
    package: str
    version: str
    vuln_id: str
    description: str
    severity: str
    cvss_score: float | None
    fixed_versions: list[str]
    references: list[str]


@dataclass
class DependencyReport:
    package: str
    current_version: str
    latest_version: str | None
    vulnerabilities: list[Vulnerability]
    is_direct: bool


class DependencyScanner:
    def __init__(self, repo_root: Path, output_dir: Path):
        self.repo_root = repo_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports: list[DependencyReport] = []

    def find_requirements_files(self) -> list[Path]:
        """Find all requirements files"""
        patterns = [
            "requirements*.txt",
            "requirements/*.txt",
            "Pipfile",
            "Pipfile.lock",
            "pyproject.toml",
            "poetry.lock",
            "setup.py",
            "setup.cfg"
        ]
        files = []
        for pattern in patterns:
            files.extend(self.repo_root.rglob(pattern))
        return [f for f in files if not any(p in f.parts for p in [".git", "__pycache__", ".venv", "venv", "node_modules"])]

    def run_pip_audit(self, requirements_file: Path) -> list[dict]:
        """Run pip-audit on a requirements file"""
        try:
            cmd = ["pip-audit", "-r", str(requirements_file), "--format", "json", "--desc", "on"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode in [0, 1] and result.stdout:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Dependency] pip-audit failed for {requirements_file}: {e}", file=sys.stderr)
        return []

    def run_pip_audit_env(self) -> list[dict]:
        """Run pip-audit on current environment"""
        try:
            cmd = ["pip-audit", "--format", "json", "--desc", "on"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode in [0, 1] and result.stdout:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Dependency] pip-audit env failed: {e}", file=sys.stderr)
        return []

    def get_latest_version(self, package: str) -> str | None:
        """Get latest version from PyPI"""
        try:
            result = subprocess.run(
                ["pip", "index", "versions", package],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.stdout:
                for line in result.stdout.splitlines():
                    if "Available versions:" in line:
                        versions = line.split("Available versions:")[1].strip().split(", ")
                        return versions[0] if versions else None
        except Exception:
            pass
        return None

    def parse_pip_audit_results(self, results: list[dict]) -> list[Vulnerability]:
        """Parse pip-audit JSON output"""
        vulns = []
        for item in results:
            for vuln in item.get("vulns", []):
                vulns.append(Vulnerability(
                    package=item.get("name", ""),
                    version=item.get("version", ""),
                    vuln_id=vuln.get("id", ""),
                    description=vuln.get("description", "")[:500],
                    severity=vuln.get("severity", "unknown").lower(),
                    cvss_score=vuln.get("cvss", {}).get("score") if vuln.get("cvss") else None,
                    fixed_versions=vuln.get("fix_versions", []),
                    references=vuln.get("references", [])
                ))
        return vulns

    def scan(self) -> list[DependencyReport]:
        """Scan all dependencies"""
        print(f"[Dependency Scanner] Scanning repository: {self.repo_root}")

        req_files = self.find_requirements_files()
        print(f"[Dependency] Found {len(req_files)} requirements files")

        all_vulns = []

        for req_file in req_files:
            print(f"[Dependency] Scanning {req_file.relative_to(self.repo_root)}")
            results = self.run_pip_audit(req_file)
            vulns = self.parse_pip_audit_results(results)
            all_vulns.extend(vulns)

        print("[Dependency] Scanning current environment...")
        env_results = self.run_pip_audit_env()
        env_vulns = self.parse_pip_audit_results(env_results)
        all_vulns.extend(env_vulns)

        package_vulns: dict[str, list[Vulnerability]] = {}
        for vuln in all_vulns:
            key = f"{vuln.package}=={vuln.version}"
            if key not in package_vulns:
                package_vulns[key] = []
            package_vulns[key].append(vuln)

        for key, vulns in package_vulns.items():
            package, version = key.split("==", 1)
            latest = self.get_latest_version(package)
            self.reports.append(DependencyReport(
                package=package,
                current_version=version,
                latest_version=latest,
                vulnerabilities=vulns,
                is_direct=True
            ))

        print(f"[Dependency] Total vulnerable packages: {len(self.reports)}")
        return self.reports

    def save_results(self):
        """Save results as JSON"""
        output = {
            "scan_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "repo_root": str(self.repo_root),
                "scanner_version": "1.0.0",
                "total_packages": len(self.reports),
                "total_vulnerabilities": sum(len(r.vulnerabilities) for r in self.reports),
                "by_severity": self._count_by_severity()
            },
            "reports": [asdict(r) for r in self.reports]
        }

        json_file = self.output_dir / "dependency_audit_results.json"
        json_file.write_text(json.dumps(output, indent=2, default=str))
        print(f"[Dependency] Results saved to {json_file}")

    def _count_by_severity(self) -> dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
        for report in self.reports:
            for vuln in report.vulnerabilities:
                counts[vuln.severity] = counts.get(vuln.severity, 0) + 1
        return counts

    def get_exit_code(self) -> int:
        """Exit code based on findings"""
        has_critical = any(
            any(v.severity == "critical" for v in r.vulnerabilities)
            for r in self.reports
        )
        has_high = any(
            any(v.severity == "high" for v in r.vulnerabilities)
            for r in self.reports
        )
        if has_critical:
            return 2
        elif has_high:
            return 1
        return 0


def main():
    parser = argparse.ArgumentParser(description="Dependency Audit Scanner")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output-dir", default="security-reports/dependencies", help="Output directory")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    scanner = DependencyScanner(repo_root, output_dir)
    scanner.scan()
    scanner.save_results()
    sys.exit(scanner.get_exit_code())


if __name__ == "__main__":
    main()
