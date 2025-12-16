import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------------
# STYLE
# --------------------------------------------------------
st.markdown("""
<style>
h1, h2, h3 { text-align: center; }

/* Tabla principal */
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
    background-color: #c8efb4 !important;  /* verde suave */
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.title("Screening Tool")

# --------------------------------------------------------
# CLEANING FUNCTIONS
# --------------------------------------------------------
def clean_year(x):
    """Return clean 4-digit year or NaN."""
    try:
        x = str(x).strip()

        if x.lower() in ["nan", "none", "null", "n/a", "-", "--", "", " "]:
            return np.nan

        digits = "".join(ch for ch in x if ch.isdigit())
        if len(digits) == 4:
            return int(digits)

        return np.nan
    except:
        return np.nan


# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("DB_FINAL_WITH_SCORES.csv")

    # Clean vintage column
    df["VINTAGE / INCEPTION YEAR"] = df["VINTAGE / INCEPTION YEAR"].apply(clean_year)

    # Convert GPScore to numeric
    df["GPScore"] = pd.to_numeric(df["GPScore"], errors="coerce")

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

# Expand vintage
expand_vintage = st.sidebar.number_input("Expand Vintage (yrs)", 0, 20, 1)

# Fund size minimum
min_fund_size = st.sidebar.number_input("Minimum Fund Size (USDm)", 0, 5000, 2)

# Current year
current_year = st.sidebar.number_input("Año Actual", 1990, 2035, 2025)

selected_asset = st.sidebar.selectbox(
    "Asset Class",
    ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
)

# GP list depends on Asset Class
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

# VERY IMPORTANT: fix GPScore here (not in df)
df_filtered["GPScore"] = pd.to_numeric(df_filtered["GPScore"], errors="coerce").fillna(0)

# --------------------------------------------------------
# RANKING
# --------------------------------------------------------
df_rank = df_filtered.copy()

df_rank["Rank"] = (
    df_rank["GPScore"]
    .rank(method="min", ascending=False)
    .astype(int)
)

df_rank = df_rank.sort_values("GPScore", ascending=False)

total_gps = df_rank["FUND MANAGER"].nunique()

# --------------------------------------------------------
# SELECTED GP BLOCK
# --------------------------------------------------------
gp_rows = df_rank[df_rank["FUND MANAGER"] == selected_gp]

if len(gp_rows) > 0:

    gp_rank = int(gp_rows["Rank"].iloc[0])

    num_funds = len(gp_rows)

    # Fix vintage safely
    last_vintage = gp_rows["VINTAGE / INCEPTION YEAR"].max()
    last_vintage_clean = "" if pd.isna(last_vintage) else int(last_vintage)

    # Fix last_fund_size safely
    if gp_rows["VINTAGE / INCEPTION YEAR"].notna().any():
        idx = gp_rows["VINTAGE / INCEPTION YEAR"].idxmax()
        last_fund_size = gp_rows.loc[idx, "FUND SIZE (USD MN)"]
    else:
        last_fund_size = 0

    total_aum_considered = gp_rows["FUND SIZE (USD MN)"].sum()
    gp_total_aum = gp_rows["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]
    asset_class = gp_rows["ASSET CLASS"].iloc[0]
    strategy = gp_rows["STRATEGY"].iloc[0]
    region = gp_rows["PRIMARY REGION FOCUS"].iloc[0]
    gp_score = f"{gp_rows['GPScore'].iloc[0] * 100:.2f}%"

    # --------------------------------------------------------
    # GREEN SUMMARY BOX
    # --------------------------------------------------------
    st.markdown(f"""
    <div class="highlight" style="padding: 12px; width: 95%; margin-left:auto;margin-right:auto;">
    <h3>{selected_gp} — {gp_rank} de {total_gps}</h3>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # TABLE FOR SELECTED GP
    # --------------------------------------------------------
    html_gp = f"""
    <table>
        <thead>
            <tr>
                <th>GP (Fund Manager)</th>
                <th>Asset Class</th>
                <th>Strategy</th>
                <th>Region</th>
                <th># Funds</th>
                <th>Last Vintage</th>
                <th>Last Fund Size (USDm)</th>
                <th>Total AUM Considerado (USDm)</th>
                <th>GP Total AUM (USDm)</th>
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
# FULL TABLE OF ALL GPS FROM ASSET CLASS
# --------------------------------------------------------
st.subheader("Todos los GPs del Asset Class (ordenados por Score)")

df_rank_display = df_rank[[
    "FUND MANAGER", "ASSET CLASS", "STRATEGY",
    "PRIMARY REGION FOCUS", "FUND SIZE (USD MN)",
    "VINTAGE / INCEPTION YEAR", "GPScore", "Rank"
]]

df_rank_display["Score %"] = df_rank_display["GPScore"] * 100

st.dataframe(df_rank_display, use_container_width=True)









