import streamlit as st
import pandas as pd
import numpy as np # Necesario si usas datos dummy para prueba

# ----------------------------
# ESTILO GLOBAL PARA TÍTULOS Y TABLA
# ----------------------------
st.markdown("""
<style>
h1, h2, h3 { text-align: center; }

/* Estilo tabla: Ajustado para que las celdas sean más compactas */
table {
    border-collapse: collapse;
    margin-left: auto;
    margin-right: auto;
    width: 90%; /* Mantener el ancho controlado */
    table-layout: fixed; /* Mantenemos fixed para que el ancho se distribuya equitativamente */
}

th, td {
    border: 1px solid #ddd;
    /* Reducimos el padding vertical y horizontal para compactar la tabla */
    padding: 5px 3px; 
    text-align: center;
    font-size: 13px; /* Reducir ligeramente el tamaño de la fuente si es necesario */
    vertical-align: top; /* Alinear el texto de las celdas en la parte superior */
    word-wrap: break-word; /* Permite romper palabras largas si es necesario */
}

th {
    background-color: #f0f0f0;
    font-weight: 600;
    font-size: 13px; /* Ajustar fuente del encabezado al mismo tamaño o ligeramente mayor */
    line-height: 1.2; /* Reduce el espacio entre líneas en el encabezado */
}

tbody tr:nth-child(even) {
    background-color: #fafafa;
}

/* Contenedor de la tabla: asegura que se muestre sin scroll */
div[data-testid="stMarkdown"] > div > div {
    overflow-x: hidden !important;
}

</style>
""", unsafe_allow_html=True)

st.title("Screening Tool")


# ----------------------------
# Cargar CSV
# ----------------------------
@st.cache_data
def load_data():
    try:
        # Intenta cargar el archivo real
        df = pd.read_csv("DB_FINAL_WITH_SCORES.csv")
    except FileNotFoundError:
        # Datos Dummy para asegurar que el código funcione sin el CSV
        # Asegúrate de que las columnas tengan los mismos nombres que en tu DB real
        st.warning("Archivo 'DB_FINAL_WITH_SCORES.csv' no encontrado. Usando datos dummy para la demostración.")
        df = pd.DataFrame({
            "FUND MANAGER": ["1 SEED PARTNERS", "1 SEED PARTNERS", "2 VENTURE CAPITAL"],
            "ASSET CLASS": ["Real Estate", "Real Estate", "Private Equity"],
            "FUND SIZE (USD MN)": [100, 150, 50],
            "VINTAGE / INCEPTION YEAR": [2010, 2018, 2020],
            "STRATEGY": ["Real Estate Fund of Funds", "Real Estate Value Add", "Venture Capital Seed"],
            "PRIMARY REGION FOCUS": ["North America", "North America", "Europe"],
            "FUND MANAGER TOTAL AUM (USD MN)": [5000, 5000, 2000],
            "GPScore": [0.4405, 0.4405, 0.75]
        })
        for col in ["FUND SIZE (USD MN)", "VINTAGE / INCEPTION YEAR", "FUND MANAGER TOTAL AUM (USD MN)", "GPScore"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

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
    gps_filtered = sorted(df["FUND MANAGER"].dropna().unique().tolist())
else:
    gps_filtered = sorted(df[df["ASSET CLASS"] == selected_asset]["FUND MANAGER"].dropna().unique().tolist())

# Manejo de la selección del GP 
if len(gps_filtered) > 0:
    try:
        # Selecciona el GP del ejemplo por defecto
        default_index = gps_filtered.index("1 SEED PARTNERS")
    except ValueError:
        default_index = 0
        
    selected_gp = st.sidebar.selectbox("Seleccionar GP", gps_filtered, index=default_index)
else:
    st.sidebar.info("No hay GPs disponibles para la Asset Class seleccionada.")
    selected_gp = None


# ----------------------------
# FILTRADO FINAL
# ----------------------------
filtered = df.copy()

if selected_asset != "Todos":
    filtered = filtered[filtered["ASSET CLASS"] == selected_asset]

gp_df = pd.DataFrame() # Inicializar como vacío

if selected_gp:
    filtered_gp = filtered[filtered["FUND MANAGER"] == selected_gp]
    gp_df = filtered_gp[filtered_gp["FUND SIZE (USD MN)"] >= min_fund_size].copy()


# ----------------------------
# RESULTADOS
# ----------------------------
st.subheader("Resultados del GP Seleccionado")

if selected_gp and len(gp_df) > 0:
    
    # Cálculos
    num_funds = len(gp_df)
    last_vintage = gp_df["VINTAGE / INCEPTION YEAR"].max()
    
    idx_max_vintage = gp_df["VINTAGE / INCEPTION YEAR"].idxmax()
    last_fund_size = gp_df.loc[idx_max_vintage, "FUND SIZE (USD MN)"]
    
    total_aum_considered = gp_df["FUND SIZE (USD MN)"].sum()
    gp_total_aum = gp_df["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]

    asset_class = gp_df["ASSET CLASS"].iloc[0]
    strategy = gp_df["STRATEGY"].iloc[0]
    region = gp_df["PRIMARY REGION FOCUS"].iloc[0]

    gp_score_raw = gp_df["GPScore"].iloc[0]
    gp_score = f"{gp_score_raw * 100:.2f}%"

    # -------------------------
    # TABLA HTML CORREGIDA: Usando <br> para títulos limpios
    # -------------------------
    html_table = f"""
    <div style="width: 100%;">
    <table style="width: 100%; table-layout: fixed;">
        <thead>
            <tr>
                <th>GP<br>(Fund Manager)</th>
                <th>Asset<br>Class</th>
                <th>Strategy</th>
                <th>Region</th>
                <th>#<br>Funds</th>
                <th>Last<br>Vintage</th>
                <th>Last Fund<br>Size (USDm)</th>
                <th>Total AUM<br>Considerado (USDm)</th>
                <th>GP Total<br>AUM (USDm)</th>
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
                <td>{int(last_vintage)}</td>
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
    st.info("Seleccione un GP para ver el resumen o ajuste los filtros.")


