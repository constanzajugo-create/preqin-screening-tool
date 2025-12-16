import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------------
# STYLE
# --------------------------------------------------------
st.markdown("""
<style>
h1, h2, h3 { text-align: center; }

.highlight {
    background-color: #c8efb4 !important;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.title("Screening Tool")

# --------------------------------------------------------
# CLEANING
# --------------------------------------------------------
def clean_year(x):
    try:
        x = str(x).strip()
        digits = "".join(ch for ch in x if ch.isdigit())
        return int(digits) if len(digits) == 4 else np.nan
    except:
        return np.nan

# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("DB_FINAL_WITH_SCORES.csv")
    df["VINTAGE / INCEPTION YEAR"] = df["VINTAGE / INCEPTION YEAR"].apply(clean_year)
    df["GPScore"] = pd.to_numeric(df["GPScore"], errors="coerce").fillna(0)
    df["FundScore"] = pd.to_numeric(df["FundScore"], errors="coerce").fillna(0)
    return df

df = load_data()

# --------------------------------------------------------
# NORMALIZE ASSET CLASS
# --------------------------------------------------------
def normalize_asset(x):
    x = str(x).lower()
    if "debt" in x: return "Private Debt"
    if "equity" in x: return "Private Equity"
    if "infra" in x: return "Infrastructure"
    if "real" in x: return "Real Estate"
    return "Other"

df["ASSET CLASS"] = df["ASSET CLASS"].apply(normalize_asset)

# --------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------
st.sidebar.header("Filtros")

min_fund_size = st.sidebar.number_input("Minimum Fund Size (USDm)", 0, 5000, 2)

selected_asset = st.sidebar.selectbox(
    "Asset Class",
    ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
)

df_filtered = df.copy()
if selected_asset != "Todos":
    df_filtered = df_filtered[df_filtered["ASSET CLASS"] == selected_asset]

df_filtered = df_filtered[df_filtered["FUND SIZE (USD MN)"] >= min_fund_size]

gps = sorted(df_filtered["FUND MANAGER"].dropna().unique())
selected_gp = st.sidebar.selectbox("Seleccionar GP", gps)

# --------------------------------------------------------
# GP RANKING
# --------------------------------------------------------
df_rank = df_filtered.copy()
df_rank["Rank"] = df_rank["GPScore"].rank(method="min", ascending=False).astype(int)
df_rank = df_rank.sort_values("GPScore", ascending=False)

total_gps = df_rank["FUND MANAGER"].nunique()
gp_rows = df_rank[df_rank["FUND MANAGER"] == selected_gp]

# --------------------------------------------------------
# GP SUMMARY
# --------------------------------------------------------
if not gp_rows.empty:

    gp_rank = gp_rows["Rank"].iloc[0]
    num_funds = len(gp_rows)
    last_vintage = gp_rows["VINTAGE / INCEPTION YEAR"].max()

    idx = gp_rows["VINTAGE / INCEPTION YEAR"].idxmax()
    last_fund_size = gp_rows.loc[idx, "FUND SIZE (USD MN)"]

    total_aum_considered = gp_rows["FUND SIZE (USD MN)"].sum()
    gp_total_aum = gp_rows["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]

    st.markdown(f"""
    <div class="highlight" style="padding:12px; width:95%; margin:auto;">
    <h3>{selected_gp} — {gp_rank} de {total_gps}</h3>
    </div>
    """, unsafe_allow_html=True)

    st.write({
        "Asset Class": gp_rows["ASSET CLASS"].iloc[0],
        "Strategy": gp_rows["STRATEGY"].iloc[0],
        "Region": gp_rows["PRIMARY REGION FOCUS"].iloc[0],
        "# Funds": num_funds,
        "Last Vintage": int(last_vintage),
        "Last Fund Size (USDm)": round(last_fund_size, 0),
        "Total AUM Considerado (USDm)": round(total_aum_considered, 0),
        "GP Total AUM (USDm)": round(gp_total_aum, 0),
        "GP Score (%)": round(gp_rows["GPScore"].iloc[0] * 100, 2)
    })

# --------------------------------------------------------
# FUNDS TABLE (EXCEL RIGHT SIDE)
# --------------------------------------------------------
st.subheader("Fondos del GP seleccionado")

df_funds = df_filtered[df_filtered["FUND MANAGER"] == selected_gp].copy()
df_funds = df_funds.sort_values("VINTAGE / INCEPTION YEAR")

df_funds_display = df_funds[[
    "NAME",
    "VINTAGE / INCEPTION YEAR",
    "FUND SIZE (USD MN)",
    "NET MULTIPLE (X)",
    "IRR",
    "DPI (%)",
    "FundScore",
    "TVPI_p95", "TVPI_p75", "TVPI_p50", "TVPI_p25",
    "IRR_p95", "IRR_p75", "IRR_p50", "IRR_p25",
    "DPI_p95", "DPI_p75", "DPI_p50", "DPI_p25"
]].copy()

# Rename for display (Q4 → Q1)
df_funds_display = df_funds_display.rename(columns={
    "NAME": "Fund Name",
    "NET MULTIPLE (X)": "TVPI",
    "DPI (%)": "DPI",
    "FundScore": "Fund Score",
    "TVPI_p95": "TVPI Q4", "TVPI_p75": "TVPI Q3", "TVPI_p50": "TVPI Q2", "TVPI_p25": "TVPI Q1",
    "IRR_p95": "IRR Q4", "IRR_p75": "IRR Q3", "IRR_p50": "IRR Q2", "IRR_p25": "IRR Q1",
    "DPI_p95": "DPI Q4", "DPI_p75": "DPI Q3", "DPI_p50": "DPI Q2", "DPI_p25": "DPI Q1",
})

# Percent formatting
df_funds_display["Fund Score"] = df_funds_display["Fund Score"] * 100
df_funds_display = df_funds_display.round(2)

st.dataframe(df_funds_display, use_container_width=True, hide_index=True)

# --------------------------------------------------------
# FULL GP TABLE
# --------------------------------------------------------
st.subheader("Todos los GPs del Asset Class")

df_rank_display = df_rank[[
    "FUND MANAGER",
    "ASSET CLASS",
    "STRATEGY",
    "PRIMARY REGION FOCUS",
    "FUND SIZE (USD MN)",
    "VINTAGE / INCEPTION YEAR",
    "GPScore",
    "Rank"
]].copy()

df_rank_display["Score %"] = df_rank_display["GPScore"] * 100
df_rank_display = df_rank_display.round(2)

st.dataframe(df_rank_display, use_container_width=True)




