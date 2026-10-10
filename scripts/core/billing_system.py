#!/usr/bin/env python3
"""
aig Billing System v1.0
==============================
Sistema de facturacion y suscripciones:
- Tiers: Free, Pro ($29/mes), Enterprise ($99/mes)
- Tracking de uso y limites
- Webhooks para Stripe/PayPal
- Facturacion automatica
- Alerts de limite

Autor: aig Team
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Any

# ── Configuracion ─────────────────────────────────────────────

DB_NAME = "billing.db"
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

TIERS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "daily_requests": 100,
        "concurrent_requests": 2,
        "modules": ["content_factory", "sentiment_dashboard", "email_zero_inbox"],
        "features": ["Web dashboard", "Community support"],
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 29,
        "price_yearly": 290,  # 2 meses gratis
        "daily_requests": 1000,
        "concurrent_requests": 10,
        "modules": "all",
        "features": ["All modules", "API access", "Email support", "Analytics"],
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 99,
        "price_yearly": 990,  # 2 meses gratis
        "daily_requests": -1,  # unlimited
        "concurrent_requests": 50,
        "modules": "all",
        "features": ["All Pro features", "Priority support", "White-label", "SLA 99.9%", "Custom integrations"],
    },
}


# ── Base de Datos ─────────────────────────────────────────────

def init_billing_db() -> None:

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Suscripciones
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            tier TEXT NOT NULL,
            status TEXT DEFAULT 'active',  -- active, cancelled, past_due, paused
            billing_cycle TEXT DEFAULT 'monthly',  -- monthly, yearly
            current_period_start TEXT,
            current_period_end TEXT,
            payment_provider TEXT,
            payment_method_id TEXT,
            created_at TEXT,
            cancelled_at TEXT
        )
    """)

    # Facturas
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            subscription_id TEXT,
            amount REAL,
            currency TEXT DEFAULT 'EUR',
            status TEXT DEFAULT 'pending',  -- pending, paid, failed, refunded
            description TEXT,
            paid_at TEXT,
            created_at TEXT
        )
    """)

    # Pagos
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            invoice_id TEXT,
            user_id TEXT NOT NULL,
            amount REAL,
            currency TEXT DEFAULT 'EUR',
            provider TEXT,
            provider_payment_id TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    # Usage alerts
    c.execute("""
        CREATE TABLE IF NOT EXISTS usage_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            alert_type TEXT,  -- threshold_80, threshold_100, upgrade_suggested
            message TEXT,
            sent_at TEXT,
            acknowledged INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


init_billing_db()


# ── BillingManager ────────────────────────────────────────────

class BillingManager:
    """Gestiona suscripciones, pagos y limites."""

    def __init__(self):
        self.db = DB_NAME

    def _db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db)

    # ── Suscripciones ─────────────────────────────────────────

    def create_subscription(self, user_id: str, tier: str, billing_cycle: str = "monthly", provider: str = "stripe") -> dict[str, Any]:
        """Crea una nueva suscripcion."""
        if tier not in TIERS:
            return {"success": False, "error": "Tier invalido"}

        tier_info = TIERS[tier]
        now = datetime.now()
        if billing_cycle == "yearly":
            period_end = now + timedelta(days=365)
            amount = tier_info["price_yearly"]
        else:
            period_end = now + timedelta(days=30)
            amount = tier_info["price_monthly"]

        sub_id = f"sub_{user_id[:8]}_{int(now.timestamp())}"

        conn = self._db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO subscriptions (id, user_id, tier, status, billing_cycle,
                current_period_start, current_period_end, payment_provider, created_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?)
        """, (sub_id, user_id, tier, billing_cycle, now.isoformat(), period_end.isoformat(), provider, now.isoformat()))

        # Crear factura inicial si es pago
        if amount > 0:
            inv_id = f"inv_{sub_id}"
            c.execute("""
                INSERT INTO invoices (id, user_id, subscription_id, amount, currency, description, created_at)
                VALUES (?, ?, ?, ?, 'EUR', ?, ?)
            """, (inv_id, user_id, sub_id, amount, f"Suscripcion {tier_info['name']} - {billing_cycle}", now.isoformat()))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "subscription_id": sub_id,
            "tier": tier,
            "amount": amount,
            "period_end": period_end.isoformat(),
            "invoice_id": inv_id if amount > 0 else None,
        }

    def get_subscription(self, user_id: str) -> dict[str, Any] | None:
        """Obtiene suscripcion activa del usuario."""
        conn = self._db()
        c = conn.cursor()
        c.execute("""
            SELECT id, tier, status, billing_cycle, current_period_start, current_period_end
            FROM subscriptions WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "tier": row[1],
            "status": row[2],
            "billing_cycle": row[3],
            "period_start": row[4],
            "period_end": row[5],
        }

    def cancel_subscription(self, user_id: str) -> bool:
        """Cancela suscripcion al final del periodo."""
        conn = self._db()
        c = conn.cursor()
        c.execute("""
            UPDATE subscriptions SET status = 'cancelled', cancelled_at = ?
            WHERE user_id = ? AND status = 'active'
        """, (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        return True

    def change_tier(self, user_id: str, new_tier: str) -> dict[str, Any]:
        """Cambia de tier (upgrade/downgrade)."""
        if new_tier not in TIERS:
            return {"success": False, "error": "Tier invalido"}

        # Cancelar suscripcion actual
        self.cancel_subscription(user_id)

        # Crear nueva
        return self.create_subscription(user_id, new_tier)

    # ── Limites y Usage ───────────────────────────────────────

    def check_limits(self, user_id: str, tier_name: str) -> dict[str, Any]:
        """Verifica limites del usuario."""
        tier = TIERS.get(tier_name, TIERS["free"])

        # Obtener uso del dia desde auth db.
        # Antes era "auth.db" a pelo: ruta RELATIVA, o sea la base del
        # DIRECTORIO DE TRABAJO. Lanzado desde la raiz del repo eso creaba (o
        # abria) una base vacia en vez de la buena de `data/`, y el SELECT
        # reventaba con "no such table: usage_log". `core.db_paths` existe justo
        # para resolver la ruta canonica desde este arbol; si no puede, se
        # degrada al nombre relativo en vez de romper.
        try:
            from core.db_paths import AUTH_DB as _AUTH_DB

            auth_db = str(_AUTH_DB)
        except Exception:  # noqa: BLE001
            auth_db = "auth.db"
        conn = sqlite3.connect(auth_db)
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM usage_log WHERE user_id = ? AND timestamp LIKE ?", (user_id, f"{today}%"))
        used_today = c.fetchone()[0]
        conn.close()

        daily_limit = tier["daily_requests"]
        if daily_limit == -1:
            return {
                "tier": tier_name,
                "daily_limit": "unlimited",
                "used_today": used_today,
                "remaining": "unlimited",
                "exceeded": False,
            }

        remaining = max(0, daily_limit - used_today)
        exceeded = used_today >= daily_limit

        return {
            "tier": tier_name,
            "daily_limit": daily_limit,
            "used_today": used_today,
            "remaining": remaining,
            "exceeded": exceeded,
            "percent_used": round((used_today / daily_limit) * 100, 1),
        }

    def suggest_upgrade(self, user_id: str, tier_name: str, used_today: int) -> dict[str, Any] | None:
        """Sugiere upgrade si esta cerca del limite."""
        tier = TIERS.get(tier_name, TIERS["free"])
        daily_limit = tier["daily_requests"]

        if daily_limit == -1:
            return None

        percent = (used_today / daily_limit) * 100

        if percent >= 100:
            return {
                "alert": "limit_reached",
                "message": f"Has alcanzado tu limite diario de {daily_limit} requests. Mejora a Pro para 10x mas.",
                "suggested_tier": "pro",
                "cta": "Upgrade a Pro ($29/mes)",
            }
        elif percent >= 80:
            return {
                "alert": "threshold_80",
                "message": f"Has usado el {percent:.0f}% de tu limite diario ({used_today}/{daily_limit}).",
                "suggested_tier": "pro",
                "cta": "Upgrade a Pro ($29/mes)",
            }

        return None

    # ── Facturas ──────────────────────────────────────────────

    def get_invoices(self, user_id: str) -> list[dict[str, Any]]:
        """Lista facturas del usuario."""
        conn = self._db()
        c = conn.cursor()
        c.execute("""
            SELECT id, amount, currency, status, description, paid_at, created_at
            FROM invoices WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()
        return [
            {"id": r[0], "amount": r[1], "currency": r[2], "status": r[3], "description": r[4], "paid_at": r[5], "created_at": r[6]}
            for r in rows
        ]

    def record_payment(self, invoice_id: str, provider_payment_id: str, provider: str = "stripe") -> bool:
        """Registra un pago recibido."""
        conn = self._db()
        c = conn.cursor()

        # Obtener info de factura
        c.execute("SELECT user_id, amount, currency FROM invoices WHERE id = ?", (invoice_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False

        user_id, amount, currency = row

        # Crear registro de pago
        pay_id = f"pay_{provider_payment_id[:10]}"
        now = datetime.now().isoformat()
        c.execute("""
            INSERT INTO payments (id, invoice_id, user_id, amount, currency, provider, provider_payment_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?)
        """, (pay_id, invoice_id, user_id, amount, currency, provider, provider_payment_id, now))

        # Marcar factura como pagada
        c.execute("UPDATE invoices SET status = 'paid', paid_at = ? WHERE id = ?", (now, invoice_id))

        conn.commit()
        conn.close()
        return True

    # ── Stripe Webhook ────────────────────────────────────────

    def handle_stripe_webhook(self, event: dict[str, Any]) -> dict[str, Any]:
        """Procesa eventos de Stripe."""
        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})

        if event_type == "invoice.payment_succeeded":
            sub_id = data.get("subscription", "")
            data.get("payment_intent", "")
            # Actualizar suscripcion
            return {"status": "processed", "type": "payment_succeeded", "subscription": sub_id}

        if event_type == "customer.subscription.deleted":
            sub_id = data.get("id", "")
            # Cancelar suscripcion
            return {"status": "processed", "type": "subscription_cancelled", "subscription": sub_id}

        if event_type == "customer.subscription.updated":
            sub_id = data.get("id", "")
            new_status = data.get("status", "")
            # Actualizar status
            return {"status": "processed", "type": "subscription_updated", "subscription": sub_id, "new_status": new_status}

        return {"status": "ignored", "type": event_type}

    # ── Admin Analytics ───────────────────────────────────────

    def get_mrr(self) -> dict[str, Any]:
        """Monthly Recurring Revenue."""
        conn = self._db()
        c = conn.cursor()

        # Active subscriptions by tier
        c.execute("SELECT tier, COUNT(*) FROM subscriptions WHERE status = 'active' GROUP BY tier")
        tiers_count = {r[0]: r[1] for r in c.fetchall()}

        mrr = sum(TIERS.get(t, {}).get("price_monthly", 0) * count for t, count in tiers_count.items())

        conn.close()
        return {
            "mrr": mrr,
            "active_subscriptions": sum(tiers_count.values()),
            "by_tier": tiers_count,
        }

    def get_revenue_report(self, days: int = 30) -> dict[str, Any]:
        """Reporte de ingresos."""
        conn = self._db()
        c = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute("""
            SELECT SUM(amount), COUNT(*) FROM payments
            WHERE status = 'completed' AND created_at > ?
        """, (since,))
        total, count = c.fetchone()

        conn.close()
        return {
            "period_days": days,
            "total_revenue": total or 0,
            "payments_count": count or 0,
            "currency": "EUR",
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> int:

    import argparse

    parser = argparse.ArgumentParser(description="aig Billing System")
    parser.add_argument("--create-sub", nargs=2, metavar=("USER_ID", "TIER"), help="Crear suscripcion")
    parser.add_argument("--check-limits", nargs=2, metavar=("USER_ID", "TIER"), help="Verificar limites")
    parser.add_argument("--mrr", action="store_true", help="Monthly Recurring Revenue")
    parser.add_argument("--revenue", type=int, default=30, help="Reporte de ingresos (dias)")
    parser.add_argument("--tiers", action="store_true", help="Mostrar tiers disponibles")

    args = parser.parse_args()

    billing = BillingManager()

    if args.tiers:
        print(json.dumps(TIERS, indent=2, ensure_ascii=False))

    if args.create_sub:
        result = billing.create_subscription(args.create_sub[0], args.create_sub[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.check_limits:
        result = billing.check_limits(args.check_limits[0], args.check_limits[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.mrr:
        result = billing.get_mrr()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.revenue:
        result = billing.get_revenue_report(args.revenue)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())

