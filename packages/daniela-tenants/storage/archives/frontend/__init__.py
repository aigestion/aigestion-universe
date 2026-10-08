# -*- coding: utf-8 -*-
"""Unified Frontend Optimization Engine — 24 modules."""
from flask import Flask

from .assets.animation_engine import anim_bp
from .assets.asset_optimizer import assets_bp
from .assets.frontend_cache import cache_bp
from .assets2.font_opt import font_bp
from .assets2.image_opt import img_bp
from .assets2.lazy_loading import lazy_bp

# v2 modules (build/transport)
from .code.code_splitting import split_bp
from .code.tree_shaking import tree_bp
from .perf.perf_monitor import perf_bp
from .perf2.web_workers import worker_bp
from .perf2.webassembly import wasmp_bp
from .render.ssr_engine import ssr_bp
from .security.security import sec_bp

# v1 modules (runtime UX)
from .sw.sw_engine import sw_bp
from .sw.web_manifest import manifest_bp
from .theme.theme_engine import theme_bp
from .ux.command_palette import cmd_bp
from .ux.ux_enhancements import ux_bp
from .ux2.a11y import a11y_bp
from .ux2.analytics import analytics_bp
from .virtual.virtual_scroll import virt_bp
from .web_v2.edge_compute import edge_bp
from .web_v2.http2 import http2_bp
from .web_v2.resource_hints import rh_bp

ALL_BLUEPRINTS = [
    # v1 — Runtime UX
    sw_bp, manifest_bp, virt_bp, perf_bp, assets_bp,
    cache_bp, theme_bp, ux_bp, cmd_bp, anim_bp,
    # v2 — Build/Transport
    split_bp, lazy_bp, worker_bp, ssr_bp, img_bp,
    font_bp, tree_bp, wasmp_bp, edge_bp, a11y_bp,
    sec_bp, analytics_bp, rh_bp, http2_bp,
]

def register_frontend(app):
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)
