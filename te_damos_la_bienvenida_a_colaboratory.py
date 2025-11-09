# app.py
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO

st.set_page_config(page_title="Indicadores Académicos", layout="centered")
st.title("Indicadores Académicos: Admisiones, Retención y Satisfacción")

# --------- Carga de datos (robusta) ----------
@st.cache_data
def cargar_csv(default_paths=("university_student_data.csv",
                              "data/university_student_data.csv")):
    df = None
    for p in default_paths:
        try:
            df = pd.read_csv(p)
            break
        except Exception:
            continue
    return df

df = cargar_csv()

if df is None:
    st.warning("No se encontró 'university_student_data.csv'. Carga el archivo para continuar.")
    archivo = st.file_uploader("Sube el CSV (university_student_data.csv)", type=["csv"])
    if archivo is not None:
        try:
            df = pd.read_csv(archivo)
        except Exception as e:
            st.error(f"Error leyendo el CSV: {e}")
            st.stop()
    else:
        st.stop()

# --------- Limpieza mínima / tipos ----------
df.columns = [c.strip() for c in df.columns]
# Columnas esperadas (nombres usados en el curso)
# 'Year', 'Term', 'Department', 'Applications', 'Enrolled',
# 'Retention Rate (%)', 'Student Satisfaction (%)'

# Normalización básica
if 'Year' in df.columns:
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
if 'Enrolled' in df.columns:
    df['Enrolled'] = pd.to_numeric(df['Enrolled'], errors='coerce')
for col in ['Retention Rate (%)', 'Student Satisfaction (%)', 'Applications']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

for col in ['Term', 'Department']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

df = df.dropna(subset=['Year'])

# --------- Controles (misma estructura del ejemplo) ----------
col1, col2 = st.columns([2, 1])

with col1:
    modo = st.radio(
        "Modo de visualización",
        ["Acumulado hasta el año", "Solo el año seleccionado"],
        index=0,
        help="Ver todo hasta el año elegido o únicamente el año puntual."
    )

with col2:
    show_grid = st.checkbox("Mostrar cuadrícula", value=True)
    color = st.color_picker("Color principal", value="#D7263D")  # tono estilo 'Atomic Heart' por defecto

# Slider de Año (como en el ejemplo con meses)
years_sorted = sorted([int(y) for y in df['Year'].dropna().unique()])
if not years_sorted:
    st.error("No hay valores válidos en 'Year'.")
    st.stop()

idx_min, idx_max = min(years_sorted), max(years_sorted)
anio_sel = st.slider("Selecciona el año", min_value=idx_min, max_value=idx_max, value=idx_max, step=1, format="%d")

# Filtro adicional (permite cumplir el requisito de filtros)
depts = sorted(df['Department'].dropna().unique()) if 'Department' in df.columns else []
dept_sel = st.multiselect("Filtrar por departamento (opcional)", options=depts, default=[])

# --------- Subconjunto según modo y filtros ----------
if modo == "Acumulado hasta el año":
    df_sub = df[df['Year'] <= anio_sel].copy()
else:
    df_sub = df[df['Year'] == anio_sel].copy()

if dept_sel:
    df_sub = df_sub[df_sub['Department'].isin(dept_sel)]

if df_sub.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# --------- Función de promedio ponderado ----------
def wavg(series, weights):
    w = np.nan_to_num(weights.values if hasattr(weights, "values") else np.array(weights), nan=0.0)
    x = np.nan_to_num(series.values if hasattr(series, "values") else np.array(series), nan=0.0)
    s = w.sum()
    if s <= 0:
        # si no hay pesos válidos, usar media simple
        return float(np.mean(x)) if len(x) else np.nan
    return float(np.average(x, weights=w))

# --------- KPIs (sobre el subconjunto actual) ----------
apps_total = df_sub['Applications'].sum() if 'Applications' in df_sub.columns else np.nan
enr_total = df_sub['Enrolled'].sum() if 'Enrolled' in df_sub.columns else np.nan
ret_w = wavg(df_sub['Retention Rate (%)'], df_sub['Enrolled']) if 'Retention Rate (%)' in df_sub.columns else np.nan
sat_w = wavg(df_sub['Student Satisfaction (%)'], df_sub['Enrolled']) if 'Student Satisfaction (%)' in df_sub.columns else np.nan

col_a, col_b, col_c = st.columns(3)
col_a.metric("Matriculados", f"{int(enr_total):,}" if pd.notna(enr_total) else "—")
col_b.metric("Retención (ponderada)", f"{ret_w:.1f}%" if pd.notna(ret_w) else "—")
col_c.metric("Satisfacción (ponderada)", f"{sat_w:.1f}%" if pd.notna(sat_w) else "—")

# ======================================================
# 1) LÍNEA: Retención ponderada por año
# ======================================================
# Agregar por año usando ponderación
grp_year = (df_sub.groupby('Year')
            .apply(lambda g: wavg(g['Retention Rate (%)'], g['Enrolled']))
            .rename("Retention_w"))
grp_year = grp_year.sort_index()

fig1, ax1 = plt.subplots(figsize=(10, 5))
x_idx = np.arange(len(grp_year.index))
ax1.plot(x_idx, grp_year.values, marker="o", linestyle="-", color=color, linewidth=2)

ax1.set_xticks(x_idx)
ax1.set_xticklabels([str(int(y)) for y in grp_year.index])
ax1.set_xlabel("Año")
ax1.set_ylabel("Retention Rate (%)")
titulo1 = "Retención (ponderada) por año"
if modo == "Acumulado hasta el año":
    titulo1 += f" · hasta {anio_sel}"
else:
    titulo1 += f" · año {anio_sel}"
ax1.set_title(titulo1)
ax1.grid(show_grid)
fig1.tight_layout()
st.pyplot(fig1)

# ======================================================
# 2) BARRAS: Satisfacción ponderada por año
# ======================================================
grp_sat = (df_sub.groupby('Year')
           .apply(lambda g: wavg(g['Student Satisfaction (%)'], g['Enrolled']))
           .rename("Satisfaction_w"))
grp_sat = grp_sat.sort_index()

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.bar([str(int(y)) for y in grp_sat.index], grp_sat.values)
ax2.set_xlabel("Año")
ax2.set_ylabel("Student Satisfaction (%)")
titulo2 = "Satisfacción (ponderada) por año"
if modo == "Acumulado hasta el año":
    titulo2 += f" · hasta {anio_sel}"
else:
    titulo2 += f" · año {anio_sel}"
ax2.set_title(titulo2)
ax2.grid(show_grid, axis='y')
fig2.tight_layout()
st.pyplot(fig2)

# ======================================================
# 3) DONUT: Comparación Spring vs Fall (ponderada)
# ======================================================
if 'Term' in df_sub.columns:
    term_order = ['Spring', 'Fall']
    term_vals = []
    term_labels = []
    for t in term_order:
        g = df_sub[df_sub['Term'] == t]
        if not g.empty and 'Enrolled' in g.columns:
            term_vals.append(wavg(g['Retention Rate (%)'], g['Enrolled']))
            term_labels.append(t)

    if len(term_vals) >= 2:
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        wedges, texts, autotexts = ax3.pie(
            term_vals,
            labels=term_labels,
            autopct="%1.1f%%",
            startangle=90
        )
        # Círculo central para donut
        centre_circle = plt.Circle((0, 0), 0.65, fc='white')
        fig3.gca().add_artist(centre_circle)
        ax3.set_title("Retención ponderada: Spring vs Fall")
        ax3.axis('equal')
        st.pyplot(fig3)
    else:
        st.info("No hay suficientes datos para comparar Spring vs Fall con los filtros actuales.")

# --------- Tabs de datos ----------
tab1, tab2 = st.tabs(["📈 Datos mostrados", "📚 Datos completos"])

with tab1:
    # Tabla resumen (años + métricas ponderadas)
    resumen = pd.DataFrame({
        "Year": grp_year.index.astype(int),
        "Retention_w": np.round(grp_year.values, 2),
        "Satisfaction_w": np.round(grp_sat.reindex(grp_year.index, fill_value=np.nan).values, 2)
    })
    st.dataframe(resumen.reset_index(drop=True), use_container_width=True)

with tab2:
    st.dataframe(df_sub.reset_index(drop=True), use_container_width=True)

st.caption("Usa el slider y los filtros para explorar los indicadores; todas las gráficas se actualizan en tiempo real.")
