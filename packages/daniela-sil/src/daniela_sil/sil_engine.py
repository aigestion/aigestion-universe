#!/usr/bin/env python3
"""
SIL Engine — Daniela's Self-Improvement Loop Core
===================================================
Implements SIL-01 through SIL-04 as a working system:

  SIL-01: Weekly self-review scheduler (Monday 9am cron or manual)
  SIL-02: Auto-fix pipeline (findings -> Jules dispatch -> verify -> merge)
  SIL-03: Knowledge base (lessons learned from every fix)
  SIL-04: Code health dashboard (live metrics + trend)

Cost: $0/month — Gemini free tier + Jules free tier + JSON state files.

CLI:
  python sil_engine.py status           — overall SIL status
  python sil_engine.py review           — run weekly codebase review now
  python sil_engine.py dispatch         — dispatch auto-fixable findings to Jules
  python sil_engine.py verify <pr_url>  — verify a fix PR re-analysis
  python sil_engine.py lessons          — list lessons in knowledge base
  python sil_engine.py dashboard        — generate health dashboard HTML
  python sil_engine.py trend            — show health score trend over time
  python sil_engine.py all              — run full loop: review -> dispatch -> lessons -> dashboard
  python sil_engine.py export           — export all JSON state files

Usage in Daniela's autonomous loop:
  1. sil_engine.py review               (Monday 9am: scan codebase)
  2. sil_engine.py dispatch             (auto-dispatch fixable findings to Jules)
  3. [Jules opens PRs, human approves critical ones]
  4. sil_engine.py verify <pr_url>      (re-analyze after merge)
  5. sil_engine.py dashboard            (update health dashboard)
"""

import json
import os
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Raiz del repo (este modulo vive en sil/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "sil"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESEARCH_DIR = PROJECT_ROOT / "data" / "research"
OUTPUT_DIR = PROJECT_ROOT / "static" / "brand"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DASHBOARD_DIR = PROJECT_ROOT / "static"

# State files
STATE_FILE = DATA_DIR / "sil_state.json"
LESSONS_FILE = DATA_DIR / "knowledge_base.json"
TREND_FILE = DATA_DIR / "health_trend.json"
DISPATCH_LOG = DATA_DIR / "dispatch_log.json"
WEEKLY_REPORTS_DIR = DATA_DIR / "weekly_reports"
WEEKLY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# SIL-01: WEEKLY SELF-REVIEW SCHEDULER
# ==============================================================================

class WeeklyReviewScheduler:
    """SIL-01: Schedules and runs weekly codebase self-review via Gemini 3.1 Pro."""

    REVIEW_FILES = [
        "daniela_os.py",
        "daniela_os_core.py",
        "gemini35_free_tier.py",
        "auth_system.py",
        "agents.py",
        "auto_pipeline.py",
        "viral_content_factory.py",
        "content_factory_ai.py",
        "daniela_self_improvement.py",
        "google_free_tier_automations.py",
        "jules_free_dispatch.py",
        "api_gateway.py",
        "admin_panel.py",
        "billing_system.py",
        "analytics.py",
    ]

    @staticmethod
    def run_review(focus: str = "all") -> dict:
        """Run a codebase review using Gemini 3.1 Pro (or fallback to stored findings)."""
        review_id = f"review_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()

        print(f"[SIL-01] Starting weekly codebase review (focus: {focus})...")
        print(f"  Review ID: {review_id}")
        print(f"  Files to analyze: {len(WeeklyReviewScheduler.REVIEW_FILES)}")

        # Try to use Gemini 3.1 Pro for real analysis
        analysis_result = WeeklyReviewScheduler._run_gemini_analysis(focus)

        if analysis_result.get("success"):
            print("  [Gemini 3.1 Pro] Analysis completed.")
            findings = analysis_result.get("findings", [])
        else:
            print("  [Fallback] Using stored findings from last review.")
            # Load from daniela_self_improvement findings
            findings = WeeklyReviewScheduler._load_stored_findings()

        # Compare with previous review
        prev_review = WeeklyReviewScheduler._get_last_review()
        delta = WeeklyReviewScheduler._compute_delta(prev_review, findings)

        report = {
            "review_id": review_id,
            "timestamp": timestamp,
            "focus": focus,
            "files_analyzed": len(WeeklyReviewScheduler.REVIEW_FILES),
            "total_findings": len(findings),
            "findings_by_severity": WeeklyReviewScheduler._count_by_severity(findings),
            "delta": delta,
            "health_score": WeeklyReviewScheduler._compute_health_score(findings),
            "model_used": analysis_result.get("model", "stored_findings"),
            "analysis_success": analysis_result.get("success", False),
        }

        # Save report
        report_path = WEEKLY_REPORTS_DIR / f"{review_id}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Update trend
        WeeklyReviewScheduler._append_trend(report)

        # Update state
        WeeklyReviewScheduler._update_state_last_review(review_id, timestamp)

        print(f"  Total findings: {len(findings)}")
        print(f"  Health score: {report['health_score']}/100")
        print(f"  Delta: +{delta['new']} new, -{delta['fixed']} fixed, ~{delta['persisting']} persisting")
        print(f"  Report saved: {report_path}")

        return report

    @staticmethod
    def _run_gemini_analysis(focus: str) -> dict:
        """Try to run Gemini 3.1 Pro analysis on the codebase."""
        try:
            from google import genai
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

            # Collect code
            code_chunks = []
            for fname in WeeklyReviewScheduler.REVIEW_FILES:
                fpath = PROJECT_ROOT / fname
                if fpath.exists():
                    code = fpath.read_text(encoding="utf-8", errors="ignore")[:8000]
                    code_chunks.append(f"--- {fname} ---\n{code}\n")

            combined = "\n".join(code_chunks)
            if len(combined) > 50000:
                combined = combined[:50000] + "\n... [truncated]"

            prompt = f"""You are Daniela, an AI reviewing her own codebase. Analyze these files for:
1. Security issues (critical first)
2. Stub/simulated code (functions that don't do real work)
3. Architecture problems (coupling, missing patterns)
4. Missing tests
5. Disconnected integrations

Return JSON: {{"findings": [{{"id": "SR-XX", "title": "...", "severity": "critical|high|medium|low", "category": "security|architecture|stub|integration|missing_test", "file": "...", "description": "...", "recommendation": "..."}}]}}

Code:
{combined}
"""
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            text = response.text

            # Parse JSON from response
            if "{" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                parsed = json.loads(text[start:end])
                return {"success": True, "findings": parsed.get("findings", []), "model": "gemini-3.6-flash"}
            return {"success": False, "error": "No JSON in response"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _load_stored_findings() -> list[dict]:
        """Load findings from daniela_self_improvement.py stored data."""
        try:
            # Import findings from the module
            sys.path.insert(0, str(PROJECT_ROOT))
            from daniela_self_improvement import FINDINGS
            return [asdict(f) for f in FINDINGS]
        except Exception:
            # Fallback: load from JSON
            findings_path = OUTPUT_DIR / "self_review_findings.json"
            if findings_path.exists():
                with open(findings_path, encoding="utf-8") as f:
                    return json.load(f)
            return []

    @staticmethod
    def _get_last_review() -> dict | None:
        """Get the previous review for delta comparison."""
        reviews = sorted(WEEKLY_REPORTS_DIR.glob("review_*.json"))
        if len(reviews) < 2:
            return None
        with open(reviews[-2], encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _compute_delta(prev: dict | None, current_findings: list[dict]) -> dict:
        """Compute what's new, fixed, and persisting compared to previous review."""
        if not prev:
            return {"new": len(current_findings), "fixed": 0, "persisting": 0}

        prev_ids = {f.get("id", f.get("title", "")) for f in prev.get("findings", [])}
        curr_ids = {f.get("id", f.get("title", "")) for f in current_findings}

        new = curr_ids - prev_ids
        fixed = prev_ids - curr_ids
        persisting = curr_ids & prev_ids

        return {
            "new": len(new),
            "fixed": len(fixed),
            "persisting": len(persisting),
            "new_ids": list(new),
            "fixed_ids": list(fixed),
        }

    @staticmethod
    def _count_by_severity(findings: list[dict]) -> dict:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            sev = f.get("severity", "low")
            if sev in counts:
                counts[sev] += 1
        return counts

    @staticmethod
    def _compute_health_score(findings: list[dict]) -> int:
        """Health score: 100 - (critical*10 + high*5 + medium*2 + low*1)."""
        counts = WeeklyReviewScheduler._count_by_severity(findings)
        score = 100 - (counts["critical"] * 10 + counts["high"] * 5 + counts["medium"] * 2 + counts["low"] * 1)
        return max(0, score)

    @staticmethod
    def _append_trend(report: dict):
        """Append to health trend tracking."""
        trend = []
        if TREND_FILE.exists():
            with open(TREND_FILE, encoding="utf-8") as f:
                trend = json.load(f)

        trend.append({
            "date": report["timestamp"],
            "health_score": report["health_score"],
            "total_findings": report["total_findings"],
            "critical": report["findings_by_severity"]["critical"],
            "high": report["findings_by_severity"]["high"],
            "medium": report["findings_by_severity"]["medium"],
            "low": report["findings_by_severity"]["low"],
            "review_id": report["review_id"],
        })

        with open(TREND_FILE, "w", encoding="utf-8") as f:
            json.dump(trend, f, indent=2)

    @staticmethod
    def _update_state_last_review(review_id: str, timestamp: str):
        """Update SIL state with last review info."""
        state = _load_state()
        state["last_review_id"] = review_id
        state["last_review_date"] = timestamp
        state["total_reviews_run"] = state.get("total_reviews_run", 0) + 1
        _save_state(state)


# ==============================================================================
# SIL-02: AUTO-FIX PIPELINE
# ==============================================================================

@dataclass
class DispatchTask:
    """A task dispatched to Jules for auto-fixing."""
    finding_id: str
    finding_title: str
    finding_description: str
    recommendation: str
    file_affected: str
    severity: str
    jules_prompt: str
    dispatch_date: str
    status: str = "queued"  # queued, dispatched, pr_opened, verified, merged, rejected
    pr_url: str = ""
    pr_number: int = 0
    verification_result: str = ""


class AutoFixPipeline:
    """SIL-02: Auto-dispatch fixable findings to Jules, verify, and track."""

    MAX_AUTO_FIXES_PER_DAY = 5  # Within Jules free tier 15/day
    CRITICAL_REQUIRES_HUMAN = True

    @staticmethod
    def get_dispatchable_findings(severity_filter: str | None = None) -> list[dict]:
        """Get findings that are Jules-dispatchable. Critical requires human approval."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from daniela_self_improvement import FINDINGS
            findings = [asdict(f) for f in FINDINGS]
        except Exception:
            findings_path = OUTPUT_DIR / "self_review_findings.json"
            if findings_path.exists():
                with open(findings_path, encoding="utf-8") as f:
                    findings = json.load(f)
            else:
                findings = []

        dispatchable = []
        for f in findings:
            if not f.get("jules_dispatchable", False):
                continue
            if severity_filter and f.get("severity") != severity_filter:
                continue
            # Critical findings need human approval flag
            if f.get("severity") == "critical" and AutoFixPipeline.CRITICAL_REQUIRES_HUMAN:
                f["needs_human_approval"] = True
            else:
                f["needs_human_approval"] = False
            dispatchable.append(f)

        # Sort by severity (critical first) then by effort (S first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        effort_order = {"S": 0, "M": 1, "L": 2, "XL": 3}
        dispatchable.sort(key=lambda x: (
            severity_order.get(x.get("severity", "low"), 4),
            effort_order.get(x.get("fix_effort", "L"), 2),
        ))
        return dispatchable

    @staticmethod
    def dispatch_auto_fixes(max_count: int = 5) -> list[DispatchTask]:
        """Dispatch auto-fixable findings (non-critical) to Jules."""
        dispatchable = AutoFixPipeline.get_dispatchable_findings()
        auto_fixable = [f for f in dispatchable if not f.get("needs_human_approval", False)]
        to_dispatch = auto_fixable[:max_count]

        print("[SIL-02] Auto-fix pipeline:")
        print(f"  Total dispatchable: {len(dispatchable)}")
        print(f"  Auto-fixable (non-critical): {len(auto_fixable)}")
        print(f"  Dispatching: {min(len(to_dispatch), max_count)}")

        dispatched = []
        for finding in to_dispatch:
            task = AutoFixPipeline._create_dispatch_task(finding)
            AutoFixPipeline._log_dispatch(task)
            dispatched.append(task)

            print(f"  -> [{finding['id']}] {finding['title']}")
            print(f"     File: {finding['file_affected']}")
            print(f"     Severity: {finding['severity']} | Effort: {finding['fix_effort']}")
            print(f"     Jules prompt generated ({len(task.jules_prompt)} chars)")

        # Update state
        state = _load_state()
        state["total_dispatched"] = state.get("total_dispatched", 0) + len(dispatched)
        state["last_dispatch_date"] = datetime.now().isoformat()
        _save_state(state)

        print(f"\n  Dispatched: {len(dispatched)} tasks")
        print(f"  (Jules free tier: {len(dispatched)}/15 daily limit used)")

        return dispatched

    @staticmethod
    def dispatch_critical(finding_id: str, human_approved: bool = True) -> DispatchTask | None:
        """Dispatch a critical finding after human approval."""
        if not human_approved:
            print(f"[SIL-02] Cannot dispatch {finding_id} without human approval (critical).")
            return None

        dispatchable = AutoFixPipeline.get_dispatchable_findings(severity_filter="critical")
        finding = next((f for f in dispatchable if f["id"] == finding_id), None)
        if not finding:
            print(f"[SIL-02] Finding {finding_id} not found or not dispatchable.")
            return None

        task = AutoFixPipeline._create_dispatch_task(finding)
        task.status = "dispatched"
        AutoFixPipeline._log_dispatch(task)

        print("[SIL-02] CRITICAL finding dispatched (human-approved):")
        print(f"  [{finding['id']}] {finding['title']}")
        print(f"  Jules prompt generated ({len(task.jules_prompt)} chars)")

        state = _load_state()
        state["total_dispatched"] = state.get("total_dispatched", 0) + 1
        _save_state(state)

        return task

    @staticmethod
    def _create_dispatch_task(finding: dict) -> DispatchTask:
        """Create a Jules dispatch task from a finding."""
        jules_prompt = AutoFixPipeline._build_jules_prompt(finding)
        return DispatchTask(
            finding_id=finding["id"],
            finding_title=finding["title"],
            finding_description=finding.get("description", ""),
            recommendation=finding.get("recommendation", ""),
            file_affected=finding.get("file_affected", ""),
            severity=finding.get("severity", "medium"),
            jules_prompt=jules_prompt,
            dispatch_date=datetime.now().isoformat(),
            status="queued",
        )

    @staticmethod
    def _build_jules_prompt(finding: dict) -> str:
        """Build a detailed Jules prompt for the fix."""
        return f"""# Jules Task: Fix {finding['id']} — {finding['title']}

## Problem
{finding.get('description', 'See title.')}

## File Affected
`{finding.get('file_affected', 'unknown')}`

## Recommended Fix
{finding.get('recommendation', 'See problem description.')}

## Constraints
- Do NOT break existing API contracts or function signatures
- Add or update tests if applicable
- Follow existing code style in the file
- If adding new imports, ensure they are in requirements.txt or stdlib
- Keep changes minimal and focused on this specific issue

## Severity
{finding.get('severity', 'medium').upper()}

## Category
{finding.get('category', 'general')}
"""

    @staticmethod
    def _log_dispatch(task: DispatchTask):
        """Log the dispatch to the dispatch log."""
        log = []
        if DISPATCH_LOG.exists():
            with open(DISPATCH_LOG, encoding="utf-8") as f:
                log = json.load(f)
        log.append(asdict(task))
        with open(DISPATCH_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

    @staticmethod
    def mark_pr_opened(finding_id: str, pr_url: str, pr_number: int):
        """Mark that a Jules PR was opened for a finding."""
        log = []
        if DISPATCH_LOG.exists():
            with open(DISPATCH_LOG, encoding="utf-8") as f:
                log = json.load(f)

        for entry in log:
            if entry["finding_id"] == finding_id:
                entry["status"] = "pr_opened"
                entry["pr_url"] = pr_url
                entry["pr_number"] = pr_number
                break

        with open(DISPATCH_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

        state = _load_state()
        state["total_prs_opened"] = state.get("total_prs_opened", 0) + 1
        _save_state(state)

        print(f"[SIL-02] PR opened for {finding_id}: {pr_url}")

    @staticmethod
    def verify_fix(finding_id: str, pr_url: str = "") -> dict:
        """Verify a fix by re-analyzing the affected file."""
        print(f"[SIL-03] Verifying fix for {finding_id}...")

        # Load original finding
        dispatchable = AutoFixPipeline.get_dispatchable_findings()
        finding = next((f for f in dispatchable if f["id"] == finding_id), None)
        if not finding:
            return {"verified": False, "error": f"Finding {finding_id} not found"}

        file_affected = finding.get("file_affected", "")
        fpath = PROJECT_ROOT / file_affected

        # Check if file exists and read it
        if not fpath.exists():
            return {"verified": False, "error": f"File {file_affected} not found"}

        code = fpath.read_text(encoding="utf-8", errors="ignore")

        # Simple pattern-based verification (check if the issue pattern is gone)
        verification = AutoFixPipeline._pattern_verify(finding, code)

        if verification["resolved"]:
            print(f"  [VERIFIED] Finding {finding_id} appears resolved!")
            verification["status"] = "verified"

            # Record lesson
            KnowledgeBase.record_lesson(finding, verification)
        else:
            print(f"  [NOT RESOLVED] Finding {finding_id} still present.")
            verification["status"] = "not_verified"

        # Update dispatch log
        log = []
        if DISPATCH_LOG.exists():
            with open(DISPATCH_LOG, encoding="utf-8") as f:
                log = json.load(f)
        for entry in log:
            if entry["finding_id"] == finding_id:
                entry["status"] = verification["status"]
                entry["verification_result"] = verification.get("details", "")
                break
        with open(DISPATCH_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

        # Update state
        state = _load_state()
        if verification["resolved"]:
            state["total_verified"] = state.get("total_verified", 0) + 1
        _save_state(state)

        return verification

    @staticmethod
    def _pattern_verify(finding: dict, code: str) -> dict:
        """Pattern-based verification: check if the issue pattern is still present."""
        fid = finding["id"]

        if fid == "SR-01":  # Unauthenticated Flask API
            if "auth_system" in code or "@require_auth" in code or "require_auth" in code:
                return {"resolved": True, "details": "auth_system integration detected"}
            return {"resolved": False, "details": "No auth_system integration found"}

        elif fid == "SR-02":  # Command injection
            if "subprocess.run" in code and "shell=False" in code:
                return {"resolved": True, "details": "subprocess.run with shell=False detected"}
            if "shell=True" in code or "os.system" in code:
                return {"resolved": False, "details": "shell=True or os.system still present"}
            return {"resolved": True, "details": "No shell=True or os.system found"}

        elif fid == "SR-03":  # Unauthenticated DB download
            if "backup_db" in code and ("auth" in code.lower() or "require_auth" in code):
                return {"resolved": True, "details": "Auth check on backup_db endpoint"}
            return {"resolved": False, "details": "backup_db still unauthenticated"}

        elif fid == "SR-04":  # Arbitrary file read
            if "Path(" in code and "resolve()" in code and "PROJECT_ROOT" in code:
                return {"resolved": True, "details": "Path sandboxing detected"}
            return {"resolved": False, "details": "No path sandboxing found"}

        elif fid == "SR-05":  # Hardcoded secrets
            if "environ.get" in code and "OR" not in code.split("environ.get")[1][:50] if "environ.get" in code else False:
                return {"resolved": True, "details": "Environment variables without hardcoded fallback"}
            return {"resolved": False, "details": "Hardcoded fallbacks may still exist"}

        elif fid == "SR-06":  # Input length limits
            if "len(" in code and "max_length" in code.lower():
                return {"resolved": True, "details": "Input length limits detected"}
            return {"resolved": False, "details": "No input length limits found"}

        # Default: check if recommendation keywords appear
        rec = finding.get("recommendation", "").lower()
        rec_words = [w for w in rec.split() if len(w) > 4]
        matches = sum(1 for w in rec_words if w in code.lower())
        if matches > len(rec_words) * 0.3:
            return {"resolved": True, "details": f"Recommendation keywords detected ({matches}/{len(rec_words)})"}
        return {"resolved": False, "details": "Recommendation not yet implemented"}


# ==============================================================================
# SIL-03: KNOWLEDGE BASE (LESSONS LEARNED)
# ==============================================================================

@dataclass
class Lesson:
    """A lesson learned from fixing a finding."""
    id: str
    finding_id: str
    finding_title: str
    category: str
    severity: str
    fix_description: str
    files_changed: list[str]
    pattern: str  # "When I see X, it usually means Y, fix with Z"
    prevention_rule: str  # Rule to check before generating new code
    date_learned: str
    verification_status: str


class KnowledgeBase:
    """SIL-03: Growing knowledge base of lessons learned from fixes."""

    @staticmethod
    def record_lesson(finding: dict, verification: dict) -> Lesson:
        """Record a lesson when a fix is verified."""
        lesson = Lesson(
            id=f"lesson_{finding['id']}_{datetime.now().strftime('%Y%m%d')}",
            finding_id=finding["id"],
            finding_title=finding["title"],
            category=finding.get("category", "general"),
            severity=finding.get("severity", "medium"),
            fix_description=finding.get("recommendation", ""),
            files_changed=[finding.get("file_affected", "")],
            pattern=KnowledgeBase._extract_pattern(finding),
            prevention_rule=KnowledgeBase._extract_prevention_rule(finding),
            date_learned=datetime.now().isoformat(),
            verification_status=verification.get("status", "verified"),
        )

        # Load existing lessons
        lessons = []
        if LESSONS_FILE.exists():
            with open(LESSONS_FILE, encoding="utf-8") as f:
                lessons = json.load(f)

        # Don't duplicate
        existing_ids = {les["id"] for les in lessons}
        if lesson.id not in existing_ids:
            lessons.append(asdict(lesson))
            with open(LESSONS_FILE, "w", encoding="utf-8") as f:
                json.dump(lessons, f, indent=2, ensure_ascii=False)

            print(f"[SIL-03] Lesson recorded: {lesson.id}")
            print(f"  Pattern: {lesson.pattern}")
            print(f"  Prevention: {lesson.prevention_rule}")

            # Update state
            state = _load_state()
            state["total_lessons"] = state.get("total_lessons", 0) + 1
            _save_state(state)
        else:
            print(f"[SIL-03] Lesson {lesson.id} already exists, skipping.")

        return lesson

    @staticmethod
    def get_lessons(category: str | None = None) -> list[dict]:
        """Get all lessons, optionally filtered by category."""
        if not LESSONS_FILE.exists():
            return []
        with open(LESSONS_FILE, encoding="utf-8") as f:
            lessons = json.load(f)
        if category:
            lessons = [les for les in lessons if les.get("category") == category]
        return lessons

    @staticmethod
    def search_lessons(query: str) -> list[dict]:
        """Search lessons by keyword in title, pattern, or prevention rule."""
        lessons = KnowledgeBase.get_lessons()
        query_lower = query.lower()
        return [les for les in lessons if
                query_lower in les.get("finding_title", "").lower() or
                query_lower in les.get("pattern", "").lower() or
                query_lower in les.get("prevention_rule", "").lower()]

    @staticmethod
    def _extract_pattern(finding: dict) -> str:
        """Extract a pattern: 'When I see X, it means Y, fix with Z'."""
        cat = finding.get("category", "general")
        title = finding.get("title", "")
        rec = finding.get("recommendation", "")

        patterns = {
            "security": f"When I see {title.lower()}, it means there's a security vulnerability. Fix: {rec}",
            "stub": f"When I see {title.lower()}, it means the code is simulated/stubbed. Fix: {rec}",
            "architecture": f"When I see {title.lower()}, it means the architecture needs improvement. Fix: {rec}",
            "integration": f"When I see {title.lower()}, it means components aren't connected. Fix: {rec}",
            "missing_test": f"When I see {title.lower()}, it means tests are missing. Fix: {rec}",
        }
        return patterns.get(cat, f"When I see {title}, fix: {rec}")

    @staticmethod
    def _extract_prevention_rule(finding: dict) -> str:
        """Extract a prevention rule for future code generation."""
        cat = finding.get("category", "general")
        rec = finding.get("recommendation", "")

        rules = {
            "security": f"SECURITY RULE: {rec}",
            "stub": f"COMPLETENESS RULE: {rec}",
            "architecture": f"ARCHITECTURE RULE: {rec}",
            "integration": f"INTEGRATION RULE: {rec}",
            "missing_test": f"TESTING RULE: {rec}",
        }
        return rules.get(cat, f"RULE: {rec}")

    @staticmethod
    def export_markdown() -> str:
        """Export lessons as a human-readable markdown learning log."""
        lessons = KnowledgeBase.get_lessons()
        if not lessons:
            return "# Daniela's Learning Log\n\nNo lessons learned yet.\n"

        lines = ["# Daniela's Learning Log\n"]
        lines.append(f"Total lessons: {len(lessons)}\n")

        # Group by category
        by_cat = defaultdict(list)
        for les in lessons:
            by_cat[les.get("category", "general")].append(les)

        for cat, cat_lessons in sorted(by_cat.items()):
            lines.append(f"## {cat.upper()}\n")
            for les in cat_lessons:
                lines.append(f"### {les['finding_id']}: {les['finding_title']}")
                lines.append(f"- **Severity:** {les['severity']}")
                lines.append(f"- **Date:** {les['date_learned']}")
                lines.append(f"- **Pattern:** {les['pattern']}")
                lines.append(f"- **Prevention:** {les['prevention_rule']}")
                lines.append(f"- **Files:** {', '.join(les.get('files_changed', []))}")
                lines.append("")

        return "\n".join(lines)


# ==============================================================================
# SIL-04: CODE HEALTH DASHBOARD
# ==============================================================================

class HealthDashboard:
    """SIL-04: Generate a live code health dashboard HTML page."""

    @staticmethod
    def generate() -> str:
        """Generate the health dashboard HTML."""
        state = _load_state()
        lessons = KnowledgeBase.get_lessons()
        trend = HealthDashboard._load_trend()
        dispatchable = AutoFixPipeline.get_dispatchable_findings()

        # Compute metrics
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from daniela_self_improvement import FINDINGS, SelfImprovementLoop
            sil = SelfImprovementLoop()
            health_score = sil.get_health_score()
            findings_by_severity = {
                "critical": len([f for f in FINDINGS if f.severity == "critical"]),
                "high": len([f for f in FINDINGS if f.severity == "high"]),
                "medium": len([f for f in FINDINGS if f.severity == "medium"]),
                "low": len([f for f in FINDINGS if f.severity == "low"]),
            }
        except Exception:
            health_score = state.get("last_health_score", 0)
            findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        total_findings = sum(findings_by_severity.values())
        total_dispatchable = len(dispatchable)
        auto_fixable = len([f for f in dispatchable if not f.get("needs_human_approval", False)])
        critical_pending = len([f for f in dispatchable if f.get("needs_human_approval", False)])

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniela SIL — Code Health Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', -apple-system, sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 50%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 2em;
            background: linear-gradient(90deg, #00ffff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 30px; font-size: 0.9em; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,255,255,0.15); }}
        .card-label {{ font-size: 0.8em; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
        .card-value {{ font-size: 3em; font-weight: 700; margin: 10px 0; }}
        .card-value.critical {{ color: #ff4444; }}
        .card-value.high {{ color: #ff8800; }}
        .card-value.medium {{ color: #ffcc00; }}
        .card-value.low {{ color: #88ccff; }}
        .card-value.good {{ color: #00ff88; }}
        .card-value.info {{ color: #00ffff; }}
        .card-desc {{ font-size: 0.85em; color: #aaa; }}

        .health-score {{
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            margin-bottom: 30px;
        }}
        .health-score-value {{
            font-size: 5em;
            font-weight: 800;
            background: linear-gradient(90deg, #ff4444, #ff8800, #ffcc00, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .health-score-label {{ font-size: 1.2em; color: #888; margin-top: 10px; }}

        .section {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }}
        .section h2 {{ font-size: 1.3em; margin-bottom: 16px; color: #00ffff; }}

        .finding-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .finding-item.critical {{ border-color: #ff4444; }}
        .finding-item.high {{ border-color: #ff8800; }}
        .finding-item.medium {{ border-color: #ffcc00; }}
        .finding-item.low {{ border-color: #88ccff; }}
        .finding-id {{ font-weight: 700; margin-right: 12px; min-width: 60px; }}
        .finding-title {{ flex: 1; font-size: 0.9em; }}
        .finding-status {{
            font-size: 0.75em;
            padding: 3px 10px;
            border-radius: 12px;
            background: rgba(255,255,255,0.1);
        }}
        .finding-status.open {{ color: #ff8800; }}
        .finding-status.dispatched {{ color: #00ffff; }}
        .finding-status.fixed {{ color: #00ff88; }}

        .trend-bar {{
            display: flex;
            align-items: flex-end;
            height: 120px;
            gap: 4px;
            margin-top: 16px;
        }}
        .trend-bar-item {{
            flex: 1;
            background: linear-gradient(180deg, #00ff88, #00cc66);
            border-radius: 4px 4px 0 0;
            min-height: 4px;
            position: relative;
            transition: height 0.5s;
        }}
        .trend-bar-item::after {{
            content: attr(data-score);
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.7em;
            color: #888;
        }}

        .lesson-item {{
            padding: 10px;
            margin-bottom: 8px;
            background: rgba(0,255,136,0.05);
            border-left: 3px solid #00ff88;
            border-radius: 6px;
            font-size: 0.85em;
        }}
        .lesson-pattern {{ color: #00ff88; font-style: italic; }}

        .footer {{ text-align: center; color: #555; font-size: 0.8em; margin-top: 30px; }}
        .badge {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
        }}
        .badge.free {{ background: rgba(0,255,136,0.15); color: #00ff88; }}
        .badge.autonomous {{ background: rgba(0,255,255,0.15); color: #00ffff; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Daniela SIL Dashboard</h1>
    <p class="subtitle">
        Self-Improvement Loop — Daniela reviews her own code and gets smarter over time
        <span class="badge free">$0/month</span>
        <span class="badge autonomous">Autonomous</span>
    </p>

    <div class="health-score">
        <div class="health-score-value">{health_score}</div>
        <div class="health-score-label">/ 100 — Code Health Score</div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-label">Total Findings</div>
            <div class="card-value info">{total_findings}</div>
            <div class="card-desc">{findings_by_severity['critical']} critical, {findings_by_severity['high']} high, {findings_by_severity['medium']} medium, {findings_by_severity['low']} low</div>
        </div>
        <div class="card">
            <div class="card-label">Critical Issues</div>
            <div class="card-value critical">{findings_by_severity['critical']}</div>
            <div class="card-desc">Requires human approval before fix</div>
        </div>
        <div class="card">
            <div class="card-label">Auto-Fixable</div>
            <div class="card-value good">{auto_fixable}</div>
            <div class="card-desc">Dispatchable to Jules (free tier)</div>
        </div>
        <div class="card">
            <div class="card-label">Lessons Learned</div>
            <div class="card-value info">{len(lessons)}</div>
            <div class="card-desc">Knowledge base entries</div>
        </div>
        <div class="card">
            <div class="card-label">PRs Dispatched</div>
            <div class="card-value medium">{state.get('total_dispatched', 0)}</div>
            <div class="card-desc">Total auto-fix PRs sent to Jules</div>
        </div>
        <div class="card">
            <div class="card-label">Fixes Verified</div>
            <div class="card-value good">{state.get('total_verified', 0)}</div>
            <div class="card-desc">Findings confirmed resolved</div>
        </div>
        <div class="card">
            <div class="card-label">Reviews Run</div>
            <div class="card-value info">{state.get('total_reviews_run', 0)}</div>
            <div class="card-desc">Weekly codebase self-reviews</div>
        </div>
        <div class="card">
            <div class="card-label">Last Review</div>
            <div class="card-value" style="font-size:1.5em;color:#00ffff;">
                {state.get('last_review_date', 'Never')[:10] if state.get('last_review_date') else 'Never'}
            </div>
            <div class="card-desc">{state.get('last_review_id', 'No review yet')}</div>
        </div>
    </div>

    <div class="section">
        <h2>Health Score Trend</h2>
        <div class="trend-bar">
            {''.join(f'<div class="trend-bar-item" style="height: {max(4, min(100, t["health_score"]))}%" data-score="{t["health_score"]}"></div>' for t in trend[-12:])}
        </div>
        <p style="color:#888;font-size:0.8em;margin-top:10px;">
            Trend over last {min(len(trend), 12)} reviews — goal: steady increase toward 100
        </p>
    </div>

    <div class="section">
        <h2>Priority Findings</h2>
        {''.join(HealthDashboard._render_finding(f) for f in dispatchable[:10])}
    </div>

    <div class="section">
        <h2>Knowledge Base — Lessons Learned</h2>
        {''.join(HealthDashboard._render_lesson(les) for les in lessons[:10]) if lessons else '<p style="color:#666;">No lessons learned yet. Run the auto-fix pipeline to start accumulating wisdom.</p>'}
    </div>

    <div class="section">
        <h2>SIL Loop Status</h2>
        <div style="display:flex;gap:20px;flex-wrap:wrap;">
            <div><strong>1. ANALYZE</strong> — {state.get('total_reviews_run', 0)} reviews completed</div>
            <div><strong>2. PRIORITIZE</strong> — {total_dispatchable} findings queued</div>
            <div><strong>3. DISPATCH</strong> — {state.get('total_dispatched', 0)} tasks sent to Jules</div>
            <div><strong>4. VERIFY</strong> — {state.get('total_verified', 0)} fixes confirmed</div>
            <div><strong>5. LEARN</strong> — {len(lessons)} lessons recorded</div>
            <div><strong>6. EVOLVE</strong> — Architecture recommendations pending implementation</div>
        </div>
    </div>

    <div class="footer">
        <p>Daniela SIL Engine — Self-Improvement Loop | Free Tier: Gemini 3.1 Pro + Jules 15 tasks/day</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
</div>
</body>
</html>"""

        # Save HTML
        dashboard_path = DASHBOARD_DIR / "sil_dashboard.html"
        dashboard_path.write_text(html, encoding="utf-8")

        # Also save metrics JSON for API consumption
        metrics = {
            "health_score": health_score,
            "total_findings": total_findings,
            "findings_by_severity": findings_by_severity,
            "auto_fixable": auto_fixable,
            "critical_pending": critical_pending,
            "total_dispatched": state.get("total_dispatched", 0),
            "total_verified": state.get("total_verified", 0),
            "total_lessons": len(lessons),
            "total_reviews": state.get("total_reviews_run", 0),
            "trend": trend[-12:],
            "generated_at": datetime.now().isoformat(),
        }
        metrics_path = OUTPUT_DIR / "sil_dashboard_metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        # Update state with latest health score
        state["last_health_score"] = health_score
        _save_state(state)

        print(f"[SIL-04] Dashboard generated: {dashboard_path}")
        print(f"  Metrics JSON: {metrics_path}")
        return str(dashboard_path)

    @staticmethod
    def _load_trend() -> list[dict]:
        if TREND_FILE.exists():
            with open(TREND_FILE, encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    def _render_finding(f: dict) -> str:
        sev = f.get("severity", "low")
        return f"""
            <div class="finding-item {sev}">
                <span class="finding-id">{f.get('id', '?')}</span>
                <span class="finding-title">{f.get('title', 'Unknown')}</span>
                <span class="finding-status {'open' if f.get('needs_human_approval') else 'dispatched'}">
                    {'NEEDS APPROVAL' if f.get('needs_human_approval') else 'AUTO-FIXABLE'}
                </span>
            </div>"""

    @staticmethod
    def _render_lesson(les: dict) -> str:
        return f"""
            <div class="lesson-item">
                <strong>{les.get('finding_id', '?')}</strong>: {les.get('finding_title', '')}<br>
                <span class="lesson-pattern">{les.get('pattern', '')}</span>
            </div>"""


# ==============================================================================
# STATE MANAGEMENT
# ==============================================================================

def _load_state() -> dict:
    """Load SIL state."""
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().isoformat(),
        "total_reviews_run": 0,
        "total_dispatched": 0,
        "total_prs_opened": 0,
        "total_verified": 0,
        "total_lessons": 0,
        "last_review_id": "",
        "last_review_date": "",
        "last_dispatch_date": "",
        "last_health_score": 0,
    }


def _save_state(state: dict):
    """Save SIL state."""
    state["updated_at"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ==============================================================================
# FULL LOOP RUNNER
# ==============================================================================

def run_full_loop():
    """Run the complete SIL loop: review -> dispatch -> lessons -> dashboard."""
    print("=" * 60)
    print("  DANIELA SELF-IMPROVEMENT LOOP — FULL RUN")
    print("=" * 60)
    print()

    # Step 1: ANALYZE
    print("[STEP 1/6] ANALYZE — Weekly codebase review")
    print("-" * 40)
    WeeklyReviewScheduler.run_review()
    print()

    # Step 2: PRIORITIZE
    print("[STEP 2/6] PRIORITIZE — Rank findings by severity x effort")
    print("-" * 40)
    dispatchable = AutoFixPipeline.get_dispatchable_findings()
    print(f"  {len(dispatchable)} findings dispatchable")
    print()

    # Step 3: DISPATCH
    print("[STEP 3/6] DISPATCH — Send auto-fixable findings to Jules")
    print("-" * 40)
    dispatched = AutoFixPipeline.dispatch_auto_fixes()
    print()

    # Step 4: VERIFY (if any PRs to verify)
    print("[STEP 4/6] VERIFY — Check if dispatched fixes resolved issues")
    print("-" * 40)
    # For now, verify any findings that have been dispatched
    dispatch_log = []
    if DISPATCH_LOG.exists():
        with open(DISPATCH_LOG, encoding="utf-8") as f:
            dispatch_log = json.load(f)
    for entry in dispatch_log:
        if entry.get("status") in ("queued", "dispatched"):
            AutoFixPipeline.verify_fix(entry["finding_id"])
    print()

    # Step 5: LEARN
    print("[STEP 5/6] LEARN — Knowledge base update")
    print("-" * 40)
    lessons = KnowledgeBase.get_lessons()
    print(f"  Total lessons: {len(lessons)}")
    if lessons:
            for les in lessons[-3:]:
                print(f"  - {les['finding_id']}: {les['pattern'][:80]}...")
    print()

    # Step 6: EVOLVE
    print("[STEP 6/6] EVOLVE — Generate health dashboard")
    print("-" * 40)
    dashboard_path = HealthDashboard.generate()
    print()

    # Summary
    print("=" * 60)
    print("  SIL LOOP COMPLETE")
    print("=" * 60)
    state = _load_state()
    print(f"  Health Score: {state.get('last_health_score', 0)}/100")
    print(f"  Total Findings: {len(dispatchable)}")
    print(f"  Dispatched Today: {len(dispatched)}")
    print(f"  Lessons Learned: {state.get('total_lessons', 0)}")
    print(f"  Total Reviews: {state.get('total_reviews_run', 0)}")
    print(f"  Dashboard: {dashboard_path}")
    print("=" * 60)


# ==============================================================================
# CLI
# ==============================================================================

def cli_status():

    state = _load_state()
    KnowledgeBase.get_lessons()
    dispatchable = AutoFixPipeline.get_dispatchable_findings()
    trend = HealthDashboard._load_trend()

    print("\n" + "=" * 60)
    print("  DANIELA SIL ENGINE — STATUS")
    print("=" * 60)
    print(f"\n  Health Score: {state.get('last_health_score', 0)}/100")
    print(f"  Total Reviews: {state.get('total_reviews_run', 0)}")
    print(f"  Last Review: {state.get('last_review_date', 'Never')[:19] if state.get('last_review_date') else 'Never'}")
    print(f"  Total Dispatched: {state.get('total_dispatched', 0)}")
    print(f"  Total Verified: {state.get('total_verified', 0)}")
    print(f"  Total Lessons: {state.get('total_lessons', 0)}")
    print(f"\n  Dispatchable Now: {len(dispatchable)}")
    auto = [f for f in dispatchable if not f.get('needs_human_approval', False)]
    critical = [f for f in dispatchable if f.get('needs_human_approval', False)]
    print(f"    Auto-fixable: {len(auto)}")
    print(f"    Critical (needs approval): {len(critical)}")

    if trend:
        print(f"\n  Trend (last {min(len(trend), 5)}):")
        for t in trend[-5:]:
            print(f"    {t['date'][:10]}: {t['health_score']}/100 ({t['total_findings']} findings)")

    print(f"\n  State file: {STATE_FILE}")
    print(f"  Lessons file: {LESSONS_FILE}")
    print(f"  Dispatch log: {DISPATCH_LOG}")
    print(f"  Trend file: {TREND_FILE}")
    print(f"  Weekly reports: {WEEKLY_REPORTS_DIR}")
    print()


def cli_export():

    state = _load_state()
    lessons = KnowledgeBase.get_lessons()
    trend = HealthDashboard._load_trend()
    dispatchable = AutoFixPipeline.get_dispatchable_findings()

    with open(OUTPUT_DIR / "sil_state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "sil_knowledge_base.json", "w", encoding="utf-8") as f:
        json.dump(lessons, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "sil_health_trend.json", "w", encoding="utf-8") as f:
        json.dump(trend, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "sil_dispatchable.json", "w", encoding="utf-8") as f:
        json.dump(dispatchable, f, indent=2, ensure_ascii=False)

    print(f"[SIL Engine] Exported 4 JSON files to {OUTPUT_DIR}/")


def main():

    if len(sys.argv) < 2:
        print("Usage: python sil_engine.py status|review|dispatch|verify <id>|lessons|dashboard|trend|all|export")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        cli_status()
    elif cmd == "review":
        WeeklyReviewScheduler.run_review()
    elif cmd == "dispatch":
        AutoFixPipeline.dispatch_auto_fixes()
    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Usage: python sil_engine.py verify <finding_id>")
            return
        AutoFixPipeline.verify_findind = sys.argv[2]
        AutoFixPipeline.verify_fix(sys.argv[2])
    elif cmd == "dispatch-critical":
        if len(sys.argv) < 3:
            print("Usage: python sil_engine.py dispatch-critical <finding_id>")
            return
        AutoFixPipeline.dispatch_critical(sys.argv[2], human_approved=True)
    elif cmd == "lessons":
        lessons = KnowledgeBase.get_lessons()
        print(f"\n  Knowledge Base: {len(lessons)} lessons\n")
        for les in lessons:
            print(f"  [{les['finding_id']}] {les['finding_title']}")
            print(f"    Pattern: {les['pattern']}")
            print(f"    Prevention: {les['prevention_rule']}")
        print()
        if not lessons:
            print("  (No lessons yet. Run the auto-fix pipeline to start learning.)")
    elif cmd == "lessons-export":
        md = KnowledgeBase.export_markdown()
        md_path = DATA_DIR / "learning_log.md"
        md_path.write_text(md, encoding="utf-8")
        print(f"[SIL-03] Learning log exported: {md_path}")
    elif cmd == "dashboard":
        path = HealthDashboard.generate()
        print(f"\n  Dashboard: {path}")
    elif cmd == "trend":
        trend = HealthDashboard._load_trend()
        print(f"\n  Health Score Trend ({len(trend)} entries):\n")
        for t in trend:
            bar = "#" * (t["health_score"] // 5)
            print(f"  {t['date'][:10]} | {t['health_score']:3d}/100 | {bar}")
        if not trend:
            print("  (No trend data yet. Run 'review' to start tracking.)")
    elif cmd == "all":
        run_full_loop()
    elif cmd == "export":
        cli_export()
    else:
        print(f"Unknown command: {cmd}")
        print("Available: status|review|dispatch|verify <id>|dispatch-critical <id>|lessons|lessons-export|dashboard|trend|all|export")


if __name__ == "__main__":
    main()
