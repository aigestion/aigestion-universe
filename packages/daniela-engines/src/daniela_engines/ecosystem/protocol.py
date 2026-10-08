"""Protocol adapters - 10 ideas: OpenAPI, GraphQL schema, gRPC proto, AsyncAPI, WSDL, protobuf compiler, JSON Schema, XML Schema, Swagger UI, Postman collection."""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class SchemaFormat(Enum):
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    ASYNCAPI = "asyncapi"
    WSDL = "wsdl"
    JSON_SCHEMA = "json_schema"
    XML_SCHEMA = "xml_schema"


@dataclass
class SchemaResult:
    success: bool
    output: Any
    format: str
    errors: list[str] = field(default_factory=list)


@dataclass
class APIEndpoint:
    path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class OpenAPIGenerator:
    """31. OpenAPI 3.1 spec generator"""

    def __init__(self, title: str = "API", version: str = "1.0.0"):
        self.title = title
        self.version = version
        self.endpoints: list[APIEndpoint] = []
        self.schemas: dict[str, dict[str, Any]] = {}
        self.servers: list[dict[str, str]] = [{"url": "http://localhost:8080"}]
        self.security_schemes: dict[str, dict[str, Any]] = {}

    def add_endpoint(self, endpoint: APIEndpoint):
        self.endpoints.append(endpoint)

    def add_schema(self, name: str, schema: dict[str, Any]):
        self.schemas[name] = schema

    def add_server(self, url: str, description: str = ""):
        self.servers.append({"url": url, "description": description})

    def add_bearer_auth(self, name: str = "bearerAuth"):
        self.security_schemes[name] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }

    def add_api_key_auth(self, name: str = "apiKeyAuth", header: str = "X-API-Key"):
        self.security_schemes[name] = {
            "type": "apiKey",
            "in": "header",
            "name": header
        }

    def generate(self, output_format: str = "json") -> SchemaResult:
        try:
            paths = {}
            for ep in self.endpoints:
                if ep.path not in paths:
                    paths[ep.path] = {}
                operation = {
                    "summary": ep.summary,
                    "description": ep.description,
                    "parameters": ep.parameters,
                    "responses": ep.responses or {"200": {"description": "Success"}}
                }
                if ep.request_body:
                    operation["requestBody"] = ep.request_body
                if ep.tags:
                    operation["tags"] = ep.tags
                paths[ep.path][ep.method.lower()] = operation

            spec = {
                "openapi": "3.1.0",
                "info": {"title": self.title, "version": self.version},
                "servers": self.servers,
                "paths": paths,
                "components": {"schemas": self.schemas}
            }
            if self.security_schemes:
                spec["components"]["securitySchemes"] = self.security_schemes

            if output_format == "yaml":
                output = yaml.dump(spec, default_flow_style=False, sort_keys=False)
            else:
                output = json.dumps(spec, indent=2)

            return SchemaResult(success=True, output=output, format=f"openapi_{output_format}")
        except Exception as e:
            return SchemaResult(success=False, output="", format="openapi", errors=[str(e)])

    def generate_from_functions(self, functions: list[dict[str, Any]]) -> SchemaResult:
        for func in functions:
            params = []
            for pname, ptype in func.get("parameters", {}).items():
                params.append({
                    "name": pname,
                    "in": "query",
                    "schema": {"type": self._python_type_to_openapi(ptype)}
                })
            endpoint = APIEndpoint(
                path=f"/{func['name']}",
                method=func.get("method", "GET"),
                summary=func.get("description", func["name"]),
                parameters=params,
                responses={"200": {"description": "Success"}}
            )
            self.add_endpoint(endpoint)
        return self.generate()

    def _python_type_to_openapi(self, pytype) -> str:
        type_map = {
            str: "string", int: "integer", float: "number",
            bool: "boolean", list: "array", dict: "object"
        }
        return type_map.get(pytype, "string")


class GraphQLSchemaGenerator:
    """32. GraphQL schema generator"""

    def __init__(self):
        self.types: dict[str, dict[str, Any]] = {}
        self.queries: dict[str, dict[str, Any]] = {}
        self.mutations: dict[str, dict[str, Any]] = {}
        self.subscriptions: dict[str, dict[str, Any]] = {}

    def add_type(self, name: str, fields: dict[str, str], description: str = ""):
        self.types[name] = {"fields": fields, "description": description}

    def add_query(self, name: str, return_type: str, args: dict[str, str] | None = None,
                  description: str = ""):
        self.queries[name] = {"return_type": return_type, "args": args or {}, "description": description}

    def add_mutation(self, name: str, return_type: str, args: dict[str, str] | None = None,
                     description: str = ""):
        self.mutations[name] = {"return_type": return_type, "args": args or {}, "description": description}

    def add_subscription(self, name: str, return_type: str, description: str = ""):
        self.subscriptions[name] = {"return_type": return_type, "description": description}

    def generate(self) -> SchemaResult:
        try:
            lines = []
            for type_name, type_def in self.types.items():
                if type_def["description"]:
                    lines.append(f'"""{type_def["description"]}"""')
                lines.append(f"type {type_name} {{")
                for fname, ftype in type_def["fields"].items():
                    lines.append(f"  {fname}: {ftype}")
                lines.append("}")
                lines.append("")

            if self.queries:
                lines.append("type Query {")
                for qname, qdef in self.queries.items():
                    args = ", ".join(f"{k}: {v}" for k, v in qdef["args"].items())
                    args_str = f"({args})" if args else ""
                    lines.append(f"  {qname}{args_str}: {qdef['return_type']}")
                lines.append("}")
                lines.append("")

            if self.mutations:
                lines.append("type Mutation {")
                for mname, mdef in self.mutations.items():
                    args = ", ".join(f"{k}: {v}" for k, v in mdef["args"].items())
                    args_str = f"({args})" if args else ""
                    lines.append(f"  {mname}{args_str}: {mdef['return_type']}")
                lines.append("}")
                lines.append("")

            if self.subscriptions:
                lines.append("type Subscription {")
                for sname, sdef in self.subscriptions.items():
                    lines.append(f"  {sname}: {sdef['return_type']}")
                lines.append("}")

            return SchemaResult(success=True, output="\n".join(lines), format="graphql")
        except Exception as e:
            return SchemaResult(success=False, output="", format="graphql", errors=[str(e)])

    def generate_from_dict(self, schema_dict: dict[str, Any]) -> SchemaResult:
        if "types" in schema_dict:
            for name, fields in schema_dict["types"].items():
                self.add_type(name, fields)
        if "queries" in schema_dict:
            for name, qdef in schema_dict["queries"].items():
                self.add_query(name, qdef.get("return_type", "String"),
                               qdef.get("args", {}))
        if "mutations" in schema_dict:
            for name, mdef in schema_dict["mutations"].items():
                self.add_mutation(name, mdef.get("return_type", "String"),
                                  mdef.get("args", {}))
        return self.generate()


class GrpcProtoGenerator:
    """33. gRPC proto generator"""

    def __init__(self, package_name: str = "api", go_package: str = ""):
        self.package_name = package_name
        self.go_package = go_package
        self.messages: dict[str, dict[str, Any]] = {}
        self.services: dict[str, list[dict[str, Any]]] = {}
        self.enums: dict[str, list[str]] = {}

    def add_message(self, name: str, fields: dict[str, int]):
        self.messages[name] = fields

    def add_enum(self, name: str, values: list[str]):
        self.enums[name] = values

    def add_service(self, name: str, methods: list[dict[str, Any]]):
        self.services[name] = methods

    def generate(self) -> SchemaResult:
        try:
            lines = [
                'syntax = "proto3";',
                "",
                f"package {self.package_name};",
                ""
            ]
            if self.go_package:
                lines.append(f'option go_package = "{self.go_package}";')
                lines.append("")

            for enum_name, values in self.enums.items():
                lines.append(f"enum {enum_name} {{")
                for i, val in enumerate(values):
                    lines.append(f"  {val} = {i};")
                lines.append("}")
                lines.append("")

            for msg_name, fields in self.messages.items():
                lines.append(f"message {msg_name} {{")
                for fname, fnum in fields.items():
                    ptype = self._guess_proto_type(fname)
                    lines.append(f"  {ptype} {fname} = {fnum};")
                lines.append("}")
                lines.append("")

            for svc_name, methods in self.services.items():
                lines.append(f"service {svc_name} {{")
                for method in methods:
                    lines.append(f"  rpc {method['name']}({method.get('input', 'Empty')}) "
                                 f"returns ({method.get('output', 'Empty')});")
                lines.append("}")

            return SchemaResult(success=True, output="\n".join(lines), format="protobuf")
        except Exception as e:
            return SchemaResult(success=False, output="", format="protobuf", errors=[str(e)])

    def _guess_proto_type(self, field_name: str) -> str:
        name_lower = field_name.lower()
        if "id" in name_lower:
            return "int32"
        if "name" in name_lower or "title" in name_lower or "desc" in name_lower:
            return "string"
        if "price" in name_lower or "amount" in name_lower or "total" in name_lower:
            return "double"
        if "count" in name_lower or "quantity" in name_lower:
            return "int32"
        if "active" in name_lower or "enabled" in name_lower or "flag" in name_lower:
            return "bool"
        if "date" in name_lower or "time" in name_lower:
            return "string"
        return "string"


class AsyncAPIGenerator:
    """34. AsyncAPI spec generator"""

    def __init__(self, title: str = "Event API", version: str = "1.0.0"):
        self.title = title
        self.version = version
        self.channels: dict[str, dict[str, Any]] = {}
        self.messages: dict[str, dict[str, Any]] = {}
        self.schemas: dict[str, dict[str, Any]] = {}

    def add_channel(self, name: str, description: str = "",
                    publish: str | None = None, subscribe: str | None = None):
        channel = {"description": description}
        if publish:
            channel["publish"] = {"message": {"$ref": f"#/components/messages/{publish}"}}
        if subscribe:
            channel["subscribe"] = {"message": {"$ref": f"#/components/messages/{subscribe}"}}
        self.channels[name] = channel

    def add_message(self, name: str, payload_schema: str, description: str = ""):
        self.messages[name] = {
            "description": description,
            "payload": {"$ref": f"#/components/schemas/{payload_schema}"}
        }

    def add_schema(self, name: str, schema: dict[str, Any]):
        self.schemas[name] = schema

    def generate(self) -> SchemaResult:
        try:
            spec = {
                "asyncapi": "3.0.0",
                "info": {"title": self.title, "version": self.version},
                "channels": self.channels,
                "components": {
                    "messages": self.messages,
                    "schemas": self.schemas
                }
            }
            output = json.dumps(spec, indent=2)
            return SchemaResult(success=True, output=output, format="asyncapi")
        except Exception as e:
            return SchemaResult(success=False, output="", format="asyncapi", errors=[str(e)])


class WSDLGenerator:
    """35. WSDL generator"""

    def __init__(self, service_name: str = "Service", namespace: str = "http://api.example.com"):
        self.service_name = service_name
        self.namespace = namespace
        self.operations: list[dict[str, Any]] = []
        self.types: dict[str, dict[str, str]] = {}

    def add_operation(self, name: str, input_type: str, output_type: str,
                      action: str | None = None):
        self.operations.append({
            "name": name,
            "input": input_type,
            "output": output_type,
            "action": action or f"{self.namespace}#{name}"
        })

    def add_type(self, name: str, fields: dict[str, str]):
        self.types[name] = fields

    def generate(self) -> SchemaResult:
        try:
            types_xml = ""
            for type_name, fields in self.types.items():
                fields_xml = ""
                for fname, ftype in fields.items():
                    wsdl_type = self._python_to_xsd(ftype)
                    fields_xml += f'      <xs:element name="{fname}" type="{wsdl_type}"/>\n'
                types_xml += f"""    <xs:complexType name="{type_name}">
{fields_xml}    </xs:complexType>\n"""

            messages_xml = ""
            for op in self.operations:
                messages_xml += f"""    <xs:message name="{op['name']}Request">
      <xs:element name="{op['input']}" type="tns:{op['input']}"/>
    </xs:message>
    <xs:message name="{op['name']}Response">
      <xs:element name="{op['output']}" type="tns:{op['output']}"/>
    </xs:message>\n"""

            operations_xml = ""
            for op in self.operations:
                operations_xml += f"""      <wsdl:operation name="{op['name']}">
        <wsdl:input message="tns:{op['name']}Request"/>
        <wsdl:output message="tns:{op['name']}Response"/>
      </wsdl:operation>\n"""

            wsdl = f"""<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:tns="{self.namespace}"
             xmlns:xs="http://www.w3.org/2001/XMLSchema"
             name="{self.service_name}"
             targetNamespace="{self.namespace}">

  <types>
    <xs:schema targetNamespace="{self.namespace}">
{types_xml}    </xs:schema>
  </types>

{messages_xml}
  <portType name="{self.service_name}PortType">
{operations_xml}  </portType>

  <binding name="{self.service_name}Binding" type="tns:{self.service_name}PortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
  </binding>

  <service name="{self.service_name}">
    <port name="{self.service_name}Port" binding="tns:{self.service_name}Binding">
      <soap:address location="http://localhost:8080/{self.service_name}"/>
    </port>
  </service>
</definitions>"""

            return SchemaResult(success=True, output=wsdl, format="wsdl")
        except Exception as e:
            return SchemaResult(success=False, output="", format="wsdl", errors=[str(e)])

    def _python_to_xsd(self, pytype: str) -> str:
        type_map = {"str": "xs:string", "int": "xs:int", "float": "xs:decimal",
                     "bool": "xs:boolean", "date": "xs:date", "datetime": "xs:dateTime"}
        return type_map.get(pytype, "xs:string")


class ProtobufCompiler:
    """36. Protocol buffer compiler"""

    def __init__(self):
        self._compiled_schemas: dict[str, dict[str, Any]] = {}

    def parse_proto(self, proto_content: str) -> SchemaResult:
        try:
            messages = {}
            current_message = None
            current_fields = {}
            in_message = False

            for line in proto_content.split("\n"):
                line = line.strip()
                if line.startswith("message "):
                    if current_message and current_fields:
                        messages[current_message] = current_fields
                    current_message = line.split()[1].rstrip("{").strip()
                    current_fields = {}
                    in_message = True
                elif in_message and "}":
                    if line == "}":
                        if current_message and current_fields:
                            messages[current_message] = current_fields
                        in_message = False
                        current_message = None
                    elif "=" in line:
                        parts = line.split("=")
                        if len(parts) == 2:
                            field_type = parts[0].strip().split()[0]
                            field_name = parts[0].strip().split()[-1]
                            field_num = int(parts[1].strip().rstrip(";"))
                            current_fields[field_name] = {"type": field_type, "number": field_num}

            self._compiled_schemas.update(messages)
            return SchemaResult(success=True, output=messages, format="parsed_proto")
        except Exception as e:
            return SchemaResult(success=False, output={}, format="parsed_proto", errors=[str(e)])

    def validate_proto(self, proto_content: str) -> SchemaResult:
        errors = []
        if 'syntax = "proto3"' not in proto_content:
            errors.append("Missing proto3 syntax declaration")
        if "package " not in proto_content:
            errors.append("Missing package declaration")
        return SchemaResult(success=len(errors) == 0, output={"valid": len(errors) == 0},
                           format="validation", errors=errors)

    def get_message_fields(self, message_name: str) -> dict[str, Any]:
        return self._compiled_schemas.get(message_name, {})


class JSONSchemaValidator:
    """37. JSON Schema validator"""

    def __init__(self):
        self._schemas: dict[str, dict[str, Any]] = {}

    def register_schema(self, name: str, schema: dict[str, Any]):
        self._schemas[name] = schema

    def validate(self, data: Any, schema: dict[str, Any]) -> SchemaResult:
        errors = self._validate_recursive(data, schema, "$")
        return SchemaResult(
            success=len(errors) == 0,
            output={"valid": len(errors) == 0, "errors": errors},
            format="json_schema_validation",
            errors=errors
        )

    def _validate_recursive(self, data: Any, schema: dict[str, Any], path: str) -> list[str]:
        errors = []
        schema_type = schema.get("type")

        if schema_type:
            type_errors = self._check_type(data, schema_type, path)
            errors.extend(type_errors)

        if "properties" in schema and isinstance(data, dict):
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    prop_path = f"{path}.{prop}"
                    errors.extend(self._validate_recursive(data[prop], prop_schema, prop_path))
                elif prop in schema.get("required", []):
                    errors.append(f"{path}: Missing required property '{prop}'")

        if "items" in schema and isinstance(data, list):
            for i, item in enumerate(data):
                errors.extend(self._validate_recursive(item, schema["items"], f"{path}[{i}]"))

        if "enum" in schema:
            if data not in schema["enum"]:
                errors.append(f"{path}: Value '{data}' not in enum {schema['enum']}")

        if "minimum" in schema and isinstance(data, (int, float)):
            if data < schema["minimum"]:
                errors.append(f"{path}: Value {data} below minimum {schema['minimum']}")

        if "maximum" in schema and isinstance(data, (int, float)):
            if data > schema["maximum"]:
                errors.append(f"{path}: Value {data} above maximum {schema['maximum']}")

        if "minLength" in schema and isinstance(data, str):
            if len(data) < schema["minLength"]:
                errors.append(f"{path}: String too short (min {schema['minLength']})")

        if "maxLength" in schema and isinstance(data, str):
            if len(data) > schema["maxLength"]:
                errors.append(f"{path}: String too long (max {schema['maxLength']})")

        if "pattern" in schema and isinstance(data, str):
            import re
            if not re.match(schema["pattern"], data):
                errors.append(f"{path}: String doesn't match pattern")

        return errors

    def _check_type(self, data: Any, expected_type: str, path: str) -> list[str]:
        type_checks = {
            "string": str, "number": (int, float), "integer": int,
            "boolean": bool, "array": list, "object": dict, "null": type(None)
        }
        if expected_type in type_checks:
            expected = type_checks[expected_type]
            if not isinstance(data, expected):
                return [f"{path}: Expected type {expected_type}, got {type(data).__name__}"]
        return []

    def generate_schema(self, data: Any, name: str = "GeneratedSchema") -> dict[str, Any]:
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": name}
        schema.update(self._infer_schema(data))
        return schema

    def _infer_schema(self, data: Any) -> dict[str, Any]:
        if isinstance(data, dict):
            props = {}
            for k, v in data.items():
                props[k] = self._infer_schema(v)
            return {"type": "object", "properties": props}
        elif isinstance(data, list):
            if data:
                return {"type": "array", "items": self._infer_schema(data[0])}
            return {"type": "array"}
        elif isinstance(data, str):
            return {"type": "string"}
        elif isinstance(data, bool):
            return {"type": "boolean"}
        elif isinstance(data, int):
            return {"type": "integer"}
        elif isinstance(data, float):
            return {"type": "number"}
        elif data is None:
            return {"type": "null"}
        return {"type": "string"}


class XMLSchemaValidator:
    """38. XML Schema validator"""

    def __init__(self):
        self._schemas: dict[str, str] = {}

    def register_schema(self, name: str, xsd_content: str):
        self._schemas[name] = xsd_content

    def validate(self, xml_content: str, schema_name: str | None = None) -> SchemaResult:
        import xml.etree.ElementTree as ET
        errors = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            return SchemaResult(success=False, output={"valid": False},
                               format="xml_validation", errors=[f"XML parse error: {e}"])

        if schema_name and schema_name in self._schemas:
            schema = self._schemas[schema_name]
            xsd_errors = self._validate_against_xsd(root, schema)
            errors.extend(xsd_errors)

        return SchemaResult(
            success=len(errors) == 0,
            output={"valid": len(errors) == 0},
            format="xml_validation",
            errors=errors
        )

    def _validate_against_xsd(self, element, xsd_content: str) -> list[str]:
        errors = []
        import xml.etree.ElementTree as ET
        try:
            xsd_root = ET.fromstring(xsd_content)
            required_elements = []
            for elem in xsd_root.iter():
                if elem.tag.endswith("element") and "name" in elem.attrib:
                    required_elements.append(elem.attrib["name"])

            found_elements = {child.tag for child in element}
            for req in required_elements:
                if req not in found_elements:
                    errors.append(f"Missing required element: {req}")
        except ET.ParseError:
            errors.append("Invalid XSD schema")
        return errors

    def generate_xsd(self, name: str, root_element: str,
                     fields: dict[str, str]) -> SchemaResult:
        type_map = {"str": "xs:string", "int": "xs:decimal", "float": "xs:decimal",
                     "bool": "xs:boolean"}
        elements = ""
        for fname, ftype in fields.items():
            xsd_type = type_map.get(ftype, "xs:string")
            elements += f'    <xs:element name="{fname}" type="{xsd_type}"/>\n'

        xsd = f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="{root_element}">
    <xs:complexType>
      <xs:sequence>
{elements}      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""
        return SchemaResult(success=True, output=xsd, format="xsd")


class SwaggerUIGenerator:
    """39. Swagger UI generator"""

    def __init__(self, title: str = "API Documentation"):
        self.title = title
        self.spec_url: str | None = None
        self.spec_content: str | None = None

    def generate_from_url(self, spec_url: str) -> SchemaResult:
        self.spec_url = spec_url
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{self.title}</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            url: "{spec_url}",
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "StandaloneLayout"
        }});
    </script>
</body>
</html>"""
        return SchemaResult(success=True, output=html, format="swagger_ui")

    def generate_from_spec(self, spec: dict[str, Any]) -> SchemaResult:
        spec_json = json.dumps(spec)
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{self.title}</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        const spec = {spec_json};
        SwaggerUIBundle({{
            spec: spec,
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwandalonePreset],
            layout: "StandaloneLayout"
        }});
    </script>
</body>
</html>"""
        return SchemaResult(success=True, output=html, format="swagger_ui")

    def generate_empty(self, spec_url: str = "/openapi.json") -> SchemaResult:
        return self.generate_from_url(spec_url)


class PostmanCollectionGenerator:
    """40. Postman collection generator"""

    def __init__(self, name: str = "API Collection"):
        self.name = name
        self.items: list[dict[str, Any]] = []
        self.environments: dict[str, dict[str, str]] = {}
        self.auth: dict[str, Any] | None = None

    def set_auth(self, auth_type: str, config: dict[str, Any]):
        self.auth = {"type": auth_type, **config}

    def add_request(self, name: str, method: str, url: str,
                    headers: dict[str, str] | None = None,
                    body: Any | None = None,
                    description: str = ""):
        item = {
            "name": name,
            "request": {
                "method": method.upper(),
                "header": [{"key": k, "value": v} for k, v in (headers or {}).items()],
                "url": url,
                "description": description
            },
            "response": []
        }
        if body:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(body) if isinstance(body, (dict, list)) else str(body),
                "options": {"raw": {"language": "json"}}
            }
        self.items.append(item)

    def add_folder(self, name: str, items: list[dict[str, Any]]):
        self.items.append({
            "name": name,
            "item": items,
            "description": f"Folder: {name}"
        })

    def add_environment(self, name: str, variables: dict[str, str]):
        self.environments[name] = variables

    def generate(self) -> SchemaResult:
        try:
            collection = {
                "info": {
                    "name": self.name,
                    "_postman_id": f"collection-{id(self)}",
                    "description": f"Generated collection: {self.name}",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
                },
                "item": self.items
            }
            if self.auth:
                collection["auth"] = self.auth

            environments = []
            for env_name, vars_dict in self.environments.items():
                env = {
                    "name": env_name,
                    "values": [
                        {"key": k, "value": v, "enabled": True}
                        for k, v in vars_dict.items()
                    ]
                }
                environments.append(env)

            output = {
                "collection": collection,
                "environments": environments
            }
            return SchemaResult(success=True, output=json.dumps(output, indent=2),
                               format="postman_collection")
        except Exception as e:
            return SchemaResult(success=False, output="", format="postman_collection",
                               errors=[str(e)])

    def generate_from_openapi(self, openapi_spec: dict[str, Any]) -> SchemaResult:
        try:
            for path, methods in openapi_spec.get("paths", {}).items():
                for method, operation in methods.items():
                    if method in ("get", "post", "put", "delete", "patch"):
                        headers = {}
                        params = operation.get("parameters", [])
                        for param in params:
                            if param.get("in") == "header":
                                headers[param["name"]] = f"{{{{{param['name']}}}}}"
                        body = None
                        if "requestBody" in operation:
                            body = {"placeholder": "request body"}
                        self.add_request(
                            name=operation.get("summary", path),
                            method=method.upper(),
                            url=f"{{{{base_url}}}}{path}",
                            headers=headers,
                            body=body,
                            description=operation.get("description", "")
                        )
            return self.generate()
        except Exception as e:
            return SchemaResult(success=False, output="", format="postman_collection",
                               errors=[str(e)])
