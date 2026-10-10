#!/usr/bin/env python3
"""
aig Analytics v1.0
=========================
Sistema de analytics y reporting:
- Tracking de uso en tiempo real
- Metricas de negocio (MRR, churn, LTV)
- Reportes automaticos
- Dashboard de metricas

Autor: aig Team
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class AnalyticsEngine:
    """Motor de analytics para aig."""

    def __init__(self):
        self.auth_db = "aig_auth.db"
        self.billing_db = "billing.db"

    def _query_auth(self, query: str, params: tuple = ()) -> list[Any]:
        if not Path(self.auth_db).exists():
            return []
        conn = sqlite3.connect(self.auth_db)
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return rows

    def _query_billing(self, query: str, params: tuple = ()) -> list[Any]:
        if not Path(self.billing_db).exists():
            return []
        conn = sqlite3.connect(self.billing_db)
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return rows

    # ── Usage Metrics ─────────────────────────────────────────

    def get_usage_over_time(self, days: int = 30) -> list[dict[str, Any]]:
        """Requests por dia."""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self._query_auth("""
            SELECT DATE(timestamp) as day, COUNT(*) as requests
            FROM usage_log WHERE timestamp > ? GROUP BY day ORDER BY day
        """, (since,))
        return [{"date": r[0], "requests": r[1]} for r in rows]

    def get_top_modules(self, limit: int = 10) -> list[dict[str, Any]]:
        """Modulos mas usados."""
        rows = self._query_auth("""
            SELECT module, COUNT(*) as count FROM usage_log
            WHERE module != '' GROUP BY module ORDER BY count DESC LIMIT ?
        """, (limit,))
        return [{"module": r[0] or "unknown", "requests": r[1]} for r in rows]

    def get_top_users(self, limit: int = 10) -> list[dict[str, Any]]:
        """Usuarios mas activos."""
        rows = self._query_auth("""
            SELECT user_id, COUNT(*) as requests FROM usage_log
            GROUP BY user_id ORDER BY requests DESC LIMIT ?
        """, (limit,))
        return [{"user_id": r[0][:8] + "...", "requests": r[1]} for r in rows]

    def get_average_requests_per_user(self, days: int = 30) -> float:
        """Promedio de requests por usuario."""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self._query_auth("""
            SELECT COUNT(DISTINCT user_id) as users, COUNT(*) as requests
            FROM usage_log WHERE timestamp > ?
        """, (since,))
        if not rows or rows[0][0] == 0:
            return 0.0
        return round(rows[0][1] / rows[0][0], 2)

    # ── Business Metrics ──────────────────────────────────────

    def get_mrr_breakdown(self) -> dict[str, Any]:
        """Desglose de MRR."""
        rows = self._query_billing("""
            SELECT tier, COUNT(*) as count FROM subscriptions
            WHERE status = 'active' GROUP BY tier
        """)
        tiers = {"free": 0, "pro": 29, "enterprise": 99}
        mrr = 0
        breakdown = {}
        for r in rows:
            tier, count = r[0], r[1]
            price = tiers.get(tier, 0)
            contribution = price * count
            mrr += contribution
            breakdown[tier] = {"subscribers": count, "price": price, "contribution": contribution}

        return {"mrr": mrr, "currency": "EUR", "breakdown": breakdown}

    def get_churn_rate(self, days: int = 30) -> float:
        """Tasa de churn (suscripciones canceladas / total activas al inicio)."""
        since = (datetime.now() - timedelta(days=days)).isoformat()

        cancelled = self._query_billing(
            "SELECT COUNT(*) FROM subscriptions WHERE status = 'cancelled' AND cancelled_at > ?",
            (since,)
        )
        total = self._query_billing(
            "SELECT COUNT(*) FROM subscriptions WHERE created_at < ?",
            (since,)
        )

        cancelled_count = cancelled[0][0] if cancelled else 0
        total_count = total[0][0] if total else 0

        if total_count == 0:
            return 0.0
        return round((cancelled_count / total_count) * 100, 2)

    def get_conversion_rate(self) -> float:
        """Tasa de conversion free -> paid."""
        total_users = self._query_auth("SELECT COUNT(*) FROM users")
        paid_users = self._query_billing(
            "SELECT COUNT(DISTINCT user_id) FROM subscriptions WHERE tier != 'free' AND status = 'active'"
        )

        total = total_users[0][0] if total_users else 0
        paid = paid_users[0][0] if paid_users else 0

        if total == 0:
            return 0.0
        return round((paid / total) * 100, 2)

    def get_arpu(self) -> float:
        """Average Revenue Per User."""
        mrr_data = self.get_mrr_breakdown()
        total_users = self._query_auth("SELECT COUNT(*) FROM users")
        total = total_users[0][0] if total_users else 0
        if total == 0:
            return 0.0
        return round(mrr_data["mrr"] / total, 2)

    # ── Reportes ──────────────────────────────────────────────

    def generate_daily_report(self) -> dict[str, Any]:
        """Genera reporte diario."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Requests hoy vs ayer
        today_req = self._query_auth(
            "SELECT COUNT(*) FROM usage_log WHERE timestamp LIKE ?", (f"{today}%",)
        )
        yesterday_req = self._query_auth(
            "SELECT COUNT(*) FROM usage_log WHERE timestamp LIKE ?", (f"{yesterday}%",)
        )

        t_count = today_req[0][0] if today_req else 0
        y_count = yesterday_req[0][0] if yesterday_req else 0
        growth = round(((t_count - y_count) / max(y_count, 1)) * 100, 1)

        # Nuevos usuarios hoy
        new_users = self._query_auth(
            "SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (f"{today}%",)
        )

        return {
            "date": today,
            "requests_today": t_count,
            "requests_yesterday": y_count,
            "growth_percent": growth,
            "new_users": new_users[0][0] if new_users else 0,
            "mrr": self.get_mrr_breakdown()["mrr"],
            "top_modules": self.get_top_modules(5),
        }

    def generate_weekly_report(self) -> dict[str, Any]:
        """Genera reporte semanal."""
        daily = self.get_usage_over_time(7)
        total_week = sum(d["requests"] for d in daily)

        return {
            "period": "7 dias",
            "total_requests": total_week,
            "daily_average": round(total_week / 7, 1) if daily else 0,
            "usage_by_day": daily,
            "top_modules": self.get_top_modules(5),
            "top_users": self.get_top_users(5),
            "mrr": self.get_mrr_breakdown()["mrr"],
            "churn_rate": self.get_churn_rate(7),
            "conversion_rate": self.get_conversion_rate(),
            "arpu": self.get_arpu(),
        }

    def generate_monthly_report(self) -> dict[str, Any]:
        """Genera reporte mensual completo."""
        return {
            "period": "30 dias",
            "usage_over_time": self.get_usage_over_time(30),
            "top_modules": self.get_top_modules(10),
            "top_users": self.get_top_users(10),
            "avg_requests_per_user": self.get_average_requests_per_user(30),
            "business_metrics": {
                "mrr": self.get_mrr_breakdown(),
                "churn_rate": self.get_churn_rate(30),
                "conversion_rate": self.get_conversion_rate(),
                "arpu": self.get_arpu(),
            },
        }

    # ── Real-time Dashboard Data ──────────────────────────────

    def get_dashboard_data(self) -> dict[str, Any]:
        """Datos para dashboard en tiempo real."""
        today = datetime.now().strftime("%Y-%m-%d")

        today_req = self._query_auth(
            "SELECT COUNT(*) FROM usage_log WHERE timestamp LIKE ?", (f"{today}%",)
        )
        active_users_now = self._query_auth(
            "SELECT COUNT(DISTINCT user_id) FROM usage_log WHERE timestamp > datetime('now', '-1 hour')"
        )
        total_users = self._query_auth("SELECT COUNT(*) FROM users")

        return {
            "requests_today": today_req[0][0] if today_req else 0,
            "active_users_last_hour": active_users_now[0][0] if active_users_now else 0,
            "total_users": total_users[0][0] if total_users else 0,
            "mrr": self.get_mrr_breakdown()["mrr"],
            "conversion_rate": self.get_conversion_rate(),
            "top_modules": self.get_top_modules(5),
            "timestamp": datetime.now().isoformat(),
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> int:

    import argparse

    parser = argparse.ArgumentParser(description="aig Analytics")
    parser.add_argument("--daily", action="store_true", help="Reporte diario")
    parser.add_argument("--weekly", action="store_true", help="Reporte semanal")
    parser.add_argument("--monthly", action="store_true", help="Reporte mensual")
    parser.add_argument("--dashboard", action="store_true", help="Datos para dashboard")
    parser.add_argument("--mrr", action="store_true", help="MRR breakdown")
    parser.add_argument("--export", help="Exportar reporte a archivo JSON")

    args = parser.parse_args()

    engine = AnalyticsEngine()
    result = None

    if args.daily:
        result = engine.generate_daily_report()
    elif args.weekly:
        result = engine.generate_weekly_report()
    elif args.monthly:
        result = engine.generate_monthly_report()
    elif args.dashboard:
        result = engine.get_dashboard_data()
    elif args.mrr:
        result = engine.get_mrr_breakdown()
    else:
        # Default: dashboard
        result = engine.get_dashboard_data()

    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.export:
        Path(args.export).write_text(output, encoding="utf-8")
        print(f"Reporte exportado a: {args.export}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
