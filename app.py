import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from statistics import mean

st.set_page_config(layout="wide")

# Carica i dati dal CSV
df = pd.read_csv('/Users/umbertobertonelli/PycharmProjects/pythonProject4/dati_uniti.csv')
df=df[df['Ruolo']!='Ruolo']
df['Punteggio FantaCalcioPedia'] = pd.to_numeric(df['Punteggio FantaCalcioPedia'], errors='coerce')
df['Solidità fantainvestimento'] = pd.to_numeric(df['Solidità fantainvestimento'], errors='coerce')
df['Resistenza infortuni'] = pd.to_numeric(df['Resistenza infortuni'], errors='coerce')

df = df.rename(columns={"Squadra_csv": "Squadra"})
df = df.rename(columns={"Nome_csv": "Nome"})
# Calcoliamo la mediana della colonna 'Qt.A'
# Funzione per sostituire NaN con la mediana filtrata per ruolo
def sostituisci_nan_per_ruolo(df, colonna, colonna_ruolo):
    # Trova i ruoli unici
    ruoli = df[colonna_ruolo].unique()

    for ruolo in ruoli:
        # Filtra i dati per il ruolo corrente
        filtro = df[colonna_ruolo] == ruolo
        mediana = df.loc[filtro, colonna].median()

        # Sostituisci i valori NaN per quel ruolo
        df.loc[filtro & df[colonna].isna(), colonna] = mediana


# Applichiamo la funzione al nostro DataFrame
sostituisci_nan_per_ruolo(df, 'Qt.A', 'Ruolo')
columns_to_combine = [
    "Ultimi Arrivi", "In Crescita", "Rischiosi", "Fuoriclasse", "Outsider",
    "Titolari", "Economici", "Giovani", "Infortunati", "Buona Media",
    "Goleador", "Assistman", "Rigorista", "Sp. Piazzati"
]
df["Attributi"] = df[columns_to_combine].apply(
    lambda row: '-'.join(filter(None, [str(x) for x in row if pd.notna(x)])), axis=1)

# Funzione per estrarre il numero1
def estrai_numero1(val):
    if isinstance(val, str):
        # Se la stringa contiene una '/', prendi la parte prima della '/'
        if '/' in val:
            return int(val.split('/')[0])
        # Se la stringa contiene un '+', prendi la parte dopo il '+'
        elif '+' in val:
            return int(val.replace('+', ''))
        # Tenta di convertire la stringa in un intero, se possibile
        else:
            try:
                return int(val)
            except ValueError:
                # Se la conversione fallisce, restituisci None o un valore di default
                return None
    # Se il valore non è una stringa, restituiscilo così com'è
    return val

# Applicare la funzione alle colonne interessate
df["Gol previsti"] = df["Gol previsti"].apply(estrai_numero1)
df["Presenze previste"] = df["Presenze previste"].apply(estrai_numero1)
df["Assist previsti"] = df["Assist previsti"].apply(estrai_numero1)
df.loc[df['Ruolo'] == 'P', 'Gol previsti'] *= -1




# Crea una lista dei ruoli
ruolo_list = df['Ruolo'].unique().tolist()


# Titolo dell'applicazione
st.title('Fanta 24-25')

budget = st.number_input("Budget della lega", value=500)
df['Prezzo'] = round((df['Punteggio FantaCalcioPedia'].max() / (budget / 25) *
                                      df["Punteggio FantaCalcioPedia"] *
                                      (df['Solidità fantainvestimento'] / 100) *
                                      (df['Resistenza infortuni'] / 100)) * (
                                                 df["Qt.A"] / df["Qt.A"].max()))



# Percorsi dei file CSV
csv_fasce_file = 'fasce_prezzo.csv'
csv_assegnazioni_file = 'assegnazioni_giocatori.csv'

# Funzioni per caricare le fasce e le assegnazioni dal CSV
def carica_fasce_da_csv():
    if os.path.exists(csv_fasce_file):
        df_fasce = pd.read_csv(csv_fasce_file)
        return df_fasce['Fascia'].tolist() if 'Fascia' in df_fasce.columns else []
    return []

def carica_assegnazioni_da_csv():
    if os.path.exists(csv_assegnazioni_file):
        df_assegnazioni = pd.read_csv(csv_assegnazioni_file)
        if 'Fascia' in df_assegnazioni.columns and 'Giocatori' in df_assegnazioni.columns:
            assegnazioni = {}
            for _, row in df_assegnazioni.iterrows():
                # Converti i valori in stringa e gestisci i NaN
                giocatori = str(row['Giocatori']) if pd.notna(row['Giocatori']) else ''
                assegnazioni[row['Fascia']] = giocatori.split(';')
            return assegnazioni
    return {}

# Carica fasce e assegnazioni dal CSV
fasce_predefinite = carica_fasce_da_csv()
assegnazioni_predefinite = carica_assegnazioni_da_csv()

# Imposta le fasce e le assegnazioni predefinite se disponibili
if fasce_predefinite:
    st.session_state.fasce = fasce_predefinite
if assegnazioni_predefinite:
    st.session_state.assegnazioni = assegnazioni_predefinite

# Sezione per definire o modificare le fasce di prezzo
with st.expander("Definisci o Modifica le Fasce di Prezzo"):
    st.header("Definisci le fasce di prezzo")

    num_fasce = st.number_input("Numero di fasce", min_value=1, max_value=10, value=len(fasce_predefinite) or 3)
    fasce = [st.text_input(f"Inserisci il nome della fascia {i + 1}",
                           value=fasce_predefinite[i] if i < len(fasce_predefinite) else "", key=f"fascia_{i}")
             for i in range(num_fasce)]

    st.write("Fasce definite:")
    for i, fascia in enumerate(fasce):
        st.write(f"{i + 1}. {fascia}")

    if st.button("Salva Fasce"):
        st.session_state.fasce = fasce
        df_fasce = pd.DataFrame(fasce, columns=['Fascia'])
        df_fasce.to_csv(csv_fasce_file, index=False)
        st.success("Fasce salvate con successo!")

# Sezione per visualizzare giocatori per ruolo
if not df.empty:
    # Ottieni la lista unica degli attributi
    attributi_unici = list(set('-'.join(df['Attributi'].dropna().astype(str)).split('-')))
    attributi_unici.sort()

    # Intestazione della sezione
    st.header("Griglia Calciatori")

    with st.expander("Apri per vedere la griglia"):
        # Filtri per attributi
        attributi_selezionati = st.multiselect(
            "Filtra per attributi",
            options=attributi_unici,
            default=attributi_unici,
            key="attributi_filtri"  # Chiave unica per attributi
        )

        ruoli_selezionati = st.multiselect(
            "Filtra per ruolo",
            options=ruolo_list,
            default=ruolo_list,
            key="ruoli_filtri"  # Chiave unica per ruoli
        )

        # Filtra il DataFrame in base agli attributi selezionati
        if attributi_selezionati:
            df_filtrato = df[
                df['Attributi'].apply(lambda x: any(attr in attributi_selezionati for attr in str(x).split('-')))
            ]
        else:
            df_filtrato = df.copy()

        # Filtra il DataFrame in base ai ruoli selezionati
        if ruoli_selezionati:
            df_filtrato = df_filtrato[
                df_filtrato['Ruolo'].isin(ruoli_selezionati)
            ]

        # Filtri per squadra
        squadra_selezionata = st.selectbox(
            "Filtra per squadra",
            options=['Tutti'] + list(df_filtrato['Squadra'].unique()),
            key="squadra_filtri"  # Chiave unica per squadra
        )

        if squadra_selezionata != 'Tutti':
            df_filtrato = df_filtrato[df_filtrato['Squadra'] == squadra_selezionata]

        # Opzioni di ordinamento
        ordinamento = st.selectbox(
            "Ordina per",
            options=[
                "Punteggio FantaCalcioPedia (Ascendente)",
                "Punteggio FantaCalcioPedia (Discendente)",
                "Prezzo (Ascendente)",
                "Prezzo (Discendente)"
            ],
            key="ordinamento_filtri"  # Chiave unica per ordinamento
        )

        if ordinamento == "Punteggio FantaCalcioPedia (Ascendente)":
            df_filtrato = df_filtrato.sort_values("Punteggio FantaCalcioPedia")
        elif ordinamento == "Punteggio FantaCalcioPedia (Discendente)":
            df_filtrato = df_filtrato.sort_values("Punteggio FantaCalcioPedia", ascending=False)
        elif ordinamento == "Prezzo (Ascendente)":
            df_filtrato = df_filtrato.sort_values("Prezzo")
        elif ordinamento == "Prezzo (Discendente)":
            df_filtrato = df_filtrato.sort_values("Prezzo", ascending=False)

        # Mostra il DataFrame filtrato e ordinato
        st.dataframe(df_filtrato[["Nome", "Squadra", "Ruolo", "ALG FCP", "Punteggio FantaCalcioPedia",
                                  "Solidità fantainvestimento", "Resistenza infortuni", "Qt.A", "Attributi",
                                  "Gol previsti", "Presenze previste", "Assist previsti", "Prezzo"]])
else:
    st.warning("Nessun dato disponibile per la visualizzazione.")

# Carica i dati dei calciatori


st.header('Gestione Fasce')
with st.expander("Seleziona i calciatori e imposta la fascia"):
    st.subheader('Seleziona i calciatori e imposta la fascia')

    fasce_df = df.copy()
    fasce_df['fasce'] = None

    # Selezione dei calciatori disponibili
    giocatori_fasce_disponibili = fasce_df[fasce_df['fasce'].isna()]['Nome'].tolist()
    calciatori_fasce_selezionati = st.multiselect('Seleziona i calciatori da assegnare alle fasce', giocatori_fasce_disponibili)

    fasce_selezionate = {}

    if calciatori_fasce_selezionati:
        for calciatore in calciatori_fasce_selezionati:
            col1, col2 = st.columns(2)

            with col1:
                # Imposta la fascia per il calciatore
                fascia = st.selectbox(f'Fascia di {calciatore}', options=fasce)
                fasce_selezionate[calciatore] = fascia

    # Bottone per salvare le informazioni
    if st.button('Salva Selezione Fasce'):
        if fasce_selezionate:
            # Crea un DataFrame con le informazioni dei calciatori e le loro fasce
            fasce_df_selezionati = pd.DataFrame(list(fasce_selezionate.items()), columns=['Nome', 'Fascia'])

            # Controlla se il file CSV esiste già
            if os.path.exists('fasce_calciatori.csv'):
                # Leggi il CSV esistente
                fasce_df_esistente = pd.read_csv('fasce_calciatori.csv')

                # Aggiorna le righe esistenti o aggiungi nuove righe
                fasce_df_aggiornato = pd.concat([fasce_df_esistente, fasce_df_selezionati]).drop_duplicates(subset='Nome', keep='last')
            else:
                fasce_df_aggiornato = fasce_df_selezionati

            # Salva il DataFrame aggiornato nel file CSV
            fasce_df_aggiornato.to_csv('fasce_calciatori.csv', index=False)
            st.success('Le fasce dei calciatori sono state salvate con successo!')
        else:
            st.warning('Nessun calciatore selezionato.')

with st.expander(f"Griglia fasce"):
    st.subheader('Griglia dei calciatori assegnati alle fasce')
    # Percorso del file CSV
    file_path = 'fasce_calciatori.csv'

    # Verifica se il file esiste
    if not os.path.isfile(file_path):
        print("Nessuna selezione")
    else:
        # Se il file esiste, crea un DataFrame
        fasce_selezionate = pd.read_csv(file_path)
        fasce_selezionate_op = fasce_selezionate.merge(df, on='Nome', how='left')

        # Selezione delle colonne da mostrare
        fasce_selezionate_op = fasce_selezionate_op[[
            "Nome", "Squadra", "Ruolo", "ALG FCP", "Punteggio FantaCalcioPedia",
            "Solidità fantainvestimento", "Resistenza infortuni", "Qt.A", "Attributi",
            "Gol previsti", "Presenze previste", "Assist previsti", "Prezzo", 'Fascia'
        ]]

        ruoli_filtra_griglia=st.multiselect(
            "Filtra per ruolo",
            options=ruolo_list,
            default=ruolo_list,
            key="ruoli_filtri_griglia"  # Chiave unica per ruoli
        )
        attributi_filtra_griglia = st.multiselect(
            "Filtra per attributi",
            options=attributi_unici,
            default=attributi_unici,
            key="attributi_filtri_griglia"  # Chiave unica per attributi
        )

        fasce_filtra_griglia = st.multiselect(
            "Filtra per fasce",
            options=fasce,
            default=fasce,
            key="fasce_filtri_griglia"  # Chiave unica per ruoli
        )

        st.dataframe(
            fasce_selezionate_op[
                (fasce_selezionate_op.Ruolo.isin(ruoli_filtra_griglia)) &
                (fasce_selezionate_op.Fascia.isin(fasce_filtra_griglia)) &
                (fasce_selezionate_op.Attributi.apply(
                    lambda x: any(attr in x.split('-') for attr in attributi_filtra_griglia)))
                ]
        )











# Sezione Obiettivi
with st.expander("Simulazione Rosa"):
    col7, col8 = st.columns([1, 1])

    # Nome del file CSV per i giocatori selezionati
    csv_file = 'selected_players.csv'

    # Carica i dati selezionati precedentemente se esiste il file CSV
    if os.path.exists(csv_file):
        selected_data = pd.read_csv(csv_file)
        previously_selected_players = selected_data['Nome'].tolist()
    else:
        previously_selected_players = []

    # Definisci le colonne con i ruoli
    with col7:
        st.header("Seleziona i giocatori")
        num_portieri = 3
        num_difensori = 8
        num_centrocampisti = 8
        num_attaccanti = 6

        portieri = df[df['Ruolo'] == 'P']
        difensori = df[df['Ruolo'] == 'D']
        centrocampisti = df[df['Ruolo'] == 'C']
        attaccanti = df[df['Ruolo'] == 'A']

        # Seleziona i giocatori e pre-seleziona quelli precedentemente salvati
        selected_portieri = st.multiselect("Seleziona i portieri",
                                           portieri['Nome'].tolist(),
                                           default=[p for p in previously_selected_players if
                                                    p in portieri['Nome'].tolist()],
                                           max_selections=num_portieri)

        selected_difensori = st.multiselect("Seleziona i difensori",
                                            difensori['Nome'].tolist(),
                                            default=[p for p in previously_selected_players if
                                                     p in difensori['Nome'].tolist()],
                                            max_selections=num_difensori)

        selected_centrocampisti = st.multiselect("Seleziona i centrocampisti",
                                                 centrocampisti['Nome'].tolist(),
                                                 default=[p for p in previously_selected_players if
                                                          p in centrocampisti['Nome'].tolist()],
                                                 max_selections=num_centrocampisti)

        selected_attaccanti = st.multiselect("Seleziona gli attaccanti",
                                             attaccanti['Nome'].tolist(),
                                             default=[p for p in previously_selected_players if
                                                      p in attaccanti['Nome'].tolist()],
                                             max_selections=num_attaccanti)

        selected_players = selected_portieri + selected_difensori + selected_centrocampisti + selected_attaccanti

        selected_data = df[df['Nome'].isin(selected_players)]

        moduli = ['4-3-3', '4-4-2', '3-5-2', '3-4-3']
        selected_modulo = st.selectbox("Seleziona un modulo", moduli)

    # Salva i dati selezionati nel file CSV quando vengono selezionati i giocatori
    if selected_players:
        selected_data.to_csv(csv_file, index=False)
    with col8:
        if selected_modulo:
            if selected_modulo == '4-3-3':
                modulo_posizioni = {'P': 1, 'D': 4, 'C': 3, 'A': 3}
            elif selected_modulo == '4-4-2':
                modulo_posizioni = {'P': 1, 'D': 4, 'C': 4, 'A': 2}
            elif selected_modulo == '3-5-2':
                modulo_posizioni = {'P': 1, 'D': 3, 'C': 5, 'A': 2}
            elif selected_modulo == '3-4-3':
                modulo_posizioni = {'P': 1, 'D': 3, 'C': 4, 'A': 3}

            migliori_portieri = selected_data[selected_data['Ruolo'] == 'P'].nlargest(modulo_posizioni['P'], 'Punteggio FantaCalcioPedia')
            migliori_difensori = selected_data[selected_data['Ruolo'] == 'D'].nlargest(modulo_posizioni['D'], 'Punteggio FantaCalcioPedia')
            migliori_centrocampisti = selected_data[selected_data['Ruolo'] == 'C'].nlargest(modulo_posizioni['C'], 'Punteggio FantaCalcioPedia')
            migliori_attaccanti = selected_data[selected_data['Ruolo'] == 'A'].nlargest(modulo_posizioni['A'], 'Punteggio FantaCalcioPedia')

            modulo_players = pd.concat([
                migliori_portieri,
                migliori_difensori,
                migliori_centrocampisti,
                migliori_attaccanti
            ])




            modulo_fanta_media = modulo_players['Punteggio FantaCalcioPedia'].mean()
            st.write(f"Fantamedia del modulo {selected_modulo}: {modulo_fanta_media:.2f}")
            st.write(f"Goal previsti del modulo {selected_modulo}: {modulo_players['Gol previsti'].sum()/36:.2f}")
            st.write(f"Prezzo squadra: {selected_data.Prezzo.sum():.0f}")

            st.write("Formazione migliore:")
            modulo_selezionato=pd.DataFrame(modulo_players[['Nome', 'Ruolo', 'Punteggio FantaCalcioPedia',"Attributi", "Gol previsti", "Presenze previste", "Assist previsti",'Prezzo']])

            st.table(modulo_selezionato.set_index('Nome',drop=True))
            st.write("Formazione completa:")
            selected_data['Status'] = selected_data['Nome'].apply(
                lambda x: 'titolare' if x in modulo_players['Nome'].values else 'panchinaro'
            )
            st.table(pd.DataFrame(selected_data[['Nome', 'Ruolo', 'Punteggio FantaCalcioPedia',"Attributi", "Gol previsti", "Presenze previste", "Assist previsti",'Prezzo', 'Status']].sort_values('Prezzo', ascending=False)).set_index('Nome', drop=True))
        else:
            st.write("Seleziona un modulo per calcolare la fantamedia.")

# Sezione per l'input del budget e dei range di acquisto
col3, col4 = st.columns([1, 2])

with col3:

    with st.expander("Budget per ruolo"):
        budget_portieri=st.number_input("Budget portieri", min_value=1, max_value=budget, value=int(budget*0.07))
        budget_difensori = st.number_input("Budget difensori", min_value=1, max_value=budget-budget_portieri, value=int(budget*0.16))
        budget_centrocampisti = st.number_input("Budget centrocampisti", min_value=1, max_value=budget - budget_portieri-budget_difensori, value=int(budget*0.235))
        budget_attaccanti = st.number_input("Budget centrocampisti", min_value=1,
                                                max_value=budget - budget_portieri - budget_difensori -budget_centrocampisti, value=int(budget*0.535))
    proposta = st.number_input("Proposta", value=1)

    on = st.checkbox("Vuoi modificare i range di acquisto?")
    range_portieri = 0.05
    range_difensori = 0.10
    range_centrocampisti = 0.15
    range_attaccanti = 0.20

    if on:
        range_portieri = st.number_input("Range Portieri", value=0.05)
        range_difensori = st.number_input("Range Difensori", value=0.10)
        range_centrocampisti = st.number_input("Range Centrocampisti", value=0.15)
        range_attaccanti = st.number_input("Range Attaccanti", value=0.20)

    selected_ruolo = st.selectbox('Seleziona un ruolo (opzionale)', [''] + ruolo_list)
    # Creare la lista di attributi unici senza duplicati
    lista_attributi = list(set('-'.join(df['Attributi']).split('-')))

    # Permettere la selezione di un attributo dalla lista (opzionale)
    Attributi = st.selectbox('Seleziona un attributo (opzionale)', lista_attributi)

    # Iniziare il filtraggio dal DataFrame originale
    df_filtrato = df.copy()

    if selected_ruolo:
        df_filtrato = df_filtrato[df_filtrato['Ruolo'].str.contains(selected_ruolo)]

    # Filtrare in base all'attributo selezionato se è stato scelto
    if Attributi:
        df_filtrato = df_filtrato[df_filtrato['Attributi'].str.contains(Attributi)]

    # Ottenere la lista unica di giocatori filtrati
    available_players = df_filtrato['Nome'].unique().tolist()

    # Permettere la selezione di uno o più giocatori dalla lista filtrata
    selected_players = st.multiselect('Seleziona uno o più giocatori', available_players)



    if selected_players:
        with col4:
            fig = go.Figure()

            for selected_player in selected_players:
                player_data = df[df['Nome'] == selected_player].iloc[0]
                skill_values = [
                    player_data['ALG FCP'],
                    player_data['Punteggio FantaCalcioPedia'],
                    player_data['Solidità fantainvestimento'],
                    player_data['Resistenza infortuni'],
                    player_data["Gol previsti"],
                    player_data["Presenze previste"],
                    player_data["Assist previsti"]
                ]
                skill_values = pd.to_numeric(skill_values, errors='coerce')
                skill_names = [
                    'ALG FCP',
                    'Punteggio FantaCalcioPedia',
                    'Solidità fantainvestimento',
                    'Resistenza infortuni',
                    "Gol previsti",
                    "Presenze previste",
                    "Assist previsti"
                ]

                fig.add_trace(go.Scatterpolar(
                    r=skill_values,
                    theta=skill_names,
                    fill='toself',
                    name=selected_player
                ))

                acquisto = (df['Punteggio FantaCalcioPedia'].max() / (budget / 25) *
                            player_data["Punteggio FantaCalcioPedia"] *
                            (player_data['Solidità fantainvestimento'] / 100) *
                            (player_data['Resistenza infortuni'] / 100)) * (player_data["Qt.A"] / df["Qt.A"].max())
                range_acquisto = {
                    'P': range_portieri,
                    'D': range_difensori,
                    'C': range_centrocampisti,
                    'A': range_attaccanti
                }.get(selected_ruolo, 0)

                min_acquisto = max(1, acquisto * (1 - range_acquisto))
                max_acquisto = max(1, acquisto * (1 + range_acquisto))

                st.write(
                    f'{selected_player} per fantagazzetta vale {player_data["Qt.A"]}, il sistema stima un prezzo di {acquisto:.0f} (considerando i dati di Fantapedia relativi a Fantamedia, resistenza infortuni, solidità investimento e Budget) con range consigliato: {min_acquisto:.0f}-{max_acquisto:.0f} crediti')
                st.write(
                    f'{selected_player} gol previsti {player_data["Gol previsti"]}, assist previsti {player_data["Assist previsti"]}, presenze previste {player_data["Presenze previste"]}, attributi {player_data["Attributi"]},')
                st.write(f'{"Rilancia" if proposta < acquisto else "Valuta" if proposta < max_acquisto else "Molla"}')

            fig.update_layout(
                polar=dict(
                    bgcolor='rgba(255,255,255,0.1)',
                    radialaxis=dict(
                        visible=True,
                        linewidth=2,
                        linecolor='grey',
                        gridcolor='lightgrey',
                        gridwidth=1,
                        range=[0, max(skill_values) * 1.2],
                        tickfont=dict(size=12, color='white'),
                    ),
                    angularaxis=dict(
                        linewidth=2,
                        linecolor='grey',
                        gridcolor='lightgrey',
                        gridwidth=1,
                        tickfont=dict(size=12, color='white'),
                    )
                ),
                showlegend=True,
                title=dict(
                    text='Grafico Radar dei Giocatori Selezionati',
                    font=dict(size=20, color='white')
                ),
                margin=dict(l=60, r=60, t=60, b=60),
            )
st.divider()
if 'fig' in locals() and fig is not None:
    st.plotly_chart(fig)
st.divider()

# Verifica e crea la colonna 'AcquistatoDa' se non esiste
if 'AcquistatoDa' not in df.columns:
    df['AcquistatoDa'] = None

# Verifica e crea la colonna 'AcquistatoDa' se non esiste
if 'AcquistatoDa' not in df.columns:
    df['AcquistatoDa'] = None

# Richiedi il numero di fantallenatori
numero_giocatori = st.number_input("Numero di avversari (incluso te stesso)", min_value=2, value=5, step=1)
numero_giocatori = int(numero_giocatori)

# Dizionari per gestire le rose e gli acquisti
fantallenatori = {}
rose = {f'Fantallenatore {i}': [] for i in range(1, numero_giocatori + 1)}
prezzi = {f'Fantallenatore {i}': {} for i in range(1, numero_giocatori + 1)}

# Colonne dell'interfaccia
col1, col2 = st.columns([1, 1])

with col1:
    st.header('Input Fantallenatori')
    with st.expander("Nome fantallenatori"):
        for i in range(1, numero_giocatori + 1):
            nome_fantallenatore = st.text_input(f'Nome del Fantallenatore {i}', value=f'Fantallenatore {i}', key=f'nome_{i}')
            fantallenatori[f'Fantallenatore {i}'] = nome_fantallenatore

with col2:
    st.header('Gestione Acquisti')
    st.subheader('Seleziona i calciatori e imposta il prezzo e l\'allenatore')

    # Selezione dei calciatori disponibili
    giocatori_disponibili = df[df['AcquistatoDa'].isna()]['Nome'].tolist()
    calciatori_selezionati = st.multiselect('Seleziona i calciatori', giocatori_disponibili)

    if calciatori_selezionati:
        for calciatore in calciatori_selezionati:
            col1, col2 = st.columns(2)

            with col1:
                with st.expander(f"{calciatore}"):
                    # Imposta il prezzo per il calciatore
                    prezzo = st.number_input(f'Prezzo di {calciatore}', min_value=1, value=1, key=f'prezzo_{calciatore}')
                    # Seleziona il fantallenatore che ha acquistato il calciatore
                    fantallenatore_acquisto = st.selectbox(
                        f'Seleziona il fantallenatore per {calciatore}',
                        options=[fantallenatori[f'Fantallenatore {i}'] for i in range(1, numero_giocatori + 1)],
                        key=f'fantallenatore_{calciatore}'
                    )

                    # Trova la chiave corrispondente a 'fantallenatore_acquisto'
                    fantallenatore_key = next(
                        (key for key, value in fantallenatori.items() if value == fantallenatore_acquisto), None)

                    if fantallenatore_key:
                        if fantallenatore_key not in prezzi:
                            prezzi[fantallenatore_key] = {}
                        prezzi[fantallenatore_key][calciatore] = prezzo
                        rose[fantallenatore_key].append({
                            'Nome': calciatore,
                            'Prezzo': prezzo,
                            'Punteggio FantaCalcioPedia': df.loc[df['Nome'] == calciatore, 'Punteggio FantaCalcioPedia'].values[0]  # Aggiungi la Fanta media
                        })
                        # Aggiorna il DataFrame
                        df.loc[df['Nome'] == calciatore, 'AcquistatoDa'] = fantallenatore_acquisto

    # Pulsante per salvare i dati
    if st.button('Salva'):
        df.to_csv('acquisti_fantacalcio.csv', index=False)
        st.success('Stato degli acquisti salvato con successo!')

with st.expander("Rose dei Fantallenatori"):
    st.header('Rose dei Fantallenatori')
    for i in range(1, numero_giocatori + 1):
        fantallenatore = fantallenatori[f'Fantallenatore {i}']
        st.subheader(fantallenatore)
        if rose[f'Fantallenatore {i}']:
            df_rosa = pd.DataFrame(rose[f'Fantallenatore {i}'])
            st.write(f"Totale Speso: {sum(item['Prezzo'] for item in rose[f'Fantallenatore {i}'])} crediti")
            st.write(f"Budget rimanente: {budget-sum(item['Prezzo'] for item in rose[f'Fantallenatore {i}'])} crediti")
            st.write(
                f"Media Fantacalcio Pedia della Rosa: {mean(item['Punteggio FantaCalcioPedia'] for item in rose[f'Fantallenatore {i}'])}")
            st.table(df_rosa)
        else:
            st.write("Nessun acquisto effettuato.")



