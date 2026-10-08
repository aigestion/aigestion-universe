"""Flask Server - Data Engine API on port 9870."""

from datetime import datetime

from flask import Flask, jsonify, request

from .analytics import (
    ABTestAnalytics,
    CohortAnalysis,
    CorrelationAnalysis,
    FunnelAnalysis,
    MetricsAggregator,
    MovingAverageCalculator,
    PercentileCalculator,
    RegressionAnalysis,
    RetentionAnalysis,
    StatisticalSignificanceCalculator,
)
from .pipeline import (
    BatchPipeline,
    DataValidationPipeline,
    DeduplicationPipeline,
    ETLPipeline,
    PipelineMonitor,
)
from .reports import (
    ExcelCSVExporter,
    ExecutiveSummaryGenerator,
    HTMLReportGenerator,
    PDFReportGenerator,
)
from .storage import (
    DocumentStore,
    FullTextSearchEngine,
    KeyValueCacheStore,
    TimeSeriesStore,
)
from .visualization import (
    ChartGenerator,
    GaugeMeterVisualizer,
    HeatmapGenerator,
    SparklineGenerator,
    TreemapVisualizer,
    WordCloudGenerator,
)

app = Flask(__name__)

pipeline_monitor = PipelineMonitor()
metrics_agg = MetricsAggregator()
ts_store = TimeSeriesStore()
cache_store = KeyValueCacheStore()
doc_store = DocumentStore()
search_engine = FullTextSearchEngine()
chart_gen = ChartGenerator()


@app.route("/api/data/status", methods=["GET"])
def status():
    return jsonify({
        "status": "running",
        "service": "data_engine",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "pipeline": "/api/data/pipeline",
            "analytics": "/api/data/analytics",
            "reports": "/api/data/reports",
            "visualize": "/api/data/visualize",
            "storage": "/api/data/storage",
        },
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "data_engine"})


@app.route("/api/data/pipeline", methods=["POST"])
def pipeline_create():
    data = request.get_json() or {}
    action = data.get("action", "create")

    if action == "create":
        name = data.get("name", "default_pipeline")
        ETLPipeline(name)
        pipeline_monitor.record_metric(name, "created", 1)
        return jsonify({"status": "created", "pipeline": name})

    elif action == "validate":
        rules = data.get("rules", [])
        payload = data.get("data", {})
        validator = DataValidationPipeline()
        for rule in rules:
            if rule.get("type") == "required":
                validator.required_field(rule["field"])
            elif rule.get("type") == "type":
                validator.type_check(rule["field"], eval(rule["expected_type"]))
            elif rule.get("type") == "range":
                validator.range_check(rule["field"], rule.get("min"), rule.get("max"))
        result = validator.validate(payload)
        return jsonify(result)

    elif action == "deduplicate":
        records = data.get("records", [])
        key_fields = data.get("key_fields", [])
        dedup = DeduplicationPipeline()
        dedup.set_key_fields(key_fields)
        result = dedup.deduplicate(records)
        return jsonify(result)

    elif action == "batch":
        items = data.get("items", [])
        batch_size = data.get("batch_size", 100)
        bp = BatchPipeline(batch_size)
        bp.add_job("process", lambda x: x, items)
        result = bp.run_all()
        return jsonify(result)

    return jsonify({"error": "Invalid action"}), 400


@app.route("/api/data/pipeline/status", methods=["GET"])
def pipeline_status():
    dashboard = pipeline_monitor.get_dashboard()
    return jsonify(dashboard)


@app.route("/api/data/analytics", methods=["POST"])
def analytics():
    data = request.get_json() or {}
    analysis_type = data.get("type", "metrics")

    if analysis_type == "metrics":
        metrics_agg.increment(data.get("name", "counter"), data.get("value", 1))
        return jsonify(metrics_agg.get_all())

    elif analysis_type == "cohorts":
        records = data.get("records", [])
        cohort = CohortAnalysis()
        cohort.set_keys(
            data.get("cohort_key", "cohort"),
            data.get("period_key", "period"),
            data.get("value_key", "value"),
        )
        cohort.add_data(records)
        return jsonify(cohort.analyze())

    elif analysis_type == "funnels":
        steps = data.get("steps", {})
        funnel = FunnelAnalysis()
        for step_name, count in steps.items():
            funnel.add_step(step_name, count)
        return jsonify(funnel.analyze())

    elif analysis_type == "retention":
        records = data.get("records", [])
        retention = RetentionAnalysis()
        retention.from_records(
            records,
            data.get("user_key", "user_id"),
            data.get("date_key", "date"),
        )
        return jsonify(retention.calculate_retention(
            data.get("period_days", 30),
            data.get("num_periods", 12),
        ))

    elif analysis_type == "ab_test":
        experiment = data.get("experiment", "test")
        variants = data.get("variants", ["A", "B"])
        ab = ABTestAnalytics()
        ab.create_experiment(experiment, variants)
        for event in data.get("events", []):
            ab.record_event(
                experiment,
                event.get("variant", "A"),
                event.get("converted", False),
                event.get("value", 0),
            )
        return jsonify(ab.analyze(experiment))

    elif analysis_type == "significance":
        result = StatisticalSignificanceCalculator.is_significant(
            data.get("p1", 0.1),
            data.get("p2", 0.15),
            data.get("n1", 1000),
            data.get("n2", 1000),
            data.get("alpha", 0.05),
        )
        return jsonify(result)

    elif analysis_type == "percentiles":
        values = data.get("values", [])
        return jsonify(PercentileCalculator.summary(values))

    elif analysis_type == "moving_average":
        values = data.get("values", [])
        window = data.get("window", 5)
        ma_type = data.get("ma_type", "simple")
        if ma_type == "exponential":
            result = MovingAverageCalculator.exponential(values, data.get("span", 5))
        else:
            result = MovingAverageCalculator.simple(values, window)
        return jsonify({"values": result, "type": ma_type})

    elif analysis_type == "correlation":
        x = data.get("x", [])
        y = data.get("y", [])
        method = data.get("method", "pearson")
        if method == "spearman":
            r = CorrelationAnalysis.spearman(x, y)
        else:
            r = CorrelationAnalysis.pearson(x, y)
        return jsonify({
            "correlation": round(r, 4),
            "interpretation": CorrelationAnalysis.interpret(r),
            "method": method,
        })

    elif analysis_type == "regression":
        x = data.get("x", [])
        y = data.get("y", [])
        result = RegressionAnalysis.linear(x, y)
        return jsonify(result)

    return jsonify({"error": "Invalid analysis type"}), 400


@app.route("/api/data/analytics/metrics", methods=["GET"])
def analytics_metrics():
    return jsonify(metrics_agg.get_all())


@app.route("/api/data/analytics/cohorts", methods=["POST"])
def analytics_cohorts():
    data = request.get_json() or {}
    cohort = CohortAnalysis()
    cohort.set_keys(
        data.get("cohort_key", "cohort"),
        data.get("period_key", "period"),
        data.get("value_key", "value"),
    )
    cohort.add_data(data.get("records", []))
    return jsonify(cohort.analyze())


@app.route("/api/data/analytics/funnels", methods=["POST"])
def analytics_funnels():
    data = request.get_json() or {}
    funnel = FunnelAnalysis()
    for step_name, count in data.get("steps", {}).items():
        funnel.add_step(step_name, count)
    return jsonify(funnel.analyze())


@app.route("/api/data/reports", methods=["POST"])
def reports():
    data = request.get_json() or {}
    report_type = data.get("type", "pdf")

    if report_type == "pdf":
        gen = PDFReportGenerator()
        gen.set_metadata(data.get("title", "Report"))
        for section in data.get("sections", []):
            if section.get("type") == "table":
                gen.add_table_page(section.get("headers", []), section.get("rows", []))
            else:
                gen.add_text_page(section.get("content", ""))
        return jsonify({"html": gen.generate_html(), "base64": gen.to_base64()})

    elif report_type == "csv":
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        csv_content = ExcelCSVExporter.to_csv(headers, rows)
        return jsonify({"csv": csv_content})

    elif report_type == "html":
        gen = HTMLReportGenerator()
        for section in data.get("sections", []):
            gen.add_section(section.get("title", ""), section.get("content", ""))
        return jsonify({"html": gen.generate()})

    elif report_type == "summary":
        gen = ExecutiveSummaryGenerator()
        for kpi_name, kpi_data in data.get("kpis", {}).items():
            gen.add_kpi(kpi_name, kpi_data.get("value"), kpi_data.get("status", "neutral"))
        for highlight in data.get("highlights", []):
            gen.add_highlight(highlight)
        for risk in data.get("risks", []):
            gen.add_risk(risk)
        return jsonify(gen.generate())

    return jsonify({"error": "Invalid report type"}), 400


@app.route("/api/data/reports/generate", methods=["POST"])
def reports_generate():
    data = request.get_json() or {}

    gen = HTMLReportGenerator()
    gen.add_section("Report", f"Generated at {datetime.now().isoformat()}")
    if "data" in data:
        gen.add_table_section("Data", list(data["data"][0].keys()) if data["data"] else [],
                              [list(r.values()) for r in data["data"]])
    return jsonify({"html": gen.generate()})


@app.route("/api/data/reports/export", methods=["POST"])
def reports_export():
    data = request.get_json() or {}
    format_type = data.get("format", "csv")

    if format_type == "csv":
        csv_content = ExcelCSVExporter.dict_list_to_csv(data.get("records", []))
        return jsonify({"csv": csv_content, "format": "csv"})
    elif format_type == "json":
        return jsonify({"data": data.get("records", []), "format": "json"})

    return jsonify({"error": "Invalid format"}), 400


@app.route("/api/data/visualize", methods=["POST"])
def visualize():
    data = request.get_json() or {}
    chart_type = data.get("chart_type", "bar")

    if chart_type == "bar":
        chart = chart_gen.bar_chart(
            data.get("labels", []),
            data.get("datasets", [{"values": data.get("values", []), "label": "Data"}]),
            data.get("title", ""),
        )
    elif chart_type == "line":
        chart = chart_gen.line_chart(
            data.get("labels", []),
            data.get("datasets", [{"values": data.get("values", []), "label": "Data"}]),
            data.get("title", ""),
        )
    elif chart_type == "pie":
        chart = chart_gen.pie_chart(
            data.get("labels", []),
            data.get("values", []),
            data.get("title", ""),
        )
    elif chart_type == "scatter":
        chart = chart_gen.scatter_chart(
            data.get("points", []),
            data.get("title", ""),
        )
    elif chart_type == "heatmap":
        hm = HeatmapGenerator()
        chart = hm.generate(
            data.get("matrix", [[]]),
            data.get("row_labels", []),
            data.get("col_labels", []),
            data.get("title", ""),
        )
    elif chart_type == "treemap":
        tm = TreemapVisualizer()
        chart = tm.generate(data.get("data", {}), data.get("title", ""))
    elif chart_type == "sparkline":
        sp = SparklineGenerator()
        chart = {"text": sp.text_sparkline(data.get("values", [])),
                 "svg": sp.svg_sparkline(data.get("values", []))}
    elif chart_type == "gauge":
        gm = GaugeMeterVisualizer()
        chart = gm.gauge(data.get("value", 0), title=data.get("title", ""))
    elif chart_type == "wordcloud":
        wc = WordCloudGenerator()
        chart = wc.generate(data.get("word_freq", {}))
    else:
        return jsonify({"error": "Invalid chart type"}), 400

    return jsonify(chart)


@app.route("/api/data/visualize/chart", methods=["POST"])
def visualize_chart():
    data = request.get_json() or {}
    chart_type = data.get("chart_type", "bar")

    if chart_type == "bar":
        chart = chart_gen.bar_chart(data.get("labels", []), data.get("datasets", []), data.get("title", ""))
    elif chart_type == "line":
        chart = chart_gen.line_chart(data.get("labels", []), data.get("datasets", []), data.get("title", ""))
    elif chart_type == "pie":
        chart = chart_gen.pie_chart(data.get("labels", []), data.get("values", []), data.get("title", ""))
    else:
        return jsonify({"error": "Invalid chart type"}), 400

    return jsonify(chart)


@app.route("/api/data/visualize/heatmap", methods=["POST"])
def visualize_heatmap():
    data = request.get_json() or {}
    hm = HeatmapGenerator()
    chart = hm.generate(
        data.get("matrix", [[]]),
        data.get("row_labels", []),
        data.get("col_labels", []),
        data.get("title", ""),
        data.get("color_scale", "red"),
    )
    return jsonify(chart)


@app.route("/api/data/visualize/treemap", methods=["POST"])
def visualize_treemap():
    data = request.get_json() or {}
    tm = TreemapVisualizer()
    chart = tm.generate(data.get("data", {}), data.get("title", ""))
    return jsonify(chart)


@app.route("/api/data/storage", methods=["POST"])
def storage():
    data = request.get_json() or {}
    action = data.get("action", "store")

    if action == "store":
        collection = data.get("collection", "default")
        document = data.get("document", {})
        doc_id = doc_store.insert(collection, document)
        return jsonify({"id": doc_id, "collection": collection})

    elif action == "query":
        collection = data.get("collection", "default")
        query = data.get("query", {})
        results = doc_store.find(collection, query)
        return jsonify({"results": results, "count": len(results)})

    elif action == "search":
        query = data.get("query", "")
        limit = data.get("limit", 10)
        results = search_engine.search(query, limit)
        return jsonify({"results": results})

    elif action == "cache_set":
        cache_store.set(data.get("key", ""), data.get("value"), data.get("ttl"))
        return jsonify({"status": "set"})

    elif action == "cache_get":
        value = cache_store.get(data.get("key", ""))
        return jsonify({"value": value, "found": value is not None})

    elif action == "timeseries":
        ts_store.insert(
            data.get("metric", "default"),
            data.get("value", 0),
            data.get("timestamp"),
            data.get("tags"),
        )
        return jsonify({"status": "inserted"})

    elif action == "timeseries_query":
        result = ts_store.query(
            data.get("metric", "default"),
            data.get("start"),
            data.get("end"),
            data.get("aggregation", "avg"),
        )
        return jsonify(result)

    return jsonify({"error": "Invalid action"}), 400


@app.route("/api/data/storage/query", methods=["POST"])
def storage_query():
    data = request.get_json() or {}
    collection = data.get("collection", "default")
    query = data.get("query", {})
    results = doc_store.find(collection, query)
    return jsonify({"results": results, "count": len(results)})


@app.route("/api/data/storage/store", methods=["POST"])
def storage_store():
    data = request.get_json() or {}
    collection = data.get("collection", "default")
    document = data.get("document", {})
    doc_id = doc_store.insert(collection, document)
    return jsonify({"id": doc_id, "collection": collection})


@app.route("/api/data/storage/search", methods=["POST"])
def storage_search():
    data = request.get_json() or {}
    query = data.get("query", "")
    limit = data.get("limit", 10)
    results = search_engine.search(query, limit)
    return jsonify({"results": results})


def create_app():
    return app


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "9870")), debug=False)
