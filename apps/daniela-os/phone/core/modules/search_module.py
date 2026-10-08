import os
import sys

import requests

YOU_KEY = os.getenv("YOU_COM_API_KEY")


def search_live_info(query):
    if YOU_KEY and "ydc-" in YOU_KEY:
        try:
            url = "https://api.ydc-index.io/search"
            headers = {"X-API-Key": YOU_KEY}
            r = requests.get(url, headers=headers, params={"query": query}, timeout=3.0)
            if r.status_code == 200:
                snippets = [item.get("snippet", "") for item in r.json().get("hits", [])[:2]]
                return "\n".join(snippets)
        except Exception:
            pass
    return f"Resultado simulado de búsqueda táctica para: '{query}'. Sin novedades críticas."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Avances DeepSeek"
    print(search_live_info(q))
