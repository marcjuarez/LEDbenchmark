import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="LED Roadmap Pro", layout="wide")
DB_FILE = "led_database.csv"

# --- CONSTANTES ---
EU_COUNTRIES = ["Spain", "Germany", "France", "Italy", "United Kingdom", "Netherlands", "Poland", "Sweden"]
BRAND_COLORS = {
    "Seoul Semi": "#339933", "CREE": "#005596", "Nichia": "#003366",
    "Osram": "#FF6600", "Samsung": "#034EA2", "Lumileds": "#FFB81C",
    "Bridgelux": "#E31D2B", "Everlight": "#009DDC", "Other...": "#808080"
}

# --- FUNCIONES DE APOYO ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                df = df.dropna(subset=["Date"])
            return df
        except Exception as e:
            st.error(f"Error al leer el CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame(columns=[
        "Date", "Entered By", "Country", "Manufacturer", "Part Number", "Package", 
        "Phosphor Tech", "CCT (K)", "CRI", "Flux Bin", "Lumen Typ", "Vf Bin", 
        "Vf Typ", "Current (mA)", "Temp (°C)", "Price (€)", "lm/W", "€/klm"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def get_options(df, column, defaults):
    existing = df[column].unique().astype(str).tolist() if not df.empty else []
    if column == "Phosphor Tech": existing = [x for x in existing if x != "4000"]
    combined = sorted(list(set(defaults + existing)))
    return combined + ["Other..."]

# --- CARGA INICIAL ---
df = load_data()

# --- CABECERA ---
st.title("💡 LED Benchmark: Roadmap & Analytics (€)")

# --- BARRA LATERAL: REGISTRO ---
with st.sidebar:
    st.header("👤 Analista y Región")
    user_name = st.text_input("Nombre de la persona", placeholder="Ej. Juan Pérez")
    
    country_opts = get_options(df, "Country", EU_COUNTRIES)
    sel_country = st.selectbox("País", country_opts)
    final_country = st.text_input("¿Cuál?") if sel_country == "Other..." else sel_country

    st.divider()
    st.header("📥 Registro de Componente")
    
    selected_mfr = st.selectbox("Fabricante", get_options(df, "Manufacturer", [k for k in BRAND_COLORS.keys() if k != "Other..."]))
    final_mfr = st.text_input("Marca") if selected_mfr == "Other..." else selected_mfr

    st.divider()

    existing_pns = sorted(df[df["Manufacturer"] == final_mfr]["Part Number"].unique().tolist()) if not df.empty else []
    pn_selection = st.selectbox("Producto (PN)", ["+ Añadir Nuevo PN"] + existing_pns)
    
    d_pn, d_pkg, d_phos, d_cct, d_cri = "", "3030", "YAG traditional", 4000, 80
    if pn_selection != "+ Añadir Nuevo PN":
        last_info = df[df["Part Number"] == pn_selection].iloc[-1]
        d_pn, d_pkg, d_phos, d_cct, d_cri = pn_selection, str(last_info["Package"]), str(last_info.get("Phosphor Tech", "YAG traditional")), int(last_info["CCT (K)"]), int(last_info["CRI"])
        st.success(f"Cargado: {pn_selection}")

    pn = st.text_input("Número de Parte", value=d_pn) if pn_selection == "+ Añadir Nuevo PN" else d_pn

    pkg_options = get_options(df, "Package", ["3528", "3030", "5050", "3535", "COB"])
    sel_pkg = st.selectbox("Package", pkg_options, index=pkg_options.index(d_pkg) if d_pkg in pkg_options else 0)
    final_pkg = st.text_input("¿Package?") if sel_pkg == "Other..." else sel_pkg

    phos_options = get_options(df, "Phosphor Tech", ["YAG traditional", "NPR/KSF", "660nm", "730nm"])
    sel_phos = st.selectbox("Tecnología", phos_options, index=phos_options.index(d_phos) if d_phos in phos_options else 0)
    final_phos = st.text_input("¿Tecnología?") if sel_phos == "Other..." else sel_phos

    col_cct, col_cri = st.columns(2)
    cct = col_cct.number_input("CCT (K)", min_value=0, value=d_cct, step=100)
    cri = col_cri.number_input("CRI", min_value=0, value=d_cri, step=1)

    st.divider()
    st.markdown("**Valores de Test**")
    b1, b2 = st.columns(2)
    bin_lm = b1.text_input("Flux Bin")
    bin_vf = b2.text_input("Vf Bin")

    v1, v2 = st.columns(2)
    val_lm = v1.number_input("Lúmenes (lm)", min_value=0.01, step=0.1)
    val_vf = v2.number_input("Vf Típ. (V)", min_value=0.01, step=0.01)
    current_ma = st.number_input("mA", min_value=1, value=65) # Estándar 65mA
    temp = st.radio("Temp. Test (°C)", [25, 85], index=0, horizontal=True) # Estándar 25°C
    
    st.divider()
    st.markdown("**Precio**")
    price_eur = st.number_input("Precio (€)", min_value=0.01, step=0.01, format="%.2f")
    test_date = st.date_input("Fecha del Test", datetime.now())

    if st.button("🚀 Registrar Entrada", use_container_width=True):
        if not pn or not user_name:
            st.error("Persona y PN obligatorios.")
        else:
            full_datetime = datetime.combine(test_date, datetime.now().time())
            power = val_vf * (current_ma / 1000)
            lm_per_w = val_lm / power if power > 0 else 0
            eur_per_klm = (price_eur / val_lm) * 1000
            
            new_entry = {
                "Date": full_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "Entered By": user_name, "Country": final_country,
                "Manufacturer": final_mfr, "Part Number": pn, "Package": final_pkg,
                "Phosphor Tech": final_phos, "CCT (K)": cct, "CRI": cri, 
                "Flux Bin": bin_lm, "Lumen Typ": val_lm, "Vf Bin": bin_vf, 
                "Vf Typ": val_vf, "Current (mA)": current_ma, "Temp (°C)": temp, 
                "Price (€)": round(price_eur, 2), "lm/W": round(lm_per_w, 2), 
                "€/klm": round(eur_per_klm, 4)
            }
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)
            st.success("¡Registrado!")
            st.rerun()

# --- PANEL PRINCIPAL ---
if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📊 Mapa de Mercado", "📈 Evolución", "📋 Historial Completo"])

    with tab1:
        st.subheader("Filtros de Búsqueda Avanzada")
        
        # FILTROS RESTAURADOS - FILA 1
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        f_mfr = r1c1.multiselect("Marca", sorted(df["Manufacturer"].unique()), df["Manufacturer"].unique())
        f_pkg = r1c2.multiselect("Package", sorted(df["Package"].unique()), df["Package"].unique())
        f_phos = r1c3.multiselect("Tecnología", sorted(df["Phosphor Tech"].unique()), df["Phosphor Tech"].unique())
        f_country = r1c4.multiselect("País", sorted(df["Country"].unique()), df["Country"].unique())

        # FILTROS RESTAURADOS - FILA 2
        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        f_cct = r2c1.multiselect("CCT (K)", sorted(df["CCT (K)"].unique()), df["CCT (K)"].unique())
        f_cri = r2c2.multiselect("CRI", sorted(df["CRI"].unique()), df["CRI"].unique())
        f_ma = r2c3.multiselect("mA", sorted(df["Current (mA)"].unique()), df["Current (mA)"].unique())
        f_temp = r2c4.multiselect("Temperatura (°C)", sorted(df["Temp (°C)"].unique()), df["Temp (°C)"].unique())

        filtered_df = df[
            (df["Manufacturer"].isin(f_mfr)) & (df["Package"].isin(f_pkg)) &
            (df["Phosphor Tech"].isin(f_phos)) & (df["Country"].isin(f_country)) &
            (df["CCT (K)"].isin(f_cct)) & (df["CRI"].isin(f_cri)) &
            (df["Current (mA)"].isin(f_ma)) & (df["Temp (°C)"].isin(f_temp))
        ]

        if not filtered_df.empty:
            plot_df = filtered_df
            fig = px.scatter(
                plot_df, x="Price (€)", y="lm/W", color="Manufacturer",
                color_discrete_map=BRAND_COLORS, size="Lumen Typ",
                text="Part Number", 
                hover_data=["Date", "€/klm", "Flux Bin", "Vf Bin", "Entered By"],
                height=750,
                title="Mapa de Rendimiento (Todos los registros)"
            )
            max_p = plot_df["Price (€)"].max() if not plot_df.empty else 1
            fig.update_xaxes(range=[0, max_p * 1.15], title_text="Precio (€)")
            fig.update_yaxes(rangemode="tozero", title_text="Eficacia (lm/W)")
            fig.update_traces(textposition='top right', marker=dict(sizeref=2.5, sizemode='area', line=dict(width=0.5, color='white')))
            fig.update_layout(margin=dict(r=150))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos que coincidan con estos filtros.")

    with tab2:
        st.subheader("Análisis de Evolución con Tendencia")
        c_sel1, c_sel2, c_sel3 = st.columns(3)
        with c_sel1:
            sel_mfr_evol = st.selectbox("1. Fabricante:", sorted(df["Manufacturer"].unique()))
        with c_sel2:
            pns_in_mfr = sorted(df[df["Manufacturer"] == sel_mfr_evol]["Part Number"].unique())
            sel_pn_evol = st.selectbox("2. Producto:", pns_in_mfr)
        with c_sel3:
            countries_in_pn = sorted(df[(df["Manufacturer"] == sel_mfr_evol) & (df["Part Number"] == sel_pn_evol)]["Country"].unique())
            sel_country_evol = st.selectbox("3. País:", ["Todos"] + countries_in_pn)
        
        # Lógica de filtrado
        if sel_country_evol == "Todos":
            h_df = df[(df["Manufacturer"] == sel_mfr_evol) & (df["Part Number"] == sel_pn_evol)].sort_values("Date")
            color_param = "Country"
        else:
            h_df = df[(df["Country"] == sel_country_evol) & (df["Part Number"] == sel_pn_evol)].sort_values("Date")
            color_param = None
        
        if len(h_df) >= 2:
            c1, c2 = st.columns(2)
            fig_eff = px.scatter(h_df, x="Date", y="lm/W", color=color_param, trendline="ols", title=f"Tendencia Eficacia: {sel_pn_evol}")
            c1.plotly_chart(fig_eff, use_container_width=True)
            fig_cost = px.scatter(h_df, x="Date", y="€/klm", color=color_param, trendline="ols", title=f"Tendencia Coste: {sel_pn_evol}")
            c2.plotly_chart(fig_cost, use_container_width=True)
        else:
            st.info("Necesitas al menos 2 registros para calcular líneas de tendencia.")

    with tab3:
        st.subheader("Base de Datos Histórica")
        st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True, height=850)
        st.download_button("📂 Descargar CSV", df.to_csv(index=False), "led_benchmark_full.csv")
else:
    st.info("La base de datos está vacía.")