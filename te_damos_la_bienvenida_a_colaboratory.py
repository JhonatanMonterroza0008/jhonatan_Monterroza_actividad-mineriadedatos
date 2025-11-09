import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Config base (mismo patrón del ejemplo del profesor) ---
st.set_page_config(page_title="Admisiones • Retención • Satisfacción", layout="wide")
st.title("Analítica de Admisiones, Retención y Satisfacción Estudiantil")

# Tema oscuro tipo "Atomic Heart" para Matplotlib
plt.rcParams.update({
    "figure.facecolor": "#0E0F12",
    "axes.facecolor": "#111417",
    "axes.edgecolor": "#E8E8E8",
    "axes.labelcolor": "#E8E8E8",
    "xtick.color": "#E8E8E8",
    "ytick.color": "#E8E8E8",
    "grid.color": "#2A2F38",
    "text.color": "#E8E8E8",
    "axes.titleweight": "bold",
    "axes.titlesize": 22,
    "axes.titlecolor": "#FF3B3B",
    "font.size": 12,
})

# Carga
@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    df["Term"] = df["Term"].astype(str)
    df["Year"] = df["Year"].astype(int)
    return df

DATA_PATH = "university_student_data.csv"
df = load_data(DATA_PATH)

# Sidebar: equipo (un solo integrante)
with st.sidebar:
    st.subheader("Equipo")
    st.write("- Jhonatan Monterroza Carreño")

# Controles (mismos widgets que el ejemplo)
colA, colB, colC, colD = st.columns([1.2, 1.2, 1.4, 1])
with colA:
    years = sorted(df["Year"].unique())
    year_sel = st.slider("Selecciona el año", min_value=int(min(years)), max_value=int(max(years)),
                         value=int(max(years)), step=1, format="%d")
with colB:
    term_sel = st.radio("Term", options=["Todos", "Spring", "Fall"], index=0)
with colC:
    dept_options = ["Todos (Enrolled)", "Engineering Enrolled", "Business Enrolled", "Arts Enrolled", "Science Enrolled"]
    dept_sel = st.selectbox("Departamento", options=dept_options, index=0)
with colD:
    color = st.color_picker("Color de línea", value="#FF3B3B")

col1, col2 = st.columns([2, 1])
with col1:
    modo = st.radio(
        "Modo de visualización de tendencia",
        ["Acumulado hasta el año", "Solo el año seleccionado"],
        index=0
    )
with col2:
    show_grid = st.checkbox("Mostrar cuadrícula", value=True)

# Filtro base
df_f = df.copy()
if term_sel != "Todos":
    df_f = df_f[df_f["Term"] == term_sel]
df_f = df_f[df_f["Year"] <= year_sel]

# Serie objetivo
serie_y = "Enrolled" if dept_sel == "Todos (Enrolled)" else dept_sel

# KPIs (año elegido y term si aplica)
df_kpi = df[(df["Year"] == year_sel) & ((df["Term"] == term_sel) if term_sel != "Todos" else True)]
apps = int(df_kpi["Applications"].sum()) if not df_kpi.empty else 0
adm  = int(df_kpi["Admitted"].sum()) if not df_kpi.empty else 0
enr  = int(df_kpi["Enrolled"].sum()) if not df_kpi.empty else 0
ret  = float(df_kpi["Retention Rate (%)"].mean()) if not df_kpi.empty else 0.0
sat  = float(df_kpi["Student Satisfaction (%)"].mean()) if not df_kpi.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Applications", f"{apps:,}")
k2.metric("Admitted", f"{adm:,}")
k3.metric("Enrolled", f"{enr:,}")
k4.metric("Retention Rate", f"{ret:.1f}%")
k5.metric("Student Satisfaction", f"{sat:.1f}%")

# --- Gráfico 1: Línea (tendencia) ---
df_line = df_f.groupby("Year", as_index=False).agg({
    serie_y: "sum",
    "Retention Rate (%)": "mean",
    "Student Satisfaction (%)": "mean"
}).sort_values("Year")

if modo == "Acumulado hasta el año":
    df_plot = df_line.copy()
    titulo = f"Tendencia de {serie_y} (acumulado hasta {year_sel})"
else:
    df_plot = df_line[df_line["Year"] == year_sel].copy()
    titulo = f"{serie_y} en {year_sel}"

fig1, ax1 = plt.subplots(figsize=(14, 6), dpi=100)
ax1.plot(df_plot["Year"], df_plot[serie_y], marker="o", linestyle="-", color=color, linewidth=3, markersize=8)
if modo == "Acumulado hasta el año" and len(df_plot) > 1:
    ax1.fill_between(df_plot["Year"], df_plot[serie_y], step=None, alpha=0.12, color=color)
ax1.set_xlabel("Year")
ax1.set_ylabel(serie_y)
ax1.set_title(titulo)
ax1.grid(show_grid, linestyle="--", linewidth=0.8)
for spine in ax1.spines.values():
    spine.set_color("#E8E8E8")
st.pyplot(fig1, use_container_width=True)

# --- Gráfico 2: Barras (Satisfacción por año) ---
df_sat = df_f.groupby("Year", as_index=False)["Student Satisfaction (%)"].mean()
fig2, ax2 = plt.subplots(figsize=(14, 5), dpi=100)
ax2.bar(df_sat["Year"], df_sat["Student Satisfaction (%)"], color="#D9DBDE", edgecolor="#FF3B3B", linewidth=1.2)
ax2.set_xlabel("Year")
ax2.set_ylabel("Satisfaction (%)")
ax2.set_title("Satisfacción promedio por año (según filtros)")
ax2.grid(show_grid, axis="y", linestyle="--", linewidth=0.8)
for spine in ax2.spines.values():
    spine.set_color("#E8E8E8")
st.pyplot(fig2, use_container_width=True)

# --- Gráfico 3: Donut (Spring vs Fall en el año seleccionado) ---
df_term = df[df["Year"] == year_sel]
values = df_term.groupby("Term")[serie_y if serie_y != "Enrolled" else "Enrolled"].sum()
labels = values.index.tolist()
sizes = values.values.tolist()

fig3, ax3 = plt.subplots(figsize=(8, 8), dpi=100)
colors = ["#FF3B3B", "#D9DBDE"]
wedges, _ = ax3.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors,
                    textprops={"color": "#E8E8E8"})
centre_circle = plt.Circle((0, 0), 0.68, fc="#0E0F12")
fig3.gca().add_artist(centre_circle)
ax3.set_title(f"Distribución por Term en {year_sel} — {serie_y}")
st.pyplot(fig3, use_container_width=True)

# --- Tablas ---
tab1, tab2, tab3 = st.tabs(["📈 Datos mostrados", "📚 Datos completos", "🧪 Diccionario de columnas (EDA)"])
with tab1:
    st.dataframe(df_plot.reset_index(drop=True), use_container_width=True)
with tab2:
    st.dataframe(df, use_container_width=True)
with tab3:
    st.markdown("""
**Diccionario**  
- **Year**: año académico.  
- **Term**: periodo (Spring/Fall).  
- **Applications**: aplicaciones.  
- **Admitted**: admitidos.  
- **Enrolled**: matriculados.  
- **Retention Rate (%)**: retención.  
- **Student Satisfaction (%)**: satisfacción.  
- **Engineering/Business/Arts/Science Enrolled**: matrícula por departamento.
""")

st.caption("Ajusta filtros para explorar. Repo con `app.py`, `requirements.txt` y `university_student_data.csv`.")
