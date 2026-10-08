"""
E-47: Centralized env loading + validation.

Single source of truth: root .env file.
config/.env is deprecated (all placeholders).

Usage:
    from shared.config.env_loader import load_env, validate_env
    load_env()  # loads root .env
    validate_env()  # checks critical keys, fail-loud
"""

import os
from pathlib import Path


def _repo_root():
    """Find the repo root (where .env lives)."""
    # Walk up from this file until we find .env
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / ".env").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path.cwd()


def load_env(override=False):
    """
    Load .env from repo root. Single source of truth.

    Args:
        override: If True, existing env vars are overwritten.
                  If False (default), existing env vars are kept.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return  # dotenv not installed, skip silently

    root = _repo_root()
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=override)


# Critical keys that MUST be set for the system to function
CRITICAL_KEYS = {
    "FREELLMAPI_KEY": "FreeLLMAPI API key for AI chat",
    "FREELLMAPI_URL": "FreeLLMAPI endpoint URL",
}

# Important keys (warn but don't fail)
IMPORTANT_KEYS = {
    "OPENAI_API_KEY": "OpenAI API key",
    "OLLAMA_BASE_URL": "Ollama server URL (default: http://localhost:11434)",
    "REDIS_URL": "Redis connection URL",
}


def validate_env(strict=False):
    """
    Validate that critical env vars are set.

    Args:
        strict: If True, raises ValueError on missing critical keys.
                If False (default), prints warnings.

    Returns:
        dict with "ok", "missing_critical", "missing_important" lists.
    """
    missing_critical = []
    missing_important = []

    for key, desc in CRITICAL_KEYS.items():
        val = os.getenv(key, "").strip()
        if not val or val in ("YOUR_VALUE_HERE", "TODO", "CHANGE_ME"):
            missing_critical.append(f"{key} ({desc})")

    for key, desc in IMPORTANT_KEYS.items():
        val = os.getenv(key, "").strip()
        if not val or val in ("YOUR_VALUE_HERE", "TODO", "CHANGE_ME"):
            missing_important.append(f"{key} ({desc})")

    result = {
        "ok": len(missing_critical) == 0,
        "missing_critical": missing_critical,
        "missing_important": missing_important,
    }

    if missing_critical:
        msg = f"[env] CRITICAL keys missing: {', '.join(missing_critical)}"
        if strict:
            raise ValueError(msg)
        else:
            print(msg)

    if missing_important:
        print(f"[env] Important keys not set: {', '.join(missing_important)}")

    if not missing_critical and not missing_important:
        print("[env] All critical keys present")

    return result


def get_env_summary():
    """Return a summary of env status (no secrets)."""
    all_keys = {**CRITICAL_KEYS, **IMPORTANT_KEYS}
    summary = {}
    for key, _desc in all_keys.items():
        val = os.getenv(key, "")
        if not val:
            summary[key] = "NOT SET"
        elif val in ("YOUR_VALUE_HERE", "TODO", "CHANGE_ME"):
            summary[key] = "PLACEHOLDER"
        else:
            summary[key] = "SET"
    return summary
