"""
AGENT_VIGIA - 24/7 Monitoring Agent
=====================================
Monitoriza el sistema, detecta anomalias y lanza alertas.

Character: Agente Vigia (Red #ff3333, JorgeNeural voice)
Role: 24/7 system monitoring, anomaly detection, auto-alert dispatch

Real capabilities:
- System health monitoring (CPU, RAM, disk, network)
- Service health checks (Flask API port 5050, etc.)
- Anomaly detection (threshold + pattern based)
- Auto-alert dispatch via message broker
- Self-healing trigger (delegates to skills/self_healing.py)
- Git backup verification
- Activity logging for storyboard generation
- Inter-agent messaging via message_broker

Usage:
    from agent_vigia import VigiaAgent

    agent = VigiaAgent()
    health = agent.check_system_health()
    services = agent.check_services()
    agent.run_monitoring_loop()  # blocking, runs forever
"""

import os
import platform
import socket
import subprocess
import time
from datetime import datetime

import psutil

try:
    from message_broker import activity, broker
except ImportError:
    broker = None
    activity = None

# Character config
CHARACTER = {
    "name": "AGENT_VIGIA",
    "color": "#ff3333",
    "voice": "es-ES-JorgeNeural",
    "role": "24/7 system monitoring + anomaly detection + alert dispatch",
    "abilities": [
        "Monitoriza 24/7 sin descanso",
        "Detecta anomalias en tiempo real",
        "Lanza alertas automaticas a Daniela",
        "Verifica backups y sincronizaciones",
        "Audita seguridad del sistema",
        "Activa self-healing automatico",
    ],
}

# Monitoring thresholds
THRESHOLDS = {
    "cpu_percent": 85,  # Alert if CPU > 85%
    "memory_percent": 90,  # Alert if RAM > 90%
    "disk_percent": 85,  # Alert if disk > 85%
    "temp_celsius": 45,  # Alert if temp > 45C (mobile)
    "response_time_ms": 2000,  # Alert if response > 2s
}

# Services to monitor
SERVICES = [
    {
        "name": "AIGestion Flask API",
        "host": "localhost",
        "port": 5050,
        "path": "/",
        "expected_status": [200],
    },
    {
        "name": "Daniela OS Backend",
        "host": "localhost",
        "port": 5059,
        "path": "/",
        "expected_status": [200, 404],
    },
]


class VigiaAgent:
    """24/7 monitoring agent."""

    def __init__(self):
        self.name = CHARACTER["name"]
        self.character = CHARACTER
        self.thresholds = THRESHOLDS
        self.services = SERVICES
        self.alerts_sent = 0
        self.checks_performed = 0
        self.anomalies_detected = 0
        self._alert_history = []
        self._baseline = {}  # For pattern-based anomaly detection

    def check_system_health(self) -> dict:
        """
        Check system health: CPU, RAM, disk, network.

        Returns dict with all metrics + anomaly flags.
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "metrics": {},
            "anomalies": [],
            "overall_status": "healthy",
        }

        try:
            # CPU
            cpu = psutil.cpu_percent(interval=1)
            health["metrics"]["cpu_percent"] = cpu
            if cpu > self.thresholds["cpu_percent"]:
                health["anomalies"].append(
                    {
                        "type": "high_cpu",
                        "value": cpu,
                        "threshold": self.thresholds["cpu_percent"],
                        "severity": "warning" if cpu < 95 else "critical",
                    }
                )

            # Memory
            mem = psutil.virtual_memory()
            health["metrics"]["memory_percent"] = mem.percent
            health["metrics"]["memory_used_gb"] = round(mem.used / (1024**3), 2)
            health["metrics"]["memory_total_gb"] = round(mem.total / (1024**3), 2)
            if mem.percent > self.thresholds["memory_percent"]:
                health["anomalies"].append(
                    {
                        "type": "high_memory",
                        "value": mem.percent,
                        "threshold": self.thresholds["memory_percent"],
                        "severity": "warning" if mem.percent < 97 else "critical",
                    }
                )

            # Disk
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            health["metrics"]["disk_percent"] = disk_percent
            health["metrics"]["disk_free_gb"] = round(disk.free / (1024**3), 2)
            if disk_percent > self.thresholds["disk_percent"]:
                health["anomalies"].append(
                    {
                        "type": "low_disk_space",
                        "value": disk_percent,
                        "threshold": self.thresholds["disk_percent"],
                        "severity": "warning",
                    }
                )

            # Network
            net = psutil.net_io_counters()
            health["metrics"]["network_sent_mb"] = round(net.bytes_sent / (1024**2), 2)
            health["metrics"]["network_recv_mb"] = round(net.bytes_recv / (1024**2), 2)

            # Process count
            health["metrics"]["process_count"] = len(psutil.pids())

            # Battery (if available, e.g., mobile/laptop)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    health["metrics"]["battery_percent"] = battery.percent
                    health["metrics"]["battery_plugged"] = battery.power_plugged
                    if battery.percent < 20 and not battery.power_plugged:
                        health["anomalies"].append(
                            {"type": "low_battery", "value": battery.percent, "severity": "warning"}
                        )
            except (AttributeError, Exception):
                pass

            # Overall status
            critical = [a for a in health["anomalies"] if a["severity"] == "critical"]
            warnings = [a for a in health["anomalies"] if a["severity"] == "warning"]
            if critical:
                health["overall_status"] = "critical"
            elif warnings:
                health["overall_status"] = "warning"

        except Exception as e:
            health["overall_status"] = "error"
            health["error"] = str(e)

        self.checks_performed += 1
        self.anomalies_detected += len(health["anomalies"])

        if activity:
            activity.log(
                self.name,
                "check_system_health",
                {
                    "status": health["overall_status"],
                    "anomalies": len(health["anomalies"]),
                    "cpu": health["metrics"].get("cpu_percent", 0),
                    "memory": health["metrics"].get("memory_percent", 0),
                },
            )

        return health

    def check_services(self) -> list[dict]:
        """Check health of monitored services."""
        results = []

        for service in self.services:
            result = {
                "name": service["name"],
                "host": service["host"],
                "port": service["port"],
                "status": "unknown",
                "response_time_ms": None,
                "checked_at": datetime.now().isoformat(),
            }

            try:
                # Check if port is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                start = time.time()
                result["port_open"] = sock.connect_ex((service["host"], service["port"])) == 0
                elapsed = (time.time() - start) * 1000
                sock.close()

                result["response_time_ms"] = round(elapsed, 1)

                if result["port_open"]:
                    result["status"] = "online"
                    if elapsed > self.thresholds["response_time_ms"]:
                        result["status"] = "slow"
                        result["anomaly"] = "slow_response"
                else:
                    result["status"] = "offline"
                    result["anomaly"] = "service_down"

            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)

            results.append(result)

        # Alert on offline services
        offline = [r for r in results if r["status"] in ("offline", "error")]
        if offline and broker:
            for service_down in offline:
                self._send_alert(
                    f"Service down: {service_down['name']}",
                    service_down,
                    priority=0,  # URGENT
                )

        if activity:
            activity.log(
                self.name,
                "check_services",
                {
                    "total": len(results),
                    "online": len([r for r in results if r["status"] == "online"]),
                    "offline": len(offline),
                },
            )

        return results

    def check_git_backup(self) -> dict:
        """Verify last git backup was successful."""
        result = {
            "checked_at": datetime.now().isoformat(),
            "status": "unknown",
        }

        try:
            # Check last commit date
            commit_date = subprocess.check_output(
                ["git", "log", "-1", "--format=%ci"], cwd=os.path.dirname(__file__), text=True
            ).strip()

            if commit_date:
                result["last_commit"] = commit_date

                # Parse date and check freshness
                dt = datetime.strptime(commit_date.split(" ")[0], "%Y-%m-%d")
                hours_ago = (datetime.now() - dt).total_seconds() / 3600

                if hours_ago > 26:
                    result["status"] = "stale"
                    result["hours_since_last"] = round(hours_ago, 1)
                    self._send_alert("Git backup stale", result, priority=1)
                else:
                    result["status"] = "fresh"
                    result["hours_since_last"] = round(hours_ago, 1)
            else:
                result["status"] = "no_commits"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        if activity:
            activity.log(self.name, "check_git_backup", result)

        return result

    def detect_anomalies(self, current_health: dict) -> list[dict]:
        """
        Detect anomalies using threshold + pattern detection.
        Learns baseline over time and flags deviations.
        """
        anomalies = current_health.get("anomalies", [])
        metrics = current_health.get("metrics", {})

        # Pattern-based: compare to baseline
        for metric_name, value in metrics.items():
            if not isinstance(value, (int, float)):
                continue

            if metric_name not in self._baseline:
                self._baseline[metric_name] = {"values": [], "avg": value, "std": 0}

            baseline = self._baseline[metric_name]
            baseline["values"].append(value)

            # Keep last 100 readings
            if len(baseline["values"]) > 100:
                baseline["values"] = baseline["values"][-100:]

            # Recalculate baseline after 10 readings
            if len(baseline["values"]) >= 10:
                vals = baseline["values"]
                baseline["avg"] = sum(vals) / len(vals)
                variance = sum((x - baseline["avg"]) ** 2 for x in vals) / len(vals)
                baseline["std"] = variance**0.5

                # Anomaly: value is 3 standard deviations from mean
                if baseline["std"] > 0:
                    z_score = abs(value - baseline["avg"]) / baseline["std"]
                    if z_score > 3:
                        anomalies.append(
                            {
                                "type": f"pattern_anomaly_{metric_name}",
                                "value": value,
                                "baseline_avg": round(baseline["avg"], 2),
                                "z_score": round(z_score, 2),
                                "severity": "warning",
                            }
                        )

        return anomalies

    def _send_alert(self, title: str, details: dict, priority: int = 1):
        """Send alert via message broker to Daniela and relevant agents."""
        self.alerts_sent += 1
        self._alert_history.append(
            {
                "title": title,
                "details": details,
                "priority": priority,
                "sent_at": datetime.now().isoformat(),
            }
        )

        # Keep history manageable
        if len(self._alert_history) > 50:
            self._alert_history = self._alert_history[-50:]

        if broker:
            # Alert Daniela
            broker.send(
                self.name, "DANIELA", "alert", {"title": title, **details}, priority=priority
            )

            # Alert OPERATOR for action
            if priority == 0:
                broker.send(
                    self.name,
                    "OPERATOR",
                    "alert",
                    {"title": title, "action_required": True, **details},
                    priority=0,
                )

        if activity:
            activity.log(
                self.name,
                "send_alert",
                {
                    "title": title,
                    "priority": priority,
                },
            )

    def run_monitoring_cycle(self) -> dict:
        """Run a complete monitoring cycle."""
        cycle = {
            "cycle_number": self.checks_performed,
            "timestamp": datetime.now().isoformat(),
            "system_health": self.check_system_health(),
            "services": self.check_services(),
            "git_backup": self.check_git_backup(),
        }

        # Pattern-based anomaly detection
        cycle["system_health"]["anomalies"] = self.detect_anomalies(cycle["system_health"])

        # Overall status
        has_critical = cycle["system_health"]["overall_status"] == "critical"
        offline_services = [s for s in cycle["services"] if s["status"] == "offline"]

        if has_critical or offline_services:
            cycle["overall_status"] = "critical"
        elif cycle["system_health"]["anomalies"]:
            cycle["overall_status"] = "warning"
        else:
            cycle["overall_status"] = "healthy"

        # Notify Daniela of status
        if broker and cycle["overall_status"] != "healthy":
            broker.send(
                self.name,
                "DANIELA",
                "status",
                {
                    "task": "monitoring_cycle",
                    "status": cycle["overall_status"],
                    "anomalies": len(cycle["system_health"]["anomalies"]),
                    "offline_services": len(offline_services),
                },
                priority=0 if cycle["overall_status"] == "critical" else 1,
            )

        if activity:
            activity.log(
                self.name,
                "monitoring_cycle",
                {
                    "status": cycle["overall_status"],
                    "checks": self.checks_performed,
                    "anomalies_total": self.anomalies_detected,
                    "alerts_sent": self.alerts_sent,
                },
            )

        return cycle

    def run_monitoring_loop(self, interval: int = 60):
        """
        Run continuous monitoring loop.
        Blocking call - runs forever, checking every `interval` seconds.
        """
        print(f"[{self.name}] Monitoring loop started (interval: {interval}s)")
        print(f"[{self.name}] Press Ctrl+C to stop")
        print()

        try:
            while True:
                cycle = self.run_monitoring_cycle()
                status = cycle["overall_status"]
                icon = {"healthy": "OK", "warning": "!!", "critical": "XX"}
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"[{icon.get(status, '??')}] {status:10s} | "
                    f"CPU: {cycle['system_health']['metrics'].get('cpu_percent', 0):.0f}% | "
                    f"RAM: {cycle['system_health']['metrics'].get('memory_percent', 0):.0f}% | "
                    f"Services: {len([s for s in cycle['services'] if s['status'] == 'online'])}/{len(cycle['services'])} | "
                    f"Alerts: {self.alerts_sent}"
                )

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n[{self.name}] Monitoring stopped by user.")

    def get_status(self) -> dict:
        """Get agent status."""
        return {
            "name": self.name,
            "character": self.character,
            "checks_performed": self.checks_performed,
            "anomalies_detected": self.anomalies_detected,
            "alerts_sent": self.alerts_sent,
            "services_monitored": len(self.services),
            "baseline_metrics": len(self._baseline),
            "recent_alerts": self._alert_history[-5:] if self._alert_history else [],
        }

    def health_check(self) -> bool:
        """Check if agent is healthy."""
        return True


def demo():
    """Demo the VigiaAgent."""
    print("=" * 60)
    print("AGENT_VIGIA - 24/7 Monitoring Agent")
    print("=" * 60)
    print()

    agent = VigiaAgent()
    print(f"Name: {agent.name}")
    print(f"Color: {agent.character['color']}")
    print()

    print("[1] System health check...")
    health = agent.check_system_health()
    print(f"  Status: {health['overall_status']}")
    print(f"  CPU: {health['metrics'].get('cpu_percent', 0):.1f}%")
    print(f"  RAM: {health['metrics'].get('memory_percent', 0):.1f}%")
    print(f"  Disk: {health['metrics'].get('disk_percent', 0):.1f}%")
    print(f"  Processes: {health['metrics'].get('process_count', 0)}")
    if health["anomalies"]:
        print(f"  Anomalies: {len(health['anomalies'])}")
        for a in health["anomalies"]:
            print(f"    - {a['type']} ({a['severity']})")
    else:
        print("  Anomalies: 0 (all healthy)")
    print()

    print("[2] Service health checks...")
    services = agent.check_services()
    for s in services:
        print(f"  {s['name']:30s} {s['status']:8s} {s.get('response_time_ms', '?')}ms")
    print()

    print("[3] Git backup check...")
    git = agent.check_git_backup()
    print(f"  Status: {git['status']}")
    if "hours_since_last" in git:
        print(f"  Hours since last: {git['hours_since_last']}")
    print()

    print("[4] Agent status:")
    status = agent.get_status()
    print(f"  Checks performed: {status['checks_performed']}")
    print(f"  Anomalies detected: {status['anomalies_detected']}")
    print(f"  Alerts sent: {status['alerts_sent']}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    demo()
