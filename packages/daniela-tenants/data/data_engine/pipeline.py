"""Data Pipeline Engine - Ideas 1-10."""

import json
import time
import uuid
import hashlib
import threading
import re
import copy
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from collections import OrderedDict
from enum import Enum


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class StepResult:
    def __init__(self, step_name: str, status: str, data: Any = None, error: str = None):
        self.step_name = step_name
        self.status = status
        self.data = data
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "step_name": self.step_name,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class PipelineStep:
    def __init__(self, name: str, func: Callable, config: dict = None):
        self.name = name
        self.func = func
        self.config = config or {}
        self.result = None

    def execute(self, data: Any) -> Any:
        try:
            self.result = StepResult(self.name, "running")
            output = self.func(data, self.config)
            self.result = StepResult(self.name, "completed", data=output)
            return output
        except Exception as e:
            self.result = StepResult(self.name, "failed", error=str(e))
            raise


class ETLPipeline:
    """Idea 1: ETL Pipeline (Extract/Transform/Load)"""

    def __init__(self, name: str):
        self.name = name
        self.extractors: List[Callable] = []
        self.transformers: List[Callable] = []
        self.loaders: List[Callable] = []
        self.history: List[dict] = []

    def add_extractor(self, func: Callable, config: dict = None):
        self.extractors.append({"func": func, "config": config or {}})
        return self

    def add_transformer(self, func: Callable, config: dict = None):
        self.transformers.append({"func": func, "config": config or {}})
        return self

    def add_loader(self, func: Callable, config: dict = None):
        self.loaders.append({"func": func, "config": config or {}})
        return self

    def run(self, context: dict = None) -> dict:
        context = context or {}
        start_time = time.time()
        results = {"pipeline": self.name, "steps": [], "status": "success"}

        # Extract
        extracted_data = []
        for ext in self.extractors:
            try:
                data = ext["func"](context)
                extracted_data.append(data)
                results["steps"].append({"phase": "extract", "status": "success"})
            except Exception as e:
                results["steps"].append({"phase": "extract", "status": "failed", "error": str(e)})
                results["status"] = "failed"
                break

        if results["status"] == "failed":
            return results

        # Transform
        transformed_data = extracted_data
        for tr in self.transformers:
            try:
                transformed_data = [tr["func"](d, tr["config"]) for d in transformed_data]
                results["steps"].append({"phase": "transform", "status": "success"})
            except Exception as e:
                results["steps"].append({"phase": "transform", "status": "failed", "error": str(e)})
                results["status"] = "failed"
                break

        # Load
        if results["status"] != "failed":
            for loader in self.loaders:
                try:
                    for data in transformed_data:
                        loader["func"](data, loader["config"])
                    results["steps"].append({"phase": "load", "status": "success"})
                except Exception as e:
                    results["steps"].append({"phase": "load", "status": "failed", "error": str(e)})
                    results["status"] = "failed"

        results["duration"] = time.time() - start_time
        self.history.append(results)
        return results


class StreamingPipeline:
    """Idea 2: Real-time Streaming Pipeline"""

    def __init__(self):
        self.processors: List[Callable] = []
        self.buffer: List[Any] = []
        self.buffer_size: int = 100
        self._running = False
        self._thread = None
        self.window_size = timedelta(seconds=60)
        self.windows: Dict[str, List] = {}

    def add_processor(self, func: Callable):
        self.processors.append(func)
        return self

    def ingest(self, event: dict):
        event["_ingested_at"] = datetime.now().isoformat()
        self.buffer.append(event)
        if len(self.buffer) >= self.buffer_size:
            self._flush()

    def _flush(self):
        if not self.buffer:
            return
        batch = self.buffer.copy()
        self.buffer.clear()
        for processor in self.processors:
            batch = [processor(e) for e in batch if e is not None]
        window_key = datetime.now().strftime("%Y%m%d%H%M")
        self.windows.setdefault(window_key, []).extend(batch)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        while self._running:
            self._flush()
            time.sleep(0.1)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._flush()

    def get_window(self, window_key: str) -> List:
        return self.windows.get(window_key, [])


class BatchPipeline:
    """Idea 3: Batch Processing Pipeline"""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.jobs: List[dict] = []
        self.results: List[dict] = []

    def add_job(self, name: str, func: Callable, data_source: Any):
        self.jobs.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "func": func,
            "data_source": data_source,
            "status": PipelineStatus.PENDING.value,
        })

    def process_batch(self, batch: List[Any], func: Callable) -> List[Any]:
        results = []
        for i in range(0, len(batch), self.batch_size):
            chunk = batch[i:i + self.batch_size]
            processed = func(chunk)
            results.extend(processed)
        return results

    def run_all(self) -> List[dict]:
        results = []
        for job in self.jobs:
            job["status"] = PipelineStatus.RUNNING.value
            try:
                start = time.time()
                if isinstance(job["data_source"], list):
                    output = self.process_batch(job["data_source"], job["func"])
                else:
                    output = job["func"](job["data_source"])
                job["status"] = PipelineStatus.COMPLETED.value
                result = {
                    "job_id": job["id"],
                    "name": job["name"],
                    "status": "success",
                    "duration": time.time() - start,
                    "output_size": len(output) if isinstance(output, list) else 1,
                }
            except Exception as e:
                job["status"] = PipelineStatus.FAILED.value
                result = {
                    "job_id": job["id"],
                    "name": job["name"],
                    "status": "failed",
                    "error": str(e),
                }
            results.append(result)
        self.results = results
        return results


class DataValidationPipeline:
    """Idea 4: Data Validation Pipeline"""

    def __init__(self):
        self.rules: List[dict] = []
        self.results: List[dict] = []

    def add_rule(self, name: str, validator: Callable, severity: str = "error"):
        self.rules.append({"name": name, "validator": validator, "severity": severity})
        return self

    def required_field(self, field: str):
        def validate(data):
            return field in data and data[field] is not None
        self.rules.append({"name": f"required_{field}", "validator": validate, "severity": "error"})
        return self

    def type_check(self, field: str, expected_type: type):
        def validate(data):
            return isinstance(data.get(field), expected_type)
        self.rules.append({"name": f"type_{field}", "validator": validate, "severity": "error"})
        return self

    def range_check(self, field: str, min_val=None, max_val=None):
        def validate(data):
            val = data.get(field)
            if val is None:
                return False
            if min_val is not None and val < min_val:
                return False
            if max_val is not None and val > max_val:
                return False
            return True
        self.rules.append({"name": f"range_{field}", "validator": validate, "severity": "error"})
        return self

    def pattern_check(self, field: str, pattern: str):
        def validate(data):
            val = data.get(field, "")
            return bool(re.match(pattern, str(val)))
        self.rules.append({"name": f"pattern_{field}", "validator": validate, "severity": "error"})
        return self

    def validate(self, data: dict) -> dict:
        errors = []
        warnings = []
        for rule in self.rules:
            try:
                is_valid = rule["validator"](data)
                if not is_valid:
                    entry = {"rule": rule["name"], "severity": rule["severity"]}
                    if rule["severity"] == "error":
                        errors.append(entry)
                    else:
                        warnings.append(entry)
            except Exception as e:
                errors.append({"rule": rule["name"], "error": str(e)})

        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "rules_checked": len(self.rules),
        }
        self.results.append(result)
        return result


class DeduplicationPipeline:
    """Idea 5: Data Deduplication Pipeline"""

    def __init__(self):
        self.key_fields: List[str] = []
        self.hash_cache: Dict[str, dict] = {}
        self.stats = {"total": 0, "duplicates": 0, "unique": 0}

    def set_key_fields(self, fields: List[str]):
        self.key_fields = fields
        return self

    def _compute_key(self, record: dict) -> str:
        key_data = {f: record.get(f) for f in self.key_fields}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _compute_hash(self, record: dict) -> str:
        record_str = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(record_str.encode()).hexdigest()

    def deduplicate(self, records: List[dict], strategy: str = "first") -> dict:
        self.stats["total"] = len(records)
        seen_keys = {}
        unique_records = []

        for record in records:
            key = self._compute_key(record)
            record_hash = self._compute_hash(record)

            if key not in seen_keys:
                seen_keys[key] = {"hash": record_hash, "count": 1, "record": record}
                unique_records.append(record)
            else:
                seen_keys[key]["count"] += 1
                if strategy == "last":
                    seen_keys[key]["record"] = record
                    unique_records[-1] = record

        self.stats["duplicates"] = self.stats["total"] - len(unique_records)
        self.stats["unique"] = len(unique_records)

        return {
            "unique_records": unique_records,
            "stats": self.stats.copy(),
            "duplicate_groups": {k: v["count"] for k, v in seen_keys.items() if v["count"] > 1},
        }


class EnrichmentPipeline:
    """Idea 6: Data Enrichment Pipeline"""

    def __init__(self):
        self.enrichers: List[dict] = []
        self.cache: Dict[str, Any] = {}

    def add_enricher(self, name: str, func: Callable, priority: int = 0):
        self.enrichers.append({"name": name, "func": func, "priority": priority})
        self.enrichers.sort(key=lambda x: x["priority"])
        return self

    def geo_enrich(self, field: str):
        def enricher(record):
            geo_data = self.cache.get(record.get(field))
            if geo_data is None:
                geo_data = {"country": "US", "region": "unknown"}
                self.cache[record.get(field)] = geo_data
            record["geo"] = geo_data
            return record
        self.add_enricher(f"geo_{field}", enricher)
        return self

    def timestamp_enrich(self, field: str):
        def enricher(record):
            ts = record.get(field)
            if ts:
                dt = datetime.fromisoformat(str(ts))
                record[f"{field}_hour"] = dt.hour
                record[f"{field}_day"] = dt.strftime("%A")
                record[f"{field}_month"] = dt.strftime("%B")
            return record
        self.add_enricher(f"timestamp_{field}", enricher)
        return self

    def enrich(self, record: dict) -> dict:
        for enricher in self.enrichers:
            record = enricher["func"](record)
        return record

    def enrich_batch(self, records: List[dict]) -> List[dict]:
        return [self.enrich(r) for r in records]


class SchemaEvolutionTracker:
    """Idea 7: Schema Evolution Tracker"""

    def __init__(self):
        self.schemas: Dict[str, List[dict]] = {}
        self.changes: List[dict] = []

    def register_schema(self, schema_name: str, schema: dict, version: str = None):
        version = version or f"v{len(self.schemas.get(schema_name, [])) + 1}"
        entry = {
            "version": version,
            "schema": schema,
            "timestamp": datetime.now().isoformat(),
            "fields": list(schema.keys()),
        }
        self.schemas.setdefault(schema_name, []).append(entry)
        return entry

    def detect_changes(self, schema_name: str, old_version: str = None, new_version: str = None) -> dict:
        versions = self.schemas.get(schema_name, [])
        if len(versions) < 2:
            return {"changes": []}

        if old_version and new_version:
            old = next((v for v in versions if v["version"] == old_version), None)
            new = next((v for v in versions if v["version"] == new_version), None)
        else:
            old = versions[-2]
            new = versions[-1]

        if not old or not new:
            return {"changes": []}

        old_fields = set(old["schema"].keys())
        new_fields = set(new["schema"].keys())

        added = new_fields - old_fields
        removed = old_fields - new_fields
        common = old_fields & new_fields
        type_changes = []

        for field in common:
            old_type = type(old["schema"][field]).__name__
            new_type = type(new["schema"][field]).__name__
            if old_type != new_type:
                type_changes.append({"field": field, "old": old_type, "new": new_type})

        changes = {
            "added": list(added),
            "removed": list(removed),
            "type_changes": type_changes,
            "breaking": bool(removed or type_changes),
        }
        self.changes.append({"schema": schema_name, "changes": changes})
        return changes

    def get_history(self, schema_name: str) -> List[dict]:
        return self.schemas.get(schema_name, [])


class DataLineageTracker:
    """Idea 8: Data Lineage Tracker"""

    def __init__(self):
        self.nodes: Dict[str, dict] = {}
        self.edges: List[dict] = []

    def register_source(self, name: str, metadata: dict = None):
        self.nodes[name] = {
            "type": "source",
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        return self

    def register_transform(self, name: str, operation: str, inputs: List[str], outputs: List[str]):
        self.nodes[name] = {
            "type": "transform",
            "operation": operation,
            "created_at": datetime.now().isoformat(),
        }
        for inp in inputs:
            self.edges.append({"from": inp, "to": name, "type": "input"})
        for out in outputs:
            self.edges.append({"from": name, "to": out, "type": "output"})
        return self

    def register_output(self, name: str, metadata: dict = None):
        self.nodes[name] = {
            "type": "output",
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        return self

    def trace_upstream(self, node: str) -> List[str]:
        upstream = set()
        queue = [node]
        while queue:
            current = queue.pop()
            for edge in self.edges:
                if edge["to"] == current:
                    upstream.add(edge["from"])
                    queue.append(edge["from"])
        return list(upstream)

    def trace_downstream(self, node: str) -> List[str]:
        downstream = set()
        queue = [node]
        while queue:
            current = queue.pop()
            for edge in self.edges:
                if edge["from"] == current:
                    downstream.add(edge["to"])
                    queue.append(edge["to"])
        return list(downstream)

    def get_full_lineage(self) -> dict:
        return {"nodes": self.nodes, "edges": self.edges}


class PipelineVersionManager:
    """Idea 9: Pipeline Versioning"""

    def __init__(self):
        self.versions: Dict[str, List[dict]] = {}

    def create_version(self, pipeline_name: str, config: dict, changelog: str = ""):
        versions = self.versions.setdefault(pipeline_name, [])
        version_num = len(versions) + 1
        entry = {
            "version": version_num,
            "config": copy.deepcopy(config),
            "changelog": changelog,
            "created_at": datetime.now().isoformat(),
        }
        versions.append(entry)
        return entry

    def get_version(self, pipeline_name: str, version: int) -> Optional[dict]:
        versions = self.versions.get(pipeline_name, [])
        for v in versions:
            if v["version"] == version:
                return v
        return None

    def get_latest(self, pipeline_name: str) -> Optional[dict]:
        versions = self.versions.get(pipeline_name, [])
        return versions[-1] if versions else None

    def list_versions(self, pipeline_name: str) -> List[dict]:
        return self.versions.get(pipeline_name, [])

    def rollback(self, pipeline_name: str, target_version: int) -> Optional[dict]:
        version = self.get_version(pipeline_name, target_version)
        if version:
            self.create_version(
                pipeline_name,
                version["config"],
                f"Rollback to version {target_version}"
            )
        return version


class PipelineMonitor:
    """Idea 10: Pipeline Monitoring Dashboard"""

    def __init__(self):
        self.metrics: Dict[str, List[dict]] = {}
        self.alerts: List[dict] = []
        self.thresholds: Dict[str, dict] = {}

    def record_metric(self, pipeline_name: str, metric_name: str, value: float):
        self.metrics.setdefault(f"{pipeline_name}.{metric_name}", []).append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
        })
        self._check_threshold(pipeline_name, metric_name, value)

    def set_threshold(self, metric_key: str, min_val: float = None, max_val: float = None):
        self.thresholds[metric_key] = {"min": min_val, "max": max_val}

    def _check_threshold(self, pipeline_name: str, metric_name: str, value: float):
        key = f"{pipeline_name}.{metric_name}"
        threshold = self.thresholds.get(key)
        if not threshold:
            return
        if threshold.get("max") and value > threshold["max"]:
            self.alerts.append({
                "pipeline": pipeline_name,
                "metric": metric_name,
                "value": value,
                "threshold": threshold["max"],
                "type": "exceeded",
                "timestamp": datetime.now().isoformat(),
            })
        if threshold.get("min") and value < threshold["min"]:
            self.alerts.append({
                "pipeline": pipeline_name,
                "metric": metric_name,
                "value": value,
                "threshold": threshold["min"],
                "type": "below",
                "timestamp": datetime.now().isoformat(),
            })

    def get_dashboard(self, pipeline_name: str = None) -> dict:
        if pipeline_name:
            relevant = {k: v for k, v in self.metrics.items() if k.startswith(pipeline_name)}
        else:
            relevant = self.metrics

        summary = {}
        for key, values in relevant.items():
            nums = [v["value"] for v in values]
            summary[key] = {
                "count": len(nums),
                "latest": nums[-1] if nums else None,
                "avg": sum(nums) / len(nums) if nums else None,
                "min": min(nums) if nums else None,
                "max": max(nums) if nums else None,
            }

        return {
            "metrics": summary,
            "alerts": self.alerts[-10:],
            "thresholds": self.thresholds,
        }

    def get_alerts(self, pipeline_name: str = None) -> List[dict]:
        if pipeline_name:
            return [a for a in self.alerts if a["pipeline"] == pipeline_name]
        return self.alerts
