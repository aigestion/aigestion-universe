#!/usr/bin/env python3
"""
AIGestion White-Label Solution v1.0
====================================
Permite a empresas Enterprise rebrandear AIGestion con:
- Logo y colores personalizados
- Dominio propio
- Nombre de la IA personalizado
- CSS/JS custom
- Subdominios por cliente

Autor: AIGestion Team
"""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

DB_NAME = "whitelabel.db"


def init_db() -> None:

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS whitelabel_configs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            brand_name TEXT,
            logo_url TEXT,
            favicon_url TEXT,
            primary_color TEXT DEFAULT '#0ea5e9',
            secondary_color TEXT DEFAULT '#8b5cf6',
            accent_color TEXT DEFAULT '#22c55e',
            custom_css TEXT,
            custom_js TEXT,
            ai_name TEXT DEFAULT 'Daniela',
            ai_avatar TEXT,
            domain TEXT,
            subdomain TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


@dataclass
class WhiteLabelConfig:
    id: str
    user_id: str
    brand_name: str = "AIGestion"
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#0ea5e9"
    secondary_color: str = "#8b5cf6"
    accent_color: str = "#22c55e"
    custom_css: str = ""
    custom_js: str = ""
    ai_name: str = "Daniela"
    ai_avatar: str = ""
    domain: str = ""
    subdomain: str = ""
    status: str = "active"


class WhiteLabelManager:
    """Gestiona configuraciones white-label para clientes Enterprise."""

    def __init__(self):
        self.db = DB_NAME

    def _db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db)

    def create_config(self, user_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """Crea nueva configuracion white-label."""
        config_id = f"wl_{user_id[:8]}_{int(datetime.now().timestamp())}"
        now = datetime.now().isoformat()

        conn = self._db()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO whitelabel_configs
            (id, user_id, brand_name, logo_url, favicon_url, primary_color, secondary_color,
             accent_color, custom_css, custom_js, ai_name, ai_avatar, domain, subdomain, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                config_id,
                user_id,
                config.get("brand_name", "AIGestion"),
                config.get("logo_url", ""),
                config.get("favicon_url", ""),
                config.get("primary_color", "#0ea5e9"),
                config.get("secondary_color", "#8b5cf6"),
                config.get("accent_color", "#22c55e"),
                config.get("custom_css", ""),
                config.get("custom_js", ""),
                config.get("ai_name", "Daniela"),
                config.get("ai_avatar", ""),
                config.get("domain", ""),
                config.get("subdomain", ""),
                now,
                now,
            ),
        )
        conn.commit()
        conn.close()

        return {"success": True, "config_id": config_id}

    def get_config(self, user_id: str) -> WhiteLabelConfig | None:
        """Obtiene configuracion de un usuario."""
        conn = self._db()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, user_id, brand_name, logo_url, favicon_url, primary_color,
                   secondary_color, accent_color, custom_css, custom_js, ai_name,
                   ai_avatar, domain, subdomain, status
            FROM whitelabel_configs WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1
        """,
            (user_id,),
        )
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        return WhiteLabelConfig(
            id=row[0],
            user_id=row[1],
            brand_name=row[2],
            logo_url=row[3],
            favicon_url=row[4],
            primary_color=row[5],
            secondary_color=row[6],
            accent_color=row[7],
            custom_css=row[8],
            custom_js=row[9],
            ai_name=row[10],
            ai_avatar=row[11],
            domain=row[12],
            subdomain=row[13],
            status=row[14],
        )

    def update_config(self, config_id: str, updates: dict[str, Any]) -> bool:
        """Actualiza configuracion existente."""
        allowed = [
            "brand_name",
            "logo_url",
            "favicon_url",
            "primary_color",
            "secondary_color",
            "accent_color",
            "custom_css",
            "custom_js",
            "ai_name",
            "ai_avatar",
            "domain",
            "subdomain",
        ]

        set_clause = ", ".join([f"{k} = ?" for k in updates if k in allowed])
        if not set_clause:
            return False

        values = [updates[k] for k in updates if k in allowed]
        values.append(datetime.now().isoformat())
        values.append(config_id)

        conn = self._db()
        c = conn.cursor()
        c.execute(
            f"""
            UPDATE whitelabel_configs SET {set_clause}, updated_at = ? WHERE id = ?
        """,
            values,
        )
        conn.commit()
        conn.close()
        return True

    def generate_branded_css(self, config: WhiteLabelConfig) -> str:
        """Genera CSS con los colores de marca del cliente."""
        return f"""
:root {{
    --primary: {config.primary_color};
    --secondary: {config.secondary_color};
    --accent: {config.accent_color};
}}
.logo {{ content: url({config.logo_url}); }}
.ai-name::after {{ content: "{config.ai_name}"; }}
{config.custom_css}
"""

    def generate_branded_html(self, config: WhiteLabelConfig) -> str:
        """Genera HTML de landing page con branding personalizado."""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{config.brand_name} - Powered by AIGestion</title>
<style>
:root{{--primary:{config.primary_color};--secondary:{config.secondary_color};--accent:{config.accent_color};}}
body{{font-family:system-ui;margin:0;padding:40px;text-align:center;background:#0f172a;color:#f1f5f9;}}
h1{{color:var(--primary);font-size:3rem;}}
.sub{{color:#94a3b8;margin:20px 0;}}
.btn{{background:var(--primary);color:#fff;padding:14px 32px;border:none;border-radius:8px;font-size:1.1rem;cursor:pointer;}}
.powered{{position:fixed;bottom:20px;right:20px;color:#64748b;font-size:0.8rem;}}
</style>
</head>
<body>
<img src="{config.logo_url}" alt="{config.brand_name}" style="max-height:80px;margin-bottom:20px;">
<h1>{config.brand_name}</h1>
<p class="sub">Asistente de IA especializado para tu gestoria</p>
<button class="btn">Empezar Ahora</button>
<div class="powered">Powered by AIGestion</div>
{config.custom_js and f"<script>{config.custom_js}</script>" or ""}
</body>
</html>"""


def main() -> int:

    import argparse

    parser = argparse.ArgumentParser(description="AIGestion White-Label")
    parser.add_argument(
        "--create", nargs=2, metavar=("USER_ID", "BRAND"), help="Crear configuracion"
    )
    parser.add_argument("--get", metavar="USER_ID", help="Obtener configuracion")
    parser.add_argument("--generate", metavar="CONFIG_ID", help="Generar HTML branded")
    args = parser.parse_args()

    manager = WhiteLabelManager()

    if args.create:
        result = manager.create_config(args.create[0], {"brand_name": args.create[1]})
        print(json.dumps(result, indent=2))

    if args.get:
        config = manager.get_config(args.get)
        if config:
            print(json.dumps(config.__dict__, indent=2))
        else:
            print("No se encontro configuracion")

    return 0


if __name__ == "__main__":
    sys.exit(main())
