import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime

def obtener_noticias(tema="economia Venezuela", max_noticias=10):
    """
    Obtiene noticias desde Google News RSS.
    """
    # Codificar el tema para URL
    tema_url = tema.replace(" ", "+")

    url = f"https://news.google.com/rss/search?q={tema_url}&hl=es-419&gl=VE&ceid=VE:es-419"

    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)

    # Parsear XML
    root = ET.fromstring(r.content)

    noticias = []
    for item in root.findall('.//item')[:max_noticias]:
        titulo = item.find('title').text if item.find('title') is not None else 'Sin título'
        enlace = item.find('link').text if item.find('link') is not None else ''
        fecha = item.find('pubDate').text if item.find('pubDate') is not None else ''

        noticias.append({
            'titulo': titulo,
            'enlace': enlace,
            'fecha': fecha,
        })

    return noticias


if __name__ == "__main__":
    # Prueba rápida
    noticias = obtener_noticias()
    for i, n in enumerate(noticias, 1):
        print(f"{i}. {n['titulo']}")
        print(f"   {n['fecha']}")
        print()
