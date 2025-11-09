# app.py — Visualización (estilo profesor, limpio y sin textos “IA”)

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ---------------- Configuración ----------------
st.set_page_config(page_title="Indicadores", layout="centered")
st.title("Indicadores")

# ---------------- Carga de datos ----------------
def cargar():
    try:
        return pd.read_csv("university_student_data.csv")
    except Exception:
        up = st.file_uploader("Cargar CSV", type=["csv"])
        if up is not None:
            try:
                return pd.read_csv(up)
            except Exception:
                st.error("No se pudo leer el CSV.")
    return None

df_raw = cargar()
if df_raw is None or df_raw.empty:
    st.stop()

# ---------------- Utilidades ----------------
def numify(s):
    if s.dtype == object:
        return pd.to_numeric(s.astype(str).str.replace("%", "").str.replace(",", "."), errors="coerce")
    return pd.to_numeric(s, errors="coerce")

def pick(cols, *needles):
    for c in cols:
        k = c.lower()
        if any(n in k for n in needles):
            return c
    return None

cols = list(df_raw.columns)

col_year = pick(cols, "year", "anio", "ano")
col_term = pick(cols, "term", "semestre", "period")
col_apps = pick(cols, "applications", "applicant", "solicitud", "aplicac")
col_enrl = pick(cols, "enroll", "matric", "inscrit", "registr")  # opcional
col_ret  = pick(cols, "retention", "retencion")
col_sat  = pick(cols, "satisf")

req = [col_year, col_apps, col_ret, col_sat]
if any(x is None for x in req):
    st.error("Revisa encabezados: year, applications, retention, satisfaction.")
    st.write("Detectadas:", {
        "year": col_year, "term": col_term, "applications": col_apps,
        "enrollments": col_enrl, "retention": col_ret, "satisfaction": col_sat
    })
    st.stop()

U = pd.DataFrame({
    "year": numify(df_raw[col_year]),
    "applications": numify(df_raw[col_apps]),
    "retention": numify(df_raw[col_ret]),
    "satisfaction": numify(df_raw[col_sat]),
})
if col_term: U["term"] = df_raw[col_term].astype(str)
if col_enrl: U["enrollments"] = numify(df_raw[col_enrl])

# Escalar % si vienen en 0–1
if U["retention"].max() <= 1: U["retention"] = U["retention"] * 100
if U["satisfaction"].max() <= 1: U["satisfaction"] = U["satisfaction"] * 100

# ---------------- Controles (estilo profe) ----------------
col1, col2 = st.columns([2, 1])

with col1:
    modo = st.radio(
        "Modo",
        ["Acumulado hasta el año", "Solo el año seleccionado"],
        index=0
    )

with col2:
    grid = st.checkbox("Cuadrícula", value=True)
    color1 = st.color_picker("Color principal", value="#4169E1")

years = sorted([int(y) for y in U["year"].dropna().unique()])
if not years: st.stop()

idx = st.slider("Selecciona el año", min_value=1, max_value=len(years), value=len(years), step=1, format="%d")
anio_sel = years[idx - 1]

# ---------------- Subconjuntos ----------------
if modo == "Acumulado hasta el año":
    F = U[U["year"] <= anio_sel].copy()
    titulo = f"Acumulado hasta {anio_sel}"
else:
    F = U[U["year"] == anio_sel].copy()
    titulo = f"Año {anio_sel}"

# ---------------- Métricas ----------------
cA, cB, cC = st.columns(3)
apps_tot = int(F["applications"].sum())
ret_avg  = F["retention"].mean()
sat_avg  = F["satisfaction"].mean()
cA.metric("Solicitudes", f"{apps_tot:,}")
cB.metric("Retención ⌀", f"{ret_avg:.1f}%")
cC.metric("Satisfacción ⌀", f"{sat_avg:.1f}%")

# ---------------- Gráfica 1: Retención por año (línea) ----------------
serie_ret = U.groupby("year")["retention"].mean().sort_index()
if modo == "Acumulado hasta el año":
    serie_ret = serie_ret[serie_ret.index <= anio_sel]
else:
    serie_ret = serie_ret[serie_ret.index == anio_sel]

fig1, ax1 = plt.subplots(figsize=(10, 4.5))
ax1.plot(serie_ret.index.astype(str), serie_ret.values, marker="o", linestyle="-", color=color1)
ax1.set_xlabel("Año"); ax1.set_ylabel("Retención (%)"); ax1.set_title(f"Retención — {titulo}")
if grid: ax1.grid(True, alpha=0.3)
fig1.tight_layout()
st.pyplot(fig1)

# ---------------- Gráfica 2: Satisfacción por año (barras) ----------------
serie_sat = U.groupby("year")["satisfaction"].mean().sort_index()
if modo == "Acumulado hasta el año":
    serie_sat = serie_sat[serie_sat.index <= anio_sel]
else:
    serie_sat = serie_sat[serie_sat.index == anio_sel]

fig2, ax2 = plt.subplots(figsize=(10, 4.5))
ax2.bar(serie_sat.index.astype(str), serie_sat.values, color="#2DBE7E")
ax2.set_xlabel("Año"); ax2.set_ylabel("Satisfacción (%)"); ax2.set_title(f"Satisfacción — {titulo}")
if grid: ax2.grid(True, axis="y", alpha=0.3)
fig2.tight_layout()
st.pyplot(fig2)

# ---------------- Gráfica 3: Distribución por term (pastel) ----------------
if "term" in U.columns:
    if modo == "Acumulado hasta el año":
        G = U[U["year"] <= anio_sel]
    else:
        G = U[U["year"] == anio_sel]
    if len(G) > 0:
        dist = G.groupby("term")["applications"].sum().sort_values(ascending=False)
        if dist.sum() > 0:
            fig3, ax3 = plt.subplots(figsize=(8, 4.8))
            wedges, _ = ax3.pie(dist.values, labels=dist.index.astype(str), autopct="%1.0f%%", startangle=90, wedgeprops={"width": 0.6})
            ax3.set_title("Aplicaciones por term")
            st.pyplot(fig3)

# ---------------- Tabs de datos ----------------
tab1, tab2 = st.tabs(["Datos mostrados", "Datos completos"])
with tab1:
    st.dataframe(F.reset_index(drop=True), use_container_width=True)
with tab2:
    st.dataframe(U, use_container_width=True)
