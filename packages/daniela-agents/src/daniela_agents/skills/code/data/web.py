import logging
import re
import urllib.request
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
    def handle_data(self, data):
        clean = data.strip()
        if clean:
            self.text.append(clean)

def scrape_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            parser = TextExtractor()
            parser.feed(html)
            full_text = " ".join(parser.text)
            summary = re.sub(r'\s+', ' ', full_text)[:300]
            logging.info(f"URL procesada con éxito: {url}")
            return f"Resumen extraído de {url}: {summary}..."
    except Exception as e:
        logging.error(f"Error extrayendo URL: {str(e)}")
        return f"No se pudo acceder a la URL: {e}"
