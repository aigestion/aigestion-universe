import urllib.request
import urllib.parse
import json
import re

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return ' '.join(cleantext.split())

def run(context):
    cmd = context.lower()
    
    # Extraer la consulta eliminando el prefijo del comando
    query = context
    for prefix in ["busca", "buscar", "web_scout", "scout"]:
        if query.lower().startswith(prefix):
            query = query[len(prefix):].strip()
            break

    if not query:
        return "❌ [WEB SCOUT]: Indica qué deseas buscar. Ejemplo: 'web_scout ciberseguridad'."

    try:
        # Búsqueda liviana utilizando la API pública de DuckDuckGo (Instant Answer)
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            abstract = data.get("AbstractText", "")
            if abstract:
                source = data.get("AbstractSource", "Web")
                return f"🔍 [WEB SCOUT - {source}]: {abstract}"
            
            # Si no hay Abstract directo, extraer temas relacionados
            related = data.get("RelatedTopics", [])
            results = []
            for item in related[:3]:
                if "Text" in item:
                    results.append(item["Text"])
            
            if results:
                return f"🔍 [WEB SCOUT]: " + " | ".join(results)
                
            return f"🌐 [WEB SCOUT]: No se encontraron respuestas directas instantáneas para '{query}'. Probando extracción directa..."

    except Exception as e:
        return f"❌ [WEB SCOUT]: Error de conexión durante la búsqueda: {str(e)}"
