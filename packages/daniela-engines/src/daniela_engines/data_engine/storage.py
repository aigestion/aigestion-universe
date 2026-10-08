"""Data Storage - Ideas 31-40."""

import gzip
import hashlib
import json
import os
import re
import threading
import time
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from typing import Any


class TimeSeriesStore:
    """Idea 31: Time-series Data Store"""

    def __init__(self, retention_days: int = 365):
        self.data: dict[str, list[dict]] = {}
        self.retention_days = retention_days
        self._lock = threading.Lock()

    def insert(self, metric: str, value: float, timestamp: str = None, tags: dict = None):
        ts = timestamp or datetime.now().isoformat()
        entry = {"timestamp": ts, "value": value, "tags": tags or {}}
        with self._lock:
            self.data.setdefault(metric, []).append(entry)

    def query(self, metric: str, start: str = None, end: str = None,
              aggregation: str = "avg", window: str = None) -> dict:
        entries = self.data.get(metric, [])
        if start:
            entries = [e for e in entries if e["timestamp"] >= start]
        if end:
            entries = [e for e in entries if e["timestamp"] <= end]

        values = [e["value"] for e in entries]

        if not values:
            return {"metric": metric, "count": 0, "result": None}

        result = {
            "metric": metric,
            "count": len(values),
            "min": min(values),
            "max": max(values),
        }

        if aggregation == "avg":
            result["result"] = sum(values) / len(values)
        elif aggregation == "sum":
            result["result"] = sum(values)
        elif aggregation == "count":
            result["result"] = len(values)
        elif aggregation == "min":
            result["result"] = min(values)
        elif aggregation == "max":
            result["result"] = max(values)
        elif aggregation == "last":
            result["result"] = values[-1]
        elif aggregation == "first":
            result["result"] = values[0]

        return result

    def downsample(self, metric: str, interval: str = "1h", aggregation: str = "avg") -> list[dict]:
        entries = self.data.get(metric, [])
        if not entries:
            return []

        buckets = defaultdict(list)
        for entry in entries:
            ts = datetime.fromisoformat(entry["timestamp"])
            if interval == "1h":
                key = ts.strftime("%Y-%m-%dT%H:00:00")
            elif interval == "1d":
                key = ts.strftime("%Y-%m-%d")
            elif interval == "1m":
                key = ts.strftime("%Y-%m-%dT%H:%M:00")
            else:
                key = ts.strftime("%Y-%m-%dT%H:00:00")
            buckets[key].append(entry["value"])

        result = []
        for bucket_key in sorted(buckets.keys()):
            vals = buckets[bucket_key]
            if aggregation == "avg":
                agg_val = sum(vals) / len(vals)
            elif aggregation == "sum":
                agg_val = sum(vals)
            elif aggregation == "max":
                agg_val = max(vals)
            elif aggregation == "min":
                agg_val = min(vals)
            else:
                agg_val = sum(vals) / len(vals)
            result.append({"timestamp": bucket_key, "value": agg_val, "count": len(vals)})

        return result

    def cleanup(self):
        cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        with self._lock:
            for metric in self.data:
                self.data[metric] = [e for e in self.data[metric] if e["timestamp"] >= cutoff]


class KeyValueCacheStore:
    """Idea 32: Key-Value Cache Store"""

    def __init__(self, max_size: int = 10000, default_ttl: int = 300):
        self.store: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.ttls: dict[str, float] = {}
        self.stats = {"hits": 0, "misses": 0}

    def set(self, key: str, value: Any, ttl: int = None):
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        self.ttls[key] = time.time() + (ttl or self.default_ttl)

        while len(self.store) > self.max_size:
            oldest_key, _ = self.store.popitem(last=False)
            self.ttls.pop(oldest_key, None)

    def get(self, key: str) -> Any | None:
        if key not in self.store:
            self.stats["misses"] += 1
            return None

        if time.time() > self.ttls.get(key, 0):
            del self.store[key]
            self.ttls.pop(key, None)
            self.stats["misses"] += 1
            return None

        self.store.move_to_end(key)
        self.stats["hits"] += 1
        return self.store[key]

    def delete(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
            self.ttls.pop(key, None)
            return True
        return False

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def keys(self, pattern: str = None) -> list[str]:
        all_keys = list(self.store.keys())
        if pattern:
            regex = re.compile(pattern.replace("*", ".*"))
            return [k for k in all_keys if regex.match(k)]
        return all_keys

    def size(self) -> int:
        return len(self.store)

    def clear(self):
        self.store.clear()
        self.ttls.clear()

    def get_stats(self) -> dict:
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        return {
            "size": len(self.store),
            "max_size": self.max_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate, 2),
        }


class DocumentStore:
    """Idea 33: Document Store (JSON)"""

    def __init__(self):
        self.collections: dict[str, list[dict]] = {}
        self.indexes: dict[str, dict[str, list[int]]] = {}

    def insert(self, collection: str, document: dict) -> str:
        doc_id = document.get("_id") or hashlib.md5(json.dumps(document, sort_keys=True, default=str).encode()).hexdigest()[:12]
        document["_id"] = doc_id
        document["_created_at"] = datetime.now().isoformat()
        self.collections.setdefault(collection, []).append(document)
        self._update_indexes(collection, document, len(self.collections[collection]) - 1)
        return doc_id

    def find(self, collection: str, query: dict = None) -> list[dict]:
        docs = self.collections.get(collection, [])
        if not query:
            return docs
        return [d for d in docs if self._match(d, query)]

    def find_one(self, collection: str, query: dict) -> dict | None:
        results = self.find(collection, query)
        return results[0] if results else None

    def update(self, collection: str, query: dict, update: dict) -> int:
        docs = self.collections.get(collection, [])
        count = 0
        for doc in docs:
            if self._match(doc, query):
                for key, value in update.items():
                    if key.startswith("$set"):
                        for k, v in value.items():
                            doc[k] = v
                    elif key.startswith("$unset"):
                        for k in value.keys():
                            doc.pop(k, None)
                    elif key.startswith("$inc"):
                        for k, v in value.items():
                            doc[k] = doc.get(k, 0) + v
                doc["_updated_at"] = datetime.now().isoformat()
                count += 1
        return count

    def delete(self, collection: str, query: dict) -> int:
        docs = self.collections.get(collection, [])
        before = len(docs)
        self.collections[collection] = [d for d in docs if not self._match(d, query)]
        return before - len(self.collections[collection])

    def count(self, collection: str, query: dict = None) -> int:
        return len(self.find(collection, query))

    def create_index(self, collection: str, field: str):
        key = f"{collection}.{field}"
        self.indexes[key] = defaultdict(list)
        for i, doc in enumerate(self.collections.get(collection, [])):
            val = doc.get(field)
            if val is not None:
                self.indexes[key][str(val)].append(i)

    def _match(self, doc: dict, query: dict) -> bool:
        for key, condition in query.items():
            if isinstance(condition, dict):
                doc_val = doc.get(key)
                for op, expected in condition.items():
                    if op == "$eq" and doc_val != expected:
                        return False
                    elif op == "$ne" and doc_val == expected:
                        return False
                    elif op == "$gt" and (doc_val is None or doc_val <= expected):
                        return False
                    elif op == "$gte" and (doc_val is None or doc_val < expected):
                        return False
                    elif op == "$lt" and (doc_val is None or doc_val >= expected):
                        return False
                    elif op == "$lte" and (doc_val is None or doc_val > expected):
                        return False
                    elif op == "$in" and doc_val not in expected:
                        return False
                    elif op == "$nin" and doc_val in expected:
                        return False
            else:
                if doc.get(key) != condition:
                    return False
        return True

    def _update_indexes(self, collection: str, doc: dict, index: int):
        for key, idx in self.indexes.items():
            if key.startswith(collection + "."):
                field = key.split(".")[-1]
                val = doc.get(field)
                if val is not None:
                    idx[str(val)].append(index)


class GraphDataStore:
    """Idea 34: Graph Data Store (Relationships)"""

    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self.adjacency: dict[str, list[dict]] = defaultdict(list)

    def add_node(self, node_id: str, data: dict = None):
        self.nodes[node_id] = {"id": node_id, "data": data or {}, "created_at": datetime.now().isoformat()}

    def add_edge(self, source: str, target: str, relationship: str, properties: dict = None):
        edge = {
            "source": source,
            "target": target,
            "relationship": relationship,
            "properties": properties or {},
        }
        self.edges.append(edge)
        self.adjacency[source].append(edge)
        self.adjacency[target].append(edge)

    def get_node(self, node_id: str) -> dict | None:
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, relationship: str = None) -> list[dict]:
        neighbors = []
        for edge in self.adjacency.get(node_id, []):
            if relationship and edge["relationship"] != relationship:
                continue
            neighbor_id = edge["target"] if edge["source"] == node_id else edge["source"]
            neighbor = self.nodes.get(neighbor_id)
            if neighbor:
                neighbors.append({"node": neighbor, "edge": edge})
        return neighbors

    def find_path(self, start: str, end: str, max_depth: int = 5) -> list[str] | None:
        if start not in self.nodes or end not in self.nodes:
            return None

        queue = [(start, [start])]
        visited = {start}

        while queue:
            current, path = queue.pop(0)
            if current == end:
                return path
            if len(path) > max_depth:
                continue

            for edge in self.adjacency.get(current, []):
                neighbor = edge["target"] if edge["source"] == current else edge["source"]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_subgraph(self, node_id: str, depth: int = 2) -> dict:
        visited = set()
        nodes = {}
        edges = []

        def traverse(nid, d):
            if d > depth or nid in visited:
                return
            visited.add(nid)
            if nid in self.nodes:
                nodes[nid] = self.nodes[nid]
            for edge in self.adjacency.get(nid, []):
                neighbor = edge["target"] if edge["source"] == nid else edge["source"]
                if neighbor in self.nodes:
                    edges.append(edge)
                    traverse(neighbor, d + 1)

        traverse(node_id, 0)
        return {"nodes": nodes, "edges": edges}

    def get_all_paths(self, start: str, end: str, max_depth: int = 4) -> list[list[str]]:
        paths = []

        def dfs(current, target, path, depth):
            if depth > max_depth:
                return
            if current == target:
                paths.append(path[:])
                return
            for edge in self.adjacency.get(current, []):
                neighbor = edge["target"] if edge["source"] == current else edge["source"]
                if neighbor not in path:
                    path.append(neighbor)
                    dfs(neighbor, target, path, depth + 1)
                    path.pop()

        dfs(start, end, [start], 0)
        return paths


class FullTextSearchEngine:
    """Idea 35: Full-text Search Engine"""

    def __init__(self):
        self.index: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.documents: dict[str, dict] = {}
        self.doc_count: int = 0

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                      "have", "has", "had", "do", "does", "did", "will", "would", "could",
                      "should", "may", "might", "must", "shall", "can", "need", "dare",
                      "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
                      "from", "as", "into", "through", "during", "before", "after", "above",
                      "below", "between", "out", "off", "over", "under", "again", "further",
                      "then", "once", "here", "there", "when", "where", "why", "how", "all",
                      "both", "each", "few", "more", "most", "other", "some", "such", "no",
                      "nor", "not", "only", "own", "same", "so", "than", "too", "very"}
        return [t for t in tokens if t not in stop_words and len(t) > 1]

    def _stem(self, word: str) -> str:
        suffixes = ["ing", "ly", "ed", "ious", "ies", "ive", "es", "s", "ment"]
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                return word[:-len(suffix)]
        return word

    def index_document(self, doc_id: str, content: str, metadata: dict = None):
        tokens = self._tokenize(content)
        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata or {},
            "indexed_at": datetime.now().isoformat(),
        }
        for token in tokens:
            stemmed = self._stem(token)
            self.index[stemmed][doc_id] += 1
        self.doc_count += 1

    def search(self, query: str, limit: int = 10) -> list[dict]:
        tokens = self._tokenize(query)
        scores = defaultdict(float)

        for token in tokens:
            stemmed = self._stem(token)
            df = len(self.index.get(stemmed, {}))
            idf = math.log(self.doc_count / (1 + df)) if self.doc_count > 0 else 0

            for doc_id, tf in self.index.get(stemmed, {}).items():
                scores[doc_id] += tf * idf

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        for doc_id, score in ranked:
            doc = self.documents.get(doc_id, {})
            results.append({
                "id": doc_id,
                "score": round(score, 4),
                "content": doc.get("content", "")[:200],
                "metadata": doc.get("metadata", {}),
            })

        return results

    def get_stats(self) -> dict:
        return {
            "total_documents": self.doc_count,
            "total_terms": len(self.index),
            "avg_terms_per_doc": sum(len(v) for v in self.index.values()) / max(self.doc_count, 1),
        }


import math


class DataArchivalSystem:
    """Idea 36: Data Archival System"""

    def __init__(self, archive_path: str = "/tmp/archive"):
        self.archive_path = archive_path
        self.archives: list[dict] = []
        self.policies: list[dict] = []

    def add_policy(self, name: str, retention_days: int, archive_after_days: int):
        self.policies.append({
            "name": name,
            "retention_days": retention_days,
            "archive_after_days": archive_after_days,
        })
        return self

    def archive(self, data: dict, category: str = "default") -> dict:
        archive_entry = {
            "id": hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12],
            "category": category,
            "data": data,
            "archived_at": datetime.now().isoformat(),
            "size_bytes": len(json.dumps(data).encode()),
        }
        self.archives.append(archive_entry)
        return archive_entry

    def restore(self, archive_id: str) -> dict | None:
        entry = next((a for a in self.archives if a["id"] == archive_id), None)
        return entry["data"] if entry else None

    def list_archives(self, category: str = None) -> list[dict]:
        if category:
            return [a for a in self.archives if a["category"] == category]
        return self.archives

    def get_stats(self) -> dict:
        total_size = sum(a["size_bytes"] for a in self.archives)
        categories = defaultdict(int)
        for a in self.archives:
            categories[a["category"]] += 1
        return {
            "total_archives": len(self.archives),
            "total_size_bytes": total_size,
            "categories": dict(categories),
        }


class DataCompression:
    """Idea 37: Data Compression"""

    @staticmethod
    def compress(data: bytes) -> bytes:
        return gzip.compress(data)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        return gzip.decompress(data)

    @staticmethod
    def compress_json(data: dict) -> bytes:
        json_str = json.dumps(data, sort_keys=True, default=str)
        return gzip.compress(json_str.encode())

    @staticmethod
    def decompress_json(data: bytes) -> dict:
        decompressed = gzip.decompress(data)
        return json.loads(decompressed.decode())

    @staticmethod
    def get_ratio(original: bytes, compressed: bytes) -> float:
        if len(original) == 0:
            return 0
        return len(compressed) / len(original)

    @staticmethod
    def rle_encode(data: str) -> str:
        if not data:
            return ""
        result = []
        count = 1
        for i in range(1, len(data)):
            if data[i] == data[i - 1]:
                count += 1
            else:
                result.append(f"{data[i - 1]}{count}" if count > 1 else data[i - 1])
                count = 1
        result.append(f"{data[-1]}{count}" if count > 1 else data[-1])
        return "".join(result)

    @staticmethod
    def rle_decode(data: str) -> str:
        result = []
        i = 0
        while i < len(data):
            char = data[i]
            i += 1
            num_str = ""
            while i < len(data) and data[i].isdigit():
                num_str += data[i]
                i += 1
            count = int(num_str) if num_str else 1
            result.append(char * count)
        return "".join(result)


class DataEncryption:
    """Idea 38: Data Encryption at Rest.

    2026-10-04 (S12): antes XOR contra PBKDF2 con `salt = md5(time)[:16]`
    (predecible) y sin autententicacion. Ahora AES-256-GCM con nonce aleatorio
    de 12 bytes por cifrado (confidencialidad + integridad).
    """

    def __init__(self, key: str = None):
        # Sin clave no se puede cifrar (fail-closed). hash_data/verify_hash
        # siguen funcionando sin clave (no la necesitan).
        self._key_bytes = hashlib.sha256(key.encode()).digest() if key else None

    def encrypt(self, data: str) -> dict:
        if self._key_bytes is None:
            raise ValueError("DataEncryption sin clave: define DATA_ENCRYPTION_KEY")
        nonce = os.urandom(12)
        ct = AESGCM(self._key_bytes).encrypt(nonce, data.encode(), None)
        return {
            "data": base64.b64encode(nonce + ct).decode(),
            "algorithm": "aes-256-gcm",
        }

    def decrypt(self, encrypted_data: dict) -> str:
        if self._key_bytes is None:
            raise ValueError("DataEncryption sin clave: define DATA_ENCRYPTION_KEY")
        raw = base64.b64decode(encrypted_data["data"])
        nonce, ct = raw[:12], raw[12:]
        return AESGCM(self._key_bytes).decrypt(nonce, ct, None).decode()

    def hash_data(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_hash(self, data: str, expected_hash: str) -> bool:
        return self.hash_data(data) == expected_hash


import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class BackupRestoreSystem:
    """Idea 39: Backup/Restore System"""

    def __init__(self):
        self.backups: list[dict] = []
        self.backup_data: dict[str, Any] = {}

    def create_backup(self, name: str, data: Any, metadata: dict = None) -> dict:
        backup = {
            "id": f"backup_{len(self.backups) + 1}",
            "name": name,
            "data": data,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "size_bytes": len(json.dumps(data, default=str).encode()),
        }
        self.backups.append(backup)
        self.backup_data[backup["id"]] = data
        return backup

    def restore(self, backup_id: str) -> Any | None:
        return self.backup_data.get(backup_id)

    def list_backups(self) -> list[dict]:
        return [{k: v for k, v in b.items() if k != "data"} for b in self.backups]

    def delete_backup(self, backup_id: str) -> bool:
        for i, b in enumerate(self.backups):
            if b["id"] == backup_id:
                self.backups.pop(i)
                self.backup_data.pop(backup_id, None)
                return True
        return False

    def get_latest(self) -> dict | None:
        if not self.backups:
            return None
        return self.backups[-1]

    def export_backup(self, backup_id: str) -> str | None:
        data = self.backup_data.get(backup_id)
        if data is None:
            return None
        return json.dumps(data, default=str, indent=2)

    def import_backup(self, json_str: str, name: str = "imported") -> dict:
        data = json.loads(json_str)
        return self.create_backup(name, data)


class DataRetentionPolicyEngine:
    """Idea 40: Data Retention Policy Engine"""

    def __init__(self):
        self.policies: list[dict] = []
        self.data_store: dict[str, list[dict]] = {}

    def add_policy(self, name: str, category: str, retention_days: int,
                   archive: bool = False, delete: bool = False):
        self.policies.append({
            "name": name,
            "category": category,
            "retention_days": retention_days,
            "archive": archive,
            "delete": delete,
        })
        return self

    def add_data(self, category: str, record: dict):
        record["_category"] = category
        record["_created_at"] = datetime.now().isoformat()
        self.data_store.setdefault(category, []).append(record)

    def evaluate(self, category: str = None) -> dict:
        now = datetime.now()
        results = {"actions": [], "stats": {"archived": 0, "deleted": 0, "kept": 0}}

        for policy in self.policies:
            if category and policy["category"] != category:
                continue

            cutoff = now - timedelta(days=policy["retention_days"])
            records = self.data_store.get(policy["category"], [])
            to_process = []

            for record in records:
                created = datetime.fromisoformat(record.get("_created_at", now.isoformat()))
                if created < cutoff:
                    to_process.append(record)

            for record in to_process:
                action = {
                    "policy": policy["name"],
                    "record_id": record.get("_id", "unknown"),
                    "category": policy["category"],
                }

                if policy.get("delete"):
                    action["action"] = "deleted"
                    results["stats"]["deleted"] += 1
                elif policy.get("archive"):
                    action["action"] = "archived"
                    results["stats"]["archived"] += 1
                else:
                    action["action"] = "kept"
                    results["stats"]["kept"] += 1

                results["actions"].append(action)

        return results

    def cleanup(self, category: str = None) -> int:
        now = datetime.now()
        deleted = 0

        for policy in self.policies:
            if category and policy["category"] != category:
                continue
            if not policy.get("delete"):
                continue

            cutoff = now - timedelta(days=policy["retention_days"])
            records = self.data_store.get(policy["category"], [])
            before = len(records)
            self.data_store[policy["category"]] = [
                r for r in records
                if datetime.fromisoformat(r.get("_created_at", now.isoformat())) >= cutoff
            ]
            deleted += before - len(self.data_store[policy["category"]])

        return deleted

    def get_stats(self) -> dict:
        total_records = sum(len(v) for v in self.data_store.values())
        return {
            "total_policies": len(self.policies),
            "total_records": total_records,
            "categories": {k: len(v) for k, v in self.data_store.items()},
        }
