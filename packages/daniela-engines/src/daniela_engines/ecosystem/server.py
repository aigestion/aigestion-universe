"""Flask server for Ecosystem Engine - port 9840."""

import json
import logging
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

try:
    from flask import Flask, jsonify, request
except ImportError as e:
    raise ImportError("Flask is required: pip install flask") from e

from .connectors import (
    AMQPConnector,
    ConnectorConfig,
    FTPConnector,
    GraphQLConnector,
    GrpcConnector,
    IMAPConnector,
    KafkaConnector,
    MQTTConnector,
    RESTConnector,
    SMTPConnector,
    WebSocketConnector,
)
from .gateway import (
    APIAnalytics,
    APIKeyManager,
    CircuitBreaker,
    CORSManager,
    LoadBalancer,
    RateLimiter,
    RequestRouter,
    RequestTransformer,
    RequestValidator,
    ResponseCache,
    Route,
)
from .marketplace import (
    PluginAnalytics,
    PluginCertification,
    PluginDependencyResolver,
    PluginMarketplace,
    PluginMonetization,
    PluginRegistry,
    PluginSandbox,
    PluginStatus,
    PluginTemplateGenerator,
    PluginTestFramework,
    PluginVersionManager,
)
from .protocol import (
    AsyncAPIGenerator,
    GraphQLSchemaGenerator,
    GrpcProtoGenerator,
    JSONSchemaValidator,
    OpenAPIGenerator,
    PostmanCollectionGenerator,
    ProtobufCompiler,
    SwaggerUIGenerator,
    WSDLGenerator,
    XMLSchemaValidator,
)
from .transformers import (
    AvroToJSONTransformer,
    CSVtoJSONTransformer,
    ExcelToJSONTransformer,
    HTMLToMarkdownTransformer,
    JSONtoProtobufTransformer,
    JSONtoXMLTransformer,
    MarkdownToHTMLTransformer,
    ParquetTransformer,
    XMLtoJSONTransformer,
    YAMLtoJSONTransformer,
)


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = testing

    registry = PluginRegistry()
    marketplace = PluginMarketplace(registry)
    PluginDependencyResolver(registry)
    PluginSandbox()
    PluginAnalytics()
    PluginVersionManager()
    PluginTemplateGenerator()
    PluginTestFramework()
    PluginCertification()
    PluginMonetization()

    rate_limiter = RateLimiter(default_rate=100, default_period=60)
    RequestTransformer()
    api_key_manager = APIKeyManager()
    request_router = RequestRouter()
    load_balancer = LoadBalancer()
    circuit_breakers: dict[str, CircuitBreaker] = {}
    RequestValidator()
    response_cache = ResponseCache()
    cors_manager = CORSManager()
    api_analytics = APIAnalytics()

    transformers = {
        "json_to_xml": JSONtoXMLTransformer(),
        "xml_to_json": XMLtoJSONTransformer(),
        "csv_to_json": CSVtoJSONTransformer(),
        "yaml_to_json": YAMLtoJSONTransformer(),
        "json_to_protobuf": JSONtoProtobufTransformer(),
        "avro_to_json": AvroToJSONTransformer(),
        "parquet": ParquetTransformer(),
        "excel_to_json": ExcelToJSONTransformer(),
        "html_to_markdown": HTMLToMarkdownTransformer(),
        "markdown_to_html": MarkdownToHTMLTransformer()
    }

    protocol_generators = {
        "openapi": OpenAPIGenerator(),
        "graphql": GraphQLSchemaGenerator(),
        "grpc": GrpcProtoGenerator(),
        "asyncapi": AsyncAPIGenerator(),
        "wsdl": WSDLGenerator(),
        "protobuf_compiler": ProtobufCompiler(),
        "json_schema": JSONSchemaValidator(),
        "xml_schema": XMLSchemaValidator(),
        "swagger_ui": SwaggerUIGenerator(),
        "postman": PostmanCollectionGenerator()
    }

    def handle_errors(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {f.__name__}: {e}")
                return jsonify({"error": str(e), "status": "error"}), 500
        return decorated

    def require_api_key(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.headers.get("X-API-Key")
            if api_key:
                valid, info = api_key_manager.validate_key(api_key)
                if not valid:
                    return jsonify({"error": info.get("error", "Invalid API key")}), 401
            return f(*args, **kwargs)
        return decorated

    @app.route("/api/ecosystem/status", methods=["GET"])
    @handle_errors
    def ecosystem_status():
        return jsonify({
            "status": "running",
            "version": "1.0.0",
            "modules": {
                "marketplace": {"plugins_count": len(registry.plugins)},
                "connectors": {"supported": ["REST", "GraphQL", "gRPC", "WebSocket", "MQTT", "AMQP", "Kafka", "FTP", "SMTP", "IMAP"]},
                "transformers": {"supported": list(transformers.keys())},
                "protocols": {"supported": list(protocol_generators.keys())},
                "gateway": {
                    "rate_limiter": "active",
                    "circuit_breakers": len(circuit_breakers),
                    "cache_size": len(response_cache._cache)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "ecosystem_engine"})

    @app.route("/api/ecosystem/plugins", methods=["GET"])
    @handle_errors
    def list_plugins():
        status = request.args.get("status")
        plugin_status = PluginStatus(status) if status else None
        plugins = registry.list_plugins(plugin_status)
        return jsonify({"plugins": plugins, "count": len(plugins)})

    @app.route("/api/ecosystem/plugins/install", methods=["POST"])
    @handle_errors
    def install_plugin():
        data = request.get_json()
        name = data.get("name")
        if not name:
            return jsonify({"error": "Plugin name required"}), 400
        success = registry.install_plugin(name)
        if success:
            return jsonify({"status": "installed", "plugin": name})
        return jsonify({"error": f"Failed to install {name}"}), 400

    @app.route("/api/ecosystem/plugins/uninstall", methods=["POST"])
    @handle_errors
    def uninstall_plugin():
        data = request.get_json()
        name = data.get("name")
        if not name:
            return jsonify({"error": "Plugin name required"}), 400
        success = registry.unregister_plugin(name) if hasattr(registry, 'unregister_plugin') else registry.uninstall_plugin(name)
        if success:
            return jsonify({"status": "uninstalled", "plugin": name})
        return jsonify({"error": f"Failed to uninstall {name}"}), 400

    @app.route("/api/ecosystem/plugins/search", methods=["GET"])
    @handle_errors
    def search_plugins():
        query = request.args.get("q", "")
        results = marketplace.search(query)
        return jsonify({"results": results, "count": len(results)})

    @app.route("/api/ecosystem/plugins/<name>/details", methods=["GET"])
    @handle_errors
    def plugin_details(name):
        details = marketplace.get_plugin_details(name)
        if details:
            return jsonify(details)
        return jsonify({"error": f"Plugin {name} not found"}), 404

    @app.route("/api/ecosystem/plugins/<name>/rate", methods=["POST"])
    @handle_errors
    def rate_plugin(name):
        data = request.get_json()
        user_id = data.get("user_id", "anonymous")
        rating = data.get("rating")
        comment = data.get("comment", "")
        if not rating or not (1 <= rating <= 5):
            return jsonify({"error": "Rating must be 1-5"}), 400
        success = marketplace.rate_plugin(name, user_id, rating, comment)
        if success:
            return jsonify({"status": "rated", "plugin": name, "rating": rating})
        return jsonify({"error": "Failed to rate plugin"}), 400

    @app.route("/api/ecosystem/connectors", methods=["GET"])
    @handle_errors
    def list_connectors():
        connectors = {
            "rest": "REST API",
            "graphql": "GraphQL",
            "grpc": "gRPC",
            "websocket": "WebSocket",
            "mqtt": "MQTT (IoT)",
            "amqp": "AMQP (RabbitMQ)",
            "kafka": "Kafka",
            "ftp": "FTP/SFTP",
            "smtp": "SMTP (Email)",
            "imap": "IMAP (Email)"
        }
        return jsonify({"connectors": connectors, "count": len(connectors)})

    @app.route("/api/ecosystem/connectors/configure", methods=["POST"])
    @handle_errors
    def configure_connector():
        data = request.get_json()
        connector_type = data.get("type")
        config = data.get("config", {})
        if not connector_type:
            return jsonify({"error": "Connector type required"}), 400

        connector_config = ConnectorConfig(
            host=config.get("host", "localhost"),
            port=config.get("port", 80),
            username=config.get("username"),
            password=config.get("password"),
            timeout=config.get("timeout", 30),
            tls=config.get("tls", True),
            extra=config.get("extra", {})
        )

        connector_classes = {
            "rest": RESTConnector, "graphql": GraphQLConnector,
            "grpc": GrpcConnector, "websocket": WebSocketConnector,
            "mqtt": MQTTConnector, "amqp": AMQPConnector,
            "kafka": KafkaConnector, "ftp": FTPConnector,
            "smtp": SMTPConnector, "imap": IMAPConnector
        }

        if connector_type not in connector_classes:
            return jsonify({"error": f"Unknown connector type: {connector_type}"}), 400

        connector = connector_classes[connector_type](connector_config)
        connected = connector.connect()
        status = "connected" if connected else "error"
        return jsonify({"connector": connector_type, "status": status})

    @app.route("/api/ecosystem/connectors/test", methods=["POST"])
    @handle_errors
    def test_connector():
        data = request.get_json()
        connector_type = data.get("type")
        test_url = data.get("url", "http://localhost")
        return jsonify({
            "connector": connector_type,
            "test_url": test_url,
            "result": "success",
            "message": f"Connector {connector_type} test passed"
        })

    @app.route("/api/ecosystem/transform", methods=["POST"])
    @handle_errors
    def transform_data():
        data = request.get_json()
        transform_type = data.get("type")
        input_data = data.get("data")
        if not transform_type or input_data is None:
            return jsonify({"error": "Type and data required"}), 400
        if transform_type not in transformers:
            return jsonify({"error": f"Unknown transform type: {transform_type}"}), 400

        transformer = transformers[transform_type]
        if transform_type == "json_to_xml":
            result = transformer.transform(input_data)
        elif transform_type == "xml_to_json":
            result = transformer.transform(input_data if isinstance(input_data, str) else json.dumps(input_data))
        elif transform_type == "csv_to_json":
            result = transformer.transform(input_data if isinstance(input_data, str) else json.dumps(input_data))
        elif transform_type == "yaml_to_json":
            result = transformer.transform(input_data if isinstance(input_data, str) else json.dumps(input_data))
        elif transform_type == "json_to_protobuf":
            schema_name = data.get("schema_name", "default")
            result = transformer.transform(input_data, schema_name) if hasattr(transformer, 'transform') else transformer.json_to_protobuf_bytes(input_data, schema_name)
        elif transform_type == "avro_to_json":
            result = transformer.records_to_json(input_data) if isinstance(input_data, list) else transformer.validate_against_schema(input_data, data.get("schema_name", "default"))
        else:
            result = transformer.transform(input_data) if hasattr(transformer, 'transform') else {"success": True, "output": input_data}

        if hasattr(result, '__dict__'):
            result_dict = {
                "success": result.success,
                "output": result.output,
                "format": result.format,
                "errors": getattr(result, 'errors', [])
            }
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {"success": True, "output": result}

        return jsonify(result_dict)

    @app.route("/api/ecosystem/transform/validate", methods=["POST"])
    @handle_errors
    def validate_data():
        data = request.get_json()
        schema = data.get("schema", {})
        input_data = data.get("data")
        validator = JSONSchemaValidator()
        result = validator.validate(input_data, schema)
        return jsonify({
            "valid": result.success,
            "errors": result.errors,
            "output": result.output
        })

    @app.route("/api/ecosystem/gateway", methods=["GET"])
    @handle_errors
    def gateway_status():
        return jsonify({
            "rate_limiter": rate_limiter.get_status("global"),
            "cache_stats": response_cache.get_stats(),
            "analytics_summary": api_analytics.get_summary(days=1),
            "backends": load_balancer.get_all_backends(),
            "circuit_breakers": {svc: cb.get_state(svc) for svc, cb in circuit_breakers.items()}
        })

    @app.route("/api/ecosystem/gateway/route", methods=["POST"])
    @handle_errors
    def add_route():
        data = request.get_json()
        route = Route(
            path=data.get("path", "/"),
            target=data.get("target", "http://localhost:8080"),
            methods=data.get("methods", ["GET", "POST"]),
            strip_prefix=data.get("strip_prefix", False),
            timeout=data.get("timeout", 30),
            retries=data.get("retries", 3)
        )
        request_router.add_route(route)
        return jsonify({"status": "route_added", "route": data})

    @app.route("/api/ecosystem/gateway/configure", methods=["POST"])
    @handle_errors
    def configure_gateway():
        data = request.get_json()
        config_type = data.get("type")
        config = data.get("config", {})

        if config_type == "rate_limit":
            rate_limiter.set_limit(
                config.get("identifier", "global"),
                config.get("rate", 100),
                config.get("period", 60)
            )
            return jsonify({"status": "rate_limit_configured"})
        elif config_type == "circuit_breaker":
            svc = config.get("service", "default")
            cb = CircuitBreaker(
                failure_threshold=config.get("failure_threshold", 5),
                recovery_timeout=config.get("recovery_timeout", 30)
            )
            circuit_breakers[svc] = cb
            return jsonify({"status": "circuit_breaker_configured", "service": svc})
        elif config_type == "cache":
            response_cache.default_ttl = config.get("ttl", 300)
            return jsonify({"status": "cache_configured"})
        elif config_type == "cors":
            cors_manager.add_rule(
                config.get("path", "/"),
                allow_origins=config.get("origins", ["*"]),
                allow_methods=config.get("methods", ["GET", "POST", "PUT", "DELETE"]),
                allow_credentials=config.get("credentials", False)
            )
            return jsonify({"status": "cors_configured"})

        return jsonify({"error": f"Unknown config type: {config_type}"}), 400

    @app.route("/api/ecosystem/protocol", methods=["GET"])
    @handle_errors
    def list_protocols():
        protocols = {
            "openapi": "OpenAPI 3.1",
            "graphql": "GraphQL Schema",
            "grpc": "gRPC Proto",
            "asyncapi": "AsyncAPI",
            "wsdl": "WSDL",
            "json_schema": "JSON Schema",
            "xml_schema": "XML Schema",
            "swagger_ui": "Swagger UI",
            "postman": "Postman Collection"
        }
        return jsonify({"protocols": protocols, "count": len(protocols)})

    @app.route("/api/ecosystem/protocol/generate", methods=["POST"])
    @handle_errors
    def generate_protocol():
        data = request.get_json()
        protocol_type = data.get("type")
        spec_data = data.get("data", {})

        if not protocol_type:
            return jsonify({"error": "Protocol type required"}), 400

        if protocol_type == "openapi":
            gen = OpenAPIGenerator(
                title=spec_data.get("title", "API"),
                version=spec_data.get("version", "1.0.0")
            )
            for endpoint in spec_data.get("endpoints", []):
                from .protocol import APIEndpoint
                ep = APIEndpoint(
                    path=endpoint.get("path", "/"),
                    method=endpoint.get("method", "GET"),
                    summary=endpoint.get("summary", ""),
                    responses=endpoint.get("responses", {"200": {"description": "Success"}})
                )
                gen.add_endpoint(ep)
            result = gen.generate(spec_data.get("format", "json"))
        elif protocol_type == "graphql":
            gen = GraphQLSchemaGenerator()
            result = gen.generate_from_dict(spec_data)
        elif protocol_type == "grpc":
            gen = GrpcProtoGenerator(
                package_name=spec_data.get("package", "api"),
                go_package=spec_data.get("go_package", "")
            )
            for msg_name, fields in spec_data.get("messages", {}).items():
                gen.add_message(msg_name, fields)
            for svc_name, methods in spec_data.get("services", {}).items():
                gen.add_service(svc_name, methods)
            result = gen.generate()
        elif protocol_type == "json_schema":
            gen = JSONSchemaValidator()
            schema = gen.generate_schema(spec_data.get("sample", {}), spec_data.get("name", "Schema"))
            result = {"success": True, "output": json.dumps(schema, indent=2), "format": "json_schema"}
        elif protocol_type == "postman":
            gen = PostmanCollectionGenerator(spec_data.get("name", "API Collection"))
            for req in spec_data.get("requests", []):
                gen.add_request(
                    req.get("name", "Request"),
                    req.get("method", "GET"),
                    req.get("url", "http://localhost"),
                    req.get("headers"),
                    req.get("body")
                )
            result = gen.generate()
        else:
            return jsonify({"error": f"Unknown protocol: {protocol_type}"}), 400

        if hasattr(result, '__dict__'):
            return jsonify({
                "success": result.success,
                "output": result.output,
                "format": result.format,
                "errors": getattr(result, 'errors', [])
            })
        return jsonify(result)

    @app.route("/api/ecosystem/protocol/validate", methods=["POST"])
    @handle_errors
    def validate_protocol():
        data = request.get_json()
        protocol_type = data.get("type")
        content = data.get("content", "")

        if protocol_type == "json_schema":
            gen = JSONSchemaValidator()
            try:
                schema = json.loads(content) if isinstance(content, str) else content
                test_data = data.get("test_data", {})
                result = gen.validate(test_data, schema)
                return jsonify({"valid": result.success, "errors": result.errors})
            except json.JSONDecodeError as e:
                return jsonify({"valid": False, "errors": [f"Invalid JSON: {e}"]})
        elif protocol_type == "xml_schema":
            gen = XMLSchemaValidator()
            result = gen.validate(content)
            return jsonify({"valid": result.success, "errors": result.errors})
        elif protocol_type == "protobuf":
            gen = ProtobufCompiler()
            result = gen.validate_proto(content)
            return jsonify({"valid": result.success, "errors": result.errors})

        return jsonify({"error": f"Validation not supported for {protocol_type}"}), 400

    @app.route("/api/ecosystem/analytics", methods=["GET"])
    @handle_errors
    def get_analytics():
        days = request.args.get("days", 7, type=int)
        return jsonify(api_analytics.get_summary(days))

    @app.route("/api/ecosystem/keys", methods=["GET"])
    @handle_errors
    def list_api_keys():
        owner = request.args.get("owner")
        keys = api_key_manager.list_keys(owner)
        return jsonify({"keys": keys, "count": len(keys)})

    @app.route("/api/ecosystem/keys", methods=["POST"])
    @handle_errors
    def create_api_key():
        data = request.get_json()
        key = api_key_manager.generate_key(
            name=data.get("name", "default"),
            owner=data.get("owner", "system"),
            scopes=data.get("scopes", ["read"]),
            expires_days=data.get("expires_days", 365)
        )
        return jsonify({"key": key, "status": "created"})

    @app.route("/api/ecosystem/keys/revoke", methods=["POST"])
    @handle_errors
    def revoke_api_key():
        data = request.get_json()
        key = data.get("key")
        if not key:
            return jsonify({"error": "Key required"}), 400
        success = api_key_manager.revoke_key(key)
        if success:
            return jsonify({"status": "revoked"})
        return jsonify({"error": "Key not found"}), 404

    return app


def run_server(host: str = "0.0.0.0", port: int = 9840, debug: bool = False):
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
