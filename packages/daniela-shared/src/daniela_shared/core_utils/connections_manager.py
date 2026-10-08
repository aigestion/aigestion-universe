"""Connections Manager — panel central de todas las integraciones API.

Lee .env + data/connections.json, expone estado de cada provider,
permite actualizar keys, y ejecuta health checks.

CLI: python connections_manager.py status|check|update PROVIDER KEY=VAL
Rutas: GET/POST /api/connections, POST /api/connections/PROVIDER
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
STORE = _REPO_ROOT / "data" / "connections.json"
ENV_FILE = _REPO_ROOT / ".env"
VAULT_DIR = _REPO_ROOT / "data" / "content"


# ── Catalogo maestro de providers ─────────────────────────────────────────────

PROVIDERS: dict[str, dict[str, Any]] = {
    # ── AI / LLM ──────────────────────────────────────────────────────────────
    "gemini": {
        "nombre": "Google Gemini",
        "icono": "✦",
        "color": "#4285F4",
        "categoria": "ai",
        "vars": ["GEMINI_API_KEY"],
        "test_url": "https://generativelanguage.googleapis.com/v1beta/models?key=",
        "test_field": "models",
        "docs": "https://aistudio.google.com/apikey",
        "gratis": True,
    },
    "groq": {
        "nombre": "Groq (Llama 3.3)",
        "icono": "⚡",
        "color": "#F55036",
        "categoria": "ai",
        "vars": ["GROQ_API_KEY"],
        "test_url": "https://api.groq.com/openai/v1/models",
        "test_header": "Authorization: Bearer ",
        "docs": "https://console.groq.com/keys",
        "gratis": True,
    },
    "openrouter": {
        "nombre": "OpenRouter",
        "icono": "🔀",
        "color": "#6366F1",
        "categoria": "ai",
        "vars": ["OPENROUTER_API_KEY"],
        "test_url": "https://openrouter.ai/api/v1/models",
        "test_header": "Authorization: Bearer ",
        "docs": "https://openrouter.ai/keys",
        "gratis": True,
    },
    "openai": {
        "nombre": "OpenAI",
        "icono": "◉",
        "color": "#10A37F",
        "categoria": "ai",
        "vars": ["OPENAI_API_KEY"],
        "test_url": "https://api.openai.com/v1/models",
        "test_header": "Authorization: Bearer ",
        "docs": "https://platform.openai.com/api-keys",
        "gratis": False,
    },
    "anthropic": {
        "nombre": "Anthropic (Claude)",
        "icono": "◈",
        "color": "#D97706",
        "categoria": "ai",
        "vars": ["ANTHROPIC_API_KEY"],
        "test_url": "https://api.anthropic.com/v1/models",
        "test_header": "x-api-key: ",
        "docs": "https://console.anthropic.com/settings/keys",
        "gratis": False,
    },
    "deepseek": {
        "nombre": "DeepSeek",
        "icono": "🌊",
        "color": "#0EA5E9",
        "categoria": "ai",
        "vars": ["DEEPSEEK_API_KEY"],
        "test_url": "https://api.deepseek.com/models",
        "test_header": "Authorization: Bearer ",
        "docs": "https://platform.deepseek.com/api_keys",
        "gratis": True,
    },
    "qwen": {
        "nombre": "Qwen / DashScope (Alibaba)",
        "icono": "🇨🇳",
        "color": "#615CED",
        "categoria": "ai",
        "vars": ["QWEN_API_KEY", "DASHSCOPE_API_KEY"],
        "test_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/models",
        "test_header": "Authorization: Bearer ",
        "docs": "https://dashscope.console.aliyun.com/",
        "gratis": True,
    },
    "tencent_hunyuan": {
        "nombre": "Tencent Hunyuan",
        "icono": "🐧",
        "color": "#0052D9",
        "categoria": "ai",
        "vars": ["TENCENT_HUNYUAN_API_KEY"],
        "test_url": "https://tokenhub-us.tencentcloudmaas.com/v1/models",
        "test_header": "Authorization: Bearer ",
        "docs": "https://cloud.tencent.com/product/hunyuan",
        "gratis": True,
    },
    "cohere": {
        "nombre": "Cohere",
        "icono": "◆",
        "color": "#39D98A",
        "categoria": "ai",
        "vars": ["COHERE_API_KEY"],
        "docs": "https://dashboard.cohere.com/api-keys",
        "gratis": True,
    },
    "huggingface": {
        "nombre": "Hugging Face",
        "icono": "🤗",
        "color": "#FFD21E",
        "categoria": "ai",
        "vars": ["HF_TOKEN", "HUGGINGFACE_API_KEY"],
        "docs": "https://huggingface.co/settings/tokens",
        "gratis": True,
    },
    "mistral": {
        "nombre": "Mistral AI",
        "icono": "🌀",
        "color": "#FF7000",
        "categoria": "ai",
        "vars": ["MISTRAL_API_KEY"],
        "docs": "https://console.mistral.ai/api-keys/",
        "gratis": True,
    },
    "grok": {
        "nombre": "Grok (xAI)",
        "icono": "🤖",
        "color": "#1DA1F2",
        "categoria": "ai",
        "vars": ["GROK_API_KEY"],
        "docs": "https://console.x.ai",
        "gratis": False,
    },
    # ── GOOGLE SERVICES ───────────────────────────────────────────────────────
    "google_oauth": {
        "nombre": "Google OAuth (Gmail/Drive/Calendar)",
        "icono": "📧",
        "color": "#EA4335",
        "categoria": "google",
        "vars": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        "oauth": True,
        "oauth_scopes": [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/documents",
        ],
        "docs": "https://console.cloud.google.com/apis/credentials",
    },
    "youtube": {
        "nombre": "YouTube Data API",
        "icono": "▶",
        "color": "#FF0000",
        "categoria": "google",
        "vars": ["GOOGLE_PERSONAL_YOUTUBE_API_KEY"],
        "docs": "https://console.cloud.google.com/apis/library/youtube.googleapis.com",
    },
    # ── COMUNICACION ──────────────────────────────────────────────────────────
    "telegram": {
        "nombre": "Telegram Bot",
        "icono": "✈",
        "color": "#0088CC",
        "categoria": "comunicacion",
        "vars": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
        "test_url": "https://api.telegram.org/bot{TOKEN}/getMe",
        "docs": "https://t.me/BotFather",
        "gratis": True,
    },
    "elevenlabs": {
        "nombre": "ElevenLabs (TTS)",
        "icono": "🎙",
        "color": "#8B5CF6",
        "categoria": "comunicacion",
        "vars": ["ELEVENLABS_API_KEY"],
        "test_url": "https://api.elevenlabs.io/v1/user",
        "test_header": "xi-api-key: ",
        "docs": "https://elevenlabs.io/app/settings/api-keys",
    },
    "vapi": {
        "nombre": "Vapi (Voice AI)",
        "icono": "📞",
        "color": "#06B6D4",
        "categoria": "comunicacion",
        "vars": ["VAPI_PRIVATE_KEY", "VAPI_PUBLIC_KEY"],
        "docs": "https://dashboard.vapi.ai/settings",
    },
    "twilio": {
        "nombre": "Twilio (SMS/Voice)",
        "icono": "📱",
        "color": "#F22F46",
        "categoria": "comunicacion",
        "vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
        "docs": "https://console.twilio.com",
    },
    "sendgrid": {
        "nombre": "SendGrid (Email)",
        "icono": "📨",
        "color": "#1A82E2",
        "categoria": "comunicacion",
        "vars": ["TWILIO_SENDGRID_API_KEY"],
        "docs": "https://app.sendgrid.com/settings/api_keys",
    },
    # ── SOCIAL MEDIA ──────────────────────────────────────────────────────────
    "meta": {
        "nombre": "Meta (Facebook/Instagram)",
        "icono": "📘",
        "color": "#0668E1",
        "categoria": "social",
        "vars": ["META_APP_ID", "META_APP_SECRET", "FACEBOOK_PAGE_ID"],
        "oauth": True,
        "docs": "https://developers.facebook.com",
    },
    "linkedin": {
        "nombre": "LinkedIn",
        "icono": "💼",
        "color": "#0A66C2",
        "categoria": "social",
        "vars": ["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"],
        "oauth": True,
        "docs": "https://www.linkedin.com/developers/apps",
    },
    "tiktok": {
        "nombre": "TikTok",
        "icono": "🎵",
        "color": "#000000",
        "categoria": "social",
        "vars": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
        "oauth": True,
        "docs": "https://developers.tiktok.com",
    },
    "snapchat": {
        "nombre": "Snapchat",
        "icono": "👻",
        "color": "#FFFC00",
        "categoria": "social",
        "vars": ["SNAPCHAT_CLIENT_ID", "SNAPCHAT_CLIENT_SECRET"],
        "oauth": True,
        "docs": "https://developers.snap.com",
    },
    # ── DEPLOY / DEVOPS ───────────────────────────────────────────────────────
    "github": {
        "nombre": "GitHub",
        "icono": "🐙",
        "color": "#6e40c9",
        "categoria": "devops",
        "vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "test_url": "https://api.github.com/user",
        "test_header": "Authorization: token ",
        "docs": "https://github.com/settings/tokens",
        "gratis": True,
    },
    "vercel": {
        "nombre": "Vercel",
        "icono": "▲",
        "color": "#000000",
        "categoria": "devops",
        "vars": ["VERCEL_AUTH_TOKEN"],
        "docs": "https://vercel.com/account/tokens",
    },
    "netlify": {
        "nombre": "Netlify",
        "icono": "◆",
        "color": "#00C7B7",
        "categoria": "devops",
        "vars": ["NETLIFY_TOKEN"],
        "docs": "https://app.netlify.com/user/applications#personal-access-tokens",
    },
    # ── BASE DE DATOS ─────────────────────────────────────────────────────────
    "supabase": {
        "nombre": "Supabase",
        "icono": "⚡",
        "color": "#3ECF8E",
        "categoria": "datos",
        "vars": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_JWT_SECRET"],
        "docs": "https://supabase.com/dashboard/account/tokens",
    },
    "mongodb": {
        "nombre": "MongoDB Atlas",
        "icono": "🍃",
        "color": "#47A248",
        "categoria": "datos",
        "vars": ["MONGODB_ATLAS_URI"],
        "docs": "https://cloud.mongodb.com",
    },
    "pinecone": {
        "nombre": "Pinecone (Vector DB)",
        "icono": "🌲",
        "color": "#000000",
        "categoria": "datos",
        "vars": ["PINECONE_API_KEY", "PINECONE_INDEX"],
        "docs": "https://app.pinecone.io",
    },
    "redis": {
        "nombre": "Redis / Upstash",
        "icono": "🔴",
        "color": "#DC382D",
        "categoria": "datos",
        "vars": ["REDIS_URL"],
        "docs": "https://upstash.com",
    },
    # ── PAGOS ─────────────────────────────────────────────────────────────────
    "stripe": {
        "nombre": "Stripe",
        "icono": "💳",
        "color": "#635BFF",
        "categoria": "pagos",
        "vars": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"],
        "docs": "https://dashboard.stripe.com/apikeys",
    },
    # ── MONITORIZACION ────────────────────────────────────────────────────────
    "sentry": {
        "nombre": "Sentry (Error Tracking)",
        "icono": "🐛",
        "color": "#362D59",
        "categoria": "monitoring",
        "vars": ["SENTRY_DSN_NEXUS"],
        "docs": "https://sentry.io",
    },
    "nasa": {
        "nombre": "NASA APOD",
        "icono": "🚀",
        "color": "#0B3D91",
        "categoria": "datos",
        "vars": ["NASA_API_KEY"],
        "docs": "https://api.nasa.gov",
        "gratis": True,
    },
    # ── AUTOMATIZACION ────────────────────────────────────────────────────────
    "make": {
        "nombre": "Make (Integromat)",
        "icono": "🔵",
        "color": "#6D00CC",
        "categoria": "automatizacion",
        "vars": ["MAKE_COM_API_KEY"],
        "docs": "https://www.make.com",
    },
    "zapier": {
        "nombre": "Zapier",
        "icono": "⚡",
        "color": "#FF4A00",
        "categoria": "automatizacion",
        "vars": ["ZAPIER_DEPLOY_KEY"],
        "docs": "https://zapier.com",
    },
    # ── WEB3 ──────────────────────────────────────────────────────────────────
    "moralis": {
        "nombre": "Moralis (Web3)",
        "icono": "🔮",
        "color": "#7B3FE4",
        "categoria": "web3",
        "vars": ["MORALIS_WEB3_API_KEY"],
        "docs": "https://admin.moralis.io",
    },
    # ── EMAIL SMTP ────────────────────────────────────────────────────────────
    "smtp_gmail": {
        "nombre": "Gmail SMTP",
        "icono": "📬",
        "color": "#EA4335",
        "categoria": "email",
        "vars": ["GMAIL_PERSONAL", "GMAIL_PERSONAL_PASSWORD"],
        "docs": "https://myaccount.google.com/apppasswords",
    },
}


def _env_get(var: str) -> str:
    """Lee variable de .env sin dependencias externas. Ignora placeholders."""
    val = os.getenv(var, "").strip()
    if val and not val.startswith("YOUR") and not val.startswith("REPLACE_WITH"):
        return val
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            if k.strip() == var and v and not v.startswith("YOUR") and not v.startswith("REPLACE_WITH"):
                return v
    return ""


def _store_load() -> dict[str, Any]:
    if STORE.exists():
        try:
            return json.loads(STORE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _store_save(data: dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str),
                     encoding="utf-8")


def _detect_status(provider_id: str, provider: dict[str, Any]) -> dict[str, Any]:
    """Detecta estado real de una connection: configured / missing / oauth_pending."""
    keys_env = {}
    all_set = True
    for var in provider["vars"]:
        val = _env_get(var)
        keys_env[var] = bool(val)
        if not val:
            all_set = False

    store = _store_load()
    persisted = store.get(provider_id, {})

    if provider.get("oauth") and not all_set:
        estado = "oauth_needed"
    elif all_set:
        estado = persisted.get("estado", "configured")
    else:
        estado = "incomplete"

    return {
        "estado": estado,
        "keys": keys_env,
        "faltantes": [v for v, ok in keys_env.items() if not ok],
        "last_check": persisted.get("last_check"),
        "latency_ms": persisted.get("latency_ms"),
    }


def listar(only_configured: bool = False) -> list[dict[str, Any]]:
    """Lista todos los providers con su estado."""
    out = []
    for pid, prov in PROVIDERS.items():
        det = _detect_status(pid, prov)
        if only_configured and det["estado"] not in ("configured", "oauth_needed"):
            continue
        out.append({
            "id": pid,
            "nombre": prov["nombre"],
            "icono": prov["icono"],
            "color": prov["color"],
            "categoria": prov["categoria"],
            "gratis": prov.get("gratis", False),
            "oauth": prov.get("oauth", False),
            "docs": prov.get("docs", ""),
            **det,
        })
    return out


def detalle(provider_id: str) -> dict[str, Any] | None:
    """Detalle de un provider."""
    if provider_id not in PROVIDERS:
        return None
    prov = PROVIDERS[provider_id]
    det = _detect_status(provider_id, prov)
    return {
        "id": provider_id,
        "nombre": prov["nombre"],
        "icono": prov["icono"],
        "color": prov["color"],
        "categoria": prov["categoria"],
        "gratis": prov.get("gratis", False),
        "oauth": prov.get("oauth", False),
        "oauth_scopes": prov.get("oauth_scopes", []),
        "docs": prov.get("docs", ""),
        **det,
    }


def actualizar(provider_id: str, valores: dict[str, str]) -> dict[str, Any]:
    """Actualiza keys en .env y marca en store."""
    if provider_id not in PROVIDERS:
        return {"ok": False, "error": f"provider '{provider_id}' no existe"}
    prov = PROVIDERS[provider_id]
    env_lines = []
    if ENV_FILE.exists():
        env_lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    for var, val in valores.items():
        if var not in prov["vars"]:
            return {"ok": False, "error": f"var '{var}' no pertenece a {provider_id}"}
        found = False
        for i, line in enumerate(env_lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k == var:
                    env_lines[i] = f"{var}={val}"
                    found = True
                    break
        if not found:
            env_lines.append(f"{var}={val}")

    ENV_FILE.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    store = _store_load()
    store[provider_id] = {
        "estado": "configured",
        "updated_at": datetime.now().isoformat(),
        "keys_set": dict.fromkeys(valores, True),
    }
    _store_save(store)

    return {"ok": True, "provider": provider_id, "vars_updated": list(valores.keys())}


def eliminar(provider_id: str) -> dict[str, Any]:
    """Limpia keys de un provider en .env."""
    if provider_id not in PROVIDERS:
        return {"ok": False, "error": f"provider '{provider_id}' no existe"}
    prov = PROVIDERS[provider_id]
    env_lines = []
    if ENV_FILE.exists():
        env_lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    for var in prov["vars"]:
        for i, line in enumerate(env_lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k == var:
                    env_lines[i] = f"{var}=YOUR_VALUE_HERE"

    ENV_FILE.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    store = _store_load()
    store[provider_id] = {"estado": "missing", "deleted_at": datetime.now().isoformat()}
    _store_save(store)

    return {"ok": True, "provider": provider_id}


def resumen() -> dict[str, Any]:
    """Resumen global de conexiones."""
    todos = listar()
    por_cat = {}
    for c in todos:
        cat = c["categoria"]
        por_cat.setdefault(cat, []).append(c)

    configurados = sum(1 for c in todos if c["estado"] == "configured")
    total = len(todos)
    return {
        "ok": True,
        "total": total,
        "configurados": configurados,
        "incompletos": total - configurados,
        "por_categoria": {
            cat: {
                "total": len(items),
                "configurados": sum(1 for i in items if i["estado"] == "configured"),
            }
            for cat, items in por_cat.items()
        },
        "providers": todos,
    }


def register_connections_routes(app) -> None:
    """Rutas Flask para el panel de conexiones."""

    @app.route("/api/connections")
    def connections_listar():
        from flask import jsonify, request
        solo = request.args.get("configured") == "1"
        return jsonify(listar(only_configured=solo))

    @app.route("/api/connections/resumen")
    def connections_resumen():
        from flask import jsonify
        return jsonify(resumen())

    @app.route("/api/connections/<provider_id>")
    def connections_detalle(provider_id):
        from flask import jsonify
        d = detalle(provider_id)
        if d is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(d)

    @app.route("/api/connections/<provider_id>", methods=["POST"])
    def connections_actualizar(provider_id):
        from flask import jsonify, request
        data = request.get_json(force=True, silent=True) or {}
        r = actualizar(provider_id, data)
        return jsonify(r), (200 if r.get("ok") else 400)

    @app.route("/api/connections/<provider_id>", methods=["DELETE"])
    def connections_eliminar(provider_id):
        from flask import jsonify
        return jsonify(eliminar(provider_id))

    @app.route("/api/connections/<provider_id>/test")
    def connections_test(provider_id):
        """Health check basico de un provider."""
        import urllib.error
        import urllib.request

        from flask import jsonify

        d = detalle(provider_id)
        if d is None:
            return jsonify({"ok": False, "error": "not found"}), 404
        if d["estado"] != "configured":
            return jsonify({"ok": False, "error": "no configurado"})

        prov = PROVIDERS.get(provider_id, {})
        test_url = prov.get("test_url")
        if not test_url:
            return jsonify({"ok": True, "estado": "configured", "test": "sin endpoint de test"})

        api_key = _env_get(prov["vars"][0])
        if "{TOKEN}" in test_url:
            test_url = test_url.replace("{TOKEN}", api_key)

        try:
            req = urllib.request.Request(test_url)
            hdr = prov.get("test_header", "")
            if hdr:
                if hdr.endswith("Bearer "):
                    req.add_header("Authorization", f"Bearer {api_key}")
                elif hdr.endswith("token "):
                    req.add_header("Authorization", f"token {api_key}")
                else:
                    req.add_header(hdr.rstrip(": "), api_key)
            urllib.request.urlopen(req, timeout=10)
            store = _store_load()
            store.setdefault(provider_id, {})
            store[provider_id]["last_check"] = datetime.now().isoformat()
            store[provider_id]["estado"] = "configured"
            _store_save(store)
            return jsonify({"ok": True, "estado": "configured", "latency_ms": 0})
        except urllib.error.HTTPError as e:
            if e.code == 401:
                store = _store_load()
                store.setdefault(provider_id, {})
                store[provider_id]["estado"] = "invalid_key"
                _store_save(store)
                return jsonify({"ok": False, "error": "key invalida", "http": e.code})
            return jsonify({"ok": True, "estado": "configured (HTTP {e.code})"})
        except Exception as e:
            return jsonify({"ok": True, "estado": "configured (sin test: " + str(e)[:80] + ")"})


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Connections Manager")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("status", help="Resumen de todas las conexiones")
    sub.add_parser("list", help="Lista detallada")

    p_up = sub.add_parser("update", help="Actualizar key de un provider")
    p_up.add_argument("provider")
    p_up.add_argument("keyval", nargs="+", help="VAR=value")

    p_rm = sub.add_parser("remove", help="Limpiar keys de un provider")
    p_rm.add_argument("provider")

    args = p.parse_args(argv)
    if args.cmd == "status":
        r = resumen()
        print(json.dumps({k: v for k, v in r.items() if k != "providers"},
                         indent=2, ensure_ascii=False))
        print(f"\nProviders: {r['configurados']}/{r['total']} configurados")
    elif args.cmd == "list":
        for item in listar():
            st = "[OK]" if item["estado"] == "configured" else "[--]" if item["estado"] == "incomplete" else "[!!]"
            free = " [gratis]" if item.get("gratis") else ""
            falt = f" (falta: {', '.join(item['faltantes'])})" if item["faltantes"] else ""
            print(f"  {st} {item['nombre']}{free}{falt}")
    elif args.cmd == "update":
        vals = {}
        for kv in args.keyval:
            if "=" in kv:
                k, v = kv.split("=", 1)
                vals[k] = v
        r = actualizar(args.provider, vals)
        print(json.dumps(r, indent=2))
    elif args.cmd == "remove":
        print(json.dumps(eliminar(args.provider), indent=2))
    else:
        p.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
