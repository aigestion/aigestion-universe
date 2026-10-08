"""
Automation Engine - Ideas 41-50
================================

41. Auto-categorization of tickets
42. Smart email routing
43. Meeting scheduling AI
44. Code review assistant
45. Documentation generator
46. Test case generator from code
47. Commit message auto-generator
48. Bug triage automation
49. Performance bottleneck detector
50. Architecture advisor (code -> suggestions)
"""

import hashlib
import re


class AutomationEngine:
    """Core automation engine with 10 powerful AI-driven automation capabilities."""

    TICKET_CATEGORIES = {
        "bug": {"keywords": {"error", "crash", "broken", "fail", "exception", "bug", "defect", "issue", "wrong", "not working"}},
        "feature": {"keywords": {"feature", "request", "add", "new", "enhancement", "improve", "implement", "create", "support"}},
        "question": {"keywords": {"how", "what", "why", "where", "when", "help", "explain", "question", "can you", "is it possible"}},
        "security": {"keywords": {"security", "vulnerability", "hack", "breach", "auth", "permission", "access", "encrypt", "token"}},
        "performance": {"keywords": {"slow", "latency", "timeout", "memory", "cpu", "performance", "optimize", "cache", "bottleneck"}},
        "docs": {"keywords": {"documentation", "readme", "docs", "guide", "tutorial", "example", "wiki", "api docs"}},
    }

    DEPARTMENT_MAP = {
        "bug": "engineering",
        "feature": "product",
        "question": "support",
        "security": "security",
        "performance": "engineering",
        "docs": "documentation",
    }

    PRIORITY_KEYWORDS = {
        "critical": {"production", "down", "outage", "critical", "urgent", "blocking", "p0"},
        "high": {"important", "high", "asap", "priority", "p1"},
        "medium": {"medium", "normal", "p2"},
        "low": {"low", "nice-to-have", "cosmetic", "p3"},
    }

    REVIEW_RULES = [
        {"pattern": r'except\s*:', "message": "Bare except clause - use specific exception types", "severity": "warning"},
        {"pattern": r'eval\(', "message": "Use of eval() detected - potential security risk", "severity": "error"},
        {"pattern": r'exec\(', "message": "Use of exec() detected - potential security risk", "severity": "error"},
        {"pattern": r'password\s*=\s*["\'][^"\']+["\']', "message": "Hardcoded password detected", "severity": "error"},
        {"pattern": r'TODO|FIXME|HACK|XXX', "message": "TODO/FIXME comment found", "severity": "info"},
        {"pattern": r'print\(', "message": "Print statement found - consider using logging", "severity": "info"},
        {"pattern": r'def\s+\w+\(.*\)\s*->\s*None:', "message": "Function returns None explicitly", "severity": "info"},
        {"pattern": r'import\s+\*', "message": "Wildcard import detected", "severity": "warning"},
    ]

    COMMIT_TYPES = ["feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "ci", "build"]

    BUG_TRIAGE_RULES = {
        "crash": {"assignee": "platform-team", "priority": "critical"},
        "ui": {"assignee": "frontend-team", "priority": "high"},
        "api": {"assignee": "backend-team", "priority": "high"},
        "database": {"assignee": "data-team", "priority": "high"},
        "security": {"assignee": "security-team", "priority": "critical"},
        "performance": {"assignee": "performance-team", "priority": "medium"},
        "documentation": {"assignee": "docs-team", "priority": "low"},
    }

    def __init__(self):
        self.ticket_history: list[dict] = []
        self.review_history: list[dict] = []

    # ── Idea 41: Auto-Categorization of Tickets ─────────────────────
    def categorize_ticket(self, title: str, description: str = "") -> dict:
        """Auto-categorize support tickets using keyword analysis."""
        text = f"{title} {description}".lower()
        words = set(re.findall(r'\w+', text))
        scores = {}
        for category, config in self.TICKET_CATEGORIES.items():
            matches = words & config["keywords"]
            scores[category] = len(matches)
        best_category = max(scores, key=scores.get) if any(scores.values()) else "question"
        confidence = scores[best_category] / max(sum(scores.values()), 1)
        priority = "medium"
        for p_level, p_keywords in self.PRIORITY_KEYWORDS.items():
            if words & p_keywords:
                priority = p_level
                break
        department = self.DEPARTMENT_MAP.get(best_category, "general")
        ticket = {
            "title": title[:100],
            "category": best_category,
            "priority": priority,
            "department": department,
            "confidence": round(confidence, 3),
            "matched_keywords": list(words & self.TICKET_CATEGORIES[best_category]["keywords"]),
        }
        self.ticket_history.append(ticket)
        return ticket

    # ── Idea 42: Smart Email Routing ────────────────────────────────
    def route_email(self, subject: str, body: str, sender: str = "") -> dict:
        """Route emails to appropriate teams/departments."""
        text = f"{subject} {body}".lower()
        routing_rules = {
            "sales": {"keywords": {"buy", "purchase", "pricing", "quote", "demo", "trial", "enterprise", "plan"}},
            "support": {"keywords": {"help", "issue", "problem", "error", "not working", "bug", "broken"}},
            "engineering": {"keywords": {"deploy", "release", "build", "ci", "pipeline", "infrastructure", "server"}},
            "hr": {"keywords": {"vacation", "sick", "leave", "onboarding", "benefits", "payroll", "hire"}},
            "legal": {"keywords": {"contract", "nda", "compliance", "gdpr", "privacy", "terms", "license"}},
        }
        scores = {}
        for dept, config in routing_rules.items():
            words = set(re.findall(r'\w+', text))
            scores[dept] = len(words & config["keywords"])
        best_dept = max(scores, key=scores.get) if any(scores.values()) else "general"
        urgency = "high" if any(w in text for w in {"urgent", "asap", "critical", "emergency"}) else "normal"
        return {
            "routed_to": best_dept,
            "urgency": urgency,
            "scores": scores,
            "sender": sender,
            "subject": subject[:100],
        }

    # ── Idea 43: Meeting Scheduling AI ──────────────────────────────
    def suggest_meeting_slots(self, attendees: list[dict], duration_minutes: int = 30, preferred_time: str = "morning") -> dict:
        """Suggest optimal meeting slots based on attendee availability."""
        available_slots = []
        hours = list(range(9, 18))
        for hour in hours:
            slot_score = 0
            attendees_available = 0
            for att in attendees:
                free_hours = att.get("free_hours", list(range(9, 18)))
                if hour in free_hours:
                    attendees_available += 1
                    slot_score += 1
            if preferred_time == "morning" and 9 <= hour <= 12:
                slot_score += 2
            elif preferred_time == "afternoon" and 13 <= hour <= 17:
                slot_score += 2
            available_slots.append({
                "time": f"{hour:02d}:00",
                "end_time": f"{hour + duration_minutes // 60:02d}:{duration_minutes % 60:02d}",
                "attendees_available": attendees_available,
                "total_attendees": len(attendees),
                "score": slot_score,
                "available": attendees_available >= len(attendees) - 1,
            })
        available_slots.sort(key=lambda s: s["score"], reverse=True)
        best = available_slots[0] if available_slots else None
        return {
            "recommended_slot": best,
            "all_slots": available_slots[:5],
            "duration_minutes": duration_minutes,
            "preferred_time": preferred_time,
        }

    # ── Idea 44: Code Review Assistant ──────────────────────────────
    def review_code(self, code: str, language: str = "python") -> dict:
        """Automated code review with suggestions."""
        issues = []
        for rule in self.REVIEW_RULES:
            matches = re.finditer(rule["pattern"], code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append({
                    "line": line_num,
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "snippet": code[max(0, match.start() - 20):match.end() + 20],
                })
        total_lines = code.count('\n') + 1
        severity_counts = {"error": 0, "warning": 0, "info": 0}
        for issue in issues:
            severity_counts[issue["severity"]] += 1
        score = max(0, 100 - severity_counts["error"] * 20 - severity_counts["warning"] * 5 - severity_counts["info"] * 1)
        if score >= 90:
            rating = "excellent"
        elif score >= 70:
            rating = "good"
        elif score >= 50:
            rating = "needs_improvement"
        else:
            rating = "poor"
        return {
            "issues": issues,
            "total_issues": len(issues),
            "severity_counts": severity_counts,
            "score": score,
            "rating": rating,
            "lines_reviewed": total_lines,
        }

    # ── Idea 45: Documentation Generator ────────────────────────────
    def generate_docs(self, code: str, language: str = "python") -> dict:
        """Generate documentation from code."""
        functions = re.findall(r'def\s+(\w+)\s*\(([^)]*)\)', code)
        classes = re.findall(r'class\s+(\w+)(?:\([^)]*\))?:', code)
        imports = re.findall(r'(?:from\s+(\S+)\s+)?import\s+(\S+)', code)
        docs = {"module_doc": f"Module documentation for {language} code", "functions": [], "classes": [], "imports": []}
        for func_name, params in functions:
            param_list = [p.strip().split(':')[0].strip() for p in params.split(',') if p.strip()]
            docs["functions"].append({
                "name": func_name,
                "params": param_list,
                "docstring": f"TODO: Document {func_name} function",
                "suggestion": "Add parameter types and return type annotation",
            })
        for cls_name in classes:
            docs["classes"].append({
                "name": cls_name,
                "docstring": f"TODO: Document {cls_name} class",
                "suggestion": "Add class description and usage examples",
            })
        docs["imports"] = [{"module": m or i, "name": i} for m, i in imports]
        return {"documentation": docs, "language": language, "coverage_estimate": f"{len(functions)} functions, {len(classes)} classes documented"}

    # ── Idea 46: Test Case Generator ────────────────────────────────
    def generate_test_cases(self, code: str) -> dict:
        """Generate test cases from code analysis."""
        functions = re.findall(r'def\s+(\w+)\s*\(([^)]*)\)', code)
        test_cases = []
        for func_name, params in functions:
            param_list = [p.strip().split(':')[0].strip() for p in params.split(',') if p.strip()]
            test_cases.append({
                "function": func_name,
                "test_name": f"test_{func_name}_basic",
                "test_code": f"def test_{func_name}_basic():\n    result = {func_name}({', '.join(['mock_value'] * len(param_list))})\n    assert result is not None",
                "type": "unit",
            })
            if param_list:
                test_cases.append({
                    "function": func_name,
                    "test_name": f"test_{func_name}_edge_case",
                    "test_code": f"def test_{func_name}_edge_case():\n    result = {func_name}({', '.join(['None'] * len(param_list))})\n    assert result is not None or result is None",
                    "type": "edge_case",
                })
        return {"test_cases": test_cases, "total_generated": len(test_cases), "functions_covered": len(functions)}

    # ── Idea 47: Commit Message Auto-Generator ──────────────────────
    def generate_commit_message(self, changes: dict) -> dict:
        """Generate semantic commit messages from changes."""
        added = changes.get("added", [])
        modified = changes.get("modified", [])
        removed = changes.get("removed", [])
        if any("test" in f for f in added + modified):
            commit_type = "test"
        elif any("readme" in f.lower() or "doc" in f.lower() for f in added + modified):
            commit_type = "docs"
        elif any(f.endswith((".css", ".scss")) for f in added + modified):
            commit_type = "style"
        elif removed:
            commit_type = "refactor"
        elif any("fix" in f.lower() or "bug" in f.lower() for f in modified):
            commit_type = "fix"
        else:
            commit_type = "feat"
        all_files = added + modified + removed
        if len(all_files) == 1:
            scope = all_files[0].split('/')[-1].split('.')[0]
        elif len(all_files) <= 3:
            scope = ", ".join(f.split('/')[-1].split('.')[0] for f in all_files)
        else:
            scope = f"{len(all_files)} files"
        actions = []
        if added:
            actions.append(f"add {', '.join(f.split('/')[-1] for f in added[:3])}")
        if modified:
            actions.append(f"update {', '.join(f.split('/')[-1] for f in modified[:3])}")
        if removed:
            actions.append(f"remove {', '.join(f.split('/')[-1] for f in removed[:3])}")
        description = "; ".join(actions)
        message = f"{commit_type}({scope}): {description}"
        return {"commit_message": message, "type": commit_type, "scope": scope, "breaking": False}

    # ── Idea 48: Bug Triage Automation ──────────────────────────────
    def triage_bug(self, bug_report: dict) -> dict:
        """Automatically triage and route bug reports."""
        title = bug_report.get("title", "").lower()
        description = bug_report.get("description", "").lower()
        text = f"{title} {description}"
        category = "unknown"
        for cat, _config in self.BUG_TRIAGE_RULES.items():
            if cat in text:
                category = cat
                break
        if category == "unknown":
            if any(w in text for w in {"crash", "segfault", "deadlock"}):
                category = "crash"
            elif any(w in text for w in {"ui", "button", "display", "render"}):
                category = "ui"
            elif any(w in text for w in {"api", "endpoint", "rest", "graphql"}):
                category = "api"
            else:
                category = "performance"
        rule = self.BUG_TRIAGE_RULES.get(category, {"assignee": "engineering", "priority": "medium"})
        severity = "P0" if rule["priority"] == "critical" else "P1" if rule["priority"] == "high" else "P2"
        return {
            "bug_id": bug_report.get("id", "BUG-" + hashlib.md5(text.encode()).hexdigest()[:8].upper()),
            "category": category,
            "priority": rule["priority"],
            "severity": severity,
            "assignee": rule["assignee"],
            "auto_triaged": True,
            "estimated_resolution": "24h" if severity == "P0" else "72h" if severity == "P1" else "1 week",
        }

    # ── Idea 49: Performance Bottleneck Detector ────────────────────
    def detect_bottlenecks(self, metrics: dict) -> dict:
        """Detect performance bottlenecks from metrics."""
        bottlenecks = []
        recommendations = []
        cpu = metrics.get("cpu_percent", 0)
        memory = metrics.get("memory_percent", 0)
        disk_io = metrics.get("disk_io_percent", 0)
        network = metrics.get("network_latency_ms", 0)
        error_rate = metrics.get("error_rate_percent", 0)
        if cpu > 85:
            bottlenecks.append({"metric": "cpu", "value": cpu, "threshold": 85, "severity": "critical"})
            recommendations.append("Scale up CPU or optimize compute-intensive operations")
        elif cpu > 70:
            bottlenecks.append({"metric": "cpu", "value": cpu, "threshold": 70, "severity": "warning"})
            recommendations.append("Monitor CPU usage and consider optimization")
        if memory > 90:
            bottlenecks.append({"metric": "memory", "value": memory, "threshold": 90, "severity": "critical"})
            recommendations.append("Increase memory allocation or fix memory leaks")
        elif memory > 75:
            bottlenecks.append({"metric": "memory", "value": memory, "threshold": 75, "severity": "warning"})
            recommendations.append("Review memory usage patterns")
        if disk_io > 80:
            bottlenecks.append({"metric": "disk_io", "value": disk_io, "threshold": 80, "severity": "high"})
            recommendations.append("Consider SSD upgrade or optimize I/O operations")
        if network > 500:
            bottlenecks.append({"metric": "network_latency", "value": network, "threshold": 500, "severity": "high"})
            recommendations.append("Investigate network issues or add caching")
        if error_rate > 5:
            bottlenecks.append({"metric": "error_rate", "value": error_rate, "threshold": 5, "severity": "critical"})
            recommendations.append("Investigate and fix error sources immediately")
        overall = "healthy" if not bottlenecks else "degraded" if any(b["severity"] != "critical" for b in bottlenecks) else "critical"
        return {"bottlenecks": bottlenecks, "total_issues": len(bottlenecks), "overall_status": overall, "recommendations": recommendations}

    # ── Idea 50: Architecture Advisor ───────────────────────────────
    def suggest_architecture(self, project_info: dict) -> dict:
        """Suggest architecture improvements based on code analysis."""
        suggestions = []
        project_type = project_info.get("type", "unknown")
        scale = project_info.get("scale", "small")
        tech_stack = project_info.get("tech_stack", [])
        if project_type == "web" and scale in ("medium", "large"):
            suggestions.append({"category": "scalability", "suggestion": "Consider adding a load balancer", "priority": "high"})
            suggestions.append({"category": "caching", "suggestion": "Implement Redis caching layer", "priority": "high"})
        if "microservices" in str(tech_stack).lower():
            suggestions.append({"category": "observability", "suggestion": "Add distributed tracing (Jaeger/Zipkin)", "priority": "high"})
            suggestions.append({"category": "communication", "suggestion": "Consider event-driven architecture with message queues", "priority": "medium"})
        if project_info.get("database", "") == "relational":
            suggestions.append({"category": "database", "suggestion": "Consider read replicas for read-heavy workloads", "priority": "medium"})
            suggestions.append({"category": "database", "suggestion": "Implement connection pooling", "priority": "high"})
        suggestions.append({"category": "security", "suggestion": "Implement rate limiting on all endpoints", "priority": "high"})
        suggestions.append({"category": "monitoring", "suggestion": "Set up comprehensive logging and alerting", "priority": "high"})
        suggestions.append({"category": "ci_cd", "suggestion": "Implement automated testing pipeline", "priority": "high"})
        if scale == "large":
            suggestions.append({"category": "deployment", "suggestion": "Use blue-green or canary deployments", "priority": "medium"})
            suggestions.append({"category": "data", "suggestion": "Consider data partitioning/sharding strategy", "priority": "medium"})
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 4))
        return {
            "project_type": project_type,
            "scale": scale,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "architecture_maturity": "evolving" if len(suggestions) > 5 else "established" if len(suggestions) > 2 else "optimized",
        }
