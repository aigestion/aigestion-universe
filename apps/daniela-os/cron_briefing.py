import datetime
import json
import urllib.request


def run_daily_briefing():
    url = "http://localhost:8085/api/chat"
    data = json.dumps({"message": "briefing"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            print(f"⏰ [{datetime.datetime.now()}] BRIEFING EJECUTADO:\n{res['response']}")
    except Exception as e:
        print(f"⚠️ Error ejecutando Briefing Cron: {e}")


if __name__ == "__main__":
    run_daily_briefing()
