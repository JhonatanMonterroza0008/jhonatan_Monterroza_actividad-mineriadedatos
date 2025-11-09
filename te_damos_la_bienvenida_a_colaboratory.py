import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Admissions & Retention Dashboard", layout="wide")

# ---------------- UI theme (Atomic Heart inspired) ----------------
PRIMARY = st.session_state.get("primary_color", "#D32F2F")   # rojo
DARK_BG = "#0f0f0f"
CARD_BG = "#171717"
TEXT = "#EDEDED"

st.markdown(f"""
    <style>
        .stApp {{
            background: radial-gradient(circle at 20% 10%, #0c0c0c, {DARK_BG});
            color:{TEXT};
        }}
        .block-container {{ padding-top: 1.2rem; }}
        .ah-card {{
            background:{CARD_BG};
            padding:1rem 1.2rem;
            border:1px solid #2a2a2a;
            border-radius:14px;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.03) inset;
        }}
        .ah-title {{
            font-weight:800;
            letter-spacing:0.5px;
            color:{TEXT};
        }}
        .ah-accent {{ color:{PRIMARY}; }}
        .metric-small > div > div {{
            background:{CARD_BG};
            border:1px solid #2a2a2a;
            border-radius:12px;
        }}
        div[data-testid="stMetricDelta"] svg {{ display:none; }}
        .stTabs [data-baseweb="tab-list"] button {{ background:{CARD_BG}; border-radius:12px; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<h2 class="ah-title">Dashboard — Admisiones, Retención y Satisfacción <span class="ah-accent">2015–2024</span></h2>', unsafe_allow_html=True)

# ---------------- Carga de datos ----------------
def cargar_datos():
    try:
        return pd.read_csv("university_student_data.csv")
    except Exception:
        return None

df = cargar_datos()

archivo = st.sidebar.file_uploader("Cargar university_student_data.csv", type=["csv"])
if df is None and archivo is not None:
    df = pd.read_csv(archivo)

# Si no hay datos, mostrar instrucción breve
if df is None:
    st.info("Sube **university_student_data.csv** para continuar.")
    st.stop()

# ---------------- Ajustes y columnas esperadas ----------------
esperadas = [
    "Year","Term","Applications","Admitted","Enrolled",
    "Retention Rate (%)","Student Satisfaction (%)",
    "Engineering Enrolled","Business Enrolled","Arts Enrolled","Science Enrolled"
]
faltantes = [c for c in esperadas if c not in df.columns]
if faltantes:
    st.error(f"Faltan columnas esperadas: {faltantes}")
    st.stop()

df = df.copy()
df["Year"] = df["Year"].astype(int)
df["Term"] = df["Term"].astype(str)

# Long format por departamento
dept_cols = ["Engineering Enrolled","Business Enrolled","Arts Enrolled","Science Enrolled"]
depts = ["Engineering","Business","Arts","Science"]
df_long = df.melt(id_vars=["Year","Term","Applications","Admitted","Enrolled","Retention Rate (%)","Student Satisfaction (%)"],
                  value_vars=dept_cols, var_name="Department", value_name="Dept Enrolled")
df_long["Department"] = df_long["Department"].str.replace(" Enrolled","", regex=False)

# ---------------- Controles ----------------
with st.sidebar:
    st.subheader("Filtros")
    years = sorted(df["Year"].unique().tolist())
    yr_min, yr_max = min(years), max(years)
    años_sel = st.slider("Años", min_value=int(yr_min), max_value=int(yr_max), value=(int(yr_min), int(yr_max)))
    term_sel = st.multiselect("Term", options=sorted(df["Term"].unique()), default=sorted(df["Term"].unique()))
    dept_sel = st.multiselect("Departamento", options=depts, default=depts)

    st.subheader("Gráficos")
    modo = st.radio("Tendencia de retención", ["Acumulado hasta el año", "Solo el año seleccionado"], index=0)
    año_corte = st.slider("Año de referencia", min_value=int(yr_min), max_value=int(yr_max), value=int(yr_max))
    show_grid = st.checkbox("Cuadrícula", value=True)
    color_linea = st.color_picker("Color línea", value="#D32F2F")
    color_barras = st.color_picker("Color barras", value="#C62828")
    color_pie = st.color_picker("Color donut", value="#B71C1C")

# Aplicar filtros
mask_rango = (df["Year"] >= años_sel[0]) & (df["Year"] <= años_sel[1]) & (df["Term"].isin(term_sel))
df_f = df.loc[mask_rango].copy()
df_long_f = df_long.loc[(df_long["Year"].between(años_sel[0], años_sel[1])) & (df_long["Term"].isin(term_sel)) & (df_long["Department"].isin(dept_sel))].copy()

# ---------------- KPIs ----------------
def safe_mean(s):
    return float(s.mean()) if len(s) else 0.0

tot_app = int(df_f["Applications"].sum())
tot_adm = int(df_f["Admitted"].sum())
tot_enr = int(df_f["Enrolled"].sum())
adm_rate = (tot_adm / tot_app * 100) if tot_app else 0.0
ret_mean = safe_mean(df_f["Retention Rate (%)"])
sat_mean = safe_mean(df_f["Student Satisfaction (%)"])

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Aplicaciones", f"{tot_app:,}")
with c2:
    st.metric("Admitidos", f"{tot_adm:,}")
with c3:
    st.metric("Matrícula (Enrolled)", f"{tot_enr:,}")
with c4:
    st.metric("Tasa de admisión", f"{adm_rate:.1f}%")
with c5:
    st.metric("Retención promedio", f"{ret_mean:.1f}%")

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs(["Tendencia de Retención", "Satisfacción por Año", "Comparativas"])

# ---- Tab 1: línea de retención ----
with tab1:
    g = df_f.groupby("Year", as_index=False)["Retention Rate (%)"].mean().sort_values("Year")
    if modo == "Acumulado hasta el año":
        g_plot = g[g["Year"] <= año_corte]
        titulo = f"Retención promedio (acumulado hasta {año_corte})"
    else:
        g_plot = g[g["Year"] == año_corte]
        titulo = f"Retención promedio en {año_corte}"

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(g_plot["Year"], g_plot["Retention Rate (%)"], marker="o", linestyle="-", label="Retención", color=color_linea)
    if modo == "Acumulado hasta el año" and len(g_plot) > 1:
        ax.fill_between(g_plot["Year"], g_plot["Retention Rate (%)"], alpha=0.15, step=None, color=color_linea)
    ax.set_title(titulo)
    ax.set_xlabel("Año")
    ax.set_ylabel("Retención (%)")
    ax.grid(show_grid)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

# ---- Tab 2: barras de satisfacción ----
with tab2:
    g2 = df_f.groupby("Year", as_index=False)["Student Satisfaction (%)"].mean().sort_values("Year")
    fig2, ax2 = plt.subplots(figsize=(10,4.5))
    ax2.bar(g2["Year"].astype(str), g2["Student Satisfaction (%)"], color=color_barras, edgecolor="#222222")
    ax2.set_title("Satisfacción estudiantil por año")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Satisfacción (%)")
    ax2.grid(show_grid, axis="y")
    plt.tight_layout()
    st.pyplot(fig2, use_container_width=True)

# ---- Tab 3: comparativas (donut Term y barras por Departamento) ----
with tab3:
    colA, colB = st.columns([1,1])

    with colA:
        # Donut Spring vs Fall por matrícula
        g3 = df_f.groupby("Term", as_index=False)["Enrolled"].sum()
        if len(g3):
            fig3, ax3 = plt.subplots(figsize=(5.6,5.6))
            wedges, _ = ax3.pie(g3["Enrolled"], labels=g3["Term"], startangle=90,
                                 wedgeprops=dict(width=0.40), autopct="%1.0f%%", colors=[color_pie, "#444444"])
            ax3.set_title("Distribución de matrícula por Term")
            plt.tight_layout()
            st.pyplot(fig3, use_container_width=False)
        else:
            st.info("Sin datos para el donut con los filtros actuales.")

    with colB:
        # Barras: distribución por departamento (suma de matriculados)
        g4 = df_long_f.groupby("Department", as_index=False)["Dept Enrolled"].sum()
        if len(g4):
            fig4, ax4 = plt.subplots(figsize=(7,5))
            ax4.bar(g4["Department"], g4["Dept Enrolled"], color=color_barras, edgecolor="#222222")
            ax4.set_title("Matrícula total por departamento")
            ax4.set_xlabel("Departamento")
            ax4.set_ylabel("Estudiantes")
            ax4.grid(show_grid, axis="y")
            plt.tight_layout()
            st.pyplot(fig4, use_container_width=True)
        else:
            st.info("Sin datos para departamentos con los filtros actuales.")

# ---------------- Datos ----------------
with st.expander("Ver datos filtrados"):
    st.dataframe(df_f.reset_index(drop=True), use_container_width=True)

st.caption("Autor: Jhonatan Monterroza — Data Mining / Universidad de la Costa")
