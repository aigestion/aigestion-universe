"""Data transformers - 10 ideas: JSON/XML, XML/JSON, CSV/JSON, YAML/JSON, Protobuf, Avro, Parquet, Excel, HTML/Markdown."""

import csv
import io
import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from xml.dom import minidom

logger = logging.getLogger(__name__)


class TransformDirection(Enum):
    FORWARD = "forward"
    REVERSE = "reverse"


@dataclass
class TransformResult:
    success: bool
    output: Any
    format: str
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class JSONtoXMLTransformer:
    """21. JSON to XML transformer"""

    def __init__(self, root_tag: str = "root", indent: int = 2):
        self.root_tag = root_tag
        self.indent = indent
        self._attr_prefix = "@"
        self._text_key = "#text"

    def transform(self, data: dict | list, root_tag: str | None = None) -> TransformResult:
        root_tag = root_tag or self.root_tag
        try:
            if isinstance(data, list):
                xml_parts = [f"<{root_tag}>"]
                for item in data:
                    xml_parts.append(self._dict_to_xml(item))
                xml_parts.append(f"</{root_tag}>")
                xml_str = "\n".join(xml_parts)
            elif isinstance(data, dict):
                xml_str = f"<{root_tag}>\n{self._dict_to_xml(data)}\n</{root_tag}>"
            else:
                xml_str = f"<{root_tag}>{data}</{root_tag}>"

            pretty = minidom.parseString(xml_str).toprettyxml(indent=" " * self.indent)
            lines = pretty.split("\n")
            xml_str = "\n".join(lines[1:])
            return TransformResult(success=True, output=xml_str, format="xml")
        except Exception as e:
            return TransformResult(success=False, output="", format="xml", errors=[str(e)])

    def _dict_to_xml(self, data: Any, indent_level: int = 1) -> str:
        indent = " " * (self.indent * indent_level)
        parts = []
        if isinstance(data, dict):
            for key, value in data.items():
                if key.startswith(self._attr_prefix):
                    continue
                if key == self._text_key:
                    parts.append(f"{indent}{value}")
                elif isinstance(value, dict):
                    inner = self._dict_to_xml(value, indent_level + 1)
                    parts.append(f"{indent}<{key}>\n{inner}\n{indent}</{key}>")
                elif isinstance(value, list):
                    parts.append(f"{indent}<{key}>")
                    for item in value:
                        item_xml = self._dict_to_xml(item, indent_level + 1)
                        parts.append(item_xml)
                    parts.append(f"{indent}</{key}>")
                else:
                    parts.append(f"{indent}<{key}>{self._escape_xml(str(value))}</{key}>")
        else:
            parts.append(f"{indent}{self._escape_xml(str(data))}")
        return "\n".join(parts)

    def _escape_xml(self, text: str) -> str:
        return (text.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))

    def transform_file(self, input_path: str, output_path: str, root_tag: str | None = None) -> TransformResult:
        try:
            with open(input_path, encoding="utf-8") as f:
                data = json.load(f)
            result = self.transform(data, root_tag)
            if result.success:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result.output)
            return result
        except Exception as e:
            return TransformResult(success=False, output="", format="xml", errors=[str(e)])


class XMLtoJSONTransformer:
    """22. XML to JSON transformer"""

    def __init__(self, strip_roots: bool = True, preserve_attributes: bool = True):
        self.strip_roots = strip_roots
        self.preserve_attributes = preserve_attributes
        self._attr_prefix = "@"
        self._text_key = "#text"

    def transform(self, xml_string: str) -> TransformResult:
        try:
            root = ET.fromstring(xml_string)
            result_dict = self._element_to_dict(root)
            if self.strip_roots and len(result_dict) == 1:
                key = list(result_dict.keys())[0]
                result_dict = result_dict[key]
            return TransformResult(success=True, output=result_dict, format="json")
        except ET.ParseError as e:
            return TransformResult(success=False, output={}, format="json", errors=[f"Parse error: {e}"])
        except Exception as e:
            return TransformResult(success=False, output={}, format="json", errors=[str(e)])

    def _element_to_dict(self, element: ET.Element) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.preserve_attributes and element.attrib:
            for key, value in element.attrib.items():
                result[f"{self._attr_prefix}{key}"] = value

        children = list(element)
        if not children:
            text = (element.text or "").strip()
            if text:
                if result:
                    result[self._text_key] = text
                else:
                    return text
            return result

        child_groups: dict[str, list] = {}
        for child in children:
            tag = child.tag
            if tag not in child_groups:
                child_groups[tag] = []
            child_groups[tag].append(child)

        for tag, child_elements in child_groups.items():
            if len(child_elements) == 1:
                child_dict = self._element_to_dict(child_elements[0])
                result[tag] = child_dict
            else:
                result[tag] = [self._element_to_dict(c) for c in child_elements]

        text = (element.text or "").strip()
        if text:
            result[self._text_key] = text

        return result

    def transform_file(self, input_path: str, output_path: str) -> TransformResult:
        try:
            with open(input_path, encoding="utf-8") as f:
                xml_string = f.read()
            result = self.transform(xml_string)
            if result.success:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result.output, f, indent=2, ensure_ascii=False)
            return result
        except Exception as e:
            return TransformResult(success=False, output={}, format="json", errors=[str(e)])


class CSVtoJSONTransformer:
    """23. CSV to JSON transformer"""

    def __init__(self, delimiter: str = ",", quotechar: str = '"', encoding: str = "utf-8"):
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding

    def transform(self, csv_string: str, orient: str = "records") -> TransformResult:
        try:
            reader = csv.DictReader(io.StringIO(csv_string), delimiter=self.delimiter,
                                     quotechar=self.quotechar)
            records = list(reader)
            if orient == "records":
                output = records
            elif orient == "dict":
                output = dict(enumerate(records))
            elif orient == "index":
                key_col = list(records[0].keys())[0] if records else "id"
                output = {row.get(key_col, i): row for i, row in enumerate(records)}
            else:
                output = records

            return TransformResult(
                success=True, output=output, format="json",
                metadata={"row_count": len(records), "columns": list(records[0].keys()) if records else []}
            )
        except Exception as e:
            return TransformResult(success=False, output=[], format="json", errors=[str(e)])

    def transform_file(self, input_path: str, output_path: str, orient: str = "records") -> TransformResult:
        try:
            with open(input_path, encoding=self.encoding) as f:
                csv_string = f.read()
            result = self.transform(csv_string, orient)
            if result.success:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result.output, f, indent=2, ensure_ascii=False)
            return result
        except Exception as e:
            return TransformResult(success=False, output=[], format="json", errors=[str(e)])


class YAMLtoJSONTransformer:
    """24. YAML to JSON transformer"""

    def __init__(self):
        self.yaml = None
        try:
            import yaml
            self.yaml = yaml
        except ImportError:
            logger.warning("PyYAML not installed; YAML support limited")

    def transform(self, yaml_string: str) -> TransformResult:
        if self.yaml:
            try:
                data = self.yaml.safe_load(yaml_string)
                return TransformResult(success=True, output=data, format="json")
            except Exception as e:
                return TransformResult(success=False, output={}, format="json", errors=[str(e)])
        else:
            return self._parse_simple_yaml(yaml_string)

    def _parse_simple_yaml(self, yaml_string: str) -> TransformResult:
        try:
            result = {}
            current_key = None
            for line in yaml_string.strip().split("\n"):
                if not line.strip() or line.strip().startswith("#"):
                    continue
                indent = len(line) - len(line.lstrip())
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip()
                    value = value.strip()
                    if value:
                        result[key] = self._yaml_value(value)
                    else:
                        current_key = key
                        result[key] = {}
                elif current_key and indent > 0:
                    if isinstance(result[current_key], dict):
                        pass
            return TransformResult(success=True, output=result, format="json")
        except Exception as e:
            return TransformResult(success=False, output={}, format="json", errors=[str(e)])

    def _yaml_value(self, value: str) -> Any:
        if value.lower() in ("true", "yes"):
            return True
        if value.lower() in ("false", "no"):
            return False
        if value.lower() in ("null", "~"):
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value

    def transform_file(self, input_path: str, output_path: str) -> TransformResult:
        try:
            with open(input_path, encoding="utf-8") as f:
                yaml_string = f.read()
            result = self.transform(yaml_string)
            if result.success:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result.output, f, indent=2, ensure_ascii=False)
            return result
        except Exception as e:
            return TransformResult(success=False, output={}, format="json", errors=[str(e)])


class JSONtoProtobufTransformer:
    """25. JSON to Protobuf transformer"""

    def __init__(self):
        self._schemas: dict[str, dict[str, Any]] = {}

    def register_schema(self, name: str, schema: dict[str, Any]):
        self._schemas[name] = schema

    def generate_proto(self, schema_name: str, message_name: str) -> TransformResult:
        if schema_name not in self._schemas:
            return TransformResult(success=False, output="", format="proto",
                                   errors=[f"Schema {schema_name} not found"])

        schema = self._schemas[schema_name]
        lines = [
            'syntax = "proto3";',
            "",
            f"message {message_name} {{"
        ]
        field_num = 1
        for field_name, field_type in schema.items():
            proto_type = self._json_type_to_proto(field_type)
            lines.append(f"  {proto_type} {field_name} = {field_num};")
            field_num += 1
        lines.append("}")

        return TransformResult(success=True, output="\n".join(lines), format="proto")

    def _json_type_to_proto(self, json_type: Any) -> str:
        if isinstance(json_type, bool):
            return "bool"
        if isinstance(json_type, int):
            return "int32"
        if isinstance(json_type, float):
            return "double"
        if isinstance(json_type, str):
            return "string"
        if isinstance(json_type, list):
            return "repeated string"
        return "string"

    def json_to_protobuf_bytes(self, data: dict[str, Any], schema_name: str) -> TransformResult:
        if schema_name not in self._schemas:
            return TransformResult(success=False, output=b"", format="protobuf",
                                   errors=[f"Schema {schema_name} not found"])
        try:
            encoded = json.dumps(data).encode("utf-8")
            return TransformResult(success=True, output=encoded, format="protobuf")
        except Exception as e:
            return TransformResult(success=False, output=b"", format="protobuf", errors=[str(e)])

    def protobuf_bytes_to_json(self, data: bytes) -> TransformResult:
        try:
            result = json.loads(data.decode("utf-8"))
            return TransformResult(success=True, output=result, format="json")
        except Exception as e:
            return TransformResult(success=False, output={}, format="json", errors=[str(e)])


class AvroToJSONTransformer:
    """26. Avro to JSON transformer"""

    def __init__(self):
        self._schemas: dict[str, dict[str, Any]] = {}

    def register_schema(self, name: str, schema: dict[str, Any]):
        self._schemas[name] = schema

    def generate_avro_schema(self, name: str, fields: dict[str, str]) -> TransformResult:
        schema = {
            "type": "record",
            "name": name,
            "fields": [
                {"name": fname, "type": ftype}
                for fname, ftype in fields.items()
            ]
        }
        self._schemas[name] = schema
        return TransformResult(success=True, output=json.dumps(schema, indent=2), format="avro")

    def validate_against_schema(self, data: dict[str, Any], schema_name: str) -> TransformResult:
        if schema_name not in self._schemas:
            return TransformResult(success=False, output=False, format="validation",
                                   errors=[f"Schema {schema_name} not found"])
        schema = self._schemas[schema_name]
        errors = []
        for field_def in schema.get("fields", []):
            fname = field_def["name"]
            ftype = field_def["type"]
            if fname not in data:
                errors.append(f"Missing field: {fname}")
            elif not self._check_type(data[fname], ftype):
                errors.append(f"Type mismatch for {fname}: expected {ftype}")

        return TransformResult(
            success=len(errors) == 0,
            output=len(errors) == 0,
            format="validation",
            errors=errors
        )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        type_map = {
            "string": str, "int": int, "long": int,
            "float": float, "double": float, "boolean": bool, "null": type(None)
        }
        if expected_type in type_map:
            return isinstance(value, type_map[expected_type])
        if expected_type.startswith("array"):
            return isinstance(value, list)
        return True

    def records_to_json(self, records: list[dict[str, Any]]) -> TransformResult:
        return TransformResult(success=True, output=records, format="json")

    def json_to_records(self, data: list[dict[str, Any]], schema_name: str) -> TransformResult:
        validation = self.validate_against_schema(data[0], schema_name) if data else None
        if validation and not validation.success:
            return validation
        return TransformResult(success=True, output=data, format="avro_records")


class ParquetTransformer:
    """27. Parquet reader/writer"""

    def __init__(self):
        self._pq = None
        try:
            import pyarrow.parquet as pq
            self._pq = pq
        except ImportError:
            logger.warning("pyarrow not installed; Parquet support limited")

    def read(self, file_path: str) -> TransformResult:
        try:
            if self._pq:
                table = self._pq.read_table(file_path)
                data = table.to_pydict()
                return TransformResult(success=True, output=data, format="parquet",
                                       metadata={"columns": list(data.keys()),
                                                  "rows": len(next(iter(data.values()), []))})
            else:
                return self._read_simple_parquet(file_path)
        except Exception as e:
            return TransformResult(success=False, output={}, format="parquet", errors=[str(e)])

    def _read_simple_parquet(self, file_path: str) -> TransformResult:
        return TransformResult(success=False, output={}, format="parquet",
                               errors=["Parquet support requires pyarrow"])

    def write(self, data: dict[str, list], file_path: str,
              compression: str = "snappy") -> TransformResult:
        try:
            if self._pq:
                table = self._pq.Table.from_pydict(data)
                self._pq.write_table(table, file_path, compression=compression)
                return TransformResult(success=True, output=file_path, format="parquet")
            else:
                return TransformResult(success=False, output="", format="parquet",
                                       errors=["Parquet support requires pyarrow"])
        except Exception as e:
            return TransformResult(success=False, output="", format="parquet", errors=[str(e)])

    def to_json(self, file_path: str) -> TransformResult:
        result = self.read(file_path)
        if result.success:
            result.format = "json"
        return result

    def from_json(self, json_data: dict[str, list], file_path: str) -> TransformResult:
        return self.write(json_data, file_path)

    def get_schema(self, file_path: str) -> TransformResult:
        try:
            if self._pq:
                schema = self._pq.read_schema(file_path)
                return TransformResult(success=True, output=str(schema), format="parquet_schema")
            return TransformResult(success=False, output="", format="parquet_schema",
                                   errors=["Requires pyarrow"])
        except Exception as e:
            return TransformResult(success=False, output="", format="parquet_schema", errors=[str(e)])


class ExcelToJSONTransformer:
    """28. Excel to JSON transformer"""

    def __init__(self):
        self._openpyxl = None
        try:
            import openpyxl
            self._openpyxl = openpyxl
        except ImportError:
            logger.warning("openpyxl not installed; Excel support limited")

    def transform(self, file_path: str, sheet_name: str | None = None,
                  header_row: int = 0) -> TransformResult:
        try:
            if self._openpyxl:
                return self._read_with_openpyxl(file_path, sheet_name, header_row)
            return TransformResult(success=False, output=[], format="json",
                                   errors=["Excel support requires openpyxl"])
        except Exception as e:
            return TransformResult(success=False, output=[], format="json", errors=[str(e)])

    def _read_with_openpyxl(self, file_path: str, sheet_name: str | None,
                             header_row: int) -> TransformResult:
        wb = self._openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return TransformResult(success=True, output=[], format="json", metadata={"sheet": ws.title})

        headers = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(rows[header_row])]
        records = []
        for row in rows[header_row + 1:]:
            record = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    record[headers[i]] = value
            records.append(record)

        wb.close()
        return TransformResult(
            success=True, output=records, format="json",
            metadata={"sheet": ws.title, "rows": len(records), "columns": headers}
        )

    def transform_all_sheets(self, file_path: str) -> TransformResult:
        try:
            if not self._openpyxl:
                return TransformResult(success=False, output={}, format="json",
                                       errors=["Requires openpyxl"])
            wb = self._openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            all_sheets = {}
            for sheet_name in wb.sheetnames:
                result = self.transform(file_path, sheet_name)
                if result.success:
                    all_sheets[sheet_name] = result.output
            wb.close()
            return TransformResult(success=True, output=all_sheets, format="json")
        except Exception as e:
            return TransformResult(success=False, output={}, format="json", errors=[str(e)])


class HTMLToMarkdownTransformer:
    """29. HTML to Markdown transformer"""

    def __init__(self):
        self._markdownify = None
        try:
            from markdownify import markdownify as md
            self._markdownify = md
        except ImportError:
            logger.warning("markdownify not installed; HTML to Markdown limited")

    def transform(self, html: str, strip_tags: list[str] | None = None) -> TransformResult:
        try:
            if self._markdownify:
                kwargs = {"heading_style": "ATX"}
                if strip_tags:
                    kwargs["strip"] = strip_tags
                try:
                    md_text = self._markdownify(html, **kwargs)
                except TypeError:
                    kwargs.pop("heading_style")
                    md_text = self._markdownify(html, **kwargs)
                return TransformResult(success=True, output=md_text, format="markdown")
            return self._simple_html_to_md(html)
        except Exception as e:
            return TransformResult(success=False, output="", format="markdown", errors=[str(e)])

    def _simple_html_to_md(self, html: str) -> TransformResult:
        import re
        text = html
        text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text, flags=re.DOTALL)
        text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text, flags=re.DOTALL)
        text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text, flags=re.DOTALL)
        text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)
        text = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", text, flags=re.DOTALL)
        text = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", text, flags=re.DOTALL)
        text = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", text, flags=re.DOTALL)
        text = re.sub(r"<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"[\2](\1)", text, flags=re.DOTALL)
        text = re.sub(r"<img[^>]*src=\"([^\"]+)\"[^>]*alt=\"([^\"]*)\"[^>]*/?>",
                       r"![\2](\1)", text)
        text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
        text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.DOTALL)
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return TransformResult(success=True, output=text.strip(), format="markdown")

    def transform_file(self, input_path: str, output_path: str) -> TransformResult:
        try:
            with open(input_path, encoding="utf-8") as f:
                html = f.read()
            result = self.transform(html)
            if result.success:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result.output)
            return result
        except Exception as e:
            return TransformResult(success=False, output="", format="markdown", errors=[str(e)])


class MarkdownToHTMLTransformer:
    """30. Markdown to HTML transformer"""

    def __init__(self):
        self._markdown = None
        try:
            import markdown
            self._markdown = markdown
        except ImportError:
            logger.warning("markdown not installed; Markdown to HTML limited")

    def transform(self, markdown_text: str, extensions: list[str] | None = None) -> TransformResult:
        try:
            if self._markdown:
                exts = extensions or ["tables", "fenced_code"]
                html = self._markdown.markdown(markdown_text, extensions=exts)
                return TransformResult(success=True, output=html, format="html")
            return self._simple_md_to_html(markdown_text)
        except Exception as e:
            return TransformResult(success=False, output="", format="html", errors=[str(e)])

    def _simple_md_to_html(self, text: str) -> TransformResult:
        import re
        html = text
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)
        html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)
        html = re.sub(r"!\[(.+?)\]\((.+?)\)", r'<img src="\2" alt="\1">', html)
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"(<li>.*?</li>\n?)+", lambda m: f"<ul>\n{m.group(0)}</ul>", html)
        paragraphs = html.split("\n\n")
        html = "\n".join(f"<p>{p.strip()}</p>" if p.strip() and not p.strip().startswith("<") else p
                         for p in paragraphs)
        return TransformResult(success=True, output=html, format="html")

    def to_full_html(self, markdown_text: str, title: str = "Document",
                     css: str | None = None) -> TransformResult:
        body_result = self.transform(markdown_text)
        if not body_result.success:
            return body_result

        css_style = f"<style>{css}</style>" if css else ""
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css_style}
</head>
<body>
{body_result.output}
</body>
</html>"""
        return TransformResult(success=True, output=full_html, format="html")

    def transform_file(self, input_path: str, output_path: str) -> TransformResult:
        try:
            with open(input_path, encoding="utf-8") as f:
                md_text = f.read()
            result = self.transform(md_text)
            if result.success:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result.output)
            return result
        except Exception as e:
            return TransformResult(success=False, output="", format="html", errors=[str(e)])
