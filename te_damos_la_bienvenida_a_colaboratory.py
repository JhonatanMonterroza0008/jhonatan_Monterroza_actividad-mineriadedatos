import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Admisiones, Retención y Satisfacción", layout="wide")
st.title("Dashboard universitario — Admisiones, Retención y Satisfacción")
st.caption("Actividad: Visualización y despliegue de dashboard (Streamlit).")

# --- Datos ---
def cargar_df():
    # Intenta nombres comunes del CSV (estándar y con (1))
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

# --- Normalización mínima ---
df = df_raw.copy()
col_year = "Year"
col_term = "Term"
col_apps = "Applications"
col_adm  = "Admitted"
col_enrl = "Enrolled"
col_ret  = "Retention Rate (%)"
col_sat  = "Student Satisfaction (%)"

dept_cols = [c for c in df.columns if c.endswith(" Enrolled")]
dept_names = [c.replace(" Enrolled","") for c in dept_cols]

# --- Sidebar: equipo y filtros ---
with st.sidebar:
    st.subheader("Equipo")
    st.write("- [Tu nombre aquí]")
    st.write("- [Integrante 2]")
    st.write("- [Integrante 3]")
    st.divider()
    st.subheader("Filtros")

years = sorted(df[col_year].dropna().unique().tolist())
min_year, max_year = int(min(years)), int(max(years))
rango = st.sidebar.slider(
    "Rango de años",
    min_value=min_year, max_value=max_year,
    value=(min_year, max_year), step=1
)

terms = sorted(df[col_term].dropna().unique().tolist())
sel_terms = st.sidebar.multiselect("Term", options=terms, default=terms)

sel_depts = []
if dept_cols:
    sel_depts = st.sidebar.multiselect("Departamento", options=dept_names, default=dept_names)

# --- Filtro principal ---
mask = (df[col_year].between(rango[0], rango[1])) & (df[col_term].isin(sel_terms))
F = df.loc[mask].copy()

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
apps_tot = int(F[col_apps].sum()) if len(F) else 0
adm_tot  = int(F[col_adm].sum()) if len(F) else 0
enr_tot  = int(F[col_enrl].sum()) if len(F) else 0
ret_avg  = F[col_ret].mean() if len(F) else float("nan")
sat_avg  = F[col_sat].mean() if len(F) else float("nan")

c1.metric("Solicitudes", f"{apps_tot:,}")
c2.metric("Admitidos", f"{adm_tot:,}")
c3.metric("Matriculados", f"{enr_tot:,}")
c4.metric("Retención ⌀ / Satisfacción ⌀", f"{ret_avg:.1f}% / {sat_avg:.1f}%")

# --- Gráfica 1: Retención por año (línea) ---
serie_ret = F.groupby(col_year)[col_ret].mean().sort_index()
fig1, ax1 = plt.subplots(figsize=(8.5, 4.2))
ax1.plot(serie_ret.index.astype(str), serie_ret.values, marker="o", linestyle="-")
ax1.set_xlabel("Año"); ax1.set_ylabel("Retención (%)")
ax1.set_title("Retención promedio por año")
ax1.grid(True, alpha=0.3)
st.pyplot(fig1)

# --- Gráfica 2: Satisfacción por año (barras) ---
serie_sat = F.groupby(col_year)[col_sat].mean().sort_index()
fig2, ax2 = plt.subplots(figsize=(8.5, 4.2))
ax2.bar(serie_sat.index.astype(str), serie_sat.values)
ax2.set_xlabel("Año"); ax2.set_ylabel("Satisfacción (%)")
ax2.set_title("Satisfacción promedio por año")
ax2.grid(True, axis="y", alpha=0.3)
st.pyplot(fig2)

# --- Gráfica 3: Solicitudes por term (donut) ---
apps_by_term = F.groupby(col_term)[col_apps].sum().sort_values(ascending=False)
if len(apps_by_term) >= 2:
    fig3, ax3 = plt.subplots(figsize=(6.5, 4.0))
    ax3.pie(
        apps_by_term.values,
        labels=apps_by_term.index.astype(str),
        autopct="%1.0f%%",
        startangle=90,
        wedgeprops={"width": 0.6}
    )
    ax3.set_title("Solicitudes por term")
    st.pyplot(fig3)
elif len(apps_by_term) == 1:
    fig3, ax3 = plt.subplots(figsize=(6.5, 4.0))
    ax3.bar(apps_by_term.index.astype(str), apps_by_term.values)
    ax3.set_title("Solicitudes por term")
    ax3.grid(True, axis="y", alpha=0.3)
    st.pyplot(fig3)
else:
    st.info("Sin datos para el gráfico por term en el rango seleccionado.")

# --- Matriculados por departamento (opcional) ---
if dept_cols and sel_depts:
    long = df.melt(id_vars=[col_year, col_term], value_vars=dept_cols,
                   var_name="Dept", value_name="EnrolledDept")
    long["Dept"] = long["Dept"].str.replace(" Enrolled","", regex=False)
    long = long[long["Dept"].isin(sel_depts)]
    long = long[long[col_year].between(rango[0], rango[1]) & long[col_term].isin(sel_terms)]
    dist_dept = long.groupby("Dept")["EnrolledDept"].sum().sort_values(ascending=False)

    fig4, ax4 = plt.subplots(figsize=(6.5, 4.0))
    ax4.barh(dist_dept.index.astype(str), dist_dept.values)
    ax4.set_xlabel("Matriculados"); ax4.set_title("Matrícula acumulada por departamento")
    ax4.grid(True, axis="x", alpha=0.3)
    st.pyplot(fig4)

# --- Datos ---
tab1, tab2 = st.tabs(["Datos filtrados", "Datos completos"])
with tab1:
    st.dataframe(F.reset_index(drop=True), use_container_width=True)
with tab2:
    st.dataframe(df_raw, use_container_width=True)

st.caption("Ajusta los filtros para actualizar KPIs y gráficos. Incluye ≥ 3 visualizaciones (línea, barras, donut).")
