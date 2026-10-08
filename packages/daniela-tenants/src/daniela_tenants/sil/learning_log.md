# Daniela's Learning Log

Total lessons: 6

## INTEGRATION

### SR-07: Content factory not connected to Gemini
- **Severity:** high
- **Date:** 2026-09-05T21:57:24.648330
- **Pattern:** When I see content factory not connected to gemini, it means components aren't connected. Fix: Import ModelRouter from gemini35_free_tier.py. Replace stub with router.call('content_generation', prompt).
- **Prevention:** INTEGRATION RULE: Import ModelRouter from gemini35_free_tier.py. Replace stub with router.call('content_generation', prompt).
- **Files:** content_factory_ai.py

### SR-10: Missing aig_adapters.py
- **Severity:** medium
- **Date:** 2026-09-05T21:57:24.692132
- **Pattern:** When I see missing aig_adapters.py, it means components aren't connected. Fix: Create aig_adapters.py mapping intents to real module functions.
- **Prevention:** INTEGRATION RULE: Create aig_adapters.py mapping intents to real module functions.
- **Files:** aig_core.py

## SECURITY

### SR-01: Flask API completely unauthenticated
- **Severity:** critical
- **Date:** 2026-09-05T22:14:03.417594
- **Pattern:** When I see flask api completely unauthenticated, it means there's a security vulnerability. Fix: Import auth_system.py, create @require_auth decorator, apply to all /api/* routes. Issue JWT on PIN verification.
- **Prevention:** SECURITY RULE: Import auth_system.py, create @require_auth decorator, apply to all /api/* routes. Issue JWT on PIN verification.
- **Files:** daniela_os.py

### SR-02: Command injection via string formatting
- **Severity:** critical
- **Date:** 2026-09-05T22:14:03.492100
- **Pattern:** When I see command injection via string formatting, it means there's a security vulnerability. Fix: Use subprocess.run with list args (shell=False). Never pass untrusted data into -c strings.
- **Prevention:** SECURITY RULE: Use subprocess.run with list args (shell=False). Never pass untrusted data into -c strings.
- **Files:** viral_content_factory.py

### SR-03: Unauthenticated database download
- **Severity:** critical
- **Date:** 2026-09-05T22:14:03.499903
- **Pattern:** When I see unauthenticated database download, it means there's a security vulnerability. Fix: Protect with @require_auth and admin-only authorization.
- **Prevention:** SECURITY RULE: Protect with @require_auth and admin-only authorization.
- **Files:** daniela_os.py

### SR-04: Arbitrary file read via indexing
- **Severity:** critical
- **Date:** 2026-09-05T22:14:03.506484
- **Pattern:** When I see arbitrary file read via indexing, it means there's a security vulnerability. Fix: Restrict file reading to sandboxed directory. Validate path starts with ALLOWED_DIR.
- **Prevention:** SECURITY RULE: Restrict file reading to sandboxed directory. Validate path starts with ALLOWED_DIR.
- **Files:** google_free_tier_automations.py
