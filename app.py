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
        if x.lower() in ["nan", "none", "null", "n/a", "-", "--", "", " "]:
            return np.nan
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
    x = str(x).lower().strip()
    if "debt" in x: return "Private Debt"
    if "equity" in x: return "Private Equity"
    if "infra" in x: return "Infrastructure"
    if "real" in x: return "Real Estate"
    return "Other"

df["ASSET CLASS"] = df["ASSET CLASS"].apply(normalize_asset)

# --------------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------------
st.sidebar.header("Filtros")

expand_vintage = st.sidebar.number_input("Expand Vintage (yrs)", 0, 20, 1)
min_fund_size = st.sidebar.number_input("Minimum Fund Size (USDm)", 0, 5000, 2)
current_year = st.sidebar.number_input("Año Actual", 1990, 2035, 2025)

selected_asset = st.sidebar.selectbox(
    "Asset Class",
    ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
)

if selected_asset == "Todos":
    gps_list = sorted(df["FUND MANAGER"].dropna().unique())
else:
    gps_list = sorted(df[df["ASSET CLASS"] == selected_asset]["FUND MANAGER"].dropna().unique())

selected_gp = st.sidebar.selectbox("Seleccionar GP", gps_list)

# --------------------------------------------------------
# FILTER DATA
# --------------------------------------------------------
if selected_asset != "Todos":
    df_filtered = df[df["ASSET CLASS"] == selected_asset].copy()
else:
    df_filtered = df.copy()

df_filtered = df_filtered[df_filtered["FUND SIZE (USD MN)"] >= min_fund_size]

# --------------------------------------------------------
# RANKING GP
# --------------------------------------------------------
df_rank = df_filtered.copy()
df_rank["Rank"] = df_rank["GPScore"].rank(method="min", ascending=False).astype(int)
df_rank = df_rank.sort_values("GPScore", ascending=False)

total_gps = df_rank["FUND MANAGER"].nunique()

# --------------------------------------------------------
# SELECTED GP SUMMARY
# --------------------------------------------------------
gp_rows = df_rank[df_rank["FUND MANAGER"] == selected_gp]

if len(gp_rows) > 0:

    gp_rank = int(gp_rows["Rank"].iloc[0])
    num_funds = len(gp_rows)

    last_vintage = gp_rows["VINTAGE / INCEPTION YEAR"].max()
    idx = gp_rows["VINTAGE / INCEPTION YEAR"].idxmax()
    last_fund_size = gp_rows.loc[idx, "FUND SIZE (USD MN)"] if pd.notna(idx) else 0

    total_aum_considered = gp_rows["FUND SIZE (USD MN)"].sum()
    gp_total_aum = gp_rows["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]

    asset_class = gp_rows["ASSET CLASS"].iloc[0]
    strategy = gp_rows["STRATEGY"].iloc[0]
    region = gp_rows["PRIMARY REGION FOCUS"].iloc[0]
    gp_score = f"{gp_rows['GPScore'].iloc[0] * 100:.2f}%"

    st.markdown(f"""
    <div class="highlight" style="padding:12px; width:95%; margin:auto;">
    <h3>{selected_gp} — {gp_rank} de {total_gps}</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <table>
        <tr class="highlight">
            <td>{selected_gp}</td>
            <td>{asset_class}</td>
            <td>{strategy}</td>
            <td>{region}</td>
            <td>{num_funds}</td>
            <td>{"" if pd.isna(last_vintage) else int(last_vintage)}</td>
            <td>{last_fund_size:,.0f}</td>
            <td>{total_aum_considered:,.0f}</td>
            <td>{gp_total_aum:,.0f}</td>
            <td>{gp_score}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

# --------------------------------------------------------
# FUNDS TABLE — SELECTED GP
# --------------------------------------------------------
st.subheader("Fondos del GP seleccionado")

df_funds = df_filtered[df_filtered["FUND MANAGER"] == selected_gp].copy()
df_funds = df_funds.sort_values("VINTAGE / INCEPTION YEAR")

funds_cols = [
    "FUND NAME",
    "VINTAGE / INCEPTION YEAR",
    "FUND SIZE (USD MN)",
    "TVPI", "IRR", "DPI",
    "Fund Score",
    "TVPI_Q4","TVPI_Q3","TVPI_Q2","TVPI_Q1",
    "IRR_Q4","IRR_Q3","IRR_Q2","IRR_Q1",
    "DPI_Q4","DPI_Q3","DPI_Q2","DPI_Q1"
]

df_funds_display = df_funds[funds_cols].copy()

for col in df_funds_display.columns:
    if "IRR" in col or "Score" in col:
        df_funds_display[col] = df_funds_display[col] * 100

df_funds_display = df_funds_display.round(2)

st.dataframe(df_funds_display, use_container_width=True, hide_index=True)

# --------------------------------------------------------
# FULL GP RANKING TABLE
# --------------------------------------------------------
st.subheader("Todos los GPs del Asset Class (ordenados por Score)")

df_rank_display = df_rank[
    ["FUND MANAGER","ASSET CLASS","STRATEGY",
     "PRIMARY REGION FOCUS","FUND SIZE (USD MN)",
     "VINTAGE / INCEPTION YEAR","GPScore","Rank"]
]

df_rank_display["Score %"] = df_rank_display["GPScore"] * 100
df_rank_display = df_rank_display.round(2)

st.dataframe(df_rank_display, use_container_width=True)






