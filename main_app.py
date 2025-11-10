import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Academic Indicators", layout="centered")
st.title("Academic Indicators: Admissions, Retention and Satisfaction")

#  Data load
@st.cache_data
def load_csv(default_paths=("university_student_data.csv",
                            "data/university_student_data.csv")):
    df = None
    for p in default_paths:
        try:
            df = pd.read_csv(p)
            break
        except Exception:
            continue
    return df

df = load_csv()

if df is None:
    st.warning("File 'university_student_data.csv' not found. Please upload it to continue.")
    f = st.file_uploader("Upload CSV (university_student_data.csv)", type=["csv"])
    if f is not None:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            st.stop()
    else:
        st.stop()

# - Basic cleanup / types 
df.columns = [c.strip() for c in df.columns]

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

# Controls  
col1, col2 = st.columns([2, 1])

with col1:
    mode = st.radio(
        "Visualization mode",
        ["Cumulative up to year", "Only selected year"],
        index=0,
        help="Show everything up to the selected year or only that specific year."
    )

with col2:
    show_grid = st.checkbox("Show grid", value=True)
    color = st.color_picker("Primary color", value="#D7263D")  

years_sorted = sorted([int(y) for y in df['Year'].dropna().unique()])
if not years_sorted:
    st.error("No valid values in 'Year'.")
    st.stop()

yr_min, yr_max = min(years_sorted), max(years_sorted)
year_sel = st.slider("Select year", min_value=yr_min, max_value=yr_max, value=yr_max, step=1, format="%d")

depts = sorted(df['Department'].dropna().unique()) if 'Department' in df.columns else []
dept_sel = st.multiselect("Filter by department (optional)", options=depts, default=[])


if mode == "Cumulative up to year":
    df_sub = df[df['Year'] <= year_sel].copy()
else:
    df_sub = df[df['Year'] == year_sel].copy()

if dept_sel:
    df_sub = df_sub[df_sub['Department'].isin(dept_sel)]

if df_sub.empty:
    st.info("No data matches the current filters.")
    st.stop()


def wavg(series, weights):
    w = np.nan_to_num(weights.values if hasattr(weights, "values") else np.array(weights), nan=0.0)
    x = np.nan_to_num(series.values if hasattr(series, "values") else np.array(series), nan=0.0)
    s = w.sum()
    if s <= 0:
        return float(np.mean(x)) if len(x) else np.nan
    return float(np.average(x, weights=w))


apps_total = df_sub['Applications'].sum() if 'Applications' in df_sub.columns else np.nan
enr_total = df_sub['Enrolled'].sum() if 'Enrolled' in df_sub.columns else np.nan
ret_w = wavg(df_sub['Retention Rate (%)'], df_sub['Enrolled']) if 'Retention Rate (%)' in df_sub.columns else np.nan
sat_w = wavg(df_sub['Student Satisfaction (%)'], df_sub['Enrolled']) if 'Student Satisfaction (%)' in df_sub.columns else np.nan

col_a, col_b, col_c = st.columns(3)
col_a.metric("Enrolled", f"{int(enr_total):,}" if pd.notna(enr_total) else "—")
col_b.metric("Weighted retention", f"{ret_w:.1f}%" if pd.notna(ret_w) else "—")
col_c.metric("Weighted satisfaction", f"{sat_w:.1f}%" if pd.notna(sat_w) else "—")

# 1) LINE: Weighted retention by year

grp_year = (df_sub.groupby('Year')
            .apply(lambda g: wavg(g['Retention Rate (%)'], g['Enrolled']))
            .rename("Retention_w")
            .sort_index())

fig1, ax1 = plt.subplots(figsize=(10, 5))
x_idx = np.arange(len(grp_year.index))
ax1.plot(x_idx, grp_year.values, marker="o", linestyle="-", color=color, linewidth=2)

ax1.set_xticks(x_idx)
ax1.set_xticklabels([str(int(y)) for y in grp_year.index])
ax1.set_xlabel("Year")
ax1.set_ylabel("Retention Rate (%)")
title1 = "Weighted retention by year"
title1 += f" · up to {year_sel}" if mode == "Cumulative up to year" else f" · year {year_sel}"
ax1.set_title(title1)
ax1.grid(show_grid)
fig1.tight_layout()
st.pyplot(fig1)


# 2) BAR: Weighted satisfaction by year

grp_sat = (df_sub.groupby('Year')
           .apply(lambda g: wavg(g['Student Satisfaction (%)'], g['Enrolled']))
           .rename("Satisfaction_w")
           .sort_index())

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.bar([str(int(y)) for y in grp_sat.index], grp_sat.values)
ax2.set_xlabel("Year")
ax2.set_ylabel("Student Satisfaction (%)")
title2 = "Weighted satisfaction by year"
title2 += f" · up to {year_sel}" if mode == "Cumulative up to year" else f" · year {year_sel}"
ax2.set_title(title2)
ax2.grid(show_grid, axis='y')
fig2.tight_layout()
st.pyplot(fig2)


# 3) DONUT: Spring vs Fall (weighted retention)

if 'Term' in df_sub.columns:
    term_order, term_vals, term_labels = ['Spring', 'Fall'], [], []
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
        centre_circle = plt.Circle((0, 0), 0.65, fc='white')
        fig3.gca().add_artist(centre_circle)
        ax3.set_title("Weighted retention: Spring vs Fall")
        ax3.axis('equal')
        st.pyplot(fig3)
    else:
        st.info("Not enough data to compare Spring vs Fall with current filters.")

# Data tabs 
tab1, tab2 = st.tabs(["📈 Displayed data", "📚 Full data"])
with tab1:
    summary = pd.DataFrame({
        "Year": grp_year.index.astype(int),
        "Retention_w": np.round(grp_year.values, 2),
        "Satisfaction_w": np.round(grp_sat.reindex(grp_year.index, fill_value=np.nan).values, 2)
    })
    st.dataframe(summary.reset_index(drop=True), use_container_width=True)

with tab2:
    st.dataframe(df_sub.reset_index(drop=True), use_container_width=True)

st.caption("Use the slider and filters to explore the indicators; all charts update in real time.")
