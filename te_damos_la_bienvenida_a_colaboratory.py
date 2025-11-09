import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Dashboard académico", layout="wide")
st.title("Visualización de Admisiones, Retención y Satisfacción")

# ---------- Carga de datos ----------
def cargar_df():
    for name in ["university_student_data.csv", "university_student_data (1).csv"]:
        try:
            return pd.read_csv(name)
        except Exception:
            pass
    up = st.file_uploader("Cargar CSV (opcional)", type=["csv"])
    if up is not None:
        try:
            return pd.read_csv(up)
        except Exception:
            st.error("No se pudo leer el CSV.")
    return None

df_raw = cargar_df()
if df_raw is None or df_raw.empty:
    st.stop()

df = df_raw.copy()

# Columnas esperadas
C_YEAR = "Year"
C_TERM = "Term"
C_APPS = "Applications"
C_ADM  = "Admitted"
C_ENR  = "Enrolled"
C_RET  = "Retention Rate (%)"
C_SAT  = "Student Satisfaction (%)"
dept_cols = [c for c in df.columns if c.endswith(" Enrolled")]
dept_names = [c.replace(" Enrolled","") for c in dept_cols]

# ---------- Filtros ----------
with st.sidebar:
    st.subheader("Equipo")
    st.write("- Nombre 1")
    st.write("- Nombre 2")
    st.write("- Nombre 3")
    st.divider()

    st.subheader("Filtros")
    years = sorted(df[C_YEAR].dropna().unique().tolist())
    r_year = st.slider("Rango de años", int(min(years)), int(max(years)),
                       (int(min(years)), int(max(years))), step=1)
    terms = sorted(df[C_TERM].dropna().unique().tolist())
    sel_terms = st.multiselect("Term", options=terms, default=terms)
    if dept_cols:
        sel_depts = st.multiselect("Departamento", options=dept_names, default=dept_names)
    else:
        sel_depts = []

    st.divider()
    grid = st.checkbox("Mostrar cuadrícula", value=True)
    use_w = st.checkbox("Ajustar al ancho", value=True)

# Filtrado base
mask = (df[C_YEAR].between(r_year[0], r_year[1])) & (df[C_TERM].isin(sel_terms))
F = df.loc[mask].copy()

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
apps_tot = int(F[C_APPS].sum()) if len(F) else 0
adm_tot  = int(F[C_ADM].sum()) if len(F) else 0
enr_tot  = int(F[C_ENR].sum()) if len(F) else 0
ret_avg  = F[C_RET].mean() if len(F) else float("nan")
sat_avg  = F[C_SAT].mean() if len(F) else float("nan")

c1.metric("Solicitudes", f"{apps_tot:,}")
c2.metric("Admitidos",  f"{adm_tot:,}")
c3.metric("Matriculados", f"{enr_tot:,}")
c4.metric("Retención ⌀ / Satisfacción ⌀", f"{ret_avg:.1f}% / {sat_avg:.1f}%")

# ---------- Gráfica 1: Retención por año (línea) ----------
serie_ret = F.groupby(C_YEAR)[C_RET].mean().sort_index()
fig1, ax1 = plt.subplots(figsize=(8.5, 4.2))
ax1.plot(serie_ret.index.astype(str), serie_ret.values, marker="o", lw=2)
ax1.set_xlabel("Año"); ax1.set_ylabel("Retención (%)"); ax1.set_title("Retención promedio por año")
ax1.grid(grid)
st.pyplot(fig1, use_container_width=use_w)

# ---------- Gráfica 2: Satisfacción por año (barras) ----------
serie_sat = F.groupby(C_YEAR)[C_SAT].mean().sort_index()
fig2, ax2 = plt.subplots(figsize=(8.5, 4.2))
ax2.bar(serie_sat.index.astype(str), serie_sat.values)
ax2.set_xlabel("Año"); ax2.set_ylabel("Satisfacción (%)"); ax2.set_title("Satisfacción promedio por año")
ax2.grid(grid, axis="y")
st.pyplot(fig2, use_container_width=use_w)

# ---------- Gráfica 3: Distribución de solicitudes por term (donut/bar) ----------
apps_term = F.groupby(C_TERM)[C_APPS].sum().sort_values(ascending=False)
fig3, ax3 = plt.subplots(figsize=(6.5, 4.0))
if len(apps_term) >= 2:
    ax3.pie(apps_term.values, labels=apps_term.index.astype(str), autopct="%1.0f%%",
            startangle=90, wedgeprops={"width":0.6})
    ax3.set_title("Solicitudes por term")
else:
    ax3.bar(apps_term.index.astype(str), apps_term.values)
    ax3.set_title("Solicitudes por term"); ax3.grid(grid, axis="y")
st.pyplot(fig3, use_container_width=use_w)

# ---------- Gráfica 4: Serie de pipeline (Applications vs Admitted vs Enrolled) ----------
# Barras agrupadas por año
agg_pipe = F.groupby(C_YEAR)[[C_APPS, C_ADM, C_ENR]].sum().sort_index()
fig4, ax4 = plt.subplots(figsize=(9.5, 4.5))
x = np.arange(len(agg_pipe.index))
w = 0.28
ax4.bar(x - w, agg_pipe[C_APPS].values, width=w, label="Solicitudes")
ax4.bar(x,       agg_pipe[C_ADM].values,  width=w, label="Admitidos")
ax4.bar(x + w,   agg_pipe[C_ENR].values,  width=w, label="Matriculados")
ax4.set_xticks(x); ax4.set_xticklabels(agg_pipe.index.astype(str))
ax4.set_xlabel("Año"); ax4.set_ylabel("Estudiantes")
ax4.set_title("Serie anual: Solicitudes, Admitidos y Matriculados")
ax4.legend(); ax4.grid(grid, axis="y")
st.pyplot(fig4, use_container_width=use_w)

# ---------- Gráfica 5: Tasas de conversión (Admit rate, Yield rate) ----------
conv = F.groupby(C_YEAR)[[C_APPS, C_ADM, C_ENR]].sum().sort_index()
conv["Admit rate (%)"] = np.where(conv[C_APPS] > 0, conv[C_ADM] / conv[C_APPS] * 100, np.nan)
conv["Yield rate (%)"] = np.where(conv[C_ADM] > 0, conv[C_ENR] / conv[C_ADM] * 100, np.nan)
fig5, ax5 = plt.subplots(figsize=(8.5, 4.2))
ax5.plot(conv.index.astype(str), conv["Admit rate (%)"].values, marker="o", lw=2, label="Admit rate (%)")
ax5.plot(conv.index.astype(str), conv["Yield rate (%)"].values, marker="o", lw=2, label="Yield rate (%)")
ax5.set_xlabel("Año"); ax5.set_ylabel("Porcentaje"); ax5.set_title("Tasas de conversión")
ax5.legend(); ax5.grid(grid)
st.pyplot(fig5, use_container_width=use_w)

# ---------- Gráfica 6: Matrícula por departamento (apilado por año) ----------
if dept_cols:
    long = F.melt(id_vars=[C_YEAR, C_TERM], value_vars=dept_cols, var_name="Dept", value_name="EnrolledDept")
    long["Dept"] = long["Dept"].str.replace(" Enrolled","", regex=False)
    if sel_depts:
        long = long[long["Dept"].isin(sel_depts)]
    agg_dept = long.pivot_table(index=C_YEAR, columns="Dept", values="EnrolledDept", aggfunc="sum").fillna(0).sort_index()
    fig6, ax6 = plt.subplots(figsize=(9.5, 4.8))
    bottom = np.zeros(len(agg_dept.index))
    for col in agg_dept.columns:
        ax6.bar(agg_dept.index.astype(str), agg_dept[col].values, bottom=bottom, label=col)
        bottom += agg_dept[col].values
    ax6.set_xlabel("Año"); ax6.set_ylabel("Matriculados"); ax6.set_title("Matrícula por departamento (apilado)")
    ax6.legend(ncol=min(3, len(agg_dept.columns))); ax6.grid(grid, axis="y")
    st.pyplot(fig6, use_container_width=use_w)

# ---------- Datos ----------
tab1, tab2 = st.tabs(["Datos filtrados", "Datos completos"])
with tab1:
    st.dataframe(F.reset_index(drop=True), use_container_width=True)
with tab2:
    st.dataframe(df_raw, use_container_width=True)
