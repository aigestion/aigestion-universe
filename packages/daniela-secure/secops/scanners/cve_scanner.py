#!/usr/bin/env python3
"""
CVE Scanner for aig Monorepo
Scans all Docker images for vulnerabilities using Trivy/Gripe
Outputs: JSON + SARIF for GitHub Security tab
Severity thresholds: critical=block, high=warn
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
    id: str
    severity: str
    package: str
    version: str
    fixed_version: str | None
    description: str
    cvss_score: float | None
    references: list[str]


@dataclass
class ScanResult:
    image: str
    scanner: str
    timestamp: str
    vulnerabilities: list[Vulnerability]
    summary: dict[str, int]


class CVEScanner:
    SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
    BLOCK_THRESHOLD = "critical"
    WARN_THRESHOLD = "high"

    def __init__(self, repo_root: Path, output_dir: Path):
        self.repo_root = repo_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[ScanResult] = []

    def find_dockerfiles(self) -> list[Path]:
        """Find all Dockerfiles in the repo"""
        dockerfiles = list(self.repo_root.rglob("Dockerfile*"))
        dockerfiles += list(self.repo_root.rglob("dockerfile*"))
        return [f for f in dockerfiles if not any(p in f.parts for p in [".git", "__pycache__", ".venv", "node_modules"])]

    def get_image_names(self, dockerfile: Path) -> list[str]:
        """Extract image names from Dockerfile"""
        images = []
        try:
            content = dockerfile.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("FROM "):
                    parts = line.split()
                    if len(parts) >= 2:
                        images.append(parts[1])
        except Exception:
            pass
        return images

    def scan_with_trivy(self, image: str) -> list[Vulnerability]:
        """Scan image using Trivy"""
        vulns = []
        try:
            result = subprocess.run(
                ["trivy", "image", "--format", "json", "--severity", "CRITICAL,HIGH,MEDIUM,LOW", image],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                for target in data.get("Results", []):
                    for vuln in target.get("Vulnerabilities", []):
                        vulns.append(Vulnerability(
                            id=vuln.get("VulnerabilityID", ""),
                            severity=vuln.get("Severity", "unknown").lower(),
                            package=vuln.get("PkgName", ""),
                            version=vuln.get("InstalledVersion", ""),
                            fixed_version=vuln.get("FixedVersion"),
                            description=vuln.get("Description", "")[:500],
                            cvss_score=vuln.get("CVSS", {}).get("nvd", {}).get("V3Score"),
                            references=vuln.get("References", [])
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Trivy scan failed for {image}: {e}", file=sys.stderr)
        return vulns

    def scan_with_grype(self, image: str) -> list[Vulnerability]:
        """Scan image using Grype (Syft)"""
        vulns = []
        try:
            result = subprocess.run(
                ["grype", image, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                for match in data.get("matches", []):
                    vuln = match.get("vulnerability", {})
                    pkg = match.get("artifact", {})
                    vulns.append(Vulnerability(
                        id=vuln.get("id", ""),
                        severity=vuln.get("severity", "unknown").lower(),
                        package=pkg.get("name", ""),
                        version=pkg.get("version", ""),
                        fixed_version=vuln.get("fix", {}).get("versions", [None])[0],
                        description=vuln.get("description", "")[:500],
                        cvss_score=vuln.get("cvss", [{}])[0].get("metrics", {}).get("baseScore"),
                        references=vuln.get("relatedVulnerabilities", [])
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Grype scan failed for {image}: {e}", file=sys.stderr)
        return vulns

    def scan_image(self, image: str) -> ScanResult:
        """Scan a single image with available scanners"""
        all_vulns = []
        scanner_used = "none"

        if self._has_command("trivy"):
            vulns = self.scan_with_trivy(image)
            if vulns:
                all_vulns.extend(vulns)
                scanner_used = "trivy"

        if self._has_command("grype"):
            vulns = self.scan_with_grype(image)
            if vulns:
                all_vulns.extend(vulns)
                scanner_used = "grype" if scanner_used == "none" else f"{scanner_used}+grype"

        if not all_vulns:
            print(f"No scanner available or no vulnerabilities found for {image}", file=sys.stderr)

        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
        for v in all_vulns:
            summary[v.severity] = summary.get(v.severity, 0) + 1

        return ScanResult(
            image=image,
            scanner=scanner_used,
            timestamp=datetime.utcnow().isoformat() + "Z",
            vulnerabilities=all_vulns,
            summary=summary
        )

    def _has_command(self, cmd: str) -> bool:
        try:
            subprocess.run(["which", cmd], capture_output=True)
            return True
        except FileNotFoundError:
            return False

    def generate_sarif(self, results: list[ScanResult]) -> dict:
        """Generate SARIF format for GitHub Security tab"""
        runs = []
        for result in results:
            rules = {}
            for vuln in result.vulnerabilities:
                rule_id = vuln.id
                if rule_id not in rules:
                    rules[rule_id] = {
                        "id": rule_id,
                        "name": f"CVE: {vuln.package}",
                        "shortDescription": {"text": vuln.description[:100]},
                        "fullDescription": {"text": vuln.description},
                        "defaultConfiguration": {"level": self._severity_to_level(vuln.severity)},
                        "properties": {
                            "tags": ["security", "cve", vuln.severity],
                            "precision": "high"
                        }
                    }

            results_list = []
            for vuln in result.vulns:
                results_list.append({
                    "ruleId": vuln.id,
                    "level": self._severity_to_level(vuln.severity),
                    "message": {"text": f"{vuln.package}@{vuln.version}: {vuln.description[:200]}"},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": f"docker://{result.image}"},
                            "region": {"startLine": 1}
                        }
                    }],
                    "properties": {
                        "package": vuln.package,
                        "version": vuln.version,
                        "fixedVersion": vuln.fixed_version,
                        "cvssScore": vuln.cvss_score,
                        "references": vuln.references
                    }
                })

            runs.append({
                "tool": {
                    "driver": {
                        "name": result.scanner,
                        "version": "1.0.0",
                        "informationUri": "https://github.com/aquasecurity/trivy",
                        "rules": list(rules.values())
                    }
                },
                "results": results_list,
                "invocations": [{
                    "executionSuccessful": True,
                    "toolExecutionArguments": result.image
                }]
            })

        return {
            "version": "2.1.0",
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
            "runs": runs
        }

    def _severity_to_level(self, severity: str) -> str:
        mapping = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "unknown": "note"}
        return mapping.get(severity.lower(), "note")

    def run(self) -> int:
        """Main scan routine"""
        print(f"[CVE Scanner] Scanning repository: {self.repo_root}")

        dockerfiles = self.find_dockerfiles()
        print(f"[CVE Scanner] Found {len(dockerfiles)} Dockerfiles")

        images_to_scan = set()
        for df in dockerfiles:
            images_to_scan.update(self.get_image_names(df))

        print(f"[CVE Scanner] Images to scan: {images_to_scan}")

        for image in images_to_scan:
            print(f"[CVE Scanner] Scanning {image}...")
            result = self.scan_image(image)
            self.results.append(result)

            for vuln in result.vulnerabilities:
                print(f"  [{vuln.severity.upper()}] {vuln.id} in {vuln.package}@{vuln.version}")

        self.save_results()
        return self.get_exit_code()

    def save_results(self):
        """Save results as JSON and SARIF"""
        json_output = {
            "scan_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "repo_root": str(self.repo_root),
                "scanner_version": "1.0.0"
            },
            "results": [asdict(r) for r in self.results]
        }

        json_file = self.output_dir / "cve_scan_results.json"
        json_file.write_text(json.dumps(json_output, indent=2, default=str))
        print(f"[CVE Scanner] JSON results saved to {json_file}")

        sarif = self.generate_sarif(self.results)
        sarif_file = self.output_dir / "cve_scan_results.sarif"
        sarif_file.write_text(json.dumps(sarif, indent=2))
        print(f"[CVE Scanner] SARIF results saved to {sarif_file}")

    def get_exit_code(self) -> int:
        """Determine exit code based on severity thresholds"""
        has_critical = any(
            any(v.severity == "critical" for v in r.vulnerabilities)
            for r in self.results
        )
        has_high = any(
            any(v.severity == "high" for v in r.vulnerabilities)
            for r in self.results
        )

        if has_critical:
            print("[CVE Scanner] CRITICAL vulnerabilities found - BLOCKING build", file=sys.stderr)
            return 2
        elif has_high:
            print("[CVE Scanner] HIGH vulnerabilities found - WARNING", file=sys.stderr)
            return 1
        return 0


def main():
    parser = argparse.ArgumentParser(description="CVE Scanner for Docker images")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output-dir", default="security-reports/cve", help="Output directory")
    parser.add_argument("--fail-on", choices=["critical", "high", "medium"], default="critical",
                       help="Fail threshold")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    scanner = CVEScanner(repo_root, output_dir)
    sys.exit(scanner.run())


if __name__ == "__main__":
    main()
