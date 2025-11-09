import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Analítica de Admisiones • Retención • Satisfacción", layout="centered")
st.title("Analítica de Admisiones, Retención y Satisfacción Estudiantil")

@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    df["Year"] = df["Year"].astype(int)
    df["Term"] = df["Term"].astype(str)
    return df

DATA_PATH = "university_student_data.csv"
df = load_data(DATA_PATH)

# --- Controles ---
years = sorted(df["Year"].unique())
colA, colB, colC = st.columns([2, 1.2, 1.2])
with colA:
    year_sel = st.slider("Selecciona el año", min_value=int(min(years)), max_value=int(max(years)),
                         value=int(max(years)), step=1, format="%d")
with colB:
    term_sel = st.radio("Term", options=["Todos", "Spring", "Fall"], index=0)
with colC:
    show_grid = st.checkbox("Mostrar cuadrícula", value=True)

col1, col2 = st.columns([2, 1])
with col1:
    modo = st.radio(
        "Modo de visualización",
        ["Acumulado hasta el año", "Solo el año seleccionado"],
        index=0
    )
with col2:
    color = st.color_picker("Color de la línea", value="#4169E1")

dept_options = [
    "Todos (Enrolled)",
    "Engineering Enrolled",
    "Business Enrolled",
    "Arts Enrolled",
    "Science Enrolled",
]
dept_sel = st.selectbox("Departamento", options=dept_options, index=0)

# --- Filtro de datos ---
df_f = df.copy()
if term_sel != "Todos":
    df_f = df_f[df_f["Term"] == term_sel]

df_up_to = df_f[df_f["Year"] <= year_sel]
y_col = "Enrolled" if dept_sel == "Todos (Enrolled)" else dept_sel

# --- KPIs (año seleccionado) ---
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

# --- Gráfico 1: Tendencia (línea) ---
df_line = df_up_to.groupby("Year", as_index=False)[y_col].sum().sort_values("Year")
if modo == "Acumulado hasta el año":
    df_plot = df_line.copy()
    titulo = f"Tendencia de {y_col} (acumulado hasta {year_sel})"
else:
    df_plot = df_line[df_line["Year"] == year_sel].copy()
    titulo = f"{y_col} en {year_sel}"

fig1, ax1 = plt.subplots(figsize=(9.5, 4.5))
ax1.plot(df_plot["Year"], df_plot[y_col], marker="o", linestyle="-", color=color)
if modo == "Acumulado hasta el año" and len(df_plot) > 1:
    ax1.fill_between(df_plot["Year"], df_plot[y_col], step=None, alpha=0.15, color=color)
ax1.set_xlabel("Año")
ax1.set_ylabel(y_col)
ax1.set_title(titulo)
ax1.grid(show_grid)
st.pyplot(fig1)

# --- Gráfico 2: Barras (Satisfacción por año) ---
df_sat = df_f.groupby("Year", as_index=False)["Student Satisfaction (%)"].mean()
fig2, ax2 = plt.subplots(figsize=(9.5, 4.5))
ax2.bar(df_sat["Year"], df_sat["Student Satisfaction (%)"])
ax2.set_xlabel("Año")
ax2.set_ylabel("Satisfacción (%)")
ax2.set_title("Satisfacción promedio por año (según filtros)")
ax2.grid(show_grid, axis="y")
st.pyplot(fig2)

# --- Gráfico 3: Donut (Spring vs Fall en el año seleccionado) ---
df_year = df[df["Year"] == year_sel]
values = df_year.groupby("Term")[y_col if y_col != "Enrolled" else "Enrolled"].sum()
labels = values.index.tolist()
sizes = values.values.tolist()

fig3, ax3 = plt.subplots(figsize=(5.5, 5.5))
wedges, _ = ax3.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
centre_circle = plt.Circle((0, 0), 0.70, fc="white")
fig3.gca().add_artist(centre_circle)
ax3.set_title(f"Distribución por Term en {year_sel} — {y_col}")
st.pyplot(fig3)

# --- Tablas ---
tab1, tab2 = st.tabs(["📈 Datos mostrados", "📚 Datos completos"])
with tab1:
    st.dataframe(df_plot.reset_index(drop=True))
with tab2:
    st.dataframe(df)

st.caption("Ajusta año, term y departamento para actualizar KPIs y gráficos. Datos: university_student_data.csv.")
