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

tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}

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
        x = str(x)
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
# FORMAT FUNCTIONS
# --------------------------------------------------------
def format_multiple(x, decimals=2):
    if pd.isna(x):
        return ""
    return f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".") + "x"

def format_es(x, decimals=2):
    if pd.isna(x):
        return ""
    return f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

selected_asset = st.sidebar.selectbox(
    "Asset Class",
    ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
)

if selected_asset != "Todos":
    df_asset = df[df["ASSET CLASS"] == selected_asset].copy()
else:
    df_asset = df.copy()

gps_list = sorted(df_asset["FUND MANAGER"].dropna().unique())
selected_gp = st.sidebar.selectbox("Seleccionar GP", gps_list)

# --------------------------------------------------------
# DATASETS
# --------------------------------------------------------
df_screening = df_asset.copy()
df_funds_all = df_asset.copy()

# --------------------------------------------------------
# GP RANKING
# --------------------------------------------------------
df_gp_rank = (
    df_screening
    .groupby("FUND MANAGER", as_index=False)
    .agg({
        "GPScore": "max",
        "ASSET CLASS": "first",
        "STRATEGY": "first",
        "PRIMARY REGION FOCUS": "first",
        "FUND MANAGER TOTAL AUM (USD MN)": "first"
    })
)

df_gp_rank["Rank"] = (
    df_gp_rank["GPScore"]
    .rank(method="min", ascending=False)
    .astype(int)
)

df_gp_rank = df_gp_rank.sort_values("GPScore", ascending=False)
total_gps = len(df_gp_rank)

# --------------------------------------------------------
# SELECTED GP SUMMARY (TABLA VERDE)
# --------------------------------------------------------
gp_rows_screening = df_screening[df_screening["FUND MANAGER"] == selected_gp]

if not gp_rows_screening.empty:
    gp_rank = int(
        df_gp_rank.loc[
            df_gp_rank["FUND MANAGER"] == selected_gp,
            "Rank"
        ].iloc[0]
    )

    st.markdown(f"""
    <div class="highlight" style="padding:12px; width:95%; margin:auto;">
        <h3>{selected_gp} — {gp_rank} de {total_gps}</h3>
    </div>
    """, unsafe_allow_html=True)

    num_funds = len(gp_rows_screening)
    last_vintage = gp_rows_screening["VINTAGE / INCEPTION YEAR"].max()

    if gp_rows_screening["VINTAGE / INCEPTION YEAR"].notna().any():
        idx = gp_rows_screening["VINTAGE / INCEPTION YEAR"].idxmax()
        last_fund_size = gp_rows_screening.loc[idx, "FUND SIZE (USD MN)"]
    else:
        last_fund_size = 0

    total_aum_considered = gp_rows_screening["FUND SIZE (USD MN)"].sum()
    gp_total_aum = gp_rows_screening["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]

    asset_class = gp_rows_screening["ASSET CLASS"].iloc[0]
    strategy = gp_rows_screening["STRATEGY"].iloc[0]
    region = gp_rows_screening["PRIMARY REGION FOCUS"].iloc[0]
    gp_score = f"{gp_rows_screening['GPScore'].iloc[0] * 100:.2f}%"

    html_gp = f"""
    <table>
        <thead>
            <tr>
                <th>GP</th>
                <th>Asset Class</th>
                <th>Strategy</th>
                <th>Region</th>
                <th># Funds</th>
                <th>Last Vintage</th>
                <th>Last Fund Size</th>
                <th>Total AUM Considerado</th>
                <th>GP Total AUM</th>
                <th>Score</th>
            </tr>
        </thead>
        <tbody>
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
        </tbody>
    </table>
    """

    st.markdown(html_gp, unsafe_allow_html=True)

# --------------------------------------------------------
# (EL RESTO: TABLAS Y GRÁFICOS SIGUE IGUAL)
# --------------------------------------------------------



