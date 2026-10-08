"""DevTools Engine - Flask server on port 9890."""

import os
import time
from dataclasses import asdict
from functools import wraps

from flask import Flask, jsonify, request

from .code_analysis import (
    APIEndpointMapper,
    ArchitectureFitnessFunctions,
    CodeDuplicationDetector,
    CodeSmellDetector,
    CyclomaticComplexityAnalyzer,
    DatabaseQueryAnalyzer,
    DeadCodeDetector,
    ImportDependencyGraph,
    PerformanceCodeAnalyzer,
    SecurityCodeScanner,
)
from .debugger import (
    CPUProfiler,
    DebugSessionReplay,
    IOProfiler,
    LiveVariableInspector,
    MemoryProfiler,
    PerformanceHotspotFinder,
    RequestResponseLogger,
    ResourceLeakDetector,
    StackTraceVisualizer,
    ThreadDeadlockDetector,
)
from .documentation import (
    APIDocumentationGenerator,
    ArchitectureDiagramGenerator,
    ChangelogGenerator,
    CodeDocumentationGenerator,
    DatabaseSchemaDocumentation,
    DeploymentGuideGenerator,
    EnvironmentVariableDocumentation,
    KnowledgeBaseBuilder,
    READMEGenerator,
    RunbookGenerator,
)
from .profiling import (
    BundleSizeAnalyzer,
    CacheHitMissAnalyzer,
    ConcurrencyProfiler,
    DatabaseQueryProfiler,
    EventLoopAnalyzer,
    FunctionCallTracer,
    GarbageCollectionMonitor,
    MemoryAllocationTracker,
    NetworkLatencyProfiler,
    StartupTimeAnalyzer,
)
from .sandbox import (
    APIEndpointTester,
    CronExpressionTester,
    DockerComposeValidator,
    JavaScriptCodeExecutor,
    JSONPathTester,
    PythonCodeExecutor,
    RegexTester,
    SQLQueryTester,
    YAMLJSONValidator,
)

app = Flask(__name__)

_debugger = {
    "variable_inspector": LiveVariableInspector(),
    "request_logger": RequestResponseLogger(),
    "stack_visualizer": StackTraceVisualizer(),
    "memory_profiler": MemoryProfiler(),
    "cpu_profiler": CPUProfiler(),
    "io_profiler": IOProfiler(),
    "deadlock_detector": ThreadDeadlockDetector(),
    "leak_detector": ResourceLeakDetector(),
    "hotspot_finder": PerformanceHotspotFinder(),
    "session_replay": DebugSessionReplay(),
}

_analyzer = {
    "complexity": CyclomaticComplexityAnalyzer(),
    "duplicates": CodeDuplicationDetector(),
    "dead_code": DeadCodeDetector(),
    "imports": ImportDependencyGraph(),
    "api_mapper": APIEndpointMapper(),
    "query_analyzer": DatabaseQueryAnalyzer(),
    "security": SecurityCodeScanner(),
    "perf_analyzer": PerformanceCodeAnalyzer(),
    "smells": CodeSmellDetector(),
    "fitness": ArchitectureFitnessFunctions(),
}

_sandbox = {
    "python": PythonCodeExecutor(),
    "javascript": JavaScriptCodeExecutor(),
    "sql": SQLQueryTester(),
    "api_tester": APIEndpointTester(),
    "regex": RegexTester(),
    "jsonpath": JSONPathTester(),
    "cron": CronExpressionTester(),
    "docker_compose": DockerComposeValidator(),
    "yaml_json": YAMLJSONValidator(),
}

_docs = {
    "api_gen": APIDocumentationGenerator(),
    "code_doc": CodeDocumentationGenerator(),
    "readme": READMEGenerator(),
    "changelog": ChangelogGenerator(),
    "arch_diagram": ArchitectureDiagramGenerator(),
    "db_schema": DatabaseSchemaDocumentation(),
    "env_doc": EnvironmentVariableDocumentation(),
    "deploy_guide": DeploymentGuideGenerator(),
    "runbook": RunbookGenerator(),
    "knowledge_base": KnowledgeBaseBuilder(),
}

_profiler = {
    "call_tracer": FunctionCallTracer(),
    "db_profiler": DatabaseQueryProfiler(),
    "cache_analyzer": CacheHitMissAnalyzer(),
    "network_profiler": NetworkLatencyProfiler(),
    "memory_tracker": MemoryAllocationTracker(),
    "gc_monitor": GarbageCollectionMonitor(),
    "event_loop": EventLoopAnalyzer(),
    "concurrency": ConcurrencyProfiler(),
    "startup": StartupTimeAnalyzer(),
    "bundle": BundleSizeAnalyzer(),
}

_start_time = time.time()


def handle_errors(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e), "type": type(e).__name__}), 500
    return decorated


@app.route("/api/devtools/status")
def status():
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - _start_time, 2),
        "modules": {
            "debugger": list(_debugger.keys()),
            "analyzer": list(_analyzer.keys()),
            "sandbox": list(_sandbox.keys()),
            "docs": list(_docs.keys()),
            "profiler": list(_profiler.keys()),
        },
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "devtools_engine"})


@app.route("/api/devtools/debug", methods=["POST"])
@handle_errors
def debug():
    data = request.get_json() or {}
    action = data.get("action", "inspect")

    if action == "inspect":
        vi = _debugger["variable_inspector"]
        if data.get("sub_action") == "watch":
            vi.watch(data["name"], data.get("value"))
            return jsonify({"status": "watching", "name": data["name"]})
        elif data.get("sub_action") == "update":
            result = vi.update(data["name"], data["value"])
            return jsonify(result)
        return jsonify(vi.snapshot_all())

    elif action == "trace":
        frames = _debugger["stack_visualizer"].capture()
        show_vars = data.get("show_variables", False)
        formatted = _debugger["stack_visualizer"].format(frames, show_vars)
        return jsonify({"trace": formatted, "frame_count": len(frames)})

    elif action == "profile":
        profiler = _debugger["cpu_profiler"]
        if data.get("sub_action") == "start":
            profiler.start(data.get("label", "default"))
            return jsonify({"status": "profiling started"})
        elif data.get("sub_action") == "stop":
            elapsed = profiler.stop(data.get("label", "default"))
            return jsonify({"elapsed_ms": elapsed})
        return jsonify(profiler.get_results())

    elif action == "memory":
        mp = _debugger["memory_profiler"]
        if data.get("sub_action") == "start":
            mp.start()
            return jsonify({"status": "memory profiling started"})
        elif data.get("sub_action") == "sample":
            mp.sample()
            return jsonify({"samples": len(mp._samples)})
        return jsonify({"growth": mp.get_growth(), "samples": mp.get_samples()})

    elif action == "replay":
        replay = _debugger["session_replay"]
        if data.get("sub_action") == "start":
            sid = replay.start_session(data.get("session_id", ""))
            return jsonify({"session_id": sid})
        elif data.get("sub_action") == "record":
            replay.record_event(data.get("event_type", "unknown"), data.get("data", {}))
            return jsonify({"status": "recorded"})
        elif data.get("sub_action") == "stop":
            events = replay.stop_session()
            return jsonify({"events": events})
        return jsonify({"sessions": replay.get_sessions()})

    return jsonify({"error": f"Unknown action: {action}"}), 400


@app.route("/api/devtools/analyze", methods=["POST"])
@handle_errors
def analyze():
    data = request.get_json() or {}
    analysis_type = data.get("type", "complexity")
    filepath = data.get("file", "")

    if analysis_type == "complexity":
        analyzer = _analyzer["complexity"]
        if filepath:
            results = analyzer.analyze_file(filepath)
        else:
            results = []
        return jsonify({
            "results": [{"function": r.function, "cyclomatic": r.cyclomatic, "cognitive": r.cognitive, "rank": r.rank} for r in results],
            "summary": analyzer.get_summary(),
        })

    elif analysis_type == "duplicates":
        detector = _analyzer["duplicates"]
        directory = data.get("directory", ".")
        results = detector.analyze_directory(directory)
        return jsonify({
            "results": [{"files": d.files, "lines": d.lines_count} for d in results],
        })

    elif analysis_type == "dead_code":
        detector = _analyzer["dead_code"]
        if filepath:
            results = detector.analyze_file(filepath)
        else:
            results = []
        return jsonify({
            "results": [{"name": d.name, "line": d.line, "kind": d.kind} for d in results],
        })

    elif analysis_type == "deps":
        graph = _analyzer["imports"]
        if filepath:
            graph.analyze_file(filepath)
        return jsonify(graph.get_graph())

    elif analysis_type == "security":
        scanner = _analyzer["security"]
        if filepath:
            issues = scanner.scan_file(filepath)
        else:
            directory = data.get("directory", ".")
            issues = scanner.scan_directory(directory)
        return jsonify({
            "issues": [{"type": i.issue_type, "severity": i.severity, "file": i.file, "line": i.line} for i in issues],
            "summary": scanner.get_summary(),
        })

    elif analysis_type == "smells":
        detector = _analyzer["smells"]
        if filepath:
            smells = detector.analyze_file(filepath)
        else:
            smells = []
        return jsonify({
            "smells": [{"type": s.smell_type, "severity": s.severity, "file": s.file, "line": s.line} for s in smells],
            "summary": detector.get_summary(),
        })

    elif analysis_type == "endpoints":
        mapper = _analyzer["api_mapper"]
        if filepath:
            mapper.analyze_file(filepath)
        return jsonify({"endpoints": mapper.get_endpoints()})

    return jsonify({"error": f"Unknown analysis type: {analysis_type}"}), 400


@app.route("/api/devtools/sandbox", methods=["POST"])
@handle_errors
def sandbox():
    data = request.get_json() or {}
    operation = data.get("operation", "execute")
    lang = data.get("language", "python")

    if operation == "execute":
        code = data.get("code", "")
        if lang == "python":
            result = _sandbox["python"].execute(code)
        elif lang == "javascript":
            result = _sandbox["javascript"].execute(code)
        else:
            return jsonify({"error": f"Unsupported language: {lang}"}), 400
        return jsonify({
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
        })

    elif operation == "test_sql":
        schema = data.get("schema", "")
        query = data.get("query", "")
        tester = _sandbox["sql"]
        if schema:
            tester.execute_schema(schema)
        result = tester.execute_query(query)
        return jsonify({
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
        })

    elif operation == "test_regex":
        pattern = data.get("pattern", "")
        test_string = data.get("test_string", "")
        result = _sandbox["regex"].test(pattern, test_string)
        return jsonify({
            "success": result.success,
            "output": result.output,
            "error": result.error,
        })

    elif operation == "validate":
        content = data.get("content", "")
        fmt = data.get("format", "auto")
        validator = _sandbox["yaml_json"]
        if fmt == "json":
            result = validator.validate_json(content)
        elif fmt == "yaml":
            result = validator.validate_yaml(content)
        else:
            result = validator.auto_validate(content)
        return jsonify({
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
        })

    elif operation == "test_cron":
        expr = data.get("expression", "")
        result = _sandbox["cron"].parse(expr)
        return jsonify({
            "success": result.success,
            "output": result.output,
            "error": result.error,
        })

    elif operation == "validate_docker":
        content = data.get("content", "")
        result = _sandbox["docker_compose"].validate(content)
        return jsonify({
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
        })

    return jsonify({"error": f"Unknown operation: {operation}"}), 400


@app.route("/api/devtools/docs", methods=["POST"])
@handle_errors
def docs():
    data = request.get_json() or {}
    doc_type = data.get("type", "readme")

    if doc_type == "api_docs":
        gen = _docs["api_gen"]
        title = data.get("title", "API")
        version = data.get("version", "1.0.0")
        fmt = data.get("format", "openapi")
        if fmt == "swagger":
            return jsonify(gen.generate_swagger(title, version))
        elif fmt == "markdown":
            return jsonify({"markdown": gen.generate_markdown(title)})
        return jsonify(gen.generate_openapi(title, version))

    elif doc_type == "code_docs":
        filepath = data.get("file", "")
        if not filepath:
            return jsonify({"error": "File path required"}), 400
        gen = _docs["code_doc"]
        docs = gen.extract_docstrings(filepath)
        return jsonify({
            "docs": [{"name": d.name, "type": d.type, "docstring": d.docstring} for d in docs],
            "missing": gen.get_missing_docs(),
        })

    elif doc_type == "readme":
        gen = _docs["readme"]
        directory = data.get("directory", ".")
        readme = gen.from_project(directory)
        return jsonify({"readme": readme})

    elif doc_type == "changelog":
        gen = _docs["changelog"]
        directory = data.get("directory", ".")
        gen.from_git_log(directory)
        return jsonify({"changelog": gen.generate_markdown()})

    elif doc_type == "architecture":
        gen = _docs["arch_diagram"]
        directory = data.get("directory", ".")
        gen.from_directory(directory)
        fmt = data.get("format", "ascii")
        if fmt == "mermaid":
            return jsonify({"diagram": gen.generate_mermaid()})
        return jsonify({"diagram": gen.generate_ascii()})

    elif doc_type == "env_vars":
        gen = _docs["env_doc"]
        directory = data.get("directory", ".")
        gen.scan_directory(directory)
        return jsonify({"docs": gen.generate_docs(), "vars": gen.get_vars()})

    return jsonify({"error": f"Unknown doc type: {doc_type}"}), 400


@app.route("/api/devtools/profile", methods=["POST"])
@handle_errors
def profile():
    data = request.get_json() or {}
    profiler_type = data.get("type", "cpu")

    if profiler_type == "cpu":
        profiler = _profiler["call_tracer"]
        if data.get("sub_action") == "start":
            profiler.start()
            return jsonify({"status": "cpu profiling started"})
        elif data.get("sub_action") == "stop":
            profiler.stop()
            return jsonify({"stats": profiler.get_call_stats(), "top_calls": profiler.get_top_calls()})
        return jsonify({"stats": profiler.get_call_stats()})

    elif profiler_type == "memory":
        tracker = _profiler["memory_tracker"]
        if data.get("sub_action") == "snapshot":
            snap = tracker.take_snapshot()
            return jsonify(snap)
        elif data.get("sub_action") == "diff":
            return jsonify(tracker.get_diff() or {"message": "Need at least 2 snapshots"})
        return jsonify({"snapshots": tracker.get_snapshots()})

    elif profiler_type == "io":
        profiler = _profiler["network_profiler"]
        if data.get("sub_action") == "record":
            profiler.record(
                data.get("target", "unknown"),
                data.get("latency_ms", 0),
                data.get("success", True),
            )
            return jsonify({"status": "recorded"})
        return jsonify({"stats": profiler.get_stats(), "by_target": profiler.get_by_target()})

    elif profiler_type == "cache":
        analyzer = _profiler["cache_analyzer"]
        if data.get("sub_action") == "record":
            key = data.get("key", "")
            if data.get("hit"):
                analyzer.record_hit(key, data.get("duration_ms", 0))
            else:
                analyzer.record_miss(key, data.get("duration_ms", 0))
            return jsonify({"status": "recorded"})
        return jsonify({
            "metrics": [asdict(m) for m in analyzer.get_metrics()],
            "overall": analyzer.get_overall_stats(),
        })

    elif profiler_type == "gc":
        monitor = _profiler["gc_monitor"]
        if data.get("sub_action") == "collect":
            event = monitor.manual_collect(data.get("generation", 2))
            return jsonify({
                "collected": event.collected,
                "duration_ms": event.duration_ms,
            })
        return jsonify({"stats": monitor.get_stats(), "events": monitor.get_events()})

    elif profiler_type == "startup":
        analyzer = _profiler["startup"]
        if data.get("sub_action") == "start":
            analyzer.start()
            return jsonify({"status": "startup tracking started"})
        elif data.get("sub_action") == "mark":
            phase = analyzer.mark_phase(data.get("name", "unknown"), data.get("description", ""))
            return jsonify({"phase": phase.name, "duration_ms": phase.duration_ms})
        return jsonify({
            "phases": analyzer.get_phases(),
            "total_ms": analyzer.get_total_time(),
        })

    elif profiler_type == "bundle":
        analyzer = _profiler["bundle"]
        if data.get("directory"):
            analyzer.analyze_directory(data["directory"])
        return jsonify({
            "summary": analyzer.get_summary(),
            "largest": analyzer.get_largest_files(),
        })

    return jsonify({"error": f"Unknown profiler type: {profiler_type}"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "9890")), debug=False)
