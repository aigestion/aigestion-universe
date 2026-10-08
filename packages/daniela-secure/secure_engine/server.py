"""Secure Engine Flask Server - Port 9880."""

from __future__ import annotations

import time

from flask import Flask, jsonify, request

from .auth_engine import (
    AccountLockout,
    DeviceFingerprint,
    GeoVelocityChecker,
    IPReputationChecker,
    MagicLinkAuth,
    OAuth2Provider,
    SessionManager,
    TOTPAuth,
)
from .compliance import (
    ConsentManager,
    GDPRChecker,
    HIPAAValidator,
    PCIDSSChecklist,
    RightToErasureHandler,
)
from .encryption import AES256Cipher, HashVerifier, PIIMasker, TokenizationService
from .forensics import (
    ChainOfCustody,
    FileAccessMonitor,
    ForensicReportGenerator,
    ImmutableAuditLog,
    UserActivityTracker,
)
from .vulnerability import (
    DependencyScanner,
    HardcodedSecretScanner,
    SQLInjectionDetector,
    XSSScanner,
)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Shared instances
audit_log = ImmutableAuditLog()
auth_provider = OAuth2Provider("client-id", "client-secret", "http://localhost:9880/callback")
totp = TOTPAuth()
magic_link = MagicLinkAuth()
session_mgr = SessionManager()
lockout = AccountLockout()
geo_checker = GeoVelocityChecker()
ip_checker = IPReputationChecker()
device_fp = DeviceFingerprint()

sql_detector = SQLInjectionDetector()
xss_scanner = XSSScanner()
dep_scanner = DependencyScanner()
secret_scanner = HardcodedSecretScanner()

gdpr = GDPRChecker()
hipaa = HIPAAValidator()
pci = PCIDSSChecklist()
consent_mgr = ConsentManager()
erasure_handler = RightToErasureHandler()

cipher = AES256Cipher()
hasher = HashVerifier()
masker = PIIMasker()
tokenizer = TokenizationService()

activity_tracker = UserActivityTracker()
file_monitor = FileAccessMonitor()
chain = ChainOfCustody()
forensic_report = ForensicReportGenerator()


@app.route("/api/secure_engine/status", methods=["GET"])
def status():
    audit_log.append("api_call", "system", {"endpoint": "/status"})
    return jsonify({
        "service": "secure_engine",
        "version": "1.0.0",
        "status": "running",
        "timestamp": time.time(),
        "modules": [
            "auth", "vulnerability", "compliance", "encryption", "forensics",
        ],
    })


# ── Auth endpoints ──────────────────────────────────────────────────────
@app.route("/api/secure_engine/auth", methods=["POST"])
def auth_handler():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    if action == "login":
        user_id = data.get("user_id", "")
        ip = data.get("ip_address", "127.0.0.1")
        check = lockout.record_attempt(user_id, True)
        if not check.get("allowed"):
            audit_log.append("auth_failure", user_id, {"reason": check["reason"]})
            return jsonify(check), 429
        session = session_mgr.create_session(user_id, ip, data.get("user_agent", ""))
        audit_log.append("login", user_id, {"session_id": session["session_id"]})
        return jsonify(session)

    elif action == "mfa_generate":
        user_id = data.get("user_id", "user")
        code = totp.generate_totp()
        backup_codes = totp.generate_backup_codes(user_id)
        return jsonify({"totp_code": code, "backup_codes": backup_codes})

    elif action == "mfa_verify":
        code = data.get("code", "")
        valid = totp.verify_totp(code)
        audit_log.append("mfa_verify", data.get("user_id", ""), {"valid": valid})
        return jsonify({"valid": valid})

    elif action == "magic_link":
        user_id = data.get("user_id", "")
        link = magic_link.generate_magic_link(user_id)
        audit_log.append("magic_link_sent", user_id, {})
        return jsonify({"magic_link": link})

    elif action == "session_validate":
        sid = data.get("session_id", "")
        result = session_mgr.validate_session(sid)
        return jsonify({"valid": result is not None, "session": result})

    elif action == "session_invalidate":
        sid = data.get("session_id", "")
        invalidated = session_mgr.invalidate_session(sid)
        return jsonify({"invalidated": invalidated})

    elif action == "lockout_status":
        user_id = data.get("user_id", "")
        return jsonify(lockout.get_status(user_id))

    elif action == "geo_check":
        user_id = data.get("user_id", "")
        lat = data.get("latitude", 0.0)
        lon = data.get("longitude", 0.0)
        return jsonify(geo_checker.record_login(user_id, lat, lon))

    elif action == "ip_check":
        ip = data.get("ip_address", "")
        return jsonify(ip_checker.check_reputation(ip))

    return jsonify({"error": "unknown_action"}), 400


# ── Vulnerability endpoints ─────────────────────────────────────────────
@app.route("/api/secure_engine/vuln", methods=["POST"])
def vuln_handler():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    if action == "scan_sql":
        code = data.get("code", "")
        findings = sql_detector.detect_patterns(code, data.get("filename", "<input>"))
        return jsonify({"findings": findings, "count": len(findings)})

    elif action == "test_sql_input":
        user_input = data.get("input", "")
        return jsonify(sql_detector.test_input(user_input))

    elif action == "scan_xss":
        code = data.get("code", "")
        findings = xss_scanner.scan_code(code, data.get("filename", "<input>"))
        return jsonify({"findings": findings, "count": len(findings)})

    elif action == "sanitize":
        user_input = data.get("input", "")
        return jsonify({"sanitized": xss_scanner.sanitize_output(user_input)})

    elif action == "scan_deps":
        content = data.get("requirements", "")
        deps = dep_scanner.parse_requirements(content)
        results = dep_scanner.scan(deps)
        return jsonify({"vulnerabilities": results, "count": len(results)})

    elif action == "scan_secrets":
        code = data.get("code", "")
        findings = secret_scanner.scan_code(code, data.get("filename", "<input>"))
        return jsonify({"findings": findings, "count": len(findings)})

    elif action == "security_headers":
        headers = data.get("headers", {})
        from .vulnerability import SecurityHeaderAnalyzer
        analyzer = SecurityHeaderAnalyzer()
        return jsonify(analyzer.analyze(headers))

    return jsonify({"error": "unknown_action"}), 400


# ── Compliance endpoints ────────────────────────────────────────────────
@app.route("/api/secure_engine/compliance", methods=["POST"])
def compliance_handler():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    if action == "gdpr_assess":
        org = data.get("organization", "Unknown")
        aid = gdpr.create_assessment(org)
        for req in gdpr.REQUIREMENTS[:5]:
            gdpr.evaluate_requirement(aid, req["id"], True, "Auto-assessed")
        result = gdpr.finalize_assessment(aid)
        return jsonify(result)

    elif action == "hipaa_validate":
        org = data.get("organization", "Unknown")
        vid = hipaa.create_validation(org)
        for category in HIPAAValidator.SAFEGUARDS:
            for sg in HIPAAValidator.SAFEGUARDS[category]:
                hipaa.validate_safeguard(vid, sg["id"], True)
        return jsonify(hipaa.get_summary(vid))

    elif action == "pci_check":
        org = data.get("organization", "Unknown")
        cid = pci.create_checklist(org)
        for req in pci.REQUIREMENTS[:6]:
            pci.evaluate_requirement(cid, req["id"], "pass")
        return jsonify(pci.get_summary(cid))

    elif action == "consent_record":
        uid = data.get("user_id", "")
        ctype = data.get("consent_type", "functional")
        granted = data.get("granted", True)
        return jsonify(consent_mgr.record_consent(uid, ctype, granted))

    elif action == "consent_check":
        uid = data.get("user_id", "")
        ctype = data.get("consent_type", "functional")
        return jsonify(consent_mgr.check_consent(uid, ctype))

    elif action == "erasure_request":
        uid = data.get("user_id", "")
        rid = erasure_handler.submit_request(uid, data.get("reason", ""))
        erasure_handler.process_system(rid, "primary_db", True)
        return jsonify(erasure_handler.finalize_request(rid))

    return jsonify({"error": "unknown_action"}), 400


# ── Encryption endpoints ────────────────────────────────────────────────
@app.route("/api/secure_engine/encrypt", methods=["POST"])
def encrypt_handler():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    if action == "encrypt":
        plaintext = data.get("plaintext", "")
        result = cipher.encrypt(plaintext, data.get("aad", ""))
        audit_log.append("encryption", "api", {"type": "aes256gcm"})
        return jsonify(result)

    elif action == "decrypt":
        result = cipher.decrypt(
            data.get("ciphertext", ""),
            data.get("nonce", ""),
            data.get("aad", ""),
        )
        return jsonify({"plaintext": result})

    elif action == "hash":
        data_val = data.get("data", "")
        algo = data.get("algorithm", "sha256")
        return jsonify({"hash": hasher.hash_data(data_val, algo)})

    elif action == "hash_password":
        password = data.get("password", "")
        h = hasher.hash_password(password)
        return jsonify({"hash": h})

    elif action == "verify_password":
        password = data.get("password", "")
        h = data.get("hash", "")
        return jsonify({"valid": hasher.verify_password(password, h)})

    elif action == "mask":
        text = data.get("text", "")
        return jsonify({"masked": masker.mask(text)})

    elif action == "detect_pii":
        text = data.get("text", "")
        return jsonify({"findings": masker.detect(text)})

    elif action == "tokenize":
        value = data.get("value", "")
        token = tokenizer.tokenize(value, data.get("type", "general"))
        return jsonify({"token": token})

    elif action == "detokenize":
        token = data.get("token", "")
        value = tokenizer.detokenize(token)
        return jsonify({"value": value, "found": value is not None})

    return jsonify({"error": "unknown_action"}), 400


# ── Audit endpoints ─────────────────────────────────────────────────────
@app.route("/api/secure_engine/audit", methods=["POST"])
def audit_handler():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    if action == "log":
        entry = audit_log.append(
            data.get("event_type", "unknown"),
            data.get("actor", "system"),
            data.get("details", {}),
            data.get("resource", ""),
        )
        return jsonify(entry)

    elif action == "search":
        results = audit_log.query(
            event_type=data.get("event_type"),
            actor=data.get("actor"),
            since=data.get("since"),
        )
        return jsonify({"entries": results, "count": len(results)})

    elif action == "verify":
        return jsonify(audit_log.verify_integrity())

    elif action == "activity_track":
        uid = data.get("user_id", "")
        act = activity_tracker.track(uid, data.get("action", ""), data.get("resource", ""))
        return jsonify(act)

    elif action == "activity_summary":
        uid = data.get("user_id", "")
        return jsonify(activity_tracker.get_activity_summary(uid))

    elif action == "file_access":
        fp = file_monitor.log_access(
            data.get("filepath", ""),
            data.get("user", ""),
            data.get("operation", "read"),
        )
        return jsonify(fp)

    elif action == "file_summary":
        return jsonify(file_monitor.get_access_summary())

    elif action == "report_generate":
        rid = forensic_report.generate_report(
            data.get("case_id", "CASE-001"),
            data.get("investigator", "analyst"),
            data.get("summary", ""),
            data.get("findings", []),
            data.get("evidence_ids", []),
        )
        return jsonify({"report_id": rid})

    elif action == "report_get":
        report = forensic_report.get_report(data.get("report_id", ""))
        return jsonify(report)

    return jsonify({"error": "unknown_action"}), 400


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9880, debug=False)
