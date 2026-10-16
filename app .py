import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Monitor Económico VE", page_icon="📈", layout="wide")

# ============ DATOS CAMBIARIOS ============
@st.cache_data(ttl=600)
def obtener_cambiario():
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get("http://www.bcv.org.ve/", headers=headers, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')
    tasa_bcv = float(soup.select_one('div#dolar strong').text.strip().replace(',', '.'))

    payload = {"fiat": "VES", "asset": "USDT", "tradeType": "SELL", "page": 1, "rows": 1, "payTypes": []}
    r_p2p = requests.post("https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search", json=payload)
    tasa_usdt = float(r_p2p.json()['data'][0]['adv']['price'])

    brecha = ((tasa_usdt - tasa_bcv) / tasa_bcv) * 100
    return tasa_bcv, tasa_usdt, brecha

# ============ INFLACION ============
@st.cache_data(ttl=600)
def obtener_inflacion():
    df = pd.read_csv("inflacion.csv")
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df

# ============ MONETARIO ============
@st.cache_data(ttl=600)
def obtener_monetario():
    df = pd.read_csv("monetario.csv")
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df

# ============ PIB ============
@st.cache_data(ttl=600)
def obtener_pib():
    return pd.read_csv("Desktop/pib.csv")

@st.cache_data(ttl=600)
def obtener_sectores():
    return pd.read_csv("Desktop/sectores.csv")

# ============ TASAS ============
@st.cache_data(ttl=600)
def obtener_tasas_activas():
    df = pd.read_csv("Desktop/tasas_activas.csv")
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df

@st.cache_data(ttl=600)
def obtener_tasas_pasivas():
    df = pd.read_csv("Desktop/tasas_pasivas.csv")
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df

# ============ COMMODITIES ============
@st.cache_data(ttl=600)
def obtener_commodities():
    headers = {'User-Agent': 'Mozilla/5.0'}
    simbolos = {'Oro': 'GC=F', 'Plata': 'SI=F', 'Brent': 'BZ=F', 'WTI': 'CL=F'}
    resultados = {}
    for nombre, simbolo in simbolos.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}?interval=1d&range=5d"
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            meta = data['chart']['result'][0]['meta']
            precio = meta['regularMarketPrice']
            anterior = meta.get('chartPreviousClose', precio)
            cambio = ((precio - anterior) / anterior) * 100
            resultados[nombre] = {'precio': round(precio, 2), 'cambio': round(cambio, 2)}
        except Exception as e:
            resultados[nombre] = {'precio': 0, 'cambio': 0, 'error': str(e)}
    return resultados

# ============ NOTICIAS ============
@st.cache_data(ttl=1800)
def obtener_noticias(tema="economia Venezuela", max_noticias=10):
    tema_url = tema.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={tema_url}&hl=es-419&gl=VE&ceid=VE:es-419"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    root = ET.fromstring(r.content)
    noticias = []
    for item in root.findall('.//item')[:max_noticias]:
        titulo = item.find('title').text if item.find('title') is not None else 'Sin título'
        enlace = item.find('link').text if item.find('link') is not None else '#'
        fecha = item.find('pubDate').text if item.find('pubDate') is not None else ''
        noticias.append({'titulo': titulo, 'enlace': enlace, 'fecha': fecha})
    return noticias

# ============ TITULO ============
st.title("📈 Monitor Económico Venezuela")
st.caption("Datos en vivo — BCV, Binance P2P y Yahoo Finance")

# ============ KPIs PRINCIPALES ============
try:
    tasa_bcv, tasa_usdt, brecha = obtener_cambiario()
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Dólar BCV", f"Bs. {tasa_bcv:,.2f}")
    col2.metric("🪙 USDT Paralelo", f"Bs. {tasa_usdt:,.2f}")
    col3.metric("📊 Brecha Cambiaria", f"{brecha:.2f}%")
except Exception as e:
    st.error(f"Error al obtener datos cambiarios: {e}")

st.divider()

# ============ PESTAÑAS ============
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💱 Cambiario", "📊 Inflación", "🏦 Monetario",
    "📈 PIB & Sectores", "💹 Tasas", "🛢️ Commodities", "📰 Noticias"
])

with tab1:
    st.subheader("Tipo de Cambio y Brecha")
    st.write(f"- **Tasa oficial BCV:** {tasa_bcv:,.2f} Bs/USD")
    st.write(f"- **Tasa paralela (USDT):** {tasa_usdt:,.2f} Bs/USDT")
    st.write(f"- **Diferencia:** {tasa_usdt - tasa_bcv:,.2f} Bs ({brecha:.2f}%)")
    st.caption("Los datos se actualizan cada 10 minutos automáticamente.")

with tab2:
    st.subheader("Inflación Mensual")
    try:
        df = obtener_inflacion()
        ultimo = df.iloc[-1]
        acumulada = df['inflacion_mensual'].sum()
        anualizada = df['inflacion_mensual'].tail(12).sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Inflación Último Mes", f"{ultimo['inflacion_mensual']:.1f}%", help=f"Mes: {ultimo['mes']}")
        c2.metric("Inflación Acumulada (año)", f"{acumulada:.1f}%")
        c3.metric("Inflación Anualizada", f"{anualizada:.1f}%")
        fig = px.bar(df, x='mes', y='inflacion_mensual',
                     title='Inflación Mensual 2026 (%)',
                     color='inflacion_mensual', color_continuous_scale='Reds',
                     text='inflacion_mensual')
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Datos detallados")
        st.dataframe(df[['mes', 'inflacion_mensual', 'fuente']], use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar inflación: {e}")

with tab3:
    st.subheader("Agregados Monetarios")
    try:
        df = obtener_monetario()
        ultimo = df.iloc[-1]
        c1, c2 = st.columns(2)
        c1.metric("Liquidez Monetaria", f"{ultimo['liquidez_mmbs']:,.0f} MMBs", help=f"Mes: {ultimo['mes']}")
        c2.metric("Base Monetaria", f"{ultimo['base_monetaria_mmbs']:,.0f} MMBs", help=f"Mes: {ultimo['mes']}")
        fig = px.line(df, x='mes', y=['liquidez_mmbs', 'base_monetaria_mmbs'],
                      title='Evolución de Agregados Monetarios (MMBs)',
                      markers=True,
                      labels={'value': 'MMBs', 'mes': 'Mes', 'variable': 'Indicador'})
        fig.update_layout(legend_title_text='', hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Datos detallados")
        st.dataframe(df[['mes', 'liquidez_mmbs', 'base_monetaria_mmbs', 'fuente']], use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar monetario: {e}")

with tab4:
    st.subheader("Producto Interno Bruto (PIB)")
    try:
        df_pib = obtener_pib()
        df_sectores = obtener_sectores()
        ultimo = df_pib.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"PIB Total {ultimo['anio']}", f"{ultimo['pib_total']:.2f}%")
        c2.metric(f"Sector Público {ultimo['anio']}", f"{ultimo['pib_publico']:.2f}%")
        c3.metric(f"Sector Privado {ultimo['anio']}", f"{ultimo['pib_privado']:.2f}%")
        c4.metric(f"Impuestos Netos {ultimo['anio']}", f"{ultimo['impuestos_netos']:.2f}%")
        fig1 = px.line(df_pib, x='anio', y=['pib_total', 'pib_publico', 'pib_privado'],
                       title='Evolución del PIB (% variación anual)',
                       markers=True,
                       labels={'value': 'Variación (%)', 'anio': 'Año', 'variable': 'Indicador'})
        fig1.update_layout(legend_title_text='', hovermode='x unified')
        st.plotly_chart(fig1, use_container_width=True)
        st.subheader("Crecimiento por Sector Económico")
        df_sec = df_sectores.sort_values('crecimiento_2025', ascending=True)
        fig2 = px.bar(df_sec, x='crecimiento_2025', y='sector',
                      orientation='h',
                      title='Crecimiento por Sector (% 2025)',
                      color='crecimiento_2025',
                      color_continuous_scale='RdYlGn',
                      text='crecimiento_2025')
        fig2.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig2.update_layout(coloraxis_showscale=False, height=600)
        st.plotly_chart(fig2, use_container_width=True)
        st.subheader("Datos históricos del PIB")
        st.dataframe(df_pib, use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar PIB: {e}")

with tab5:
    st.subheader("Tasas de Interés — Bancos Universales")
    try:
        df_a = obtener_tasas_activas()
        df_p = obtener_tasas_pasivas()
        ultimo_a = df_a.iloc[0]
        ultimo_p = df_p.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tasa Activa", f"{ultimo_a['activa']:.2f}%")
        c2.metric("Tarjetas de Crédito", f"{ultimo_a['tarjetas']:.2f}%")
        c3.metric("Depósitos a Plazo", f"{ultimo_p['dep_plazo_total']:.2f}%")
        c4.metric("Depósitos de Ahorro", f"{ultimo_p['ahorro']:.2f}%")
        spread = ultimo_a['activa'] - ultimo_p['dep_plazo_total']
        st.info(f"📊 **Spread bancario** (Activa - Pasiva a Plazo): **{spread:.2f}%**")
        st.divider()
        st.subheader("📈 Evolución de Tasas Activas (2025-2026)")
        df_a_sorted = df_a.sort_values('fecha')
        fig_a = px.line(df_a_sorted, x='fecha', y=['activa', 'tarjetas', 'prestamos'],
                        markers=True,
                        title='Tasas Activas Anuales Nominales',
                        labels={'value': 'Tasa (%)', 'fecha': 'Fecha', 'variable': 'Tipo'})
        fig_a.update_layout(legend_title_text='', hovermode='x unified')
        st.plotly_chart(fig_a, use_container_width=True)
        st.subheader("📉 Evolución de Tasas Pasivas (2025-2026)")
        df_p_sorted = df_p.sort_values('fecha')
        fig_p = px.line(df_p_sorted, x='fecha', y=['ahorro', 'cuentas_corrientes', 'dep_plazo_total'],
                        markers=True,
                        title='Tasas Pasivas Anuales Nominales',
                        labels={'value': 'Tasa (%)', 'fecha': 'Fecha', 'variable': 'Tipo'})
        fig_p.update_layout(legend_title_text='', hovermode='x unified')
        st.plotly_chart(fig_p, use_container_width=True)
        st.subheader("⚖️ Comparación: Tasa Activa vs Pasiva")
        comparacion = df_a_sorted[['fecha', 'activa']].merge(
            df_p_sorted[['fecha', 'dep_plazo_total']], on='fecha', how='inner'
        )
        comparacion['spread'] = comparacion['activa'] - comparacion['dep_plazo_total']
        fig_c = px.line(comparacion, x='fecha', y=['activa', 'dep_plazo_total', 'spread'],
                        markers=True,
                        title='Tasa Activa vs Pasiva vs Spread (%)',
                        labels={'value': 'Tasa (%)', 'fecha': 'Fecha', 'variable': 'Indicador'})
        fig_c.update_layout(legend_title_text='', hovermode='x unified')
        st.plotly_chart(fig_c, use_container_width=True)
        with st.expander("📋 Ver datos completos de Tasas Activas"):
            st.dataframe(df_a, use_container_width=True)
        with st.expander("📋 Ver datos completos de Tasas Pasivas"):
            st.dataframe(df_p, use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar tasas: {e}")

with tab6:
    st.subheader("🛢️ Metales y Petróleo — Precios Internacionales")
    try:
        datos = obtener_commodities()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("🥇 Oro (oz)", f"${datos['Oro']['precio']:,.2f}",
                      delta=f"{datos['Oro']['cambio']:.2f}%")
        with c2:
            st.metric("🥈 Plata (oz)", f"${datos['Plata']['precio']:,.2f}",
                      delta=f"{datos['Plata']['cambio']:.2f}%")
        with c3:
            st.metric("🛢️ Brent", f"${datos['Brent']['precio']:,.2f}",
                      delta=f"{datos['Brent']['cambio']:.2f}%")
        with c4:
            st.metric("🛢️ WTI", f"${datos['WTI']['precio']:,.2f}",
                      delta=f"{datos['WTI']['cambio']:.2f}%")

        st.divider()
        st.subheader("💡 Referencias")
        st.write(f"- **Cesta venezolana:** pendiente de datos manuales")
        st.write(f"- **Oro / Plata:** precios spot internacionales (USD/onza)")
        st.write(f"- **Brent / WTI:** futuros de crudo (USD/barril)")

        st.caption("Los datos se actualizan cada 10 minutos automáticamente.")

        with st.expander("ℹ️ Sobre estos indicadores"):
            st.write("""
            - **Oro** es un activo refugio; sube en contextos de inflación o incertidumbre.
            - **Plata** tiene doble uso: monetario e industrial.
            - **Brent** es la referencia del crudo europeo y afecta directamente a Venezuela.
            - **WTI** es la referencia del crudo estadounidense.
            - La **cesta venezolana** se cotiza con descuento respecto al Brent.
            """)
    except Exception as e:
        st.error(f"Error al cargar commodities: {e}")

with tab7:
    st.subheader("📰 Resumen de Noticias de Impacto Económico")

    # Filtro por categoría
    categoria = st.selectbox(
        "Filtrar por categoría:",
        ["Venezuela — Economía", "Venezuela — Petróleo", "Economía Mundial", "Petróleo Mundial", "Dólar y Divisas"]
    )

    temas = {
        "Venezuela — Economía": "economia Venezuela",
        "Venezuela — Petróleo": "petroleo Venezuela",
        "Economía Mundial": "economia mundial",
        "Petróleo Mundial": "petroleo precio internacional",
        "Dólar y Divisas": "dolar euro divisas",
    }

    try:
        noticias = obtener_noticias(temas[categoria], max_noticias=15)
        if not noticias:
            st.warning("No se encontraron noticias para esta categoría.")
        else:
            for n in noticias:
                st.markdown(f"### [{n['titulo']}]({n['enlace']})")
                st.caption(f"📅 {n['fecha']}")
                st.divider()
    except Exception as e:
        st.error(f"Error al cargar noticias: {e}")

    st.caption("Las noticias se actualizan cada 30 minutos automáticamente.")
