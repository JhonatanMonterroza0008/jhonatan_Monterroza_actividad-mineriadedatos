import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Tendencia de Ventas", layout="centered")
st.title("Tendencia de Ventas Mensuales")

meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
ventas = [20, 27, 25, 32, 38, 41, 47, 53, 58, 62, 65, 70]

df = pd.DataFrame({
    "Mes": meses,
    "Ventas (en miles)": ventas
})
col1, col2 = st.columns([2, 1])

with col1:
    modo = st.radio(
        "Modo de visualización",
        ["Acumulado hasta el mes", "Solo el mes seleccionado"],
        index=0,
        help="Elige si quieres ver la serie acumulada hasta el mes o únicamente el mes seleccionado."
    )

with col2:
    show_grid = st.checkbox("Mostrar cuadrícula", value=True)
    color = st.color_picker("Color de la línea", value="#4169E1")

idx_mes = st.slider("Selecciona el mes", min_value=1, max_value=12, value=12, step=1, format="%d")
mes_seleccionado = meses[idx_mes - 1]

if modo == "Acumulado hasta el mes":
    df_plot = df.iloc[:idx_mes].copy()
    titulo = f"Tendencia de Ventas (acumulado hasta {mes_seleccionado})"
else:
    df_plot = df.iloc[idx_mes-1:idx_mes].copy()
    titulo = f"Ventas del mes de {mes_seleccionado}"

col_a, col_b, col_c = st.columns(3)
valor_mes = df.loc[df["Mes"] == mes_seleccionado, "Ventas (en miles)"].iloc[0]
promedio_hasta = df.iloc[:idx_mes]["Ventas (en miles)"].mean()
max_hasta = df.iloc[:idx_mes]["Ventas (en miles)"].max()

col_a.metric("Ventas del mes", f"{valor_mes}k")
col_b.metric("Promedio hasta el mes", f"{promedio_hasta:.1f}k")
col_c.metric("Máximo hasta el mes", f"{max_hasta}k")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df_plot["Mes"], df_plot["Ventas (en miles)"], marker='o', linestyle='-', color=color)

if modo == "Acumulado hasta el mes" and len(df_plot) > 1:
    ax.fill_between(df_plot["Mes"], df_plot["Ventas (en miles)"], step=None, alpha=0.15)

ax.set_xlabel("Mes")
ax.set_ylabel("Ventas (en miles)")
ax.set_title(titulo)
ax.grid(show_grid)
fig.tight_layout()

st.pyplot(fig)
tab1, tab2 = st.tabs(["📈 Datos mostrados", "📚 Datos completos"])
with tab1:
    st.dataframe(df_plot.reset_index(drop=True), use_container_width=True)
with tab2:
    st.dataframe(df, use_container_width=True)

st.caption("Mueve el slider para explorar mes a mes o cambia el modo para ver un único mes.")
