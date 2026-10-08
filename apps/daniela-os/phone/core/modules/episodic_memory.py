import json
import os
import sys
import time

MEMORY_FILE = os.path.expanduser("~/apps/aig/phone/core/episodic_memory.json")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


def save_memory(fact):
    memories = []
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, encoding="utf-8") as f:
                memories = json.load(f)
        except Exception:
            pass
    memories.append({"timestamp": time.time(), "fact": fact})
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories[-100:], f, indent=2, ensure_ascii=False)
    return f"Recuerdo memorizado: '{fact}'"


def recall_memories(query_text):
    if not os.path.exists(MEMORY_FILE):
        return ""
    try:
        with open(MEMORY_FILE, encoding="utf-8") as f:
            memories = json.load(f)
        words = [w.lower() for w in query_text.split() if len(w) > 3]
        matched = [m["fact"] for m in memories if any(w in m["fact"].lower() for w in words)]
        return "\n".join(matched[:3])
    except Exception:
        return ""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(save_memory(" ".join(sys.argv[1:])))
    else:
        print(recall_memories("memoria"))
