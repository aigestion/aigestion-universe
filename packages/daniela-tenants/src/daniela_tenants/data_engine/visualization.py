"""Visualization - Ideas 41-50."""

import math
import json
from datetime import datetime
from typing import Any, Dict, List
from collections import defaultdict, Counter


class ChartGenerator:
    """Idea 41: Chart Generator (Line/Bar/Pie/Scatter)"""

    def __init__(self):
        self.themes = {
            "default": ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
                        "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"],
            "pastel": ["#a8d8ea", "#aa96da", "#fcbad3", "#ffffd2", "#b5ead7"],
            "dark": ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7"],
        }

    def line_chart(self, labels: List[str], datasets: List[dict],
                   title: str = "", width: int = 800, height: int = 400) -> dict:
        return {
            "type": "line",
            "title": title,
            "width": width,
            "height": height,
            "labels": labels,
            "datasets": datasets,
            "options": {"grid": True, "legend": True, "dots": True},
        }

    def bar_chart(self, labels: List[str], datasets: List[dict],
                  title: str = "", stacked: bool = False) -> dict:
        return {
            "type": "bar",
            "title": title,
            "labels": labels,
            "datasets": datasets,
            "stacked": stacked,
            "options": {"grid": True, "legend": True},
        }

    def pie_chart(self, labels: List[str], values: List[float],
                  title: str = "", donut: bool = False) -> dict:
        total = sum(values) if values else 1
        slices = []
        theme = self.themes["default"]
        for i, (label, value) in enumerate(zip(labels, values)):
            slices.append({
                "label": label,
                "value": value,
                "percentage": round(value / total * 100, 2),
                "color": theme[i % len(theme)],
            })
        return {
            "type": "donut" if donut else "pie",
            "title": title,
            "slices": slices,
            "total": total,
        }

    def scatter_chart(self, points: List[dict], title: str = "",
                      x_label: str = "X", y_label: str = "Y") -> dict:
        return {
            "type": "scatter",
            "title": title,
            "x_label": x_label,
            "y_label": y_label,
            "points": points,
            "options": {"grid": True, "legend": True},
        }

    def area_chart(self, labels: List[str], datasets: List[dict],
                   title: str = "", stacked: bool = False) -> dict:
        return {
            "type": "area",
            "title": title,
            "labels": labels,
            "datasets": datasets,
            "stacked": stacked,
        }

    def to_svg(self, chart: dict) -> str:
        chart_type = chart.get("type", "bar")
        w = chart.get("width", 400)
        h = chart.get("height", 300)

        svg = [f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">']
        svg.append(f'<rect width="{w}" height="{h}" fill="white"/>')

        if chart_type == "bar" and "labels" in chart and "datasets" in chart:
            labels = chart["labels"]
            datasets = chart["datasets"]
            bar_width = (w - 80) / max(len(labels), 1)
            max_val = max((max(d.get("values", [0])) for d in datasets), default=1)

            for i, label in enumerate(labels):
                x = 40 + i * bar_width
                for j, dataset in enumerate(datasets):
                    values = dataset.get("values", [])
                    val = values[i] if i < len(values) else 0
                    bar_h = (val / max_val) * (h - 80) if max_val > 0 else 0
                    color = self.themes["default"][j % len(self.themes["default"])]
                    svg.append(f'<rect x="{x + j * 4}" y="{h - 40 - bar_h}" width="{bar_width - 8}" height="{bar_h}" fill="{color}"/>')
                svg.append(f'<text x="{x + bar_width / 2}" y="{h - 10}" text-anchor="middle" font-size="10">{label}</text>')

        svg.append("</svg>")
        return "\n".join(svg)


class HeatmapGenerator:
    """Idea 42: Heatmap Generator"""

    def __init__(self):
        self.color_scales = {
            "red": ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"],
            "blue": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"],
            "green": ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#006d2c", "#00441b"],
            "viridis": ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#fde725"],
        }

    def generate(self, data: List[List[float]], row_labels: List[str],
                 col_labels: List[str], title: str = "", color_scale: str = "red") -> dict:
        flat_values = [v for row in data for v in row]
        min_val = min(flat_values) if flat_values else 0
        max_val = max(flat_values) if flat_values else 1
        range_val = max_val - min_val if max_val != min_val else 1

        colors = self.color_scales.get(color_scale, self.color_scales["red"])
        colored_data = []
        for row in data:
            colored_row = []
            for val in row:
                idx = int(((val - min_val) / range_val) * (len(colors) - 1))
                colored_row.append({"value": val, "color": colors[min(idx, len(colors) - 1)]})
            colored_data.append(colored_row)

        return {
            "type": "heatmap",
            "title": title,
            "row_labels": row_labels,
            "col_labels": col_labels,
            "data": colored_data,
            "min": min_val,
            "max": max_val,
            "color_scale": color_scale,
        }

    def to_svg(self, heatmap: dict, cell_size: int = 40) -> str:
        rows = len(heatmap["data"])
        cols = len(heatmap["col_labels"]) if heatmap["data"] else 0
        w = cols * cell_size + 100
        h = rows * cell_size + 60

        svg = [f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">']
        svg.append(f'<rect width="{w}" height="{h}" fill="white"/>')

        for i, row in enumerate(heatmap["data"]):
            for j, cell in enumerate(row):
                x = 80 + j * cell_size
                y = 20 + i * cell_size
                svg.append(f'<rect x="{x}" y="{y}" width="{cell_size - 2}" height="{cell_size - 2}" fill="{cell["color"]}"/>')
                svg.append(f'<text x="{x + cell_size / 2}" y="{y + cell_size / 2 + 4}" text-anchor="middle" font-size="10" fill="white">{cell["value"]}</text>')

        for i, label in enumerate(heatmap["row_labels"]):
            svg.append(f'<text x="75" y="{20 + i * cell_size + cell_size / 2 + 4}" text-anchor="end" font-size="10">{label}</text>')

        for j, label in enumerate(heatmap["col_labels"]):
            svg.append(f'<text x="{80 + j * cell_size + cell_size / 2}" y="15" text-anchor="middle" font-size="10">{label}</text>')

        svg.append("</svg>")
        return "\n".join(svg)


class TreemapVisualizer:
    """Idea 43: Treemap Visualization"""

    def __init__(self):
        self.colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
                       "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]

    def generate(self, data: dict, title: str = "") -> dict:
        total = sum(data.values()) if data else 1
        items = []
        for i, (name, value) in enumerate(data.items()):
            items.append({
                "name": name,
                "value": value,
                "percentage": round(value / total * 100, 2),
                "color": self.colors[i % len(self.colors)],
            })

        items.sort(key=lambda x: x["value"], reverse=True)
        return {"type": "treemap", "title": title, "items": items, "total": total}

    def from_nested(self, data: dict, title: str = "") -> dict:
        flat = {}
        self._flatten(data, "", flat)
        return self.generate(flat, title)

    def _flatten(self, data: dict, prefix: str, result: dict):
        for key, value in data.items():
            full_key = f"{prefix}/{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten(value, full_key, result)
            else:
                result[full_key] = value


class NetworkGraphVisualizer:
    """Idea 44: Network Graph Visualization"""

    def __init__(self):
        self.nodes: List[dict] = []
        self.edges: List[dict] = []

    def add_node(self, id: str, label: str, size: float = 10, group: str = None):
        self.nodes.append({"id": id, "label": label, "size": size, "group": group})

    def add_edge(self, source: str, target: str, weight: float = 1, label: str = ""):
        self.edges.append({"source": source, "target": target, "weight": weight, "label": label})

    def from_data(self, nodes: List[dict], edges: List[dict]):
        self.nodes = nodes
        self.edges = edges

    def layout_force(self, iterations: int = 100, damping: float = 0.9) -> dict:
        positions = {}
        for node in self.nodes:
            positions[node["id"]] = {
                "x": hash(node["id"]) % 1000 / 1000,
                "y": hash(node["id"] + "y") % 1000 / 1000,
            }

        for _ in range(iterations):
            forces = {nid: {"x": 0, "y": 0} for nid in positions}

            for i, n1 in enumerate(self.nodes):
                for n2 in self.nodes[i + 1:]:
                    dx = positions[n2["id"]]["x"] - positions[n1["id"]]["x"]
                    dy = positions[n2["id"]]["y"] - positions[n1["id"]]["y"]
                    dist = math.sqrt(dx * dx + dy * dy) or 0.01
                    force = 0.01 / (dist * dist)
                    forces[n1["id"]]["x"] -= force * dx / dist
                    forces[n1["id"]]["y"] -= force * dy / dist
                    forces[n2["id"]]["x"] += force * dx / dist
                    forces[n2["id"]]["y"] += force * dy / dist

            for edge in self.edges:
                dx = positions[edge["target"]]["x"] - positions[edge["source"]]["x"]
                dy = positions[edge["target"]]["y"] - positions[edge["source"]]["y"]
                dist = math.sqrt(dx * dx + dy * dy) or 0.01
                force = (dist - 0.1) * 0.01
                forces[edge["source"]]["x"] += force * dx / dist
                forces[edge["source"]]["y"] += force * dy / dist
                forces[edge["target"]]["x"] -= force * dx / dist
                forces[edge["target"]]["y"] -= force * dy / dist

            for nid in positions:
                positions[nid]["x"] += forces[nid]["x"] * damping
                positions[nid]["y"] += forces[nid]["y"] * damping
                positions[nid]["x"] = max(0.05, min(0.95, positions[nid]["x"]))
                positions[nid]["y"] = max(0.05, min(0.95, positions[nid]["y"]))

        return {"nodes": self.nodes, "edges": self.edges, "positions": positions}

    def get_degree(self, node_id: str) -> int:
        return sum(1 for e in self.edges if e["source"] == node_id or e["target"] == node_id)

    def get_centrality(self) -> Dict[str, float]:
        n = len(self.nodes)
        if n <= 1:
            return {node["id"]: 1.0 for node in self.nodes}
        degrees = {node["id"]: self.get_degree(node["id"]) for node in self.nodes}
        max_degree = max(degrees.values()) or 1
        return {nid: d / max_degree for nid, d in degrees.items()}


class GeographicMapVisualizer:
    """Idea 45: Geographic Map Visualization"""

    def __init__(self):
        self.markers: List[dict] = []
        self.regions: List[dict] = []

    def add_marker(self, lat: float, lon: float, label: str, value: float = 0,
                   color: str = "#4e79a7", size: float = 10):
        self.markers.append({
            "lat": lat, "lon": lon, "label": label,
            "value": value, "color": color, "size": size,
        })

    def add_region(self, name: str, coordinates: List[List[float]], value: float = 0,
                   color: str = "#4e79a7"):
        self.regions.append({
            "name": name, "coordinates": coordinates,
            "value": value, "color": color,
        })

    def from_data(self, records: List[dict], lat_field: str = "lat",
                  lon_field: str = "lon", label_field: str = "name",
                  value_field: str = "value"):
        for record in records:
            self.add_marker(
                lat=record.get(lat_field, 0),
                lon=record.get(lon_field, 0),
                label=record.get(label_field, ""),
                value=record.get(value_field, 0),
            )

    def get_bounds(self) -> dict:
        if not self.markers:
            return {"min_lat": 0, "max_lat": 0, "min_lon": 0, "max_lon": 0}
        lats = [m["lat"] for m in self.markers]
        lons = [m["lon"] for m in self.markers]
        return {
            "min_lat": min(lats), "max_lat": max(lats),
            "min_lon": min(lons), "max_lon": max(lons),
        }

    def to_geojson(self) -> dict:
        features = []
        for marker in self.markers:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [marker["lon"], marker["lat"]]},
                "properties": {
                    "label": marker["label"],
                    "value": marker["value"],
                    "color": marker["color"],
                },
            })

        for region in self.regions:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [region["coordinates"]]},
                "properties": {
                    "name": region["name"],
                    "value": region["value"],
                    "color": region["color"],
                },
            })

        return {"type": "FeatureCollection", "features": features}


class SparklineGenerator:
    """Idea 46: Sparkline Generator"""

    def __init__(self):
        self.block_chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    def text_sparkline(self, values: List[float], width: int = 20) -> str:
        if not values:
            return ""
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        if len(values) > width:
            step = len(values) / width
            sampled = [values[int(i * step)] for i in range(width)]
        else:
            sampled = values

        return "".join(self.block_chars[min(int((v - min_val) / range_val * 7), 7)] for v in sampled)

    def svg_sparkline(self, values: List[float], width: int = 200, height: int = 50,
                      color: str = "#4e79a7", fill: bool = False) -> str:
        if not values:
            return f'<svg width="{width}" height="{height}"></svg>'

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        points = []
        for i, v in enumerate(values):
            x = (i / max(len(values) - 1, 1)) * width
            y = height - ((v - min_val) / range_val) * (height - 4) - 2
            points.append(f"{x},{y}")

        polyline = " ".join(points)

        svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
        if fill:
            first_x = points[0].split(",")[0]
            last_x = points[-1].split(",")[0]
            svg.append(f'<polygon points="{first_x},{height} {polyline} {last_x},{height}" fill="{color}" opacity="0.2"/>')
        svg.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2"/>')
        svg.append("</svg>")
        return "\n".join(svg)

    def comparison_sparkline(self, datasets: Dict[str, List[float]], width: int = 200, height: int = 50) -> dict:
        colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]
        result = {}
        for i, (name, values) in enumerate(datasets.items()):
            result[name] = {
                "text": self.text_sparkline(values),
                "svg": self.svg_sparkline(values, width, height, colors[i % len(colors)]),
            }
        return result


class GaugeMeterVisualizer:
    """Idea 47: Gauge/Meter Visualization"""

    def __init__(self):
        self.default_ranges = [
            {"min": 0, "max": 30, "color": "#e15759", "label": "Low"},
            {"min": 30, "max": 70, "color": "#f28e2b", "label": "Medium"},
            {"min": 70, "max": 100, "color": "#59a14f", "label": "High"},
        ]

    def gauge(self, value: float, min_val: float = 0, max_val: float = 100,
              title: str = "", ranges: List[dict] = None) -> dict:
        ranges = ranges or self.default_ranges
        percentage = ((value - min_val) / (max_val - min_val) * 100) if max_val != min_val else 0
        percentage = max(0, min(100, percentage))

        status = "unknown"
        for r in ranges:
            if r["min"] <= percentage <= r["max"]:
                status = r.get("label", "unknown")
                break

        return {
            "type": "gauge",
            "title": title,
            "value": value,
            "min": min_val,
            "max": max_val,
            "percentage": round(percentage, 2),
            "status": status,
            "ranges": ranges,
        }

    def svg_gauge(self, gauge_data: dict, size: int = 200) -> str:
        percentage = gauge_data.get("percentage", 0)
        cx, cy, r = size // 2, size // 2 + 20, size // 2 - 20
        start_angle = math.pi
        end_angle = 2 * math.pi
        value_angle = start_angle + (percentage / 100) * (end_angle - start_angle)

        def arc_point(angle):
            return cx + r * math.cos(angle), cy + r * math.sin(angle)

        svg = [f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">']

        x1, y1 = arc_point(start_angle)
        x2, y2 = arc_point(end_angle)
        svg.append(f'<path d="M {x1} {y1} A {r} {r} 0 1 1 {x2} {y2}" fill="none" stroke="#eee" stroke-width="20"/>')

        xv, yv = arc_point(value_angle)
        color = "#59a14f" if percentage >= 70 else "#f28e2b" if percentage >= 30 else "#e15759"
        svg.append(f'<path d="M {x1} {y1} A {r} {r} 0 {"1" if percentage > 50 else "0"} 1 {xv} {yv}" fill="none" stroke="{color}" stroke-width="20"/>')

        svg.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="24" font-weight="bold">{percentage:.0f}%</text>')
        svg.append(f'<text x="{cx}" y="{cy + 25}" text-anchor="middle" font-size="12" fill="#666">{gauge_data.get("status", "")}</text>')
        svg.append("</svg>")
        return "\n".join(svg)

    def speedometer(self, value: float, max_val: float = 100, title: str = "") -> dict:
        return self.gauge(value, 0, max_val, title, [
            {"min": 0, "max": 20, "color": "#cb181d", "label": "Critical"},
            {"min": 20, "max": 40, "color": "#ef3b2c", "label": "Warning"},
            {"min": 40, "max": 60, "color": "#f28e2b", "label": "Moderate"},
            {"min": 60, "max": 80, "color": "#76b7b2", "label": "Good"},
            {"min": 80, "max": 100, "color": "#59a14f", "label": "Excellent"},
        ])


class TimelineVisualizer:
    """Idea 48: Timeline Visualization"""

    def __init__(self):
        self.events: List[dict] = []
        self.groups: Dict[str, dict] = {}

    def add_event(self, start: str, end: str = None, label: str = "",
                  group: str = "default", color: str = None, data: dict = None):
        self.events.append({
            "start": start,
            "end": end or start,
            "label": label,
            "group": group,
            "color": color,
            "data": data or {},
        })

    def add_group(self, group_id: str, label: str, color: str = "#4e79a7"):
        self.groups[group_id] = {"label": label, "color": color}

    def from_records(self, records: List[dict], start_field: str = "start",
                     end_field: str = "end", label_field: str = "label",
                     group_field: str = "group"):
        for record in records:
            self.add_event(
                start=record.get(start_field, ""),
                end=record.get(end_field, ""),
                label=record.get(label_field, ""),
                group=record.get(group_field, "default"),
            )

    def get_span(self) -> dict:
        if not self.events:
            return {"start": "", "end": ""}
        starts = [e["start"] for e in self.events]
        ends = [e["end"] for e in self.events]
        return {"start": min(starts), "end": max(ends)}

    def get_grouped(self) -> Dict[str, List[dict]]:
        grouped = defaultdict(list)
        for event in self.events:
            grouped[event["group"]].append(event)
        return dict(grouped)

    def to_dict(self) -> dict:
        return {
            "events": self.events,
            "groups": self.groups,
            "span": self.get_span(),
            "total_events": len(self.events),
        }


class WordCloudGenerator:
    """Idea 49: Word Cloud Generator"""

    def __init__(self):
        self.stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                           "being", "have", "has", "had", "do", "does", "did", "will",
                           "would", "could", "should", "may", "might", "must", "shall",
                           "can", "need", "dare", "ought", "used", "to", "of", "in",
                           "for", "on", "with", "at", "by", "from", "as", "into",
                           "through", "during", "before", "after", "above", "below",
                           "between", "out", "off", "over", "under", "again", "further",
                           "then", "once", "here", "there", "when", "where", "why", "how"}

    def process_text(self, text: str, min_length: int = 3) -> Dict[str, int]:
        import re
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        words = [w for w in words if len(w) >= min_length and w not in self.stop_words]
        return dict(Counter(words))

    def generate(self, word_freq: Dict[str, int], max_words: int = 100) -> dict:
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_words]
        if not sorted_words:
            return {"words": [], "max_count": 0}

        max_count = sorted_words[0][1]
        min_count = sorted_words[-1][1]
        range_count = max_count - min_count if max_count != min_count else 1

        colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
                  "#edc948", "#b07aa1", "#ff9da7", "#9c755f"]

        words = []
        for i, (word, count) in enumerate(sorted_words):
            normalized = (count - min_count) / range_count
            size = 12 + normalized * 48
            color = colors[i % len(colors)]
            rotation = 0 if normalized > 0.5 else 90 if normalized < 0.2 else 0
            words.append({
                "word": word,
                "count": count,
                "size": round(size, 1),
                "color": color,
                "rotation": rotation,
                "weight": round(normalized, 2),
            })

        return {"words": words, "max_count": max_count, "total_words": len(words)}

    def from_text(self, text: str, max_words: int = 100) -> dict:
        word_freq = self.process_text(text)
        return self.generate(word_freq, max_words)


class DashboardWidgetLibrary:
    """Idea 50: Dashboard Widget Library"""

    def __init__(self):
        self.widgets: Dict[str, dict] = {}
        self.themes = {
            "light": {"bg": "#ffffff", "text": "#333333", "border": "#e0e0e0", "accent": "#4e79a7"},
            "dark": {"bg": "#1a1a1a", "text": "#ffffff", "border": "#333333", "accent": "#6baed6"},
        }

    def create_widget(self, widget_type: str, title: str, data: Any,
                      config: dict = None) -> dict:
        widget_id = f"widget_{len(self.widgets) + 1}"
        widget = {
            "id": widget_id,
            "type": widget_type,
            "title": title,
            "data": data,
            "config": config or {},
            "created_at": datetime.now().isoformat(),
        }
        self.widgets[widget_id] = widget
        return widget

    def metric_widget(self, title: str, value: Any, change: float = None,
                      icon: str = None) -> dict:
        return self.create_widget("metric", title, {
            "value": value,
            "change": change,
            "icon": icon,
        }, {"show_change": change is not None})

    def chart_widget(self, title: str, chart_type: str, data: dict) -> dict:
        return self.create_widget("chart", title, data, {"chart_type": chart_type})

    def table_widget(self, title: str, headers: List[str], rows: List[List[Any]],
                     pagination: bool = True) -> dict:
        return self.create_widget("table", title, {
            "headers": headers,
            "rows": rows,
        }, {"pagination": pagination, "page_size": 10})

    def list_widget(self, title: str, items: List[dict]) -> dict:
        return self.create_widget("list", title, items)

    def progress_widget(self, title: str, current: float, target: float,
                        label: str = "") -> dict:
        percentage = (current / target * 100) if target > 0 else 0
        return self.create_widget("progress", title, {
            "current": current,
            "target": target,
            "percentage": round(percentage, 2),
            "label": label,
        })

    def text_widget(self, title: str, content: str, format: str = "plain") -> dict:
        return self.create_widget("text", title, content, {"format": format})

    def dashboard_layout(self, widgets: List[dict], columns: int = 3) -> dict:
        rows = []
        current_row = []
        for widget in widgets:
            current_row.append(widget)
            if len(current_row) >= columns:
                rows.append(current_row)
                current_row = []
        if current_row:
            rows.append(current_row)

        return {
            "layout": "grid",
            "columns": columns,
            "rows": rows,
            "total_widgets": len(widgets),
        }

    def render_widget_html(self, widget: dict, theme: str = "light") -> str:
        theme_data = self.themes.get(theme, self.themes["light"])
        wtype = widget.get("type", "text")
        title = widget.get("title", "")
        data = widget.get("data", {})

        html = [f'<div class="widget" style="background:{theme_data["bg"]};border:1px solid {theme_data["border"]};padding:16px;border-radius:8px;margin:8px;">']
        html.append(f'<h3 style="color:{theme_data["text"]};margin:0 0 12px 0;">{title}</h3>')

        if wtype == "metric":
            value = data.get("value", "")
            change = data.get("change")
            html.append(f'<div style="font-size:28px;font-weight:bold;color:{theme_data["accent"]};">{value}</div>')
            if change is not None:
                color = "#59a14f" if change >= 0 else "#e15759"
                arrow = "+" if change >= 0 else ""
                html.append(f'<div style="color:{color};font-size:14px;">{arrow}{change}%</div>')
        elif wtype == "text":
            html.append(f'<p style="color:{theme_data["text"]};">{data}</p>')
        elif wtype == "progress":
            pct = data.get("percentage", 0)
            html.append('<div style="background:#eee;border-radius:4px;height:20px;">')
            html.append(f'<div style="background:{theme_data["accent"]};width:{pct}%;height:100%;border-radius:4px;"></div>')
            html.append('</div>')
            html.append(f'<div style="text-align:center;margin-top:4px;">{pct}%</div>')
        else:
            html.append(f'<pre style="font-size:12px;">{json.dumps(data, indent=2)[:500]}</pre>')

        html.append("</div>")
        return "\n".join(html)
