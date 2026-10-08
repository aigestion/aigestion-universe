from flask import Blueprint, jsonify

gql_bp = Blueprint("graphql_endpoint", __name__)

@gql_bp.route("/api/infra/api/graphql/status")
def g_status():
    return jsonify({"endpoint": "/v1/graphql", "engine": "Apollo-like", "queries": 15, "schema": "available"})

@gql_bp.route("/api/infra/api/graphql/web")
def g_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>GraphQL</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>GRAPHQL ENDPOINT</h1>
<div class="card"><h3>Endpoint</h3><p>/v1/graphql</p></div>
<div class="card"><h3>Engine</h3><p>Apollo-like</p></div>
<div class="card"><h3>Queries</h3><p>15 defined</p></div>
<div class="card"><h3>Schema</h3><p>Available</p></div></body></html>"""
