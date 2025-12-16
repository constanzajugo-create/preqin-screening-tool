import streamlit as st
import pandas as pd

st.title("Screening Tool")

st.table(resumen.style.set_table_styles([
    {"selector": "th", "props": "font-size: 14px; text-align: center;"},
    {"selector": "td", "props": "font-size: 13px;"}
]).set_properties(**{
    "text-align": "center",
    "width": "150px"
}))


# --- Cargar CSV ---
@st.cache_data
def load_data():
    return pd.read_csv("DB_FINAL_WITH_SCORES.csv")

df = load_data()

# Normalizar columna ASSET CLASS
def normalize_asset(x):
    x = str(x).strip().lower()

    if "debt" in x:
        return "Private Debt"
    if "equity" in x:
        return "Private Equity"
    if "infra" in x:
        return "Infrastructure"
    if "real" in x:
        return "Real Estate"

    return "Otros"

df["ASSET CLASS"] = df["ASSET CLASS"].apply(normalize_asset)

# --- Filtros ---
st.sidebar.header("Filtros")

expand_vintage = st.sidebar.number_input("Expand Vintage (yrs)", 1, 20, 1)
min_fund_size = st.sidebar.number_input("Minimum Fund Size (USDm)", 0, 5000, 2)
current_year = st.sidebar.number_input("Año Actual", 1990, 2030, 2025)

# Lista fija de Asset Classes
asset_classes = ["Todos", "Private Debt", "Private Equity", "Infrastructure", "Real Estate"]
selected_asset = st.sidebar.selectbox("Asset Class", asset_classes)

# --- GP dinámico según Asset Class ---
if selected_asset == "Todos":
    gps_filtered = df["FUND MANAGER"].dropna().unique()
else:
    gps_filtered = df[df["ASSET CLASS"] == selected_asset]["FUND MANAGER"].dropna().unique()

gps_filtered = sorted(gps_filtered)

selected_gp = st.sidebar.selectbox("Seleccionar GP", gps_filtered)


# --- Aplicar filtros ---
filtered = df.copy()

if selected_asset != "Todos":
    filtered = filtered[filtered["ASSET CLASS"] == selected_asset]

if selected_gp != "Todos":
    filtered = filtered[filtered["FUND MANAGER"] == selected_gp]

filtered = filtered[filtered["FUND SIZE (USD MN)"] >= min_fund_size]

# --- Mostrar resultados ---
# --- Mostrar resultados ---
st.subheader("Resultados del GP Seleccionado")

if selected_gp != "Todos":
    gp_df = filtered[filtered["FUND MANAGER"] == selected_gp]

    if len(gp_df) > 0:

        # Numero de fondos considerados
        num_funds = len(gp_df)

        # Último vintage
        last_vintage = gp_df["VINTAGE / INCEPTION YEAR"].max()

        # Tamaño del fondo del último vintage
        last_fund_size = gp_df.loc[
            gp_df["VINTAGE / INCEPTION YEAR"].idxmax(),
            "FUND SIZE (USD MN)"
        ]

        # Total AUM considerado
        total_aum_considered = gp_df["FUND SIZE (USD MN)"].sum()

        # AUM total del GP
        gp_total_aum = gp_df["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]

        # Asset class y estrategia principal (primera fila)
        asset_class = gp_df["ASSET CLASS"].iloc[0]
        strategy = gp_df["STRATEGY"].iloc[0]
        region = gp_df["PRIMARY REGION FOCUS"].iloc[0]

        # Score final del GP
        gp_score_raw = gp_df["GPScore"].iloc[0]
        gp_score = f"{gp_score_raw * 100:.2f}%"

        # Construir tabla resumen
        resumen = pd.DataFrame({
            "GP (Fund Manager)": [selected_gp],
            "Asset Class": [asset_class],
            "Strategy": [strategy],
            "Region": [region],
            "# Funds": [num_funds],
            "Last Vintage": [last_vintage],
            "Last Fund Size (USDm)": [last_fund_size],
            "Total AUM Considerado (USDm)": [total_aum_considered],
            "GP Total AUM (USDm)": [gp_total_aum],
            "Score": [gp_score]
        })

        st.dataframe(resumen, use_container_width=True, hide_index=True)

else:
    st.info("Seleccione un GP para ver el resumen.")













