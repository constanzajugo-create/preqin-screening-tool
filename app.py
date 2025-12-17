import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

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
# UTILS
# --------------------------------------------------------
def clean_year(x):
    try:
        x = str(x)
        d = "".join(c for c in x if c.isdigit())
        return int(d) if len(d) == 4 else np.nan
    except:
        return np.nan

def format_es(x, decimals=2):
    if pd.isna(x):
        return ""
    return f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_multiple(x, decimals=2):
    if pd.isna(x):
        return ""
    return format_es(x, decimals) + "x"

# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("DB_FINAL_WITH_SCORES.csv")

    df["VINTAGE / INCEPTION YEAR"] = df["VINTAGE / INCEPTION YEAR"].apply(clean_year)

    numeric_cols = [
        "GPScore", "FundScore",
        "Score Q1", "Score Q2", "Score Q3", "Score Q4",
        "NET MULTIPLE (X)", "NET IRR (%)", "DPI (%)"
    ]

    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

df = load_data()

# --------------------------------------------------------
# ASSET CLASS NORMALIZATION
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

selected_asset = st.sidebar.selectbox(
    "Asset Class",
    ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
)

df_asset = df if selected_asset == "Todos" else df[df["ASSET CLASS"] == selected_asset]

gps = sorted(df_asset["FUND MANAGER"].dropna().unique())
selected_gp = st.sidebar.selectbox("Seleccionar GP", gps)

# --------------------------------------------------------
# GP RANKING (SOLO PARA RANK)
# --------------------------------------------------------
df_gp_rank = (
    df_asset[df_asset["GPScore"].notna()]
    .groupby("FUND MANAGER", as_index=False)
    .agg({
        "GPScore": "max",
        "ASSET CLASS": "first",
        "STRATEGY": "first",
        "PRIMARY REGION FOCUS": "first",
        "FUND MANAGER TOTAL AUM (USD MN)": "first"
    })
)

df_gp_rank["Rank"] = df_gp_rank["GPScore"].rank(ascending=False, method="min")
df_gp_rank = df_gp_rank.sort_values("GPScore", ascending=False)

total_gps = len(df_gp_rank)

# --------------------------------------------------------
# GP SUMMARY (BLOQUE VERDE)
# --------------------------------------------------------
gp_row = df_gp_rank[df_gp_rank["FUND MANAGER"] == selected_gp]

if not gp_row.empty:
    rank = int(gp_row["Rank"].values[0])
    score = gp_row["GPScore"].values[0] * 100

    st.markdown(f"""
    <div class="highlight" style="padding:14px; width:95%; margin:auto;">
        <h3>{selected_gp} — {rank} de {total_gps} — Score {score:.2f}%</h3>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="highlight" style="padding:14px; width:95%; margin:auto;">
        <h3>{selected_gp} — Sin score disponible</h3>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------------
# ALL GPs TABLE
# --------------------------------------------------------
st.subheader("Todos los GPs")

df_rank_display = df_gp_rank.copy()
df_rank_display["Score (%)"] = df_rank_display["GPScore"] * 100
df_rank_display.drop(columns=["GPScore"], inplace=True)

for c in df_rank_display.columns:
    if "Score" in c:
        df_rank_display[c] = df_rank_display[c].apply(lambda x: format_es(x, 2))
    elif df_rank_display[c].dtype in ["float64", "int64"]:
        df_rank_display[c] = df_rank_display[c].apply(lambda x: format_es(x, 0))

st.dataframe(df_rank_display, use_container_width=True)

# --------------------------------------------------------
# FUNDS TABLE
# --------------------------------------------------------
st.subheader(f"Fondos del GP: {selected_gp}")

df_funds = df_asset[df_asset["FUND MANAGER"] == selected_gp].copy()
df_funds.sort_values("VINTAGE / INCEPTION YEAR", inplace=True)

desired_cols = [
    "NAME","VINTAGE / INCEPTION YEAR","FUND SIZE (USD MN)",
    "NET MULTIPLE (X)","NET IRR (%)","DPI (%)","FundScore",
    "Score Q1","Score Q2","Score Q3","Score Q4",
    "TVPI_p95","TVPI_p75","TVPI_p50","TVPI_p25",
    "IRR_p95","IRR_p75","IRR_p50","IRR_p25",
    "DPI_p95","DPI_p75","DPI_p50","DPI_p25"
]

df_funds = df_funds[[c for c in desired_cols if c in df_funds.columns]]

df_funds.rename(columns={
    "NAME":"Fund Name",
    "NET MULTIPLE (X)":"TVPI",
    "NET IRR (%)":"IRR (%)",
    "DPI (%)":"DPI",
    "TVPI_p95":"TVPI Q4","TVPI_p75":"TVPI Q3","TVPI_p50":"TVPI Q2","TVPI_p25":"TVPI Q1",
    "IRR_p95":"IRR Q4","IRR_p75":"IRR Q3","IRR_p50":"IRR Q2","IRR_p25":"IRR Q1",
    "DPI_p95":"DPI Q4","DPI_p75":"DPI Q3","DPI_p50":"DPI Q2","DPI_p25":"DPI Q1",
    "FundScore":"Fund Score"
}, inplace=True)

for c in ["Fund Score","Score Q1","Score Q2","Score Q3","Score Q4"]:
    if c in df_funds.columns:
        df_funds[c] = df_funds[c] * 100

df_funds_fmt = df_funds.copy()

for c in df_funds_fmt.columns:
    if "IRR" in c or "Score" in c:
        df_funds_fmt[c] = df_funds_fmt[c].apply(lambda x: format_es(x, 2))
    elif "TVPI" in c or "DPI" in c:
        df_funds_fmt[c] = df_funds_fmt[c].apply(lambda x: format_multiple(x, 2))
    elif df_funds_fmt[c].dtype in ["float64", "int64"]:
        df_funds_fmt[c] = df_funds_fmt[c].apply(lambda x: format_es(x, 0))

st.dataframe(df_funds_fmt, use_container_width=True, hide_index=True)
"%")

