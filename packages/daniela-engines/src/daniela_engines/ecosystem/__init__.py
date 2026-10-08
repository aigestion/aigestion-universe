"""Ecosystem Engine - 50 Integration & Ecosystem ideas for aig monorepo."""

from .connectors import GraphQLConnector, RESTConnector, WebSocketConnector
from .gateway import APIKeyManager, CircuitBreaker, RateLimiter
from .marketplace import PluginDependencyResolver, PluginMarketplace, PluginRegistry
from .protocol import GraphQLSchemaGenerator, JSONSchemaValidator, OpenAPIGenerator
from .server import create_app
from .transformers import CSVtoJSONTransformer, JSONtoXMLTransformer, YAMLtoJSONTransformer

__version__ = "1.0.0"
__all__ = [
    "PluginRegistry", "PluginMarketplace", "PluginDependencyResolver",
    "RESTConnector", "GraphQLConnector", "WebSocketConnector",
    "JSONtoXMLTransformer", "CSVtoJSONTransformer", "YAMLtoJSONTransformer",
    "OpenAPIGenerator", "GraphQLSchemaGenerator", "JSONSchemaValidator",
    "RateLimiter", "CircuitBreaker", "APIKeyManager",
    "create_app",
]
