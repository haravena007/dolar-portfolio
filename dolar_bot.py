import yfinance as yf
import plotly.express as px
import pandas as pd
import requests

try:
    print("[INFO]: Descargando datos de USD/CLP...")
    
    # Parche para evadir el bloqueo de Yahoo Finance
    sesion = requests.Session()
    sesion.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    datos_dolar = yf.download("CLP=X", start="2026-01-01", progress=False, session=sesion)
    
    if datos_dolar.empty:
        raise ValueError("No se recibieron datos de la API. Yahoo bloqueó el acceso.")

    # SOLUCIÓN AL KEYERROR: Forzamos que la fecha sea una columna llamada 'Date'
    datos_dolar = datos_dolar.reset_index()
    if 'Date' not in datos_dolar.columns and 'index' in datos_dolar.columns:
        datos_dolar.rename(columns={'index': 'Date'}, inplace=True)
    elif datos_dolar.columns[0] != 'Date':
        # Si el nombre viene raro (ej. MultiIndex), renombramos la primera columna a 'Date'
        columnas = list(datos_dolar.columns)
        columnas[0] = 'Date'
        datos_dolar.columns = columnas

    # Aplanamos el resto de columnas si vienen en formato MultiIndex
    if isinstance(datos_dolar.columns, pd.MultiIndex):
        datos_dolar.columns = [col[0] if isinstance(col, tuple) else col for col in datos_dolar.columns]

    # Buscamos la columna de precio de cierre
    col_cierre = 'Close' if 'Close' in datos_dolar.columns else ('Adj Close' if 'Adj Close' in datos_dolar.columns else None)
    if not col_cierre:
        # Si las columnas vienen con nombres anidados (ej. ('Close', 'CLP=X'))
        for col in datos_dolar.columns:
            if 'Close' in str(col):
                datos_dolar.rename(columns={col: 'Close'}, inplace=True)
                col_cierre = 'Close'
                break

    datos_dolar['Close'] = pd.to_numeric(datos_dolar[col_cierre]).astype(float)
    datos_dolar = datos_dolar.dropna(subset=['Close'])

    # Creación del dataframe acumulativo para la animación
    lista_marcos = []
    for i in range(len(datos_dolar)):
        sub_df = datos_dolar.iloc[:i+1].copy()
        sub_df['Frame_Animacion'] = pd.to_datetime(datos_dolar['Date'].iloc[i]).strftime('%Y-%b-%d')
        lista_marcos.append(sub_df)
        
    df_animado = pd.concat(lista_marcos, ignore_index=True)

    max_precio = float(datos_dolar['Close'].max())
    min_precio = float(datos_dolar['Close'].min())
    prom_precio = float(datos_dolar['Close'].mean())
    ultimo_precio = float(datos_dolar['Close'].iloc[-1])

    fig = px.line(df_animado, 
                  x='Date', 
                  y='Close', 
                  animation_frame='Frame_Animacion', 
                  title=f'Evolución USD/CLP (YTD 2026) | ÚLTIMO VALOR: ${ultimo_precio:.2f} CLP',
                  labels={'Close': 'Precio (CLP)', 'Date': 'Fecha'},
                  range_x=[datos_dolar['Date'].min(), datos_dolar['Date'].max()],
                  range_y=[datos_dolar['Close'].min() - 15, datos_dolar['Close'].max() + 15])

    fig.add_annotation(
        text=(
            f"<span style='font-size:14px; color:#38bdf8;'><b>ÚLTIMO PRECIO: ${ultimo_precio:.2f}</b></span><br>"
            f"---------------------------------<br>"
            f"<b>ESTADÍSTICAS DEL PERIODO</b><br>"
            f"Máximo: ${max_precio:.2f}<br>"
            f"Promedio: ${prom_precio:.2f}<br>"
            f"Mínimo: ${min_precio:.2f}"
        ),
        xref="paper", yref="paper",
        x=0.98, y=0.95,
        xanchor="right", yanchor="top",
        showarrow=False,
        font=dict(size=12, color="#f8fafc", family="Arial"),
        bgcolor="rgba(15, 23, 42, 0.9)",
        bordercolor="rgba(56, 189, 248, 0.5)",
        borderwidth=1, borderpad=12
    )

    fig.add_hline(y=max_precio, line_dash="dot", line_color="#ef4444", opacity=0.4)
    fig.add_hline(y=min_precio, line_dash="dot", line_color="#22c55e", opacity=0.4)
    fig.add_hline(y=prom_precio, line_dash="dash", line_color="#94a3b8", opacity=0.4)

    fig.add_annotation(
        text="Herramienta analítica desarrollada para el Grupo Portfolio",
        xref="paper", yref="paper",
        x=0.5, y=-0.18,
        showarrow=False,
        font=dict(size=12, color="lightblue", family="Arial")
    )

    fig.update_xaxes(rangeslider_visible=False) 
    fig.update_layout(
        template="plotly_dark", 
        margin=dict(b=90, t=60),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a"
    )
    
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 30
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 10

    fig.write_html("index.html")
    print(f"[ÉXITO]: index.html generado con el último valor: ${ultimo_precio:.2f} CLP")

except Exception as e:
    print(f"[ERROR]: {e}")
