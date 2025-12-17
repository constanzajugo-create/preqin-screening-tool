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
# ALL GPs TABLE
# --------------------------------------------------------
st.subheader("Todos los GPs del Asset Class (ordenados por Score)")

df_rank_display = df_gp_rank.copy()
df_rank_display["Score"] = df_rank_display["GPScore"] * 100
df_rank_display = df_rank_display.drop(columns=["GPScore"])

for col in df_rank_display.columns:
    if col == "Score":
        df_rank_display[col] = df_rank_display[col].apply(lambda x: format_es(x, 2))
    elif df_rank_display[col].dtype in ["float64", "int64"]:
        df_rank_display[col] = df_rank_display[col].apply(lambda x: format_es(x, 0))

st.dataframe(df_rank_display, use_container_width=True, hide_index=True)

# --------------------------------------------------------
# FUNDS TABLE
# --------------------------------------------------------

COLOR_GROUPS = {
    "TVPI": "#e8f1fb",      # azul suave
    "IRR": "#eaf7ea",       # verde suave
    "DPI": "#fff2e6",       # naranjo suave
    "Score": "#f3e8fb"      # morado suave
}

st.subheader(f"Fondos del GP: {selected_gp}")

df_funds = df_funds_all[df_funds_all["FUND MANAGER"] == selected_gp].copy()
df_funds = df_funds.sort_values("VINTAGE / INCEPTION YEAR")

desired_cols = [
    "NAME","VINTAGE / INCEPTION YEAR","FUND SIZE (USD MN)",
    "NET MULTIPLE (X)","NET IRR (%)","DPI (%)","FundScore",
    "Score Q4","Score Q3","Score Q2","Score Q1",
    "TVPI_p95","TVPI_p75","TVPI_p50","TVPI_p25",
    "IRR_p95","IRR_p75","IRR_p50","IRR_p25",
    "DPI_p95","DPI_p75","DPI_p50","DPI_p25"
]

available_cols = [c for c in desired_cols if c in df_funds.columns]
df_funds_display = df_funds[available_cols].copy()

df_funds_display = df_funds_display.rename(columns={
    "NAME":"Fund Name",
    "NET MULTIPLE (X)":"TVPI",
    "NET IRR (%)":"IRR (%)",
    "DPI (%)":"DPI",
    "FundScore":"Fund Score",
    "TVPI_p95":"TVPI Q4","TVPI_p75":"TVPI Q3","TVPI_p50":"TVPI Q2","TVPI_p25":"TVPI Q1",
    "IRR_p95":"IRR Q4","IRR_p75":"IRR Q3","IRR_p50":"IRR Q2","IRR_p25":"IRR Q1",
    "DPI_p95":"DPI Q4","DPI_p75":"DPI Q3","DPI_p50":"DPI Q2","DPI_p25":"DPI Q1",
})

if "Fund Score" in df_funds_display.columns:
    df_funds_display["Fund Score"] *= 100

for q in ["Score Q1","Score Q2","Score Q3","Score Q4"]:
    if q in df_funds_display.columns:
        df_funds_display[q] *= 100

df_funds_fmt = df_funds_display.copy()

for col in df_funds_fmt.columns:
    if "IRR" in col or "Score" in col:
        df_funds_fmt[col] = df_funds_fmt[col].apply(lambda x: format_es(x, 2))
    elif col in ["TVPI","DPI"] or "Q" in col:
        df_funds_fmt[col] = df_funds_fmt[col].apply(lambda x: format_multiple(x, 2))
    elif df_funds_fmt[col].dtype in ["float64","int64"]:
        df_funds_fmt[col] = df_funds_fmt[col].apply(lambda x: format_es(x, 0))

def color_columns(df):
    styles = pd.DataFrame("", index=df.index, columns=df.columns)

    for col in df.columns:
        if col.startswith("TVPI"):
            styles[col] = f"background-color: {COLOR_GROUPS['TVPI']}"
        elif col.startswith("IRR"):
            styles[col] = f"background-color: {COLOR_GROUPS['IRR']}"
        elif col.startswith("DPI"):
            styles[col] = f"background-color: {COLOR_GROUPS['DPI']}"
        elif "Score" in col:
            styles[col] = f"background-color: {COLOR_GROUPS['Score']}"

    return styles


styled_df = (
    df_funds_fmt
    .style
    .apply(color_columns, axis=None)
)

st.dataframe(styled_df, use_container_width=True)


# --------------------------------------------------------
# GRÁFICOS
# --------------------------------------------------------

COLORS = {
    "Q1": "#1f4e79",
    "Q2": "#5b9bd5",
    "Q3": "#d9d9d9",
    "Q4": "#ffc000"
}

# Crear alturas "reales" por tramo (igual Excel)
for base in ["TVPI", "IRR", "DPI", "Score"]:
    df_funds_display[f"{base} Q1_h"] = df_funds_display[f"{base} Q1"]
    df_funds_display[f"{base} Q2_h"] = df_funds_display[f"{base} Q2"] - df_funds_display[f"{base} Q1"]
    df_funds_display[f"{base} Q3_h"] = df_funds_display[f"{base} Q3"] - df_funds_display[f"{base} Q2"]
    df_funds_display[f"{base} Q4_h"] = df_funds_display[f"{base} Q4"] - df_funds_display[f"{base} Q3"]


def stacked_plot(base, real_col, title, ylabel, is_percent=False, suffix=""):
    fig, ax = plt.subplots(figsize=(35, 16))

    # Q1
    ax.bar(
        df_funds_display["Fund Name"],
        df_funds_display[f"{base} Q1_h"],
        color=COLORS["Q1"],
        label="Q1"
    )

    # Q2
    ax.bar(
        df_funds_display["Fund Name"],
        df_funds_display[f"{base} Q2_h"],
        bottom=df_funds_display[f"{base} Q1"],
        color=COLORS["Q2"],
        label="Q2"
    )

    # Q3
    ax.bar(
        df_funds_display["Fund Name"],
        df_funds_display[f"{base} Q3_h"],
        bottom=df_funds_display[f"{base} Q2"],
        color=COLORS["Q3"],
        label="Q3"
    )

    # Q4
    ax.bar(
        df_funds_display["Fund Name"],
        df_funds_display[f"{base} Q4_h"],
        bottom=df_funds_display[f"{base} Q3"],
        color=COLORS["Q4"],
        label="Q4"
    )

    # Punto rojo (valor real)
    ax.scatter(
        df_funds_display["Fund Name"],
        df_funds_display[real_col],
        color="red",
        s=220,
        edgecolor="white",
        linewidth=2,
        zorder=20
    )

    # Etiquetas punto rojo
    offset = 2 if is_percent else 0.15
    for x, y in zip(df_funds_display["Fund Name"], df_funds_display[real_col]):
        if pd.notna(y):
            ax.text(
                x, y + offset,
                f"{y:.2f}{suffix}",
                color="red",
                fontsize=20,
                ha="center",
                va="bottom"
            )

    # 🔥 CLAVE: NO partir desde 0 (igual Excel)
    ymin = df_funds_display[f"{base} Q1"].min() * 0.95
    ymax = df_funds_display[f"{base} Q4"].max() * 1.05
    ax.set_ylim(ymin, ymax)

    ax.set_title(title, fontsize=35)
    ax.set_xlabel("Fund Name", fontsize=28)
    ax.set_ylabel(ylabel, fontsize=28)
    ax.tick_params(axis="x", labelsize=22, rotation=45)
    ax.tick_params(axis="y", labelsize=22)

    if is_percent:
        ax.yaxis.set_major_formatter(PercentFormatter())

    ax.legend(fontsize=28)
    st.pyplot(fig)


# ----------- LLAMADAS -----------

stacked_plot("TVPI", "TVPI", "TVPI", "TVPI", suffix="x")
stacked_plot("IRR", "IRR (%)", "IRR", "IRR (%)", is_percent=True, suffix="%")
stacked_plot("DPI", "DPI", "DPI", "DPI", suffix="x")
stacked_plot("Score", "Fund Score", "Performance Score", "Score (%)", is_percent=True, suffix="%")








