import streamlit as st
import pandas as pd

st.title("Preqin Screening Tool – Panel")

# --- Cargar CSV ---
@st.cache_data
def load_data():
    return pd.read_csv("DB_FINAL_WITH_SCORES.csv")

df = load_data()

# --- Filtros ---
st.sidebar.header("Filtros")

expand_vintage = st.sidebar.number_input("Expand Vintage (yrs)", 1, 20, 1)
min_fund_size = st.sidebar.number_input("Minimum Fund Size (USDm)", 0, 5000, 2)
current_year = st.sidebar.number_input("Año Actual", 1990, 2030, 2025)

asset_classes = sorted(df["ASSET CLASS"].dropna().unique())
selected_asset = st.sidebar.selectbox("Asset Class", ["Todos"] + asset_classes)

gps = sorted(df["FUND MANAGER"].dropna().unique())
selected_gp = st.sidebar.selectbox("Seleccionar GP", ["Todos"] + gps)

# --- Aplicar filtros ---
filtered = df.copy()

if selected_asset != "Todos":
    filtered = filtered[filtered["ASSET CLASS"] == selected_asset]

if selected_gp != "Todos":
    filtered = filtered[filtered["FUND MANAGER"] == selected_gp]

filtered = filtered[filtered["FUND SIZE (USD MN)"] >= min_fund_size]

# --- Mostrar resultados ---
st.subheader("Resultados del GP Seleccionado")
st.dataframe(filtered)

