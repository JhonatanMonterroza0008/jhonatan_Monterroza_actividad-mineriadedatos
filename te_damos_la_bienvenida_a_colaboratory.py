import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuración base (igual estructura que el ejemplo del profesor) ---
st.set_page_config(page_title="Admisiones, Retención y Satisfacción — Dashboard", layout="wide")
st.title("Analítica de Admisiones, Retención y Satisfacción Estudiantil")

# --- Carga de datos ---
@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    # Columnas esperadas:
    # ['Year','Term','Applications','Admitted','Enrolled','Retention Rate (%)',
    #  'Student Satisfaction (%)','Engineering Enrolled','Business Enrolled',
    #  'Arts Enrolled','Science Enrolled']
    # Limpiezas/normalizaciones mínimas
    df['Term'] = df['Term'].astype(str)
    df['Year'] = df['Year'].astype(int)
    return df

# Ruta del CSV (debe estar en el mismo repo que app.py)
DATA_PATH = "university_student_data.csv"
df = load_data(DATA_PATH)

# --- Panel lateral: nombres de integrantes (requisito del enunciado) ---
TEAM_MEMBERS = [
    "Jhonatan Monterroza Carreño",  # <— edita si aplica
    # "Integrante 2",
    # "Integrante 3",
    # "Integrante 4",
]
with st.sidebar:
    st.subheader("Equipo")
    for m in TEAM_MEMBERS:
        st.write(f"- {m}")
    st.caption("Los nombres también deben aparecer en el README y en el despliegue.")

# --- Controles interactivos (mismo tipo de widgets del ejemplo) ---
colA, colB, colC, colD = st.columns([1.2, 1.2, 1, 1])
with colA:
    years = sorted(df['Year'].unique())
    year_sel = st.slider("Selecciona el año", min_value=int(min(years)), max_value=int(max(years)),
                         value=int(max(years)), step=1, format="%d")
with colB:
    term_sel = st.radio("Term", options=["Todos", "Spring", "Fall"], index=0,
                        help="Filtra por periodo académico.")
with colC:
    dept_options = ["Todos (Enrolled)", "Engineering Enrolled", "Business Enrolled", "Arts Enrolled", "Science Enrolled"]
    dept_sel = st.selectbox("Departamento", options=dept_options, index=0,
                            help="Para series por departamento usa la columna correspondiente.")
with colD:
    color = st.color_picker("Color de línea", value="#4169E1")

col1, col2 = st.columns([2, 1])
with col1:
    modo = st.radio(
        "Modo de visualización de tendencia",
        ["Acumulado hasta el año", "Solo el año seleccionado"],
        index=0,
        help="Elige si quieres ver la serie acumulada hasta el año o únicamente el año seleccionado."
    )
with col2:
    show_grid = st.checkbox("Mostrar cuadrícula", value=True)

# --- Filtrado base ---
df_f = df.copy()
if term_sel != "Todos":
    df_f = df_f[df_f['Term'] == term_sel]
df_f = df_f[df_f['Year'] <= year_sel]

# --- Serie objetivo según departamento ---
if dept_sel == "Todos (Enrolled)":
    serie_y = "Enrolled"
else:
    serie_y = dept_sel

# --- KPIs (dinámicos según filtros) ---
df_kpi = df.copy()
if term_sel != "Todos":
    df_kpi = df_kpi[df_kpi['Term'] == term_sel]
df_kpi = df_kpi[df_kpi['Year'] == year_sel]

apps = int(df_kpi['Applications'].sum()) if not df_kpi.empty else 0
adm = int(df_kpi['Admitted'].sum()) if not df_kpi.empty else 0
enr = int(df_kpi['Enrolled'].sum()) if not df_kpi.empty else 0
ret = float(df_kpi['Retention Rate (%)'].mean()) if not df_kpi.empty else 0.0
sat = float(df_kpi['Student Satisfaction (%)'].mean()) if not df_kpi.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Applications", f"{apps:,}")
k2.metric("Admitted", f"{adm:,}")
k3.metric("Enrolled", f"{enr:,}")
k4.metric("Retention Rate", f"{ret:.1f}%")
k5.metric("Student Satisfaction", f"{sat:.1f}%")

# --- Gráfico 1: Tendencia (línea) ---
df_line = df_f.groupby('Year', as_index=False).agg({
    serie_y: 'sum',
    'Retention Rate (%)': 'mean',
    'Student Satisfaction (%)': 'mean'
}).sort_values('Year')

if modo == "Acumulado hasta el año":
    df_plot = df_line.copy()
    titulo = f"Tendencia de {serie_y} (acumulado hasta {year_sel})"
else:
    df_plot = df_line[df_line['Year'] == year_sel].copy()
    titulo = f"{serie_y} en {year_sel}"

fig1, ax1 = plt.subplots(figsize=(10, 4.5))
ax1.plot(df_plot['Year'], df_plot[serie_y], marker='o', linestyle='-', color=color)
if modo == "Acumulado hasta el año" and len(df_plot) > 1:
    ax1.fill_between(df_plot['Year'], df_plot[serie_y], step=None, alpha=0.15)
ax1.set_xlabel("Año")
ax1.set_ylabel(serie_y)
ax1.set_title(titulo)
ax1.grid(show_grid)
st.pyplot(fig1)

# --- Gráfico 2: Barras (Satisfacción por año) ---
df_sat = df_f.groupby('Year', as_index=False)['Student Satisfaction (%)'].mean()
fig2, ax2 = plt.subplots(figsize=(10, 4.5))
ax2.bar(df_sat['Year'], df_sat['Student Satisfaction (%)'])
ax2.set_xlabel("Año")
ax2.set_ylabel("Satisfacción (%)")
ax2.set_title("Satisfacción promedio por año (según filtros)")
ax2.grid(show_grid, axis='y')
st.pyplot(fig2)

# --- Gráfico 3: Donut Spring vs Fall (comparación de términos) ---
df_term = df.copy()
df_term = df_term[df_term['Year'] == year_sel]
if dept_sel == "Todos (Enrolled)":
    values = df_term.groupby('Term')['Enrolled'].sum()
else:
    values = df_term.groupby('Term')[dept_sel].sum()
labels = values.index.tolist()
sizes = values.values.tolist()

fig3, ax3 = plt.subplots(figsize=(6, 6))
wedges, texts = ax3.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
# Donut: círculo en el centro
centre_circle = plt.Circle((0,0),0.70,fc='white')
fig3.gca().add_artist(centre_circle)
ax3.set_title(f"Distribución por Term en {year_sel} — {serie_y}")
st.pyplot(fig3)

# --- Tablas ---
tab1, tab2, tab3 = st.tabs(["📈 Datos mostrados", "📚 Datos completos", "🧪 Diccionario de columnas (EDA)"])
with tab1:
    st.dataframe(df_plot.reset_index(drop=True), use_container_width=True)
with tab2:
    st.dataframe(df, use_container_width=True)
with tab3:
    st.markdown("""
**Diccionario**  
- **Year**: año académico del registro.  
- **Term**: periodo académico (Spring/Fall).  
- **Applications**: número de aplicaciones recibidas por la universidad.  
- **Admitted**: número de admitidos.  
- **Enrolled**: número de estudiantes matriculados.  
- **Retention Rate (%)**: porcentaje de retención estudiantil.  
- **Student Satisfaction (%)**: satisfacción estudiantil promedio.  
- **Engineering/Business/Arts/Science Enrolled**: matrículas por departamento.
""")

st.caption("Usa los filtros para actualizar KPIs y visualizaciones. Para desplegar, carga este repo a GitHub y enlázalo con Streamlit Cloud.")
