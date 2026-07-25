import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import io

# Configurazione della pagina (ottimizzata anche per mobile)
st.set_page_config(
    page_title="Master Print Control | Industria 4.0",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STILE CSS DEFINITIVO PER LA LEGGIBILITÀ DEI KPI (SFONDO CHIARO E TESTO SCURO) ---
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        border-left: 4px solid #2563eb !important;
    }
    div[data-testid="stMetric"] label {
        color: #4b5563 !important;
        font-size: 14px !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1f2937 !important;
        font-weight: 700 !important;
        font-size: 24px !important;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🖨️ Master Print Control - Industria 4.0 (Enterprise)")
st.markdown("Cruscotto direzionale avanzato per il controllo dei costi, consumi, trend temporali e gestione linee FLORA F1 4T, Papyrus e Liyu.")
st.divider()

# --- LETTURA AUTOMATICA DALLA CARTELLA DATI ---
st.sidebar.header("📁 1. Sorgente Dati (Automatica)")

cartella_dati = "dati"
tutti_i_dataframe = []

if os.path.exists(cartella_dati):
    for file in os.listdir(cartella_dati):
        if file.lower().endswith('.csv'):
            file_path = os.path.join(cartella_dati, file)
            try:
                df_temp = pd.read_csv(file_path, sep=';', encoding='utf-8', on_bad_lines='skip')
                if not df_temp.empty:
                    tutti_i_dataframe.append(df_temp)
            except Exception:
                try:
                    df_temp = pd.read_csv(file_path, sep=',', encoding='utf-8', on_bad_lines='skip')
                    if not df_temp.empty:
                        tutti_i_dataframe.append(df_temp)
                except Exception:
                    continue

if tutti_i_dataframe:
    df = pd.concat(tutti_i_dataframe, ignore_index=True)
    st.sidebar.success(f"Caricati {len(tutti_i_dataframe)} file di log in automatico!")
else:
    df = pd.DataFrame()

if not df.empty:
    # Pulizia e formattazione dati rapida
    if 'AREA_TOTALE_mq' in df.columns:
        df['AREA_TOTALE_mq'] = df['AREA_TOTALE_mq'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    else:
        df['AREA_TOTALE_mq'] = 0.0
        
    if 'COPIE' in df.columns:
        df['COPIE'] = pd.to_numeric(df['COPIE'], errors='coerce').fillna(0)
    else:
        df['COPIE'] = 1
        
    if 'DATA_DI_STAMPA' in df.columns:
        df['DATA_DI_STAMPA'] = pd.to_datetime(df['DATA_DI_STAMPA'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df['ANNO'] = df['DATA_DI_STAMPA'].dt.year
        df['MESE_NUM'] = df['DATA_DI_STAMPA'].dt.month
        
        mesi_it = {1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile', 5: 'Maggio', 6: 'Giugno', 
                   7: 'Luglio', 8: 'Agosto', 9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'}
        df['MESE'] = df['MESE_NUM'].map(mesi_it).fillna('Sconosciuto')
    else:
        df['ANNO'] = 2026
        df['MESE'] = 'Gennaio'
        df['MESE_NUM'] = 1

    if 'STAMPANTE' not in df.columns:
        df['STAMPANTE'] = 'Sconosciuta'
    if 'SUPPORTO' not in df.columns:
        df['SUPPORTO'] = 'Standard'
    if 'LAVORI' not in df.columns:
        df['LAVORI'] = 'Lavoro Senza Nome'

    stampanti_disponibili = list(df['STAMPANTE'].dropna().unique())
    
    flora_nome = "FLORA F1 4T [ID 4.0]"
    if flora_nome not in stampanti_disponibili:
        stampanti_disponibili.append(flora_nome)
        
    liyu_nome = "Liyu [ID 4.0]"
    if liyu_nome not in stampanti_disponibili:
        stampanti_disponibili.append(liyu_nome)

    # Sidebar: Listini personalizzati per stampante
    st.sidebar.divider()
    st.sidebar.header("⚙️ 2. Listini & Parametri 4.0")
    
    costi_config = {}
    for stampante in stampanti_disponibili:
        nome_str = str(stampante).lower()
        
        if 'flora' in nome_str:
            ink_default = 40.0
            badge_40 = " [⚡ Industria 4.0]"
        elif 'papyrus' in nome_str or 'liyu' in nome_str:
            ink_default = 24.0
            badge_40 = " [⚡ Industria 4.0]"
        else:
            ink_default = 55.0
            badge_40 = ""
            
        with st.sidebar.expander(f"🖨️ {stampante}{badge_40}", expanded=False):
            costo_inchiostro = st.number_input(f"Inchiostro (€/Litro)", min_value=0.0, value=ink_default, step=1.0, key=f"ink_{stampante}")
            
            ml_default = 10.0 if 'flora' in nome_str else 12.0
            consumo_ml_mq = st.number_input(f"Consumo (ml/mq)", min_value=0.0, value=ml_default, step=1.0, key=f"ml_{stampante}")
            
            if 'flora' in nome_str:
                supporti_stampante = ['Carta Blue Back']
                st.sidebar.caption("📏 Bobina: 1.45 x 250 mt (362.5 mq)")
            elif 'papyrus' in nome_str or 'liyu' in nome_str:
                supporti_stampante = ['Carta Blue Back', 'Standard']
                st.sidebar.caption("📏 Bobina standard Blue Back")
            else:
                supporti_stampante = df[df['STAMPANTE'] == stampante]['SUPPORTO'].dropna().unique()
                if len(supporti_stampante) == 0:
                    supporti_stampante = ['Carta Blue Back', 'Standard']
                    
            costi_supporti = {}
            for supp in supporti_stampante:
                supp_str = str(supp).lower()
                if 'blue back' in supp_str or 'blueback' in supp_str:
                    default_cost = 1.80
                elif 'vinile' in supp_str or 'adesivo' in supp_str:
                    default_cost = 3.50
                else:
                    default_cost = 2.00
                    
                c_supp = st.number_input(f"Costo mq [{supp}]", min_value=0.0, value=default_cost, step=0.1, key=f"supp_{stampante}_{supp}")
                costi_supporti[supp] = c_supp
                
            costi_config[stampante] = {
                'inchiostro': costo_inchiostro,
                'consumo_ml': consumo_ml_mq,
                'supporti': costi_supporti
            }

    # Sidebar: Contatori Bobine
    st.sidebar.divider()
    st.sidebar.header("📦 Contatore Bobine / Rotoli")
    
    mq_flora_tot = df[df['STAMPANTE'].str.contains('Flora|F1', case=False, na=False)]['AREA_TOTALE_mq'].sum()
    rotoli_flora = mq_flora_tot / 362.5 if 362.5 > 0 else 0
    st.sidebar.markdown(f"**FLORA F1 4T [4.0]**")
    st.sidebar.caption(f"Totale stampato: **{mq_flora_tot:,.1f} mq** (~{rotoli_flora:.2f} rotoli da 250mt)")

    mq_papyrus_tot = df[df['STAMPANTE'].str.contains('Papyrus', case=False, na=False)]['AREA_TOTALE_mq'].sum()
    rotoli_papyrus = mq_papyrus_tot / 240.0 if 240.0 > 0 else 0
    st.sidebar.markdown(f"**Papyrus [4.0]**")
    st.sidebar.caption(f"Totale stampato: **{mq_papyrus_tot:,.1f} mq** (~{rotoli_papyrus:.2f} rotoli stimati)")

    mq_liyu_tot = df[df['STAMPANTE'].str.contains('Liyu', case=False, na=False)]['AREA_TOTALE_mq'].sum()
    rotoli_liyu = mq_liyu_tot / 240.0 if 240.0 > 0 else 0
    st.sidebar.markdown(f"**Liyu [4.0]**")
    st.sidebar.caption(f"Totale stampato: **{mq_liyu_tot:,.1f} mq** (~{rotoli_liyu:.2f} rotoli stimati)")

    # Sidebar: Filtri Globali Dashboard
    st.sidebar.divider()
    st.sidebar.header("🔍 3. Filtri Globali Dashboard")
    
    if 'ANNO' in df.columns:
        anni_disp = sorted(df['ANNO'].dropna().unique().tolist())
        anni_scelti = st.sidebar.multiselect("Filtra Anno", options=anni_disp, default=anni_disp)
        if anni_scelti:
            df = df[df['ANNO'].isin(anni_scelti)]

    stampante_selezionata = st.sidebar.multiselect("Filtra Stampanti", options=stampanti_disponibili, default=stampanti_disponibili)

    if 'STATO' in df.columns:
        stati_disponibili = df['STATO'].dropna().unique()
        stato_selezionato = st.sidebar.multiselect("Filtra Stato Lavori", options=stati_disponibili, default=stati_disponibili)
        if stato_selezionato:
            df = df[df['STATO'].isin(stato_selezionato)]

    # --- CALCOLO VETTORIZZATO ---
    ink_dict = {stp: cfg['inchiostro'] for stp, cfg in costi_config.items()}
    ml_dict = {stp: cfg['consumo_ml'] for stp, cfg in costi_config.items()}
    
    costi_carta_dict = {}
    for stp, cfg in costi_config.items():
        for supp, costo in cfg['supporti'].items():
            costi_carta_dict[(stp, supp)] = costo

    df['Inchiostro_Litro'] = df['STAMPANTE'].map(ink_dict).fillna(40.0)
    df['Consumo_ml_mq'] = df['STAMPANTE'].map(ml_dict).fillna(10.0)
    
    df['Costo_Mq_Carta'] = pd.MultiIndex.from_arrays([df['STAMPANTE'], df['SUPPORTO']]).map(costi_carta_dict).fillna(1.80)

    df['Costo_Carta_Totale'] = df['AREA_TOTALE_mq'] * df['Costo_Mq_Carta']
    df['Inchiostro_Stimato_ml'] = df['AREA_TOTALE_mq'] * df['Consumo_ml_mq']
    df['Costo_Inchiostro_Totale'] = (df['Inchiostro_Stimato_ml'] / 1000.0) * df['Inchiostro_Litro']
    df['Costo_Produzione_Totale'] = df['Costo_Carta_Totale'] + df['Costo_Inchiostro_Totale']

    if stampante_selezionata:
        df = df[df['STAMPANTE'].isin(stampante_selezionata)]

    # --- KPI GLOBALI IN ALTO (Responsive per Mobile) ---
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Lavori Totali", f"{len(df):,}")
    c2.metric("Superficie", f"{df['AREA_TOTALE_mq'].sum():,.1f} mq")
    c3.metric("Spesa Supporti", f"€ {df['Costo_Carta_Totale'].sum():,.2f}")
    c4.metric("Spesa Inchiostri", f"€ {df['Costo_Inchiostro_Totale'].sum():,.2f}")
    c5.metric("Costo Industriale", f"€ {df['Costo_Produzione_Totale'].sum():,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SCHEDE (TABS) ---
    tab_panoramica, tab_ispezione, tab_registro = st.tabs([
        "📊 Panoramica & Analisi", 
        "🔎 Ispezione Singolo Lavoro", 
        "📋 Registro & Export"
    ])

    with tab_panoramica:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_costi = px.bar(df, x='STAMPANTE', y='Costo_Produzione_Totale', color='STAMPANTE', title="Costo di Produzione per Macchina (€)", text_auto='.2f')
            st.plotly_chart(fig_costi, use_container_width=True)
        with col_g2:
            fig_sup = px.pie(df, names='SUPPORTO', values='AREA_TOTALE_mq', hole=0.4, title="Ripartizione Superficie per Supporto")
            st.plotly_chart(fig_sup, use_container_width=True)

        st.divider()
        st.subheader("📈 Trend Temporale della Produzione (Mq per Mese)")
        if not df.empty and 'DATA_DI_STAMPA' in df.columns:
            df_trend = df.groupby(['ANNO', 'MESE_NUM', 'MESE'], as_index=False)['AREA_TOTALE_mq'].sum().sort_values(['ANNO', 'MESE_NUM'])
            if not df_trend.empty:
                fig_trend = px.line(df_trend, x='MESE', y='AREA_TOTALE_mq', color='ANNO', markers=True, title="Andamento Mensile Metri Quadri Stampati", labels={'MESE': 'Mese', 'AREA_TOTALE_mq': 'Superficie Totale (mq)'})
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Dati temporali insufficienti per generare il trend mensile.")

    with tab_ispezione:
        st.subheader("🔎 Ricerca Avanzata Lavoro (Macchina, Calendario e Testo)")
        
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            macchine_isp = st.multiselect("Seleziona Macchina/e da ispezionare:", options=stampanti_disponibili, default=stampanti_disponibili, key="isp_macchina")
        with col_i2:
            min_d = df['DATA_DI_STAMPA'].min().date() if not df['DATA_DI_STAMPA'].isna().all() else datetime.now().date()
            max_d = df['DATA_DI_STAMPA'].max().date() if not df['DATA_DI_STAMPA'].isna().all() else datetime.now().date()
            
            if 'isp_date_val' not in st.session_state:
                st.session_state.isp_date_val = (min_d, max_d)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("📅 Seleziona Oggi"):
                    oggi = datetime.now().date()
                    if min_d <= oggi <= max_d:
                        st.session_state.isp_date_val = oggi
                    else:
                        st.session_state.isp_date_val = max_d
                    st.rerun()
            with col_b2:
                if st.button("🔄 Intervallo Totale"):
                    st.session_state.isp_date_val = (min_d, max_d)
                    st.rerun()

            intervallo_date = st.date_input(
                "Seleziona il Giorno, Mese, Anno o l'Intervallo:",
                value=st.session_state.isp_date_val,
                min_value=min_d,
                max_value=max_d,
                format="DD/MM/YYYY",
                key="isp_calendar"
            )

        testo_cerca = st.text_input("🔍 Cerca per nome file / lavoro (parola chiave):", value="", key="isp_testo")

        df_isp = df[df['STAMPANTE'].isin(macchine_isp)]
        
        if isinstance(intervallo_date, tuple) and len(intervallo_date) == 2:
            start_d, end_d = intervallo_date
            df_isp = df_isp[
                (df_isp['DATA_DI_STAMPA'].dt.date >= start_d) & 
                (df_isp['DATA_DI_STAMPA'].dt.date <= end_d)
            ]
        elif hasattr(intervallo_date, 'year'):
            df_isp = df_isp[df_isp['DATA_DI_STAMPA'].dt.date == intervallo_date]

        if testo_cerca.strip():
            df_isp = df_isp[df_isp['LAVORI'].astype(str).str.contains(testo_cerca, case=False, na=False)]

        st.markdown("---")
        st.markdown("##### 📌 Totali del Periodo / Filtro Selezionato")
        ic1, ic2, ic3, ic4, ic5 = st.columns(5)
        ic1.metric("Lavori Filtrati", f"{len(df_isp):,}")
        ic2.metric("Superficie Filtrata", f"{df_isp['AREA_TOTALE_mq'].sum():,.1f} mq")
        ic3.metric("Spesa Supporti", f"€ {df_isp['Costo_Carta_Totale'].sum():,.2f}")
        ic4.metric("Spesa Inchiostri", f"€ {df_isp['Costo_Inchiostro_Totale'].sum():,.2f}")
        ic5.metric("Costo Industriale", f"€ {df_isp['Costo_Produzione_Totale'].sum():,.2f}")
        st.markdown("---")

        lista_lavori_isp = df_isp['LAVORI'].dropna().unique().tolist()
        lavoro_cercato = st.selectbox("Seleziona il lavoro specifico tra quelli filtrati:", options=["-- Seleziona --"] + lista_lavori_isp, key="isp_lavoro_select")
        
        if lavoro_cercato != "-- Seleziona --":
            dettaglio_lavoro = df_isp[df_isp['LAVORI'] == lavoro_cercato]
            for idx, row in dettaglio_lavoro.iterrows():
                st.info(f"Dettagli tecnici per il lavoro: **{row.get('LAVORI')}**")
                d1, d2, d3, d4, d5, d6 = st.columns(6)
                d1.metric("Data", str(row.get('DATA_DI_STAMPA', 'N/D'))[:16])
                d2.metric("Stampante", str(row.get('STAMPANTE', 'N/D')))
                d3.metric("Supporto", str(row.get('SUPPORTO', 'N/D')))
                d4.metric("Mq", f"{row.get('AREA_TOTALE_mq', 0):,.2f}")
                d5.metric("Inchiostro", f"€ {row.get('Costo_Inchiostro_Totale', 0):,.2f}", help=f"{row.get('Inchiostro_Stimato_ml', 0):.1f} ml")
                d6.metric("Totale Job", f"€ {row.get('Costo_Produzione_Totale', 0):,.2f}")

    with tab_registro:
        colonne_mostrate = [c for c in ['DATA_DI_STAMPA', 'STAMPANTE', 'LAVORI', 'SUPPORTO', 'AREA_TOTALE_mq', 'Costo_Carta_Totale', 'Costo_Inchiostro_Totale', 'Costo_Produzione_Totale', 'STATO'] if c in df.columns]
        st.dataframe(df[colonne_mostrate], use_container_width=True)
        
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            csv_data = df[colonne_mostrate].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Scarica report in formato CSV",
                data=csv_data,
                file_name="report_produzione.csv",
                mime="text/csv",
            )
        with col_down2:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df[colonne_mostrate].to_excel(writer, index=False, sheet_name='Produzione')
            excel_data = output_excel.getvalue()
            
            st.download_button(
                label="📊 Scarica report professionale in Excel (.xlsx)",
                data=excel_data,
                file_name="report_produzione.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
else:
    st.warning("⚠️ Nessun file trovato nella cartella dati locale. Esegui la sincronizzazione dal NAS.")

# --- FOOTER & COPYRIGHT ---
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; color: #6b7280; font-size: 12px;'>"
    "© 2026 <b>G. Ferrante</b><br>Tutti i diritti riservati."
    "</div>",
    unsafe_allow_html=True
)