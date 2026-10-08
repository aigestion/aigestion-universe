"""
Compression (Ideas 11-20)
------------------------
Brotli, Zstandard, Gzip, WebP/AVIF images, msgpack JSON, response streaming,
delta compression, dictionary compression, auto-tuning, decompression caching.
"""

from __future__ import annotations

import bz2
import gzip
import hashlib
import json
import logging
import lzma
import struct
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Idea 13 - Gzip optimization
# ---------------------------------------------------------------------------

class GzipCompressor:
    """Optimized gzip compression with configurable levels."""

    def __init__(self, level: int = 6):
        self.level = level

    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data, compresslevel=self.level)

    def decompress(self, data: bytes) -> bytes:
        return gzip.decompress(data)

    def compress_str(self, text: str) -> bytes:
        return self.compress(text.encode("utf-8"))

    def decompress_str(self, data: bytes) -> str:
        return self.decompress(data).decode("utf-8")


# ---------------------------------------------------------------------------
# Idea 11 - Brotli compression
# ---------------------------------------------------------------------------

class BrotliCompressor:
    """
    Brotli compression using bz2 as fallback (stdlib).
    In production, use the `brotli` package for true Brotli.
    """

    def __init__(self, level: int = 6):
        self.level = level

    def compress(self, data: bytes) -> bytes:
        try:
            import brotli
            return brotli.compress(data, quality=self.level)
        except ImportError:
            return bz2.compress(data, compresslevel=min(self.level, 9))

    def decompress(self, data: bytes) -> bytes:
        try:
            import brotli
            return brotli.decompress(data)
        except ImportError:
            return bz2.decompress(data)

    def compress_str(self, text: str) -> bytes:
        return self.compress(text.encode("utf-8"))

    def decompress_str(self, data: bytes) -> str:
        return self.decompress(data).decode("utf-8")


# ---------------------------------------------------------------------------
# Idea 12 - Zstandard compression
# ---------------------------------------------------------------------------

class ZstdCompressor:
    """
    Zstandard compression using lzma as fallback.
    In production, use the `zstandard` package for true zstd.
    """

    def __init__(self, level: int = 3):
        self.level = level

    def compress(self, data: bytes) -> bytes:
        try:
            import zstandard as zstd
            ctx = zstd.ZstdCompressor(level=self.level)
            return ctx.compress(data)
        except ImportError:
            return lzma.compress(data, preset=min(self.level, 9))

    def decompress(self, data: bytes) -> bytes:
        try:
            import zstandard as zstd
            ctx = zstd.ZstdDecompressor()
            return ctx.decompress(data)
        except ImportError:
            return lzma.decompress(data)

    def compress_str(self, text: str) -> bytes:
        return self.compress(text.encode("utf-8"))

    def decompress_str(self, data: bytes) -> str:
        return self.decompress(data).decode("utf-8")


# ---------------------------------------------------------------------------
# Idea 14 - Image compression (WebP/AVIF)
# ---------------------------------------------------------------------------

class ImageFormat(Enum):
    WEBP = "webp"
    AVIF = "avif"
    PNG = "png"
    JPEG = "jpeg"


class ImageCompressor:
    """Image compression with format detection and quality control."""

    def __init__(self, default_quality: int = 80):
        self.default_quality = default_quality

    def compress(self, raw_bytes: bytes, fmt: ImageFormat = ImageFormat.WEBP,
                 quality: int | None = None) -> bytes:
        q = quality or self.default_quality
        # Stub: real implementation would use Pillow / libavif
        header = struct.pack(">4sBI", fmt.value.encode(), q, len(raw_bytes))
        return header + raw_bytes

    def decompress(self, data: bytes) -> tuple[bytes, ImageFormat, int]:
        magic, quality, size = struct.unpack(">4sBI", data[:9])
        fmt = ImageFormat(magic.decode().rstrip("\x00"))
        return data[9:], fmt, quality

    @staticmethod
    def estimate_ratio(raw_size: int, compressed_size: int) -> float:
        return compressed_size / raw_size if raw_size > 0 else 1.0


# ---------------------------------------------------------------------------
# Idea 15 - JSON compression (msgpack)
# ---------------------------------------------------------------------------

class MsgpackJsonCodec:
    """Compact JSON via msgpack encoding."""

    def encode(self, obj: Any) -> bytes:
        try:
            import msgpack
            return msgpack.packb(obj, use_bin_type=True)
        except ImportError:
            return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def decode(self, data: bytes) -> Any:
        try:
            import msgpack
            return msgpack.unpackb(data, raw=False)
        except ImportError:
            return json.loads(data.decode("utf-8"))

    @staticmethod
    def size_comparison(obj: Any) -> dict[str, int]:
        json_bytes = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        try:
            import msgpack
            mp_bytes = msgpack.packb(obj, use_bin_type=True)
        except ImportError:
            mp_bytes = json_bytes
        return {
            "json_size": len(json_bytes),
            "msgpack_size": len(mp_bytes),
            "ratio": round(len(mp_bytes) / len(json_bytes), 4) if json_bytes else 1.0,
        }


# ---------------------------------------------------------------------------
# Idea 16 - Response streaming
# ---------------------------------------------------------------------------

class StreamingCompressor:
    """Chunk-based streaming compression/decompression."""

    def __init__(self, compressor: GzipCompressor | None = None, chunk_size: int = 8192):
        self.compressor = compressor or GzipCompressor()
        self.chunk_size = chunk_size

    def compress_stream(self, data: bytes) -> list[bytes]:
        chunks = []
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i + self.chunk_size]
            chunks.append(self.compressor.compress(chunk))
        return chunks

    def decompress_stream(self, chunks: list[bytes]) -> bytes:
        parts = []
        for chunk in chunks:
            parts.append(self.compressor.decompress(chunk))
        return b"".join(parts)

    def compress_iter(self, data: bytes):
        for i in range(0, len(data), self.chunk_size):
            yield self.compressor.compress(data[i:i + self.chunk_size])


# ---------------------------------------------------------------------------
# Idea 17 - Delta compression (diff-based)
# ---------------------------------------------------------------------------

class DeltaCompressor:
    """Store only the diff between consecutive versions."""

    def __init__(self):
        self._versions: list[bytes] = []

    def compute_delta(self, old: bytes, new: bytes) -> bytes:
        """Simple XOR-based delta. Production should use xdelta3 or similar."""
        max_len = max(len(old), len(new))
        old_padded = old.ljust(max_len, b"\x00")
        new_padded = new.ljust(max_len, b"\x00")
        delta = bytes(a ^ b for a, b in zip(old_padded, new_padded))
        return struct.pack(">I", len(old)) + struct.pack(">I", len(new)) + delta

    def apply_delta(self, old: bytes, delta: bytes) -> bytes:
        new_len = struct.unpack(">I", delta[4:8])[0]
        diff = delta[8:]
        old_padded = old.ljust(max(len(old), new_len), b"\x00")
        result = bytes(a ^ b for a, b in zip(old_padded[:len(diff)], diff))
        return result[:new_len]

    def store_version(self, data: bytes) -> bytes | None:
        if self._versions:
            delta = self.compute_delta(self._versions[-1], data)
            self._versions.append(data)
            return delta
        self._versions.append(data)
        return None

    @property
    def version_count(self) -> int:
        return len(self._versions)


# ---------------------------------------------------------------------------
# Idea 18 - Dictionary compression
# ---------------------------------------------------------------------------

class DictionaryCompressor:
    """Common-prefix dictionary compression for repeated substrings."""

    def __init__(self, min_freq: int = 3):
        self.min_freq = min_freq
        self._dictionary: dict[str, int] = {}
        self._reverse: dict[int, str] = {}

    def build_dictionary(self, corpus: list[str]):
        from collections import Counter
        words: Counter = Counter()
        for text in corpus:
            for word in set(text.split()):
                if len(word) >= 4:
                    words[word] += 1

        idx = 0
        for word, count in words.items():
            if count >= self.min_freq:
                self._dictionary[word] = idx
                self._reverse[idx] = word
                idx += 1

    def compress(self, text: str) -> tuple[bytes, int]:
        tokens = []
        remaining = text
        for word, idx in sorted(self._dictionary.items(), key=lambda x: -len(x[0])):
            if word in remaining:
                tokens.append((-1, idx))
                remaining = remaining.replace(word, "", 1)

        remaining_tokens = remaining.split()
        for w in remaining_tokens:
            tokens.append((1, hash(w) % 65536))

        return json.dumps(tokens).encode(), len(self._dictionary)

    def decompress(self, data: bytes) -> str:
        tokens = json.loads(data.decode())
        parts = []
        for kind, val in tokens:
            if kind == -1 and val in self._reverse:
                parts.append(self._reverse[val])
            else:
                parts.append(f"[token:{val}]")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Idea 19 - Compression level auto-tuning
# ---------------------------------------------------------------------------

@dataclass
class CompressionProfile:
    name: str
    level: int
    avg_ratio: float
    avg_speed_us: float


class AutoTuner:
    """Automatically select best compression level based on data characteristics."""

    def __init__(self):
        self._profiles: list[CompressionProfile] = []
        self._history: list[tuple[str, int, float, float]] = []

    def add_profile(self, profile: CompressionProfile):
        self._profiles.append(profile)

    def benchmark(self, data: bytes, compressor: GzipCompressor) -> CompressionProfile:
        import time as _time
        start = _time.monotonic()
        compressed = compressor.compress(data)
        elapsed = (_time.monotonic() - start) * 1_000_000
        ratio = len(compressed) / len(data) if data else 1.0
        profile = CompressionProfile(
            name=f"level_{compressor.level}",
            level=compressor.level,
            avg_ratio=ratio,
            avg_speed_us=elapsed,
        )
        self._history.append((profile.name, profile.level, profile.avg_ratio, profile.avg_speed_us))
        return profile

    def recommend(self, target_ratio: float = 0.5, max_latency_us: float = 10_000) -> int:
        candidates = [
            p for p in self._profiles
            if p.avg_ratio <= target_ratio and p.avg_speed_us <= max_latency_us
        ]
        if not candidates:
            return 6
        return min(candidates, key=lambda p: p.avg_speed_us).level

    @property
    def history(self) -> list[dict[str, Any]]:
        return [{"name": h[0], "level": h[1], "ratio": round(h[2], 4), "latency_us": round(h[3], 2)}
                for h in self._history]


# ---------------------------------------------------------------------------
# Idea 20 - Decompression caching
# ---------------------------------------------------------------------------

class DecompressionCache:
    """Cache decompressed results to avoid repeated CPU work."""

    def __init__(self, max_size: int = 256, ttl: float = 600):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _key(self, data: bytes, algo: str) -> str:
        return hashlib.md5(data + algo.encode()).hexdigest()

    def get_or_decompress(self, data: bytes, decompressor: Callable[[bytes], Any]) -> Any:
        k = self._key(data, decompressor.__class__.__name__)
        with self._lock:
            entry = self._cache.get(k)
            if entry:
                value, ts = entry
                if time.time() - ts < self.ttl:
                    self._cache.move_to_end(k)
                    self.hits += 1
                    return value
                del self._cache[k]

        value = decompressor(data)
        with self._lock:
            self._cache[k] = (value, time.time())
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
            self.misses += 1
        return value

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "size": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0,
        }


# ---------------------------------------------------------------------------
# Unified Compression Manager
# ---------------------------------------------------------------------------

class CompressionManager:
    """Unified interface to all compression backends."""

    def __init__(self):
        self.gzip = GzipCompressor()
        self.brotli = BrotliCompressor()
        self.zstd = ZstdCompressor()
        self.image = ImageCompressor()
        self.msgpack_codec = MsgpackJsonCodec()
        self.streaming = StreamingCompressor(self.gzip)
        self.delta = DeltaCompressor()
        self.dictionary = DictionaryCompressor()
        self.auto_tuner = AutoTuner()
        self.decomp_cache = DecompressionCache()

    def compress(self, data: str, method: str = "gzip") -> bytes:
        mapping = {
            "gzip": lambda: self.gzip.compress_str(data),
            "brotli": lambda: self.brotli.compress_str(data),
            "zstd": lambda: self.zstd.compress_str(data),
            "msgpack": lambda: self.msgpack_codec.encode(data),
        }
        fn = mapping.get(method, mapping["gzip"])
        return fn()

    def decompress(self, data: bytes, method: str = "gzip") -> Any:
        mapping = {
            "gzip": lambda: self.gzip.decompress_str(data),
            "brotli": lambda: self.brotli.decompress_str(data),
            "zstd": lambda: self.zstd.decompress_str(data),
            "msgpack": lambda: self.msgpack_codec.decode(data),
        }
        fn = mapping.get(method, mapping["gzip"])
        return fn()

    def stats(self) -> dict[str, Any]:
        return {
            "decompression_cache": self.decomp_cache.stats(),
            "delta_versions": self.delta.version_count,
            "tuner_history": self.auto_tuner.history,
        }
