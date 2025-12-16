import streamlit as st
import pandas as pd
import numpy as np # Importado para manejo de datos dummy


# --- BLOQUE CSS CORREGIDO ---
st.markdown("""
<style>

/* Fuerza a que el dataframe ocupe todo el ancho disponible */
div[data-testid="stDataFrame"] > div {
    width: 100% !important;
}

/* Centrar tabla */
div[data-testid="stDataFrame"] {
    margin-left: auto !important;
    margin-right: auto !important;
}


/* --- AJUSTES CRUCIALES PARA EL WRAP DE TEXTO Y AJUSTE DE COLUMNAS --- */

/* Elimina el ancho mínimo forzado y permite que el texto se envuelva */
.dataframe th, .dataframe td {
    /* Las siguientes líneas comentadas causaban el scroll horizontal: */
    /* min-width: 150px !important; */
    /* white-space: nowrap !important; */
    
    white-space: normal !important; /* Permite que el texto se envuelva */
    word-break: break-word !important; /* Asegura que las palabras largas se rompan */
    text-align: center !important; /* Mantiene la alineación centrada */
}

/* Header estilizado: Asegura que los encabezados largos también se envuelvan */
.dataframe thead th {
    font-size: 15px !important;
    font-weight: 600 !important;
    text-align: center !important;
    white-space: normal !important; /* Crucial para encabezados largos */
    vertical-align: top !important; /* Alinea los encabezados en la parte superior */
    padding: 8px !important;
}

/* Celdas */
.dataframe tbody td {
    font-size: 14px !important;
    text-align: center !important;
}

/* Opcional: Eliminar el scroll horizontal forzado que ya no será necesario */
div[data-testid="stHorizontalBlock"] {
    overflow-x: hidden !important; 
} 

</style>
""", unsafe_allow_html=True)

st.title("Screening Tool")


# --- Cargar CSV ---
@st.cache_data
def load_data():
    try:
        # Intenta cargar el archivo real
        df = pd.read_csv("DB_FINAL_WITH_SCORES.csv")
    except FileNotFoundError:
        st.warning("Archivo 'DB_FINAL_WITH_SCORES.csv' no encontrado. Usando datos dummy para la demostración.")
        # Datos Dummy para asegurar que el código funcione sin el CSV
        df = pd.DataFrame({
            "FUND MANAGER": ["1 SEED PARTNERS", "1 SEED PARTNERS", "2 VENTURE CAPITAL", "3 INFRA GROUP"],
            "ASSET CLASS": ["Real Estate", "Real Estate", "Private Equity", "Infrastructure"],
            "FUND SIZE (USD MN)": [100, 150, 50, 200],
            "VINTAGE / INCEPTION YEAR": [2010, 2018, 2020, 2015],
            "STRATEGY": ["Real Estate Fund of Funds", "Real Estate Value Add", "Venture Capital Seed", "Infrastructure Core"],
            "PRIMARY REGION FOCUS": ["North America", "North America", "Europe", "Global"],
            "FUND MANAGER TOTAL AUM (USD MN)": [5000, 5000, 2000, 7000],
            "GPScore": [0.85, 0.85, 0.75, 0.90]
        })
        # Aseguramos que los tipos de datos sean numéricos donde se espera
        for col in ["FUND SIZE (USD MN)", "VINTAGE / INCEPTION YEAR", "FUND MANAGER TOTAL AUM (USD MN)", "GPScore"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

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

gps_filtered = sorted(gps_filtered.tolist())


# Manejo de la selección del GP (Aseguramos que haya opciones antes de crear el selectbox)
if len(gps_filtered) > 0:
    # Intenta seleccionar '1 SEED PARTNERS' por defecto si existe, sino, el primero.
    try:
        default_index = gps_filtered.index("1 SEED PARTNERS")
    except ValueError:
        default_index = 0
        
    selected_gp = st.sidebar.selectbox("Seleccionar GP", gps_filtered, index=default_index)
else:
    st.sidebar.info("No hay GPs disponibles para la Asset Class seleccionada.")
    selected_gp = None


# --- Aplicar filtros ---
filtered = df.copy()

if selected_asset != "Todos":
    filtered = filtered[filtered["ASSET CLASS"] == selected_asset]

if selected_gp:
    # Solo se filtra si hay un GP seleccionado
    filtered_gp = filtered[filtered["FUND MANAGER"] == selected_gp]
    # Aplicar el filtro de tamaño de fondo
    gp_df = filtered_gp[filtered_gp["FUND SIZE (USD MN)"] >= min_fund_size].copy() # Usamos .copy() para evitar SettingWithCopyWarning
else:
    gp_df = pd.DataFrame()


# --- Mostrar resultados ---
st.subheader("Resultados del GP Seleccionado")

if selected_gp and len(gp_df) > 0:
    
    # Numero de fondos considerados
    num_funds = len(gp_df)

    # Último vintage
    last_vintage = gp_df["VINTAGE / INCEPTION YEAR"].max()

    # Tamaño del fondo del último vintage (Buscamos la fila del max vintage)
    idx_max_vintage = gp_df["VINTAGE / INCEPTION YEAR"].idxmax()
    last_fund_size = gp_df.loc[idx_max_vintage, "FUND SIZE (USD MN)"]

    # Total AUM considerado
    total_aum_considered = gp_df["FUND SIZE (USD MN)"].sum()

    # AUM total del GP (tomamos el valor de la primera fila, ya que es el mismo para el GP)
    gp_total_aum = gp_df["FUND MANAGER TOTAL AUM (USD MN)"].iloc[0]

    # Asset class y estrategia principal (primera fila del filtrado)
    asset_class = gp_df["ASSET CLASS"].iloc[0]
    strategy = gp_df["STRATEGY"].iloc[0]
    region = gp_df["PRIMARY REGION FOCUS"].iloc[0]

    # Score final del GP (tomamos el valor de la primera fila)
    gp_score_raw = gp_df["GPScore"].iloc[0] if "GPScore" in gp_df.columns else 0.0
    gp_score = f"{gp_score_raw * 100:.2f}%"

    # Construir tabla resumen
    resumen = pd.DataFrame({
        "GP (Fund Manager)": [selected_gp],
        "Asset Class": [asset_class],
        "Strategy": [strategy],
        "Region": [region],
        "# Funds": [num_funds],
        "Last Vintage": [int(last_vintage)] if not pd.isna(last_vintage) else "-",
        # Formatear números grandes para mejor legibilidad
        "Last Fund Size (USDm)": [f"{last_fund_size:,.0f}"],
        "Total AUM Considerado (USDm)": [f"{total_aum_considered:,.0f}"],
        "GP Total AUM (USDm)": [f"{gp_total_aum:,.0f}"],
        "Score": [gp_score]
    })

    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True
    )

elif selected_gp:
    st.info(f"No se encontraron fondos para el GP '{selected_gp}' que cumplan con los filtros de 'Minimum Fund Size' y 'Asset Class'.")
else:
    st.info("Seleccione un GP para ver el resumen.")
