import glob
import pandas as pd
from unidecode import unidecode

# Funzione per caricare tutti i CSV in un unico DataFrame
def load_all_csvs():
    csv_files = glob.glob('meanSkill*.csv')
    data_frames = [pd.read_csv(file) for file in csv_files]
    return pd.concat(data_frames, ignore_index=True)

# Funzione per normalizzare i nomi
def normalize_name(name):
    name = unidecode(name).lower().replace("'", "").strip()
    return name

# Funzione per estrarre la chiave di matching
def get_matching_key(name):
    tokens = name.split()
    parole_da_verificare = ['di', 'de', "del"]

    # Verifica se il primo token è in questa lista
    if len(tokens) > 1 and tokens[0].lower() in parole_da_verificare:
        return ' '.join(tokens[:2])  # Mantiene "Di Lorenzo"
    return tokens[0]  # Usa solo la prima parola

# Carica i dati da tutti i file CSV
df = load_all_csvs()

# Carica i dati dal file Excel
df2 = pd.read_excel('/Quotazioni_Fantacalcio_Stagione_2024_25.xlsx', skiprows=1)

# Normalizza i nomi dei giocatori
df['Nome'] = df['Nome'].apply(normalize_name)
df2['Nome'] = df2['Nome'].apply(normalize_name)

# Crea una colonna per la chiave di matching
df['MatchingKey'] = df['Nome'].apply(get_matching_key)
df2['MatchingKey'] = df2['Nome'].apply(get_matching_key)

# Unisci i DataFrame df e df2 usando la chiave di matching
df = df.merge(df2, on='MatchingKey', how='left', suffixes=('_csv', '_excel'))

# Verifica le righe nel DataFrame finale
print("Righe nel DataFrame finale:", len(df))
print("Prime righe del DataFrame finale:")
print(df.head())

# Rimuovi duplicati
df.drop_duplicates(inplace=True)

df.loc[df['R'].notna() & (df['R'] != ''), 'Ruolo'] = df['R']

def keep_row(group):
    # Verifica se c'è una riga dove Nome_csv è uguale a Nome_excel
    matching_rows = group[group['Nome_csv'] == group['Nome_excel']]
    if not matching_rows.empty:
        return matching_rows.iloc[0]  # Restituisci la prima corrispondenza trovata
    else:
        return group.iloc[0]  # Altrimenti, restituisci la prima riga del gruppo

# Applica la funzione su ogni gruppo di duplicati in Nome_csv
df= df.groupby('Nome_csv').apply(keep_row).reset_index(drop=True)
df.drop_duplicates(inplace=True)
# Salva il DataFrame unito in un nuovo file CSV
df.to_csv('/Users/umbertobertonelli/PycharmProjects/pythonProject4/dati_uniti.csv', index=False)
