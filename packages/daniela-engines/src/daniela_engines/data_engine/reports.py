"""Reporting Engine - Ideas 21-30."""

import base64
import csv
import io
import json
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from typing import Any


class PDFReportGenerator:
    """Idea 21: PDF Report Generator"""

    def __init__(self):
        self.pages: list[dict] = []
        self.metadata: dict = {}

    def set_metadata(self, title: str, author: str = "", date: str = None):
        self.metadata = {
            "title": title,
            "author": author,
            "date": date or datetime.now().isoformat(),
        }
        return self

    def add_page(self, content: dict):
        self.pages.append(content)
        return self

    def add_text_page(self, text: str, font_size: int = 12):
        self.pages.append({"type": "text", "content": text, "font_size": font_size})
        return self

    def add_table_page(self, headers: list[str], rows: list[list[Any]]):
        self.pages.append({"type": "table", "headers": headers, "rows": rows})
        return self

    def add_chart_page(self, chart_type: str, data: dict):
        self.pages.append({"type": "chart", "chart_type": chart_type, "data": data})
        return self

    def generate_html(self) -> str:
        html_parts = ["<!DOCTYPE html><html><head>"]
        html_parts.append(f"<title>{self.metadata.get('title', 'Report')}</title>")
        html_parts.append("<style>")
        html_parts.append("body{font-family:Arial,sans-serif;margin:40px;}")
        html_parts.append("table{border-collapse:collapse;width:100%;margin:20px 0;}")
        html_parts.append("th,td{border:1px solid #ddd;padding:8px;text-align:left;}")
        html_parts.append("th{background-color:#f2f2f2;}")
        html_parts.append("h1{color:#333;}h2{color:#555;}")
        html_parts.append("</style></head><body>")

        html_parts.append(f"<h1>{self.metadata.get('title', 'Report')}</h1>")
        html_parts.append(f"<p>Generated: {self.metadata.get('date', '')}</p>")

        for page in self.pages:
            if page.get("type") == "text":
                html_parts.append(f"<p>{page['content']}</p>")
            elif page.get("type") == "table":
                html_parts.append("<table>")
                html_parts.append("<tr>" + "".join(f"<th>{h}</th>" for h in page["headers"]) + "</tr>")
                for row in page["rows"]:
                    html_parts.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
                html_parts.append("</table>")
            elif page.get("type") == "chart":
                html_parts.append(f"<div class='chart' data-type='{page['chart_type']}'></div>")

        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    def to_base64(self) -> str:
        html = self.generate_html()
        return base64.b64encode(html.encode()).decode()


class ExcelCSVExporter:
    """Idea 22: Excel/CSV Export"""

    @staticmethod
    def to_csv(headers: list[str], rows: list[list[Any]], delimiter: str = ",") -> str:
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()

    @staticmethod
    def from_csv(csv_string: str, delimiter: str = ",") -> dict:
        reader = csv.reader(io.StringIO(csv_string), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return {"headers": [], "data": []}
        return {"headers": rows[0], "data": rows[1:]}

    @staticmethod
    def to_tsv(headers: list[str], rows: list[list[Any]]) -> str:
        return ExcelCSVExporter.to_csv(headers, rows, delimiter="\t")

    @staticmethod
    def dict_list_to_csv(records: list[dict]) -> str:
        if not records:
            return ""
        headers = list(records[0].keys())
        rows = [[r.get(h, "") for h in headers] for r in records]
        return ExcelCSVExporter.to_csv(headers, rows)

    @staticmethod
    def pivot_table(data: list[dict], index: str, columns: str, values: str, agg: str = "sum") -> dict:
        pivot = defaultdict(lambda: defaultdict(list))
        for record in data:
            idx = record.get(index)
            col = record.get(columns)
            val = record.get(values, 0)
            pivot[idx][col].append(val)

        result = {}
        for idx, cols in pivot.items():
            result[idx] = {}
            for col, vals in cols.items():
                if agg == "sum":
                    result[idx][col] = sum(vals)
                elif agg == "avg":
                    result[idx][col] = sum(vals) / len(vals)
                elif agg == "count":
                    result[idx][col] = len(vals)
                elif agg == "max":
                    result[idx][col] = max(vals)
                elif agg == "min":
                    result[idx][col] = min(vals)

        all_cols = set()
        for cols in result.values():
            all_cols.update(cols.keys())

        return {"index": list(result.keys()), "columns": sorted(all_cols), "data": result}


class HTMLReportGenerator:
    """Idea 23: HTML Report with Charts"""

    def __init__(self):
        self.sections: list[dict] = []
        self.styles: list[str] = []
        self.scripts: list[str] = []

    def add_section(self, title: str, content: str, section_type: str = "text"):
        self.sections.append({"title": title, "content": content, "type": section_type})
        return self

    def add_chart_section(self, title: str, chart_type: str, data: dict):
        chart_html = self._render_chart(chart_type, data)
        self.sections.append({"title": title, "content": chart_html, "type": "chart"})
        return self

    def add_table_section(self, title: str, headers: list[str], rows: list[list[Any]]):
        table_html = "<table>"
        table_html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
        for row in rows:
            table_html += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        table_html += "</table>"
        self.sections.append({"title": title, "content": table_html, "type": "table"})
        return self

    def add_metric_section(self, title: str, metrics: dict[str, Any]):
        cards = ""
        for name, value in metrics.items():
            cards += f"<div class='metric-card'><h3>{name}</h3><p>{value}</p></div>"
        self.sections.append({"title": title, "content": cards, "type": "metrics"})
        return self

    def _render_chart(self, chart_type: str, data: dict) -> str:
        chart_id = f"chart_{hash(json.dumps(data)) % 10000}"
        if chart_type == "bar":
            labels = json.dumps(data.get("labels", []))
            values = json.dumps(data.get("values", []))
            return f"<div id='{chart_id}' class='chart-container'></div><script>renderBar('{chart_id}',{labels},{values})</script>"
        elif chart_type == "line":
            labels = json.dumps(data.get("labels", []))
            values = json.dumps(data.get("values", []))
            return f"<div id='{chart_id}' class='chart-container'></div><script>renderLine('{chart_id}',{labels},{values})</script>"
        elif chart_type == "pie":
            labels = json.dumps(data.get("labels", []))
            values = json.dumps(data.get("values", []))
            return f"<div id='{chart_id}' class='chart-container'></div><script>renderPie('{chart_id}',{labels},{values})</script>"
        return f"<pre>{json.dumps(data, indent=2)}</pre>"

    def generate(self) -> str:
        html = ["<!DOCTYPE html><html><head><meta charset='utf-8'>"]
        html.append("<style>")
        html.append("body{font-family:Arial,sans-serif;max-width:1000px;margin:0 auto;padding:20px;}")
        html.append(".section{margin:20px 0;padding:15px;border:1px solid #eee;border-radius:8px;}")
        html.append(".metric-card{display:inline-block;padding:15px;margin:5px;border:1px solid #ddd;border-radius:8px;text-align:center;}")
        html.append("table{width:100%;border-collapse:collapse;}th,td{padding:8px;border:1px solid #ddd;}")
        html.append("th{background:#f5f5f5;}.chart-container{height:300px;}")
        html.append("</style></head><body>")

        for section in self.sections:
            html.append("<div class='section'>")
            html.append(f"<h2>{section['title']}</h2>")
            html.append(section["content"])
            html.append("</div>")

        html.append("</body></html>")
        return "\n".join(html)


class ScheduledReportDelivery:
    """Idea 24: Scheduled Report Delivery (Email)"""

    def __init__(self):
        self.schedules: list[dict] = []
        self.sent_reports: list[dict] = []

    def create_schedule(self, name: str, cron: str, recipients: list[str], report_config: dict):
        schedule = {
            "id": len(self.schedules) + 1,
            "name": name,
            "cron": cron,
            "recipients": recipients,
            "config": report_config,
            "active": True,
            "created_at": datetime.now().isoformat(),
        }
        self.schedules.append(schedule)
        return schedule

    def send_report(self, schedule_id: int, content: str) -> dict:
        schedule = next((s for s in self.schedules if s["id"] == schedule_id), None)
        if not schedule:
            return {"error": "Schedule not found"}

        result = {
            "schedule_id": schedule_id,
            "recipients": schedule["recipients"],
            "sent_at": datetime.now().isoformat(),
            "status": "sent",
        }
        self.sent_reports.append(result)
        return result

    def get_pending(self) -> list[dict]:
        return [s for s in self.schedules if s["active"]]

    def deactivate(self, schedule_id: int):
        for s in self.schedules:
            if s["id"] == schedule_id:
                s["active"] = False
                break


class ReportTemplateEngine:
    """Idea 25: Report Template Engine (Jinja2-like)"""

    def __init__(self):
        self.templates: dict[str, str] = {}

    def register_template(self, name: str, template: str):
        self.templates[name] = template
        return self

    def render(self, template_name: str, context: dict) -> str:
        template = self.templates.get(template_name, "")
        result = template

        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            if isinstance(value, (list, dict)):
                result = result.replace(placeholder, json.dumps(value))
            else:
                result = result.replace(placeholder, str(value))

        # Handle loops: {% for item in items %}...{% endfor %}
        import re
        for_match = re.search(r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}", result, re.DOTALL)
        if for_match:
            var_name = for_match.group(1)
            list_name = for_match.group(2)
            body = for_match.group(3)
            items = context.get(list_name, [])
            rendered_items = []
            for item in items:
                item_context = {**context, var_name: item}
                item_result = body
                for k, v in item_context.items():
                    item_result = item_result.replace("{{" + k + "}}", str(v))
                rendered_items.append(item_result)
            result = result[:for_match.start()] + "".join(rendered_items) + result[for_match.end():]

        # Handle conditionals: {% if condition %}...{% endif %}
        if_match = re.search(r"\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}", result, re.DOTALL)
        if if_match:
            condition = if_match.group(1)
            body = if_match.group(2)
            if context.get(condition):
                result = result[:if_match.start()] + body + result[if_match.end():]
            else:
                result = result[:if_match.start()] + result[if_match.end():]

        return result

    def list_templates(self) -> list[str]:
        return list(self.templates.keys())


class DashboardDataProvider:
    """Idea 26: Dashboard Data Provider"""

    def __init__(self):
        self.data_sources: dict[str, Callable] = {}
        self.cache: dict[str, dict] = {}
        self.cache_ttl: int = 300

    def register_source(self, name: str, func: Callable):
        self.data_sources[name] = func
        return self

    def get_data(self, source_name: str, params: dict = None) -> dict:
        cache_key = f"{source_name}:{json.dumps(params or {}, sort_keys=True)}"
        cached = self.cache.get(cache_key)
        if cached:
            cached_time = datetime.fromisoformat(cached["timestamp"])
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return cached["data"]

        source = self.data_sources.get(source_name)
        if not source:
            return {"error": f"Source {source_name} not found"}

        data = source(params or {})
        self.cache[cache_key] = {"data": data, "timestamp": datetime.now().isoformat()}
        return data

    def get_multiple(self, sources: list[dict]) -> dict:
        results = {}
        for source_config in sources:
            name = source_config["name"]
            params = source_config.get("params", {})
            results[name] = self.get_data(name, params)
        return results

    def invalidate_cache(self, source_name: str = None):
        if source_name:
            self.cache = {k: v for k, v in self.cache.items() if not k.startswith(source_name)}
        else:
            self.cache.clear()


class KPICalculator:
    """Idea 27: KPI Calculator"""

    def __init__(self):
        self.kpis: dict[str, dict] = {}
        self.targets: dict[str, float] = {}

    def define_kpi(self, name: str, formula: str, description: str = ""):
        self.kpis[name] = {"formula": formula, "description": description, "history": []}
        return self

    def set_target(self, kpi_name: str, target: float):
        self.targets[kpi_name] = target
        return self

    def record_value(self, kpi_name: str, value: float, date: str = None):
        if kpi_name not in self.kpis:
            self.kpis[kpi_name] = {"formula": "", "description": "", "history": []}
        self.kpis[kpi_name]["history"].append({
            "value": value,
            "date": date or datetime.now().isoformat(),
        })

    def calculate(self, kpi_name: str, data: dict = None) -> dict:
        kpi = self.kpis.get(kpi_name, {})
        history = kpi.get("history", [])
        target = self.targets.get(kpi_name)

        if not history:
            return {"kpi": kpi_name, "value": None, "status": "no_data"}

        current = history[-1]["value"]
        previous = history[-2]["value"] if len(history) > 1 else None
        change = ((current - previous) / previous * 100) if previous and previous != 0 else None

        result = {
            "kpi": kpi_name,
            "current_value": current,
            "previous_value": previous,
            "change_pct": round(change, 2) if change is not None else None,
            "target": target,
            "on_target": current >= target if target is not None else None,
        }

        if target:
            result["achievement_pct"] = round((current / target) * 100, 2)

        return result

    def get_all_kpis(self) -> dict:
        return {name: self.calculate(name) for name in self.kpis}


class TrendIndicator:
    """Idea 28: Trend Indicator (Up/Down/Stable)"""

    @staticmethod
    def analyze(values: list[float], threshold: float = 2.0) -> dict:
        if len(values) < 2:
            return {"direction": "stable", "change": 0, "confidence": 0}

        recent = values[-1]
        previous = values[-2]
        change = recent - previous
        pct_change = (change / previous * 100) if previous != 0 else 0

        if abs(pct_change) < threshold:
            direction = "stable"
        elif change > 0:
            direction = "up"
        else:
            direction = "down"

        if len(values) >= 3:
            changes = [values[i] - values[i - 1] for i in range(1, len(values))]
            consistent = all(c > 0 for c in changes[-3:]) or all(c < 0 for c in changes[-3:])
            confidence = 0.9 if consistent else 0.6
        else:
            confidence = 0.5

        return {
            "direction": direction,
            "change": round(change, 4),
            "pct_change": round(pct_change, 2),
            "confidence": confidence,
            "values": values[-5:],
        }

    @staticmethod
    def sparkline(values: list[float], width: int = 10) -> str:
        blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        if not values:
            return ""
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        sampled = values[-width:] if len(values) > width else values
        return "".join(blocks[min(int((v - min_val) / range_val * 7), 7)] for v in sampled)

    @staticmethod
    def trend_strength(values: list[float]) -> dict:
        if len(values) < 3:
            return {"strength": "insufficient_data"}

        changes = [values[i] - values[i - 1] for i in range(1, len(values))]
        positive = sum(1 for c in changes if c > 0)
        negative = sum(1 for c in changes if c < 0)
        total = len(changes)

        consistency = max(positive, negative) / total
        avg_magnitude = sum(abs(c) for c in changes) / total

        return {
            "strength": "strong" if consistency > 0.7 else "moderate" if consistency > 0.5 else "weak",
            "consistency": round(consistency, 2),
            "avg_magnitude": round(avg_magnitude, 4),
            "direction": "up" if positive > negative else "down" if negative > positive else "mixed",
        }


class ComparisonReport:
    """Idea 29: Comparison Report (Period-over-Period)"""

    def __init__(self):
        self.metrics: dict[str, dict] = {}

    def add_metric(self, name: str, current: float, previous: float, target: float = None):
        self.metrics[name] = {"current": current, "previous": previous, "target": target}
        return self

    def from_records(self, current_records: list[dict], previous_records: list[dict],
                     metric_field: str, group_field: str = None):
        if group_field:
            current_agg = defaultdict(list)
            previous_agg = defaultdict(list)
            for r in current_records:
                current_agg[r.get(group_field, "total")].append(r.get(metric_field, 0))
            for r in previous_records:
                previous_agg[r.get(group_field, "total")].append(r.get(metric_field, 0))

            all_groups = set(current_agg.keys()) | set(previous_agg.keys())
            for group in all_groups:
                curr = sum(current_agg.get(group, []))
                prev = sum(previous_agg.get(group, []))
                self.metrics[group] = {"current": curr, "previous": prev}
        else:
            curr = sum(r.get(metric_field, 0) for r in current_records)
            prev = sum(r.get(metric_field, 0) for r in previous_records)
            self.metrics["total"] = {"current": curr, "previous": prev}

    def generate(self) -> dict:
        results = {}
        for name, data in self.metrics.items():
            change = data["current"] - data["previous"]
            pct_change = (change / data["previous"] * 100) if data["previous"] != 0 else 0

            result = {
                "current": data["current"],
                "previous": data["previous"],
                "absolute_change": round(change, 4),
                "pct_change": round(pct_change, 2),
                "trend": "up" if change > 0 else "down" if change < 0 else "stable",
            }

            if data.get("target") is not None:
                result["target"] = data["target"]
                result["vs_target"] = round((data["current"] / data["target"]) * 100, 2) if data["target"] != 0 else 0

            results[name] = result

        return {
            "metrics": results,
            "generated_at": datetime.now().isoformat(),
        }


class ExecutiveSummaryGenerator:
    """Idea 30: Executive Summary Generator"""

    def __init__(self):
        self.sections: list[dict] = []
        self.kpis: dict[str, dict] = {}
        self.highlights: list[str] = []
        self.risks: list[str] = []

    def add_section(self, title: str, content: str):
        self.sections.append({"title": title, "content": content})
        return self

    def add_kpi(self, name: str, value: Any, status: str = "neutral"):
        self.kpis[name] = {"value": value, "status": status}
        return self

    def add_highlight(self, text: str):
        self.highlights.append(text)
        return self

    def add_risk(self, text: str):
        self.risks.append(text)
        return self

    def generate(self) -> dict:
        summary = {
            "generated_at": datetime.now().isoformat(),
            "kpis": self.kpis,
            "highlights": self.highlights,
            "risks": self.risks,
            "sections": self.sections,
        }

        kpi_summary = []
        for name, kpi in self.kpis.items():
            emoji = "+" if kpi["status"] == "positive" else "-" if kpi["status"] == "negative" else "="
            kpi_summary.append(f"{name}: {kpi['value']} ({emoji})")

        text_summary = "Key Metrics:\n" + "\n".join(kpi_summary)
        if self.highlights:
            text_summary += "\n\nHighlights:\n" + "\n".join(f"  * {h}" for h in self.highlights)
        if self.risks:
            text_summary += "\n\nRisks:\n" + "\n".join(f"  ! {r}" for r in self.risks)

        summary["text_summary"] = text_summary
        return summary
