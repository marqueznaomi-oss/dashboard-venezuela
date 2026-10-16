import requests
import json

def obtener_commodities():
    """
    Obtiene precios de oro, plata, petróleo Brent y WTI desde Yahoo Finance.
    """
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Símbolos de Yahoo Finance
    # GC=F = Oro (futuros), SI=F = Plata (futuros)
    # BZ=F = Brent (futuros), CL=F = WTI (futuros)
    simbolos = {
        'oro': 'GC=F',
        'plata': 'SI=F',
        'brent': 'BZ=F',
        'wti': 'CL=F',
    }

    resultados = {}

    for nombre, simbolo in simbolos.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}?interval=1d&range=1d"
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()

            precio = data['chart']['result'][0]['meta']['regularMarketPrice']
            moneda = data['chart']['result'][0]['meta']['currency']

            resultados[nombre] = {
                'precio': round(precio, 2),
                'moneda': moneda,
            }
        except Exception as e:
            resultados[nombre] = {'precio': None, 'moneda': 'USD', 'error': str(e)}

    return resultados


if __name__ == "__main__":
    # Prueba rápida
    datos = obtener_commodities()
    for k, v in datos.items():
        print(f"{k.upper()}: {v}")
