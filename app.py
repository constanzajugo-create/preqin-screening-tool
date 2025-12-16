import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------------
# STYLE
# --------------------------------------------------------
st.markdown("""
<style>
h1, h2, h3 { text-align: center; }

table {
    width: 98%;
    margin-left: auto;
    margin-right: auto;
    border-collapse: collapse;
    table-layout: fixed;
}

th, td {
    border: 1px solid #ddd;
    padding: 6px 4px;
    font-size: 13px;
    text-align: center;
    vertical-align: top;
    word-wrap: break-word;
}

th {
    background-color: #e9e9e9;
    font-weight: 600;
    line-height: 1.2;
}

tbody tr:nth-child(even) { background-color: #f9f9f9; }

.highlight {
    background-color: #c8efb4 !important;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.title("Screening Tool")

# --------------------------------------------------------
# CLEANING FUNCTIONS
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

    st.markdown(f"""
    <div class="highlight" style="padding:12px; width:95%; margin:auto;">
    <h3>{selected_gp} — {gp_rank} de {total_gps}</h3>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------------
# FUNDS TABLE (ROBUST, NO CRASH)
# --------------------------------------------------------
st.subheader("Fondos del GP seleccionado")

df_funds = df_filtered[df_filtered["FUND MANAGER"] == selected_gp].copy()
df_funds = df_funds.sort_values("VINTAGE / INCEPTION YEAR")

desired_cols = [
    "NAME",
    "VINTAGE / INCEPTION YEAR",
    "FUND SIZE (USD MN)",
    "NET MULTIPLE (X)",
    "IRR",
    "DPI (%)",
    "FundScore",
    "TVPI_p95","TVPI_p75","TVPI_p50","TVPI_p25",
    "IRR_p95","IRR_p75","IRR_p50","IRR_p25",
    "DPI_p95","DPI_p75","DPI_p50","DPI_p25"
]

available_cols = [c for c in desired_cols if c in df_funds.columns]

df_funds_display = df_funds[available_cols].copy()

df_funds_display = df_funds_display.rename(columns={
    "NAME": "Fund Name",
    "NET MULTIPLE (X)": "TVPI",
    "DPI (%)": "DPI",
    "FundScore": "Fund Score",
    "TVPI_p95": "TVPI Q4", "TVPI_p75": "TVPI Q3", "TVPI_p50": "TVPI Q2", "TVPI_p25": "TVPI Q1",
    "IRR_p95": "IRR Q4", "IRR_p75": "IRR Q3", "IRR_p50": "IRR Q2", "IRR_p25": "IRR Q1",
    "DPI_p95": "DPI Q4", "DPI_p75": "DPI Q3", "DPI_p50": "DPI Q2", "DPI_p25": "DPI Q1",
})

if "Fund Score" in df_funds_display.columns:
    df_funds_display["Fund Score"] *= 100

df_funds_display = df_funds_display.round(2)

st.dataframe(df_funds_display, use_container_width=True, hide_index=True)

