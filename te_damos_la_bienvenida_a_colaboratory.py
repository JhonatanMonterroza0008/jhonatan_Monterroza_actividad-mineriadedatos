# app.py — Dashboard de indicadores (ajustado para reconocer 'enrolled')
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ---------------- Config ----------------
st.set_page_config(page_title="Dashboard de indicadores", layout="wide")

# ---------------- Utilidades ----------------
def cargar_datos():
    try:
        return pd.read_csv("university_student_data.csv")
    except Exception:
        up = st.sidebar.file_uploader("Cargar CSV", type=["csv"])
        if up is not None:
            try:
                return pd.read_csv(up)
            except Exception:
                st.error("No se pudo leer el CSV.")
    return None

def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    cols = (
        df.columns.str.strip().str.lower()
        .str.replace("á", "a").str.replace("é", "e")
        .str.replace("í", "i").str.replace("ó", "o")
        .str.replace("ú", "u").str.replace("ñ", "n")
    )
    out = df.copy()
    out.columns = cols
    return out

def mapear_columnas(df: pd.DataFrame) -> dict:
    cand = {
        "year": ["year", "anio", "ano"],
        "department": ["department", "departamento", "dept"],
        "term": ["term", "semestre", "period", "periodo"],
        "applications": ["applications", "applicants", "solicitudes", "aplicaciones"],
        # <-- ampliado: incluye 'enrolled' y variantes comunes
        "enrollments": [
            "enrollments", "enrolled", "enrollment",
            "students_enrolled", "students enrolled",
            "total_enrolled", "total enrolled",
            "matriculas", "matriculados", "inscritos", "registrados"
        ],
        "retention_rate": ["retention_rate", "retention", "tasa_retencion", "retencion"],
        "satisfaction": ["satisfaction", "satisfaccion", "satisfaction_score"],
    }
    mapping = {}
    cols = list(df.columns)
    for std, opciones in cand.items():
        for op in opciones:
            if op in cols:
                mapping[std] = op
                break
            m = [c for c in cols if op in c]  # substring
            if m:
                mapping[std] = m[0]
                break
    return mapping

def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def as_percent(x: float) -> float:
    if pd.isna(x):
        return float("nan")
    return x * 100 if 0 <= x <= 1 else x

# ---------------- Sidebar ----------------
st.sidebar.header("Opciones")
plt.style.use("default")
color_1 = st.sidebar.color_picker("Color primario", value="#4169E1")
color_2 = st.sidebar.color_picker("Color secundario", value="#2DBE7E")
show_grid = st.sidebar.checkbox("Cuadrícula", value=True)

# ---------------- Carga ----------------
df_raw = cargar_datos()
st.title("Dashboard de indicadores")

if df_raw is None or df_raw.empty:
    st.info("Coloca 'university_student_data.csv' en la raíz o súbelo desde la barra lateral.")
    st.stop()

# ---------------- Preparación ----------------
df = normalizar_columnas(df_raw)
mapping = mapear_columnas(df)

minimas = ["year", "applications", "enrollments"]
faltan = [c for c in minimas if c not in mapping]
if faltan:
    st.error("Faltan columnas mínimas: " + ", ".join(faltan))
    st.write("Detectadas:", mapping)
    st.stop()

U = pd.DataFrame()
for std, real in mapping.items():
    U[std] = df[real]

if "year" in U: U["year"] = to_num(U["year"])
for c in ["applications", "enrollments", "satisfaction", "retention_rate"]:
    if c in U: U[c] = to_num(U[c])

if {"applications", "enrollments"}.issubset(U.columns):
    U["conversion_rate"] = U["enrollments"] / U["applications"].replace(0, pd.NA)

# ---------------- Filtros ----------------
with st.expander("Filtros", expanded=True):
    c1, c2, c3 = st.columns(3)
    years = sorted(U["year"].dropna().unique()) if "year" in U else []
    sel_years = c1.multiselect("Año", years, default=years) if years else []
    if "department" in U:
        depts = sorted(U["department"].dropna().astype(str).unique())
        sel_depts = c2.multiselect("Departamento", depts, default=depts)
    else:
        sel_depts = []
    if "term" in U:
        terms = sorted(U["term"].dropna().astype(str).unique())
        sel_terms = c3.multiselect("Term", terms, default=terms)
    else:
        sel_terms = []

F = U.copy()
if sel_years: F = F[F["year"].isin(sel_years)]
if sel_depts and "department" in F: F = F[F["department"].astype(str).isin(sel_depts)]
if sel_terms and "term" in F: F = F[F["term"].astype(str).isin(sel_terms)]

# ---------------- KPIs ----------------
k1, k2, k3, k4 = st.columns(4)
apps = F["applications"].sum() if "applications" in F else 0
enrs = F["enrollments"].sum() if "enrollments" in F else 0
conv = (enrs / apps * 100) if apps and apps > 0 else float("nan")
ret = as_percent(F["retention_rate"].mean()) if "retention_rate" in F else float("nan")
sat = as_percent(F["satisfaction"].mean()) if "satisfaction" in F else float("nan")

k1.metric("Solicitudes", f"{int(apps):,}" if pd.notna(apps) else "0")
k2.metric("Matrículas", f"{int(enrs):,}" if pd.notna(enrs) else "0")
k3.metric("Conversión", f"{conv:.1f}%") if pd.notna(conv) else k3.metric("Conversión", "N/D")
k4.metric("Retención / Satisfacción", f"{ret:.1f}% / {sat:.1f}%")

st.divider()

# ---------------- Gráficas ----------------
g1, g2 = st.columns([2, 1])

with g1:
    if {"retention_rate", "year"}.issubset(F.columns):
        serie = F.groupby("year")["retention_rate"].mean().sort_index()
        y = serie * 100 if serie.max() <= 1 else serie
        fig1, ax1 = plt.subplots(figsize=(8, 4.2))
        ax1.plot(serie.index, y.values, marker="o", lw=2, color=color_1)
        ax1.set_xlabel("Año"); ax1.set_ylabel("Retención (%)"); ax1.set_title("Retención por año")
        if show_grid: ax1.grid(True, alpha=0.3)
        fig1.tight_layout(); st.pyplot(fig1, use_container_width=True)
    else:
        st.info("Se requiere 'year' y 'retention_rate'.")

with g2:
    if {"satisfaction", "year"}.issubset(F.columns):
        s = F.groupby("year")["satisfaction"].mean().sort_index()
        y = s * 100 if s.max() <= 1 else s
        fig2, ax2 = plt.subplots(figsize=(5.2, 4.2))
        ax2.bar(s.index.astype(str), y.values, color=color_2)
        ax2.set_xlabel("Año"); ax2.set_ylabel("Satisfacción (%)"); ax2.set_title("Satisfacción por año")
        if show_grid: ax2.grid(True, axis="y", alpha=0.3)
        fig2.tight_layout(); st.pyplot(fig2, use_container_width=True)
    else:
        st.info("Se requiere 'year' y 'satisfaction'.")

st.markdown("**Matrículas por categoría**")
cat_opciones = []
if "department" in F: cat_opciones.append("department")
if "term" in F: cat_opciones.append("term")

if "enrollments" in F and cat_opciones:
    cat = st.selectbox("Categoría", cat_opciones, format_func=lambda x: "Departamento" if x=="department" else "Term")
    dist = F.groupby(cat)["enrollments"].sum().sort_values(ascending=False)
    fig3, ax3 = plt.subplots(figsize=(8, 4.2))
    ax3.bar(dist.index.astype(str), dist.values, color=color_1)
    ax3.set_xlabel("Categoría"); ax3.set_ylabel("Matrículas"); ax3.set_title("Distribución de matrículas")
    if show_grid: ax3.grid(True, axis="y", alpha=0.3)
    fig3.tight_layout(); st.pyplot(fig3, use_container_width=True)
else:
    st.info("Se requiere 'enrollments' y al menos una categoría ('department' o 'term').")

st.divider()
t1, t2 = st.tabs(["Datos filtrados", "Datos completos"])
with t1: st.dataframe(F, use_container_width=True)
with t2: st.dataframe(U, use_container_width=True)
