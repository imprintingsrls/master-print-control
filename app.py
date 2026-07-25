import os
import glob
import pandas as pd

st.sidebar.header("📁 1. Sorgente Dati (Automatica)")

# INSERISCI QUI IL PERCORSO DELLA CARTELLA PRINCIPALE SULL'HARD DISK REMOTO
# Esempio su Mac: "/Volumes/NomeDiscoRemoto/CartellaLog" oppure usa "dati" se vuoi mantenere quella locale
percorso_remoto = "dati" 

tutti_i_dataframe = []

if os.path.exists(percorso_remoto):
    # os.walk attraversa tutte le sottocartelle automaticamente
    for root, dirs, files in os.walk(percorso_remoto):
        for file in files:
            if file.lower().endswith('.csv'):
                file_path = os.path.join(root, file)
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
    st.sidebar.success(f"Caricati {len(tutti_i_dataframe)} file CSV da tutte le sottocartelle!")
else:
    df = pd.DataFrame()