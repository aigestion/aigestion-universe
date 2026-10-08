#!/usr/bin/env python3
"""
Security Headers Middleware for aig Flask Apps
Implements: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
"""

import json
import re

from flask import Flask, Response, request


class SecurityHeadersMiddleware:
    """
    Comprehensive security headers middleware for Flask applications.
    Implements all recommended security headers with strict defaults.
    """

    def __init__(self, app: Flask = None, config: dict = None):
        self.config = config or self._default_config()
        if app:
            self.init_app(app)

    def _default_config(self) -> dict:
        return {
            # Content Security Policy - Strict
            "csp": {
                "default-src": ["'self'"],
                "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                "style-src": ["'self'", "'unsafe-inline'"],
                "img-src": ["'self'", "data:", "https:"],
                "font-src": ["'self'", "https:", "data:"],
                "connect-src": ["'self'", "wss:", "https:"],
                "media-src": ["'self'"],
                "object-src": ["'none'"],
                "frame-src": ["'none'"],
                "frame-ancestors": ["'none'"],
                "form-action": ["'self'"],
                "base-uri": ["'self'"],
                "manifest-src": ["'self'"],
                "worker-src": ["'self'", "blob:"],
                "upgrade-insecure-requests": True,
                "block-all-mixed-content": True,
                "report-uri": "/api/security/csp-report",
                "report-to": "csp-endpoint"
            },

            # HTTP Strict Transport Security
            "hsts": {
                "max_age": 31536000,  # 1 year
                "include_subdomains": True,
                "preload": True
            },

            # X-Frame-Options
            "x_frame_options": "DENY",

            # X-Content-Type-Options
            "x_content_type_options": "nosniff",

            # Referrer Policy
            "referrer_policy": "strict-origin-when-cross-origin",

            # Permissions Policy (Feature Policy)
            "permissions_policy": {
                "accelerometer": [],
                "ambient-light-sensor": [],
                "autoplay": [],
                "battery": [],
                "camera": [],
                "cross-origin-isolated": [],
                "display-capture": [],
                "document-domain": [],
                "encrypted-media": [],
                "execution-while-not-rendered": [],
                "execution-while-out-of-viewport": [],
                "fullscreen": ["'self'"],
                "geolocation": [],
                "gyroscope": [],
                "hid": [],
                "identity-credentials-get": [],
                "idle-detection": [],
                "local-fonts": ["'self'"],
                "magnetometer": [],
                "microphone": [],
                "midi": [],
                "otp-credentials": [],
                "payment": [],
                "picture-in-picture": [],
                "publickey-credentials-create": [],
                "publickey-credentials-get": ["'self'"],
                "screen-wake-lock": [],
                "serial": [],
                "speaker-selection": [],
                "sync-xhr": [],
                "usb": [],
                "web-share": [],
                "window-management": [],
                "xr-spatial-tracking": []
            },

            # Additional security headers
            "cross_origin_embedder_policy": "require-corp",
            "cross_origin_opener_policy": "same-origin",
            "cross_origin_resource_policy": "same-origin",
            "x_dns_prefetch_control": "off",
            "x_download_options": "noopen",
            "x_permitted_cross_domain_policies": "none",

            # Cache control for sensitive pages
            "no_cache_paths": ["/api/auth", "/api/admin", "/api/users", "/login", "/register"],

            # Custom header prefix
            "header_prefix": "X-aig-"
        }

    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        app.before_request(self._process_request)
        app.after_request(self._process_response)

        if self.config["csp"].get("report_uri"):
            app.add_url_rule(
                self.config["csp"]["report_uri"],
                "csp_report",
                self._csp_report_handler,
                methods=["POST"]
            )

    def _process_request(self):
        """Process incoming request - add security context"""

    def _process_response(self, response: Response) -> Response:
        """Add security headers to response"""
        # CSP
        csp_header = self._build_csp_header()
        if csp_header:
            response.headers["Content-Security-Policy"] = csp_header

        # CSP Report-Only for testing
        if self.config["csp"].get("report_only"):
            csp_ro = self._build_csp_header(report_only=True)
            if csp_ro:
                response.headers["Content-Security-Policy-Report-Only"] = csp_ro

        # HSTS
        hsts_header = self._build_hsts_header()
        if hsts_header:
            response.headers["Strict-Transport-Security"] = hsts_header

        # X-Frame-Options
        if self.config.get("x_frame_options"):
            response.headers["X-Frame-Options"] = self.config["x_frame_options"]

        # X-Content-Type-Options
        if self.config.get("x_content_type_options"):
            response.headers["X-Content-Type-Options"] = self.config["x_content_type_options"]

        # Referrer Policy
        if self.config.get("referrer_policy"):
            response.headers["Referrer-Policy"] = self.config["referrer_policy"]

        # Permissions Policy
        permissions_header = self._build_permissions_policy()
        if permissions_header:
            response.headers["Permissions-Policy"] = permissions_header

        # Cross-Origin Policies
        if self.config.get("cross_origin_embedder_policy"):
            response.headers["Cross-Origin-Embedder-Policy"] = self.config["cross_origin_embedder_policy"]
        if self.config.get("cross_origin_opener_policy"):
            response.headers["Cross-Origin-Opener-Policy"] = self.config["cross_origin_opener_policy"]
        if self.config.get("cross_origin_resource_policy"):
            response.headers["Cross-Origin-Resource-Policy"] = self.config["cross_origin_resource_policy"]

        # Additional headers
        if self.config.get("x_dns_prefetch_control"):
            response.headers["X-DNS-Prefetch-Control"] = self.config["x_dns_prefetch_control"]
        if self.config.get("x_download_options"):
            response.headers["X-Download-Options"] = self.config["x_download_options"]
        if self.config.get("x_permitted_cross_domain_policies"):
            response.headers["X-Permitted-Cross-Domain-Policies"] = self.config["x_permitted_cross_domain_policies"]

        # Cache control for sensitive paths
        if self._is_sensitive_path(request.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Custom security headers
        prefix = self.config.get("header_prefix", "X-aig-")
        response.headers[f"{prefix}Security-Headers"] = "enabled"
        response.headers[f"{prefix}CSP-Version"] = "1.0"

        return response

    def _build_csp_header(self, report_only: bool = False) -> str:
        """Build Content-Security-Policy header value"""
        csp_config = self.config["csp"]
        directives = []

        for directive, value in csp_config.items():
            if directive in ["report_uri", "report_to", "upgrade_insecure_requests", "block_all_mixed_content"]:
                continue

            if isinstance(value, list):
                if value:
                    directives.append(f"{directive} {' '.join(value)}")
            elif isinstance(value, bool) and value:
                directives.append(directive.replace("_", "-"))

        if csp_config.get("upgrade_insecure_requests"):
            directives.append("upgrade-insecure-requests")
        if csp_config.get("block_all_mixed_content"):
            directives.append("block-all-mixed-content")
        if csp_config.get("report_uri"):
            directives.append(f"report-uri {csp_config['report_uri']}")
        if csp_config.get("report_to"):
            directives.append(f"report-to {csp_config['report_to']}")

        return "; ".join(directives)

    def _build_hsts_header(self) -> str:
        """Build Strict-Transport-Security header value"""
        hsts = self.config["hsts"]
        parts = [f"max-age={hsts['max_age']}"]
        if hsts.get("include_subdomains"):
            parts.append("includeSubDomains")
        if hsts.get("preload"):
            parts.append("preload")
        return "; ".join(parts)

    def _build_permissions_policy(self) -> str:
        """Build Permissions-Policy header value"""
        policies = self.config.get("permissions_policy", {})
        directives = []

        for feature, allowlist in policies.items():
            if allowlist:
                origins = " ".join(allowlist)
                directives.append(f"{feature}=({origins})")
            else:
                directives.append(f"{feature}=()")

        return ", ".join(directives)

    def _is_sensitive_path(self, path: str) -> bool:
        """Check if path should have no-cache headers"""
        for sensitive in self.config.get("no_cache_paths", []):
            if path.startswith(sensitive):
                return True
        return False

    def _csp_report_handler(self):
        """Handle CSP violation reports"""
        from flask import jsonify, request
        report = request.get_json()
        if report:
            # Log CSP violation
            print(f"[CSP Violation] {json.dumps(report)}")
        return jsonify({"status": "received"}), 204


def create_security_headers_middleware(app: Flask = None, **kwargs) -> SecurityHeadersMiddleware:
    """Factory function to create security headers middleware"""
    return SecurityHeadersMiddleware(app, kwargs)


# Convenience function for quick setup
def secure_flask_app(app: Flask, csp_custom: dict = None, **kwargs) -> Flask:
    """
    Quick secure setup for Flask app.

    Usage:
        app = Flask(__name__)
        secure_flask_app(app)
    """
    config = {
        "csp": {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https:", "data:"],
            "connect-src": ["'self'"],
            "frame-src": ["'none'"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": True,
        }
    }

    if csp_custom:
        for key, value in csp_custom.items():
            if key in config["csp"]:
                if isinstance(config["csp"][key], list) and isinstance(value, list):
                    config["csp"][key].extend(value)
                else:
                    config["csp"][key] = value
            else:
                config["csp"][key] = value

    config.update(kwargs)
    SecurityHeadersMiddleware(app, config)
    return app


# Decorator for excluding paths from specific headers
def exclude_security_headers(*header_names: str):
    """Decorator to exclude specific security headers for a route"""
    def decorator(f):
        f._excluded_security_headers = header_names
        return f
    return decorator


# CSP nonce generator for inline scripts
def generate_csp_nonce() -> str:
    """Generate a random nonce for CSP"""
    import secrets
    return secrets.token_urlsafe(16)


def add_csp_nonce_to_response(response: Response, nonce: str) -> Response:
    """Add nonce to CSP script-src and style-src"""
    csp = response.headers.get("Content-Security-Policy", "")
    if csp:
        csp = re.sub(
            r"(script-src\s+[^;]+)",
            r"\1 'nonce-" + nonce + "'",
            csp
        )
        csp = re.sub(
            r"(style-src\s+[^;]+)",
            r"\1 'nonce-" + nonce + "'",
            csp
        )
        response.headers["Content-Security-Policy"] = csp
    return response


if __name__ == "__main__":
    # Demo usage
    app = Flask(__name__)
    secure_flask_app(app)

    @app.route("/")
    def index():
        return "Secure!"

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    print("Security headers middleware loaded")
    print("Run with: flask run")
