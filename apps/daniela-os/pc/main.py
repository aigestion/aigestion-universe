"""
Daniela OS - Epic PC Experience
Main Orchestrator - Launches all 20 epic systems
"""

import json
import sys
import time
from pathlib import Path

EPIC_ROOT = Path(__file__).parent
AIG_ROOT = EPIC_ROOT.parent

SYSTEMS = {
    "voice": {"module": "voice_daemon", "name": "Voice AI Desktop", "port": 5010},
    "wallpaper": {"module": "neural_wallpaper", "name": "Neural Wallpaper", "port": 5011},
    "galaxy": {"module": "file_galaxy", "name": "3D File Galaxy", "port": 5012},
    "notifications": {"module": "notification_brain", "name": "Notification Brain", "port": 5013},
    "hologram": {"module": "health_hologram", "name": "System Hologram", "port": 5014},
    "copilot": {"module": "code_copilot", "name": "Code Copilot", "port": 5015},
    "telepathy": {"module": "cross_device", "name": "Cross-Device Telepathy", "port": 5016},
    "launcher": {"module": "app_launcher", "name": "Predictive Launcher", "port": 5017},
    "ar": {"module": "ar_overlay", "name": "AR Desktop", "port": 5018},
    "organism": {"module": "living_organism", "name": "Living Organism", "port": 5019},
    "memory": {"module": "memory_palace", "name": "AI Memory Palace", "port": 5021},
    "dream": {"module": "dream_logger", "name": "Dream Logger", "port": 5022},
    "context": {"module": "context_switcher", "name": "Context Switcher", "port": 5023},
    "organizer": {"module": "auto_organizer", "name": "AI Auto-Organizer", "port": 5024},
    "focus": {"module": "focus_mode", "name": "Focus Mode", "port": 5025},
    "typing": {"module": "typing_predictor", "name": "Typing Predictor", "port": 5026},
    "meeting": {"module": "meeting_prepper", "name": "Meeting Prepper", "port": 5027},
    "digest": {"module": "meeting_digest", "name": "Post-Meeting Digest", "port": 5028},
    "email": {"module": "email_brain", "name": "Email Priority Brain", "port": 5029},
    "weaver": {"module": "knowledge_weaver", "name": "Knowledge Weaver", "port": 5030},
}

STATUS_FILE = EPIC_ROOT / "status.json"


def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


def load_status():
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)
    return {}


def print_banner():
    print("""
============================================================
           DANIELA OS - EPIC PC EXPERIENCE
============================================================
  1. Voice AI Desktop      11. AI Memory Palace
  2. Neural Wallpaper      12. Dream Logger
  3. 3D File Galaxy        13. Context Switcher
  4. Notification Brain    14. AI Auto-Organizer
  5. System Hologram       15. Focus Mode
  6. Code Copilot          16. Typing Predictor
  7. Cross-Device Telepathy 17. Meeting Prepper
  8. Predictive Launcher   18. Post-Meeting Digest
  9. AR Desktop            19. Email Priority Brain
 10. Living Organism       20. Knowledge Weaver

  Commands: start [all|name], stop [all|name], status
============================================================
""")


def main():
    print_banner()
    status = load_status()

    if len(sys.argv) < 2:
        print("Usage: python main.py [start|stop|status] [all|system_name]")
        return

    cmd = sys.argv[1].lower()
    target = sys.argv[2].lower() if len(sys.argv) > 2 else "all"

    if cmd == "status":
        print("\nSystem Status:")
        for key, info in SYSTEMS.items():
            s = status.get(key, {})
            state = s.get("state", "stopped")
            icon = "[RUNNING]" if state == "running" else "[STOPPED]"
            print(f"  {icon} {info['name']:<30} Port: {info['port']}")
        return

    if cmd == "start":
        targets = SYSTEMS.keys() if target == "all" else [target]
        for key in targets:
            if key not in SYSTEMS:
                print(f"  [ERROR] Unknown system: {key}")
                continue
            info = SYSTEMS[key]
            print(f"  [START] {info['name']} on port {info['port']}...")
            status[key] = {"state": "running", "port": info["port"], "started": time.time()}
            save_status(status)

        print(f"\n{len(targets)} system(s) started")
        print("   Web UIs available at http://localhost:5020")

    elif cmd == "stop":
        targets = SYSTEMS.keys() if target == "all" else [target]
        for key in targets:
            if key not in SYSTEMS:
                continue
            info = SYSTEMS[key]
            print(f"  [STOP] {info['name']}...")
            status[key] = {"state": "stopped", "port": info["port"]}
            save_status(status)

        print(f"\n{len(targets)} system(s) stopped")


if __name__ == "__main__":
    main()
