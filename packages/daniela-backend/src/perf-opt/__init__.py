


def register_perf(app):
    from async_io.async_io import async_bp
    from async_io.websocket_realtime import ws_bp
    from performance.bg_workers import worker_bp
    from performance.brotli_compression import brotli_bp
    from performance.connection_keepalive import ka_bp
    from performance.http2_server import http2_bp
    from quality.auto_formatting import fmt_bp
    from quality.ci_cd import ci_bp
    from quality.test_coverage import tc_bp
    from quality.type_hints import th_bp
    for bp in [async_bp, ws_bp, worker_bp, http2_bp, brotli_bp, ka_bp, th_bp, fmt_bp, tc_bp, ci_bp]:
        app.register_blueprint(bp)
