import streamlit as st
import pandas as pd

# ----------------------------
# ESTILO GLOBAL PARA TÍTULOS
# ----------------------------
st.markdown("""
<style>
/* Aumentar el ancho máximo del cuerpo central */
.main .block-container {
    max-width: 1500px;
    padding-left: 2rem;
    padding-right: 2rem;
}
</style>
""", unsafe_allow_html=True)


/* Estilo tabla */
table {
    border-collapse: collapse;
    margin-left: auto;
    margin-right: auto;
    width: 90%;
}

th, td {
    border: 1px solid #ddd;
    padding: 10px;
    text-align: center;
    font-size: 15px;
}

th {
    background-color: #f0f0f0;
    font-weight: 600;
}

tbody tr:nth-child(even) {
    background-color: #fafafa;
}

</style>
""", unsafe_allow_html=True)

st.title("Screening Tool")


# ----------------------------
# Cargar CSV
# ----------------------------
@st.cache_data
def load_data():
    return pd.read_csv("DB_FINAL_WITH_SCORES.csv")

df = load_data()


# ----------------------------
# Normalizar Asset Class
# ----------------------------
def normalize_asset(x):
    x = str(x).strip().lower()

    if "debt" in x: return "Private Debt"
    if "equity" in x: return "Private Equity"
    if "infra" in x: return "Infrastructure"
    if "real" in x: return "Real Estate"
    return "Otros"

df["ASSET CLASS"] = df["ASSET CLASS"].apply(normalize_asset)


# ----------------------------
# SIDEBAR – FILTROS
# ----------------------------
st.sidebar.header("Filtros")

expand_vintage = st.sidebar.number_input("Expand Vintage (yrs)", 1, 20, 1)
min_fund_size = st.sidebar.number_input("Minimum Fund Size (USDm)", 0, 5000, 2)
current_year = st.sidebar.number_input("Año Actual", 1990, 2030, 2025)

asset_classes = ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
selected_asset = st.sidebar.selectbox("Asset Class", asset_classes)

# GP dinámicos
if selected_asset == "Todos":
    gps_filtered = sorted(df["FUND MANAGER"].dropna().unique())
else:
    gps_filtered = sorted(df[df["ASSET CLASS"] == selected_asset]["FUND MANAGER"].dropna().unique())

selected_gp = st.sidebar.selectbox("Seleccionar GP", gps_filtered)


# ----------------------------
# FILTRADO FINAL
# ----------------------------
filtered = df.copy()

if selected_asset != "Todos":
    filtered = filtered[filtered["ASSET CLASS"] == selected_asset]

if selected_gp != "Todos":
    filtered = filtered[filtered["FUND MANAGER"] == selected_gp]

filtered = filtered[filtered["FUND SIZE (USD MN)"] >= min_fund_size]


# ----------------------------
# RESULTADOS
# ----------------------------
st.subheader("Resultados del GP Seleccionado")

if selected_gp != "Todos":
    gp_df = filtered[filtered["FUND MANAGER"] == selected_gp]

    if len(gp_df) > 0:

        # Cálculos
        num_funds = len(gp_df)
        last_vintage = gp_df["VINTAGE / INCEPTION YEAR"].max()
        last_fund_size = gp_df.loc[gp_df["VINTAGE / INCEPTION YEAR"].idxmax(), "FUND SIZE (USD MN)"]
        total_aum_considered = gp_df["FUND SIZE (USD MN)"].sum()
        gp_total_aum = gp_df["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]

        asset_class = gp_df["ASSET CLASS"].iloc[0]
        strategy = gp_df["STRATEGY"].iloc[0]
        region = gp_df["PRIMARY REGION FOCUS"].iloc[0]

        gp_score_raw = gp_df["GPScore"].iloc[0]
        gp_score = f"{gp_score_raw * 100:.2f}%"

        # -------------------------
        # TABLA HTML CORREGIDA
        # -------------------------
        html_table = f"""
        <div style="overflow-x: auto; width: 100%;">
        <table style="width: 100%; table-layout: fixed;">
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
                <tr>
                    <td>{selected_gp}</td>
                    <td>{asset_class}</td>
                    <td>{strategy}</td>
                    <td>{region}</td>
                    <td>{num_funds}</td>
                    <td>{last_vintage}</td>
                    <td>{last_fund_size:,.0f}</td>
                    <td>{total_aum_considered:,.0f}</td>
                    <td>{gp_total_aum:,.0f}</td>
                    <td><b>{gp_score}</b></td>
                </tr>
            </tbody>
        </table>
        </div>
        """


        st.markdown(html_table, unsafe_allow_html=True)

else:
    st.info("Seleccione un GP para ver el resumen.")





