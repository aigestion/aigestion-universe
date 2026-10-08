"""
Daniela OS — Jarvis Desktop Overlay
FastAPI Backend for System Monitoring
Provides real-time CPU, RAM, GPU, Network, Disk metrics
"""

import platform
import time

import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Daniela Jarvis Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()

# ═══════════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════════


@app.get("/api/system/info")
async def system_info():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_freq = psutil.cpu_freq()

    return {
        "cpu_percent": cpu_percent,
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": {
            "current": cpu_freq.current if cpu_freq else 0,
            "min": cpu_freq.min if cpu_freq else 0,
            "max": cpu_freq.max if cpu_freq else 0,
        },
        "memory": {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
        "uptime": time.time() - start_time,
        "platform": platform.system(),
        "hostname": platform.node(),
    }


@app.get("/api/system/cpu")
async def cpu_info():
    return {
        "percent": psutil.cpu_percent(interval=0.1),
        "count": psutil.cpu_count(),
        "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True),
    }


@app.get("/api/system/memory")
async def memory_info():
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "available": mem.available,
        "percent": mem.percent,
        "swap": psutil.swap_memory()._asdict(),
    }


@app.get("/api/system/disk")
async def disk_info():
    disk = psutil.disk_usage("/")
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent,
    }


@app.get("/api/system/network")
async def network_info():
    net = psutil.net_io_counters()
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
    }


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════


@app.get("/api/health")
async def health():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    checks = {}

    # CPU check
    cpu = psutil.cpu_percent(interval=0.1)
    checks["cpu"] = {"status": "ok" if cpu < 80 else "warning", "value": cpu}

    # Memory check
    checks["memory"] = {"status": "ok" if mem.percent < 85 else "warning", "value": mem.percent}

    # Disk check
    checks["disk"] = {"status": "ok" if disk.percent < 90 else "warning", "value": disk.percent}

    overall = "healthy"
    if any(c["status"] == "warning" for c in checks.values()):
        overall = "degraded"

    return {"status": overall, "checks": checks}


# ═══════════════════════════════════════════════════════════════
# PROCESSES
# ═══════════════════════════════════════════════════════════════


@app.get("/api/system/processes")
async def top_processes():
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append(
                {
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu": info["cpu_percent"] or 0,
                    "memory": round(info["memory_percent"] or 0, 1),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Sort by CPU, top 10
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return {"processes": procs[:10]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001)
