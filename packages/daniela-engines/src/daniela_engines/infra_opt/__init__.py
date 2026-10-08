


def register_infra(app):
    from api.api_versioning import av_bp
    from api.graphql_endpoint import gql_bp
    from api.grpc_bridge import grpc_bp
    from api.redis_rate_limit import rr_bp
    from api.request_caching import rc_bp
    from database.backup_scheduler import bs_bp
    from database.connection_pool import cp_bp
    from database.query_optimizer import qo_bp
    from database.sqlite_wal import wal_bp
    from database.vector_search import vs_bp
    from docker.auto_healing_v2 import ah_bp
    from docker.docker_compose import dc_bp
    from docker.health_dashboard import health_bp
    from docker.nginx_lb import nginx_bp
    from docker.zero_downtime import ztd_bp
    from monitoring.alert_system import al_bp
    from monitoring.distributed_tracing import dt_bp
    from monitoring.grafana_dashboard import graf_bp
    from monitoring.prometheus_metrics import prom_bp
    from monitoring.structured_logging import sl_bp
    for bp in [dc_bp, nginx_bp, ah_bp, health_bp, ztd_bp, wal_bp, qo_bp, cp_bp, vs_bp, bs_bp, rr_bp, rc_bp, gql_bp, grpc_bp, av_bp, prom_bp, graf_bp, sl_bp, dt_bp, al_bp]:
        app.register_blueprint(bp)
