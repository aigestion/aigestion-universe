#!/usr/bin/env python3
"""
WAF Rules for aig Monorepo
ModSecurity compatible rules with OWASP CRS subset
Custom rules for aig endpoints
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuleAction(Enum):
    DENY = "deny"
    BLOCK = "block"
    LOG = "log"
    ALLOW = "allow"
    REDIRECT = "redirect"


class RuleSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class WAFRule:
    id: str
    name: str
    description: str
    severity: RuleSeverity
    action: RuleAction
    pattern: str
    pattern_type: str  # regex, substring, exact
    variables: list[str]  # ARGS, ARGS_NAMES, REQUEST_HEADERS, REQUEST_BODY, etc.
    tags: list[str] = field(default_factory=list)
    message: str = ""
    phase: int = 2
    skip_after: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class WAFRuleSet:
    """Collection of WAF rules for aig"""

    def __init__(self):
        self.rules: list[WAFRule] = []
        self._load_core_rules()
        self._load_owasp_crs_rules()
        self._load_aig_rules()
        self._load_rate_limit_rules()
        self._load_geo_rules()

    def _load_core_rules(self):
        """Core protection rules"""
        self.rules.extend([
            # Request validation
            WAFRule(
                id="AIG-000001",
                name="Invalid HTTP Method",
                description="Block non-standard HTTP methods",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.DENY,
                pattern=r"^(?!GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|TRACE)$",
                pattern_type="regex",
                variables=["REQUEST_METHOD"],
                tags=["protocol", "method"],
                message="Invalid HTTP method used"
            ),

            # Null byte injection
            WAFRule(
                id="AIG-000002",
                name="Null Byte Injection",
                description="Detect null bytes in input",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"%00|\x00",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_HEADERS", "REQUEST_BODY"],
                tags=["injection", "null-byte"],
                message="Null byte injection attempt"
            ),

            # Path traversal
            WAFRule(
                id="AIG-000003",
                name="Path Traversal",
                description="Detect directory traversal attempts",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(\.\./|\.\.\\){2,}",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_URI", "REQUEST_BODY"],
                tags=["path-traversal", "lfi"],
                message="Path traversal attempt detected"
            ),

            WAFRule(
                id="AIG-000004",
                name="Path Traversal Encoded",
                description="Detect encoded directory traversal",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(%2e%2e%2f|%2e%2e%5c|..%2f|..%5c|%252e%252e%252f)",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_URI", "REQUEST_BODY"],
                tags=["path-traversal", "encoded"],
                message="Encoded path traversal attempt"
            ),

            # Command injection
            WAFRule(
                id="AIG-000005",
                name="Command Injection",
                description="Detect command injection attempts",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                pattern=r"(;|\||&|\$\(|\`|\|\||&&)\s*(cat|ls|id|whoami|uname|pwd|ps|netstat|ifconfig|wget|curl|nc|bash|sh|python|perl|ruby|php)",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["injection", "rce", "command"],
                message="Command injection attempt detected"
            ),

            # LDAP injection
            WAFRule(
                id="AIG-000006",
                name="LDAP Injection",
                description="Detect LDAP injection attempts",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"[\(\)\*\&\|!]=|\(\||\&\)",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["injection", "ldap"],
                message="LDAP injection attempt detected"
            ),

            # XXE
            WAFRule(
                id="AIG-000007",
                name="XXE Attack",
                description="Detect XML External Entity attacks",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                pattern=r"<!ENTITY|<!DOCTYPE|SYSTEM\s+[\"']file:|PUBLIC\s+\"",
                pattern_type="regex",
                variables=["REQUEST_BODY", "REQUEST_HEADERS:Content-Type"],
                tags=["xxe", "xml"],
                message="XXE attack attempt detected"
            ),
        ])

    def _load_owasp_crs_rules(self):
        """OWASP Core Rule Set subset - most critical rules"""
        self.rules.extend([
            # SQL Injection - Generic
            WAFRule(
                id="AIG-010001",
                name="SQL Injection - Generic",
                description="Generic SQL injection detection",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                pattern=r"(?i)(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b.+\b(from|into|table|where|set|values)\b)",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["sqli", "owasp-crs", "injection"],
                message="SQL injection attempt detected"
            ),

            # SQL Injection - Union
            WAFRule(
                id="AIG-010002",
                name="SQL Injection - Union",
                description="UNION-based SQL injection",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                pattern=r"(?i)(\bunion\b.*\bselect\b|\bselect\b.*\bunion\b)",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["sqli", "union", "owasp-crs"],
                message="UNION SQL injection attempt"
            ),

            # SQL Injection - Error-based
            WAFRule(
                id="AIG-010003",
                name="SQL Injection - Error-based",
                description="Error-based SQL injection",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(?i)(convert\(|cast\(|extractvalue\(|updatexml\(|benchmark\(|sleep\()",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["sqli", "error-based", "owasp-crs"],
                message="Error-based SQL injection attempt"
            ),

            # SQL Injection - Time-based
            WAFRule(
                id="AIG-010004",
                name="SQL Injection - Time-based",
                description="Time-based blind SQL injection",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(?i)(waitfor\s+delay|pg_sleep\(|sleep\(|benchmark\()",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["sqli", "time-based", "blind", "owasp-crs"],
                message="Time-based SQL injection attempt"
            ),

            # XSS - Script tag
            WAFRule(
                id="AIG-020001",
                name="XSS - Script Tag",
                description="Cross-site scripting via script tags",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(?i)<script[^>]*>.*?</script>|<script[^>]*>",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["xss", "owasp-crs", "script"],
                message="XSS attempt via script tag"
            ),

            # XSS - Event handlers
            WAFRule(
                id="AIG-020002",
                name="XSS - Event Handlers",
                description="XSS via HTML event handlers",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(?i)\s(on\w+\s*=\s*[\"'][^\"']*[\"'])",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["xss", "owasp-crs", "event-handler"],
                message="XSS attempt via event handler"
            ),

            # XSS - JavaScript protocol
            WAFRule(
                id="AIG-020003",
                name="XSS - JavaScript Protocol",
                description="XSS via javascript: protocol",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(?i)javascript\s*:",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY", "REQUEST_HEADERS:Referer"],
                tags=["xss", "owasp-crs", "javascript-protocol"],
                message="XSS attempt via javascript: protocol"
            ),

            # XSS - Data URI
            WAFRule(
                id="AIG-020004",
                name="XSS - Data URI",
                description="XSS via data: URI",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.BLOCK,
                pattern=r"(?i)data\s*:\s*text/html",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["xss", "data-uri", "owasp-crs"],
                message="XSS attempt via data URI"
            ),

            # RFI/LFI
            WAFRule(
                id="AIG-030001",
                name="Remote File Inclusion",
                description="Remote file inclusion attempt",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                pattern=r"(?i)(https?|ftp|php)\s*://",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_BODY"],
                tags=["rfi", "lfi", "file-inclusion", "owasp-crs"],
                message="Remote file inclusion attempt"
            ),

            # Session fixation
            WAFRule(
                id="AIG-040001",
                name="Session Fixation",
                description="Session fixation attempt",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.BLOCK,
                pattern=r"(?i)(sessionid|phpsessid|jsessionid|aspsessionid)\s*=",
                pattern_type="regex",
                variables=["REQUEST_HEADERS:Cookie", "ARGS"],
                tags=["session", "fixation", "owasp-crs"],
                message="Session fixation attempt"
            ),

            # HTTP Header injection
            WAFRule(
                id="AIG-050001",
                name="HTTP Header Injection",
                description="HTTP response splitting / header injection",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"[\r\n]\s*[A-Za-z-]+:",
                pattern_type="regex",
                variables=["ARGS", "ARGS_NAMES", "REQUEST_HEADERS"],
                tags=["header-injection", "response-splitting", "owasp-crs"],
                message="HTTP header injection attempt"
            ),
        ])

    def _load_aig_rules(self):
        """Custom rules for aig-specific endpoints"""
        self.rules.extend([
            # API endpoint protection
            WAFRule(
                id="AIG-100001",
                name="aig - Admin Endpoint Protection",
                description="Strict validation for admin endpoints",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                pattern=r"^/api/(admin|v1/admin)",
                pattern_type="regex",
                variables=["REQUEST_URI"],
                tags=["aig", "admin", "api"],
                message="Admin endpoint access blocked - unauthorized"
            ),

            # Mass assignment protection
            WAFRule(
                id="AIG-100002",
                name="aig - Mass Assignment Protection",
                description="Block mass assignment of sensitive fields",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"(is_admin|is_superuser|role|credit_limit|account_type|deleted_at|private_key|secret|password_hash)",
                pattern_type="regex",
                variables=["ARGS", "REQUEST_BODY"],
                tags=["aig", "mass-assignment", "api"],
                message="Mass assignment of protected field attempted"
            ),

            # File upload validation
            WAFRule(
                id="AIG-100003",
                name="aig - File Upload Validation",
                description="Validate file uploads",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"\.(php|phtml|php3|php4|php5|php7|phps|jsp|asp|aspx|exe|bat|cmd|sh|pl|cgi)$",
                pattern_type="regex",
                variables=["FILES_NAMES", "ARGS:filename"],
                tags=["aig", "file-upload", "malware"],
                message="Dangerous file extension uploaded"
            ),

            # API version protection
            WAFRule(
                id="AIG-100004",
                name="aig - Deprecated API Version",
                description="Block deprecated API versions",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.DENY,
                pattern=r"^/api/v0/",
                pattern_type="regex",
                variables=["REQUEST_URI"],
                tags=["aig", "api-version", "deprecated"],
                message="Deprecated API version accessed"
            ),

            # GraphQL depth limiting
            WAFRule(
                id="AIG-100005",
                name="aig - GraphQL Query Depth",
                description="Limit GraphQL query depth",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.BLOCK,
                pattern=r"(\{.*\{.*\{.*\{.*\{",
                pattern_type="regex",
                variables=["REQUEST_BODY"],
                tags=["aig", "graphql", "dos"],
                message="GraphQL query depth exceeded"
            ),

            # Webhook signature validation
            WAFRule(
                id="AIG-100006",
                name="aig - Webhook Signature Required",
                description="Require signature for webhook endpoints",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                pattern=r"^/api/webhook",
                pattern_type="regex",
                variables=["REQUEST_URI", "REQUEST_HEADERS:X-Signature"],
                tags=["aig", "webhook", "signature"],
                message="Webhook signature missing or invalid"
            ),

            # Rate limit sensitive endpoints
            WAFRule(
                id="AIG-100007",
                name="aig - Auth Endpoint Rate Limit",
                description="Strict rate limiting on auth endpoints",
                severity=RuleSeverity.HIGH,
                action=RuleAction.LOG,
                pattern=r"^/api/(auth|v1/auth)/(login|register|password|reset)",
                pattern_type="regex",
                variables=["REQUEST_URI", "REMOTE_ADDR"],
                tags=["aig", "rate-limit", "auth", "brute-force"],
                message="Auth endpoint rate limit check"
            ),
        ])

    def _load_rate_limit_rules(self):
        """Rate limiting rules"""
        self.rules.extend([
            WAFRule(
                id="AIG-200001",
                name="Rate Limit - Login",
                description="Rate limit login attempts",
                severity=RuleSeverity.HIGH,
                action=RuleAction.LOG,
                pattern=r"^/api/auth/login$",
                pattern_type="regex",
                variables=["REQUEST_URI", "REMOTE_ADDR"],
                tags=["rate-limit", "login", "brute-force"],
                message="Login rate limit",
                metadata={"limit": 5, "window": 300, "burst": 10}
            ),

            WAFRule(
                id="AIG-200002",
                name="Rate Limit - API Global",
                description="Global API rate limit",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.LOG,
                pattern=r"^/api/",
                pattern_type="regex",
                variables=["REQUEST_URI", "REMOTE_ADDR"],
                tags=["rate-limit", "api", "global"],
                message="Global API rate limit",
                metadata={"limit": 100, "window": 60, "burst": 200}
            ),

            WAFRule(
                id="AIG-200003",
                name="Rate Limit - File Upload",
                description="Strict rate limit on file uploads",
                severity=RuleSeverity.HIGH,
                action=RuleAction.LOG,
                pattern=r"^/api/(upload|files)",
                pattern_type="regex",
                variables=["REQUEST_URI", "REMOTE_ADDR"],
                tags=["rate-limit", "upload", "dos"],
                message="File upload rate limit",
                metadata={"limit": 10, "window": 3600, "burst": 20}
            ),

            WAFRule(
                id="AIG-200004",
                name="Rate Limit - Search",
                description="Rate limit search endpoints",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.LOG,
                pattern=r"^/api/search",
                pattern_type="regex",
                variables=["REQUEST_URI", "REMOTE_ADDR"],
                tags=["rate-limit", "search", "dos"],
                message="Search rate limit",
                metadata={"limit": 30, "window": 60, "burst": 50}
            ),
        ])

    def _load_geo_rules(self):
        """Geo-blocking rules (optional)"""
        self.rules.extend([
            WAFRule(
                id="AIG-300001",
                name="Geo Block - High Risk Countries",
                description="Block high-risk countries (configurable)",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.DENY,
                pattern=r"^(CN|KP|IR|SY|RU|BY)$",
                pattern_type="regex",
                variables=["GEOIP_COUNTRY_CODE"],
                tags=["geoip", "block", "high-risk"],
                message="Access denied from high-risk country",
                metadata={"enabled": False, "description": "Enable by setting enabled=true in metadata"}
            ),

            WAFRule(
                id="AIG-300002",
                name="Geo Block - Tor Exit Nodes",
                description="Block known Tor exit nodes",
                severity=RuleSeverity.HIGH,
                action=RuleAction.DENY,
                pattern=r"^1$",
                pattern_type="exact",
                variables=["GEOIP_IS_TOR"],
                tags=["geoip", "tor", "anonymity"],
                message="Access denied from Tor exit node",
                metadata={"enabled": False}
            ),

            WAFRule(
                id="AIG-300003",
                name="Geo Block - VPN/Proxy",
                description="Block known VPN/Proxy IPs",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.LOG,
                pattern=r"^1$",
                pattern_type="exact",
                variables=["GEOIP_IS_VPN", "GEOIP_IS_PROXY"],
                tags=["geoip", "vpn", "proxy"],
                message="VPN/Proxy detected",
                metadata={"enabled": False}
            ),
        ])

    def get_rules(self, tags: list[str] = None, min_severity: RuleSeverity = None) -> list[WAFRule]:
        """Filter rules by tags and severity"""
        filtered = self.rules

        if tags:
            filtered = [r for r in filtered if any(t in r.tags for t in tags)]

        if min_severity:
            severity_order = {s: i for i, s in enumerate(RuleSeverity)}
            filtered = [r for r in filtered if severity_order[r.severity] >= severity_order[min_severity]]

        return filtered

    def to_modsecurity(self) -> str:
        """Export rules in ModSecurity format"""
        output = []

        for rule in self.rules:
            if rule.metadata.get("enabled") is False:
                continue

            vars_str = "|".join(rule.variables)

            rule_str = f'SecRule {vars_str} "{rule.pattern}" \\\n'
            rule_str += f'    "id:{rule.id},phase:{rule.phase},block,msg:\'{rule.message}\',tag:\'{",".join(rule.tags)}\',severity:\'{rule.severity.value.upper()}\'"'

            output.append(rule_str)

        return "\n\n".join(output)

    def to_nginx_lua(self) -> str:
        """Export rules as OpenResty/NGINX Lua"""
        output = ['-- aig WAF Rules', '-- Auto-generated - do not edit manually', '']

        for rule in self.rules:
            if rule.metadata.get("enabled") is False:
                continue

            output.append(f'-- Rule {rule.id}: {rule.name}')
            output.append(f'-- {rule.description}')
            output.append(f'local rule_{rule.id} = {{')
            output.append(f'    pattern = [[{rule.pattern}]],')
            output.append(f'    pattern_type = "{rule.pattern_type}",')
            output.append(f'    variables = {rule.variables},')
            output.append(f'    action = "{rule.action.value}",')
            output.append(f'    severity = "{rule.severity.value}",')
            output.append(f'    message = "{rule.message}",')
            output.append(f'    tags = {rule.tags}')
            output.append('}')
            output.append('')

        output.append('return {')
        for rule in self.rules:
            if rule.metadata.get("enabled") is not False:
                output.append(f'    rule_{rule.id},')
        output.append('}')

        return "\n".join(output)

    def to_json(self) -> list[dict]:
        """Export rules as JSON"""
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "severity": r.severity.value,
                "action": r.action.value,
                "pattern": r.pattern,
                "pattern_type": r.pattern_type,
                "variables": r.variables,
                "tags": r.tags,
                "message": r.message,
                "phase": r.phase,
                "metadata": r.metadata
            }
            for r in self.rules
        ]


# Pre-configured rule sets
def get_production_ruleset() -> WAFRuleSet:
    """Get production-ready rule set"""
    rs = WAFRuleSet()
    # Disable geo rules by default
    for rule in rs.rules:
        if rule.id.startswith("AIG-300"):
            rule.metadata["enabled"] = False
    return rs


def get_development_ruleset() -> WAFRuleSet:
    """Get development rule set (log only)"""
    rs = WAFRuleSet()
    for rule in rs.rules:
        if rule.action in [RuleAction.BLOCK, RuleAction.DENY]:
            rule.action = RuleAction.LOG
    return rs


def get_strict_ruleset() -> WAFRuleSet:
    """Get strict rule set (block more aggressively)"""
    rs = WAFRuleSet()
    for rule in rs.rules:
        if rule.severity in [RuleSeverity.HIGH, RuleSeverity.CRITICAL]:
            rule.action = RuleAction.BLOCK
    return rs


if __name__ == "__main__":
    # Demo
    rs = get_production_ruleset()
    print(f"Total rules: {len(rs.rules)}")
    print(f"Critical: {len(rs.get_rules(min_severity=RuleSeverity.CRITICAL))}")
    print(f"High: {len(rs.get_rules(min_severity=RuleSeverity.HIGH))}")

    # Export examples
    print("\n--- ModSecurity Format ---")
    print(rs.to_modsecurity()[:2000] + "...")

    print("\n--- JSON Format ---")
    import json
    print(json.dumps(rs.to_json()[:3], indent=2))
