import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Tendencia de Ventas — Atomic Heart", layout="centered")
st.title("Tendencia de Ventas Mensuales — Atomic Heart")

# Paleta / estilo Atomic Heart
plt.rcParams.update({
    "figure.facecolor": "#0e0f12",
    "axes.facecolor":   "#121317",
    "axes.edgecolor":   "#EDEDED",
    "axes.labelcolor":  "#EDEDED",
    "axes.titlecolor":  "#f04a4a",
    "xtick.color":      "#d7d7d7",
    "ytick.color":      "#d7d7d7",
    "grid.color":       "#3c3c3c",
    "grid.linestyle":   "--",
    "text.color":       "#EDEDED",
    "axes.titleweight": "bold",
})
ACCENT = "#f04a4a"
ACCENT2 = "#bfbfc2"

meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
ventas = [20, 27, 25, 32, 38, 41, 47, 53, 58, 62, 65, 70]
df = pd.DataFrame({"Mes": meses, "Ventas (en miles)": ventas})

col1, col2 = st.columns([2, 1])
with col1:
    modo = st.radio(
        "Modo de visualización",
        ["Acumulado hasta el mes", "Solo el mes seleccionado"],
        index=0
    )
with col2:
    show_grid = st.checkbox("Mostrar cuadrícula", value=True)
    # Si quieres permitir color manual, descomenta:
    # ACCENT = st.color_picker("Color de línea", value=ACCENT)

idx_mes = st.slider("Selecciona el mes", 1, 12, 12, 1, format="%d")
mes_sel = meses[idx_mes - 1]

if modo == "Acumulado hasta el mes":
    df_plot = df.iloc[:idx_mes].copy()
    titulo = f"Tendencia de Ventas (acumulado hasta {mes_sel})"
else:
    df_plot = df.iloc[idx_mes-1:idx_mes].copy()
    titulo = f"Ventas del mes de {mes_sel}"

col_a, col_b, col_c = st.columns(3)
valor_mes = df.loc[df["Mes"] == mes_sel, "Ventas (en miles)"].iloc[0]
promedio_hasta = df.iloc[:idx_mes]["Ventas (en miles)"].mean()
max_hasta = df.iloc[:idx_mes]["Ventas (en miles)"].max()
col_a.metric("Ventas del mes", f"{valor_mes}k")
col_b.metric("Promedio hasta el mes", f"{promedio_hasta:.1f}k")
col_c.metric("Máximo hasta el mes", f"{max_hasta}k")

fig, ax = plt.subplots(figsize=(9, 4.8))
ax.plot(df_plot["Mes"], df_plot["Ventas (en miles)"],
        marker='o', linestyle='-', color=ACCENT, lw=2.6,
        markeredgecolor="#ffffff", markeredgewidth=1.2)
if modo == "Acumulado hasta el mes" and len(df_plot) > 1:
    ax.fill_between(df_plot["Mes"], df_plot["Ventas (en miles)"], alpha=0.15, color=ACCENT)

ax.set_xlabel("Mes"); ax.set_ylabel("Ventas (en miles)")
ax.set_title(titulo)
ax.grid(show_grid)
fig.tight_layout()
st.pyplot(fig)

tab1, tab2 = st.tabs(["📈 Datos mostrados", "📚 Datos completos"])
with tab1:
    st.dataframe(df_plot.reset_index(drop=True), use_container_width=True)
with tab2:
    st.dataframe(df, use_container_width=True)

st.caption("Estética oscura con acento rojo (Atomic Heart). Ajusta 'Mostrar cuadrícula' si lo prefieres.")
