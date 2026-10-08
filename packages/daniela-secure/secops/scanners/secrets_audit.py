#!/usr/bin/env python3
"""
Secrets Audit Scanner for aig Monorepo
Scans entire repo for secrets (API keys, passwords, tokens)
Patterns: AWS keys, GitHub tokens, JWT secrets, DB URLs, etc.
Output: findings with file, line, severity
Ignores .gitignore, test files, example configs
"""

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SecretFinding:
    file: str
    line: int
    column: int
    pattern_name: str
    severity: str
    match: str
    context: str
    entropy: float


class SecretsScanner:
    PATTERNS = {
        "aws_access_key": {
            "regex": r"(?i)(aws_access_key_id|aws_access_key)\s*[=:]\s*['\"]?([A-Z0-9]{20})['\"]?",
            "severity": "critical",
            "description": "AWS Access Key ID"
        },
        "aws_secret_key": {
            "regex": r"(?i)(aws_secret_access_key|aws_secret_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
            "severity": "critical",
            "description": "AWS Secret Access Key"
        },
        "aws_session_token": {
            "regex": r"(?i)(aws_session_token)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{100,})['\"]?",
            "severity": "critical",
            "description": "AWS Session Token"
        },
        "github_token": {
            "regex": r"(?i)(github_token|gh_token|ghp_)\s*[=:]\s*['\"]?([A-Za-z0-9_]{35,})['\"]?",
            "severity": "critical",
            "description": "GitHub Personal Access Token"
        },
        "github_app_token": {
            "regex": r"(?i)(ghs_|ghu_|gho_|ghr_)[A-Za-z0-9_]{35,}",
            "severity": "critical",
            "description": "GitHub App Token"
        },
        "jwt_secret": {
            "regex": r"(?i)(jwt_secret|jwt_key|jwt_signing_key)\s*[=:]\s*['\"]?([A-Za-z0-9_\-+=/]{32,})['\"]?",
            "severity": "critical",
            "description": "JWT Signing Secret"
        },
        "database_url": {
            "regex": r"(?i)(database_url|db_url|sqlalchemy_database_uri)\s*[=:]\s*['\"]?([a-zA-Z]+://[^'\s\"`]{10,})['\"]?",
            "severity": "high",
            "description": "Database Connection URL"
        },
        "mongodb_uri": {
            "regex": r"mongodb(?:\+srv)?://[^'\s\"`]{10,}",
            "severity": "high",
            "description": "MongoDB Connection URI"
        },
        "redis_url": {
            "regex": r"redis://[^'\s\"`]{10,}",
            "severity": "high",
            "description": "Redis Connection URL"
        },
        "api_key_generic": {
            "regex": r"(?i)(api_key|apikey|api_secret)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?",
            "severity": "high",
            "description": "Generic API Key"
        },
        "slack_token": {
            "regex": r"xox[baprs]-[A-Za-z0-9-]{10,}",
            "severity": "high",
            "description": "Slack Token"
        },
        "discord_token": {
            "regex": r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}",
            "severity": "critical",
            "description": "Discord Bot Token"
        },
        "stripe_key": {
            "regex": r"(sk|pk)_(live|test)_[A-Za-z0-9]{24,}",
            "severity": "critical",
            "description": "Stripe API Key"
        },
        "sendgrid_key": {
            "regex": r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}",
            "severity": "high",
            "description": "SendGrid API Key"
        },
        "twilio_key": {
            "regex": r"(?i)(twilio_auth_token|twilio_account_sid)\s*[=:]\s*['\"]?([A-Za-z0-9]{32,})['\"]?",
            "severity": "high",
            "description": "Twilio Credentials"
        },
        "google_api_key": {
            "regex": r"AIza[A-Za-z0-9_-]{35}",
            "severity": "high",
            "description": "Google API Key"
        },
        "azure_key": {
            "regex": r"(?i)(azure_key|azure_secret)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40,})['\"]?",
            "severity": "critical",
            "description": "Azure Key/Secret"
        },
        "private_key": {
            "regex": r"-----BEGIN (RSA |EC |DSA |OPENSSH |PRIVATE )?PRIVATE KEY-----",
            "severity": "critical",
            "description": "Private Key"
        },
        "ssh_key": {
            "regex": r"ssh-(rsa|dss|ed25519|ecdsa) [A-Za-z0-9+/]+[=]{0,3}",
            "severity": "high",
            "description": "SSH Public Key"
        },
        "generic_password": {
            "regex": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?([^\s'\"]{8,})['\"]?",
            "severity": "medium",
            "description": "Hardcoded Password"
        },
        "bearer_token": {
            "regex": r"(?i)(bearer|token)\s*[=:]\s*['\"]?([A-Za-z0-9_\-=.]{20,})['\"]?",
            "severity": "medium",
            "description": "Bearer Token"
        },
        "encryption_key": {
            "regex": r"(?i)(encryption_key|encrypt_key|cipher_key)\s*[=:]\s*['\"]?([A-Za-z0-9+/=]{32,})['\"]?",
            "severity": "critical",
            "description": "Encryption Key"
        },
        "webhook_secret": {
            "regex": r"(?i)(webhook_secret|webhook_signing_secret)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{16,})['\"]?",
            "severity": "high",
            "description": "Webhook Secret"
        }
    }

    IGNORE_PATTERNS = [
        "*.example",
        "*.sample",
        "*.template",
        "*.test.*",
        "*_test.py",
        "test_*.py",
        "*.spec.*",
        "conftest.py",
        "pytest.ini",
        ".gitignore",
        ".dockerignore",
        "*.md",
        "*.txt",
        "*.json.example",
        "*.yaml.example",
        "*.yml.example",
        "requirements*.txt",
        "Pipfile*",
        "poetry.lock",
        "yarn.lock",
        "package-lock.json",
        "*.lock",
        ".env.example",
        ".env.sample",
        ".env.template",
        "*.min.js",
        "*.bundle.js",
        "dist/*",
        "build/*",
        "node_modules/*",
        ".git/*",
        "__pycache__/*",
        ".venv/*",
        "venv/*",
        "*.pyc",
        "*.pyo",
        "*.pyd"
    ]

    IGNORE_DIRS = {
        ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
        "dist", "build", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "target", "bin", "obj", ".idea", ".vscode", ".vs", "coverage",
        ".tox", "htmlcov", ".coverage", "*.egg-info"
    }

    def __init__(self, repo_root: Path, output_dir: Path):
        self.repo_root = repo_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.findings: list[SecretFinding] = []
        self.compiled_patterns = {
            name: re.compile(pattern["regex"], re.MULTILINE)
            for name, pattern in self.PATTERNS.items()
        }
        self.gitignore_specs = self._load_gitignore()

    def _load_gitignore(self) -> list[str]:
        """Load .gitignore patterns"""
        specs = []
        gitignore = self.repo_root / ".gitignore"
        if gitignore.exists():
            for line in gitignore.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    specs.append(line)
        return specs

    def _is_ignored(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        rel_path = file_path.relative_to(self.repo_root)

        for part in rel_path.parts:
            if part in self.IGNORE_DIRS:
                return True

        rel_str = str(rel_path)
        for pattern in self.IGNORE_PATTERNS:
            if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True

        for spec in self.gitignore_specs:
            if fnmatch.fnmatch(rel_str, spec) or fnmatch.fnmatch(file_path.name, spec):
                return True

        return False

    def _calculate_entropy(self, string: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not string:
            return 0.0
        import math
        from collections import Counter
        counts = Counter(string)
        length = len(string)
        entropy = -sum((count/length) * math.log2(count/length) for count in counts.values())
        return entropy

    def _get_context(self, content: str, line_num: int, match_start: int, match_end: int, context_lines: int = 2) -> str:
        """Get context around match"""
        lines = content.splitlines()
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        context_lines_list = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            context_lines_list.append(f"{prefix}{i+1:4d}: {lines[i]}")
        return "\n".join(context_lines_list)

    def scan_file(self, file_path: Path) -> list[SecretFinding]:
        """Scan a single file for secrets"""
        findings = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return findings

        content.splitlines()

        for pattern_name, pattern_regex in self.compiled_patterns.items():
            pattern_info = self.PATTERNS[pattern_name]
            for match in pattern_regex.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                col = match.start() - content.rfind("\n", 0, match.start())
                matched_text = match.group(0)

                entropy = self._calculate_entropy(matched_text)

                if entropy < 3.0 and pattern_info["severity"] in ["critical", "high"]:
                    continue

                finding = SecretFinding(
                    file=str(file_path.relative_to(self.repo_root)),
                    line=line_num,
                    column=col,
                    pattern_name=pattern_name,
                    severity=pattern_info["severity"],
                    match=matched_text[:100],
                    context=self._get_context(content, line_num, match.start(), match.end()),
                    entropy=round(entropy, 2)
                )
                findings.append(finding)

        return findings

    def scan(self) -> list[SecretFinding]:
        """Scan entire repository"""
        print(f"[Secrets Scanner] Scanning repository: {self.repo_root}")

        file_count = 0
        for file_path in self.repo_root.rglob("*"):
            if not file_path.is_file():
                continue
            if self._is_ignored(file_path):
                continue

            file_count += 1
            findings = self.scan_file(file_path)
            self.findings.extend(findings)

        print(f"[Secrets Scanner] Scanned {file_count} files, found {len(self.findings)} potential secrets")
        return self.findings

    def save_results(self):
        """Save findings as JSON"""
        output = {
            "scan_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "repo_root": str(self.repo_root),
                "scanner_version": "1.0.0",
                "total_findings": len(self.findings),
                "by_severity": self._count_by_severity()
            },
            "findings": [asdict(f) for f in self.findings]
        }

        json_file = self.output_dir / "secrets_audit_results.json"
        json_file.write_text(json.dumps(output, indent=2, default=str))
        print(f"[Secrets Scanner] Results saved to {json_file}")

    def _count_by_severity(self) -> dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    def get_exit_code(self) -> int:
        """Exit code based on findings"""
        critical = any(f.severity == "critical" for f in self.findings)
        high = any(f.severity == "high" for f in self.findings)
        if critical:
            return 2
        elif high:
            return 1
        return 0


def main():
    parser = argparse.ArgumentParser(description="Secrets Audit Scanner")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output-dir", default="security-reports/secrets", help="Output directory")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    scanner = SecretsScanner(repo_root, output_dir)
    scanner.scan()
    scanner.save_results()
    sys.exit(scanner.get_exit_code())


if __name__ == "__main__":
    main()
