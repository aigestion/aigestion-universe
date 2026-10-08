#!/usr/bin/env python3
"""
SAST Scanner for aig Monorepo
Static Analysis Security Testing using Bandit and Semgrep
Output: SARIF format for CI integration
"""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SASTFinding:
    rule_id: str
    severity: str
    message: str
    file: str
    line: int
    column: int
    code: str
    cwe: str | None
    owasp: str | None
    confidence: str


class SASTScanner:
    BANDIT_SEVERITY_MAP = {
        "HIGH": "error",
        "MEDIUM": "warning",
        "LOW": "note"
    }

    SEMGREP_RULESETS = [
        "p/security-audit",
        "p/owasp-top-ten",
        "p/secrets",
        "p/python",
        "p/flask",
        "p/django",
        "p/fastapi"
    ]

    def __init__(self, repo_root: Path, output_dir: Path):
        self.repo_root = repo_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.findings: list[SASTFinding] = []

    def _has_command(self, cmd: str) -> bool:
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def run_bandit(self) -> list[SASTFinding]:
        """Run Bandit for Python security issues"""
        findings = []

        if not self._has_command("bandit"):
            print("[SAST] Bandit not installed, skipping", file=sys.stderr)
            return findings

        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.repo_root), "-f", "json", "-ll", "-i"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                data = json.loads(result.stdout)
                for item in data.get("results", []):
                    findings.append(SASTFinding(
                        rule_id=item.get("test_id", ""),
                        severity=self.BANDIT_SEVERITY_MAP.get(item.get("issue_severity", "").upper(), "note"),
                        message=item.get("issue_text", ""),
                        file=item.get("filename", "").replace(str(self.repo_root) + "/", ""),
                        line=item.get("line_number", 0),
                        column=item.get("col_offset", 0),
                        code=item.get("code", "")[:200],
                        cwe=item.get("cwe", {}).get("id") if item.get("cwe") else None,
                        owasp=None,
                        confidence=item.get("issue_confidence", "").lower()
                    ))
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[SAST] Bandit failed: {e}", file=sys.stderr)

        return findings

    def run_semgrep(self) -> list[SASTFinding]:
        """Run Semgrep with security rulesets"""
        findings = []

        if not self._has_command("semgrep"):
            print("[SAST] Semgrep not installed, skipping", file=sys.stderr)
            return findings

        for ruleset in self.SEMGREP_RULESETS:
            try:
                result = subprocess.run(
                    ["semgrep", "--config", ruleset, "--json", "--quiet", str(self.repo_root)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.stdout:
                    data = json.loads(result.stdout)
                    for item in data.get("results", []):
                        severity = "note"
                        if item.get("extra", {}).get("severity") == "ERROR":
                            severity = "error"
                        elif item.get("extra", {}).get("severity") == "WARNING":
                            severity = "warning"

                        findings.append(SASTFinding(
                            rule_id=item.get("check_id", ""),
                            severity=severity,
                            message=item.get("extra", {}).get("message", ""),
                            file=item.get("path", "").replace(str(self.repo_root) + "/", ""),
                            line=item.get("start", {}).get("line", 0),
                            column=item.get("start", {}).get("col", 0),
                            code=item.get("extra", {}).get("lines", "")[:200],
                            cwe=item.get("extra", {}).get("metadata", {}).get("cwe"),
                            owasp=item.get("extra", {}).get("metadata", {}).get("owasp"),
                            confidence="high"
                        ))
            except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
                print(f"[SAST] Semgrep {ruleset} failed: {e}", file=sys.stderr)

        return findings

    def run_custom_rules(self) -> list[SASTFinding]:
        """Run custom aig-specific rules"""
        findings = []

        custom_rules = [
            {
                "id": "AIG-HARDCODED-SECRET",
                "pattern": r"(?i)(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
                "message": "Potential hardcoded secret",
                "severity": "error",
                "cwe": "CWE-798"
            },
            {
                "id": "AIG-SQL-INJECTION",
                "pattern": r"(execute|executemany|raw)\s*\(\s*[f\"]",
                "message": "Potential SQL injection via f-string",
                "severity": "error",
                "cwe": "CWE-89"
            },
            {
                "id": "AIG-PATH-TRAVERSAL",
                "pattern": r"(open|read_file|send_file)\s*\(\s*[^)]*request\.(args|form|files)",
                "message": "Potential path traversal from user input",
                "severity": "error",
                "cwe": "CWE-22"
            },
            {
                "id": "AIG-XSS-RISK",
                "pattern": r"(render_template_string|mark_safe|safe)\s*\(",
                "message": "Potential XSS via unsafe template rendering",
                "severity": "warning",
                "cwe": "CWE-79"
            },
            {
                "id": "AIG-DEBUG-ENABLED",
                "pattern": r"(debug\s*=\s*True|DEBUG\s*=\s*True)",
                "message": "Debug mode enabled in production code",
                "severity": "warning",
                "cwe": "CWE-489"
            }
        ]

        import re
        for file_path in self.repo_root.rglob("*.py"):
            if any(p in file_path.parts for p in [".git", "__pycache__", ".venv", "venv", "node_modules", "test"]):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                for rule in custom_rules:
                    pattern = re.compile(rule["pattern"])
                    for match in pattern.finditer(content):
                        line_num = content[:match.start()].count("\n")
                        findings.append(SASTFinding(
                            rule_id=rule["id"],
                            severity=rule["severity"],
                            message=rule["message"],
                            file=str(file_path.relative_to(self.repo_root)),
                            line=line_num + 1,
                            column=match.start() - content.rfind("\n", 0, match.start()),
                            code=lines[line_num].strip()[:200] if line_num < len(lines) else "",
                            cwe=rule["cwe"],
                            owasp=None,
                            confidence="medium"
                        ))
            except Exception:
                pass

        return findings

    def generate_sarif(self, findings: list[SASTFinding]) -> dict:
        """Generate SARIF output"""
        rules = {}
        for finding in findings:
            if finding.rule_id not in rules:
                rules[finding.rule_id] = {
                    "id": finding.rule_id,
                    "name": finding.rule_id,
                    "shortDescription": {"text": finding.message[:100]},
                    "fullDescription": {"text": finding.message},
                    "defaultConfiguration": {"level": finding.severity},
                    "properties": {
                        "tags": ["security", "sast"],
                        "precision": "high" if finding.confidence == "high" else "medium"
                    }
                }
                if finding.cwe:
                    rules[finding.rule_id]["properties"]["cwe"] = finding.cwe
                if finding.owasp:
                    rules[finding.rule_id]["properties"]["owasp"] = finding.owasp

        results = []
        for finding in findings:
            results.append({
                "ruleId": finding.rule_id,
                "level": finding.severity,
                "message": {"text": finding.message},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.file},
                        "region": {
                            "startLine": finding.line,
                            "startColumn": finding.column
                        }
                    }
                }],
                "properties": {
                    "code": finding.code,
                    "cwe": finding.cwe,
                    "owasp": finding.owasp,
                    "confidence": finding.confidence
                }
            })

        return {
            "version": "2.1.0",
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "aig SAST Scanner",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/aig/security-hardening",
                        "rules": list(rules.values())
                    }
                },
                "results": results,
                "invocations": [{
                    "executionSuccessful": True
                }]
            }]
        }

    def run(self) -> int:
        """Main scan routine"""
        print(f"[SAST Scanner] Scanning repository: {self.repo_root}")

        all_findings = []

        print("[SAST] Running Bandit...")
        bandit_findings = self.run_bandit()
        all_findings.extend(bandit_findings)
        print(f"[SAST] Bandit found {len(bandit_findings)} issues")

        print("[SAST] Running Semgrep...")
        semgrep_findings = self.run_semgrep()
        all_findings.extend(semgrep_findings)
        print(f"[SAST] Semgrep found {len(semgrep_findings)} issues")

        print("[SAST] Running custom rules...")
        custom_findings = self.run_custom_rules()
        all_findings.extend(custom_findings)
        print(f"[SAST] Custom rules found {len(custom_findings)} issues")

        self.findings = all_findings
        self.save_results()

        return self.get_exit_code()

    def save_results(self):
        """Save results as JSON and SARIF"""
        json_output = {
            "scan_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "repo_root": str(self.repo_root),
                "scanner_version": "1.0.0",
                "total_findings": len(self.findings),
                "by_severity": self._count_by_severity()
            },
            "findings": [asdict(f) for f in self.findings]
        }

        json_file = self.output_dir / "sast_results.json"
        json_file.write_text(json.dumps(json_output, indent=2, default=str))
        print(f"[SAST] JSON results saved to {json_file}")

        sarif = self.generate_sarif(self.findings)
        sarif_file = self.output_dir / "sast_results.sarif"
        sarif_file.write_text(json.dumps(sarif, indent=2))
        print(f"[SAST] SARIF results saved to {sarif_file}")

    def _count_by_severity(self) -> dict[str, int]:
        counts = {"error": 0, "warning": 0, "note": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    def get_exit_code(self) -> int:
        """Exit code based on findings"""
        has_error = any(f.severity == "error" for f in self.findings)
        has_warning = any(f.severity == "warning" for f in self.findings)
        if has_error:
            return 2
        elif has_warning:
            return 1
        return 0


def main():
    parser = argparse.ArgumentParser(description="SAST Scanner")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output-dir", default="security-reports/sast", help="Output directory")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    scanner = SASTScanner(repo_root, output_dir)
    sys.exit(scanner.run())


if __name__ == "__main__":
    main()
