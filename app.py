import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
#  ESTILO GENERAL Y ESTILO DE TABLAS
# =====================================================
st.markdown("""
<style>

h1, h2, h3 { text-align: center; }

/* TABLA GENERAL */
table {
    border-collapse: collapse;
    margin-left: auto;
    margin-right: auto;
    width: 98%;
    table-layout: fixed;
}

/* CELDAS */
th, td {
    border: 1px solid #ddd;
    padding: 6px 4px;
    text-align: center;
    font-size: 13px;
    vertical-align: middle;
    word-wrap: break-word;
}

/* HEADERS */
th {
    background-color: #e8e8e8;
    font-weight: 600;
    line-height: 1.1;
}

/* FILAS ALTERNADAS */
tbody tr:nth-child(even) {
    background-color: #f5f5f5;
}

/* DESTACAR GP SELECCIONADO */
.highlight-row {
    background-color: #d4ed6d !important;
    font-weight: 700 !important;
}

/* Quitar scroll externo */
div[data-testid="stMarkdown"] > div > div {
    overflow-x: hidden !important;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
#  CARGAR DATA
# =====================================================
@st.cache_data
def load_data():
    return pd.read_csv("DB_FINAL_WITH_SCORES.csv")

df = load_data()

# Normalizar Asset Class
def normalize_asset(x):
    x = str(x).strip().lower()
    if "debt" in x: return "Private Debt"
    if "equity" in x: return "Private Equity"
    if "infra" in x: return "Infrastructure"
    if "real" in x: return "Real Estate"
    return "Otros"

df["ASSET CLASS"] = df["ASSET CLASS"].apply(normalize_asset)

# =====================================================
#  SIDEBAR FILTROS
# =====================================================
st.sidebar.header("Filtros")

asset_classes = ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
selected_asset = st.sidebar.selectbox("Asset Class", asset_classes)

expand_vintage = st.sidebar.number_input("Expand Vintage (yrs)", 1, 20, 1)
min_fund_size = st.sidebar.number_input("Minimum Fund Size (USDm)", 0, 50000, 2)
current_year = st.sidebar.number_input("Año Actual", 1990, 2035, 2025)

# Filtrar GPs según asset class
if selected_asset == "Todos":
    gps_filtered = sorted(df["FUND MANAGER"].dropna().unique().tolist())
else:
    gps_filtered = sorted(df[df["ASSET CLASS"] == selected_asset]["FUND MANAGER"].dropna().unique().tolist())

selected_gp = st.sidebar.selectbox("Seleccionar GP", gps_filtered)

# =====================================================
#  FILTRADO FINAL: todos los GPs del asset class
# =====================================================
if selected_asset == "Todos":
    df_filtered = df.copy()
else:
    df_filtered = df[df["ASSET CLASS"] == selected_asset].copy()

# Solo considerar fondos con tamaño mínimo
df_filtered = df_filtered[df_filtered["FUND SIZE (USD MN)"] >= min_fund_size]

# =====================================================
#  RANKING DEL ASSET CLASS
# =====================================================
df_rank = df_filtered.groupby("FUND MANAGER", as_index=False).agg({
    "GPScore": "mean"
})
# Asegurar que GPScore no tenga NaN
df_rank["GPScore"] = pd.to_numeric(df_rank["GPScore"], errors="coerce").fillna(0)

# Ranking corregido
df_rank["Rank"] = (
    df_rank["GPScore"]
    .rank(ascending=False, method="dense")
    .astype(int)
)

df_rank = df_rank.sort_values("Rank")

total_gps = len(df_rank)
rank_gp = int(df_rank[df_rank["FUND MANAGER"] == selected_gp]["Rank"].iloc[0])

# =====================================================
#  ARMAR TABLA DE RESULTADOS
# =====================================================
result_rows = []
for gp in df_rank["FUND MANAGER"]:
    sub = df_filtered[df_filtered["FUND MANAGER"] == gp]

    num_funds = len(sub)
    last_vintage = sub["VINTAGE / INCEPTION YEAR"].max()
    last_fund_size = sub.loc[sub["VINTAGE / INCEPTION YEAR"].idxmax(), "FUND SIZE (USD MN)"]
    total_aum = sub["FUND SIZE (USD MN)"].sum()
    gp_total_aum = sub["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]
    asset_class = sub["ASSET CLASS"].iloc[0]
    strategy = sub["STRATEGY"].iloc[0]
    region = sub["PRIMARY REGION FOCUS"].iloc[0]
    score = sub["GPScore"].iloc[0] * 100

    # Identificar si es el GP seleccionado
    highlight = "highlight-row" if gp == selected_gp else ""

    # Etiqueta de ranking SOLO para el GP seleccionado
    gp_label = f"{gp} <b>({rank_gp}º de {total_gps})</b>" if gp == selected_gp else gp

    result_rows.append(f"""
    <tr class="{highlight}">
        <td>{gp_label}</td>
        <td>{asset_class}</td>
        <td>{strategy}</td>
        <td>{region}</td>
        <td>{num_funds}</td>
        <td>{int(last_vintage)}</td>
        <td>{last_fund_size:,.0f}</td>
        <td>{total_aum:,.0f}</td>
        <td>{gp_total_aum:,.0f}</td>
        <td>{score:.2f}%</td>
    </tr>
    """)

html_table = f"""
<h2>Screening Results</h2>

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
        {''.join(result_rows)}
    </tbody>
</table>
"""

# Mostrar tabla final
st.markdown(html_table, unsafe_allow_html=True)



