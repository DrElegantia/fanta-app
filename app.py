import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide")

# Carica i dati dal CSV
df = pd.read_csv('/dati_uniti.csv')
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
        # Altrimenti, convertilo semplicemente in intero
        else:
            return int(val)
    return val

# Applicare la funzione alle colonne interessate
df["Gol previsti"] = df["Gol previsti"].apply(estrai_numero1)
df["Presenze previste"] = df["Presenze previste"].apply(estrai_numero1)
df["Assist previsti"] = df["Assist previsti"].apply(estrai_numero1)
df.loc[df['Ruolo'] == 'P', 'Gol previsti'] *= -1
# Nome del file CSV per i giocatori papabili
papabili_file = 'papabili_players.csv'

# Carica i giocatori papabili salvati in precedenza se esiste il file CSV
if os.path.exists(papabili_file):
    papabili_data = pd.read_csv(papabili_file)
    previously_papabili_players = papabili_data['Nome'].tolist()
else:
    previously_papabili_players = []

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
# Sezione Papabili
with st.expander("Giocatori Papabili"):
    st.header("Seleziona i giocatori papabili")

    # Seleziona i giocatori papabili e pre-seleziona quelli precedentemente salvati
    selected_papabili_players = st.multiselect("Seleziona i giocatori papabili",
                                               df['Nome'].tolist(),
                                               default=previously_papabili_players)
    df_view=df.copy()
    df_view = df_view.rename(columns={"Squadra_x": "Squadra"})
    df_view = df_view[["Nome", "Squadra", "Ruolo", "ALG FCP", "Punteggio FantaCalcioPedia", "Solidità fantainvestimento",
         "Resistenza infortuni", "Qt.A", "Attributi", "Gol previsti", "Presenze previste", "Assist previsti", "Prezzo"]]

    for ruoli in df_view.Ruolo.unique():
        st.dataframe(df_view[df_view["Ruolo"] == ruoli].sort_values("Punteggio FantaCalcioPedia", ascending=False).set_index("Nome"))

    # Salva i giocatori papabili selezionati nel file CSV
    if st.button("Salva giocatori papabili"):
        papabili_data = df[df['Nome'].isin(selected_papabili_players)]
        papabili_data = papabili_data.rename(columns={"Squadra_x": "Squadra"})
        papabili_data_view = papabili_data[
            ["Nome", "Squadra", "Ruolo", "ALG FCP", "Punteggio FantaCalcioPedia", "Solidità fantainvestimento",
             "Resistenza infortuni", "Qt.A", "Attributi", "Gol previsti", "Presenze previste", "Assist previsti", "Prezzo"]]
        papabili_data_view['Prezzo']=round((df['Punteggio FantaCalcioPedia'].max() / (budget / 25) *
                    papabili_data_view["Punteggio FantaCalcioPedia"] *
                    (papabili_data_view['Solidità fantainvestimento'] / 100) *
                    (papabili_data_view['Resistenza infortuni'] / 100)) * (papabili_data_view["Qt.A"] / df["Qt.A"].max()))


        papabili_data.to_csv(papabili_file, index=False)

        st.success("Giocatori papabili salvati con successo!")
        for ruolo in papabili_data_view["Ruolo"].unique():
            st.table(papabili_data_view[papabili_data_view["Ruolo"] == ruolo])

# Sezione Obiettivi
with st.expander("Obiettivi"):
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
            st.table(pd.DataFrame(selected_data[['Nome', 'Ruolo', 'Punteggio FantaCalcioPedia',"Attributi", "Gol previsti", "Presenze previste", "Assist previsti",'Prezzo']]).set_index('Nome', drop=True))
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

    selected_ruolo = st.selectbox('Seleziona un ruolo', ruolo_list)

    if selected_ruolo:
        available_players = df[df['Ruolo'] == selected_ruolo]['Nome'].unique().tolist()
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
# Inizializza una lista per tenere traccia dei giocatori acquistati
acquistati = set()

# Sezione per definire il numero di avversari e modificarne i nomi
numero_giocatori = st.number_input("Numero di avversari (incluso te stesso)", min_value=2, value=5, step=1)
numero_giocatori = int(numero_giocatori)

col1, col2 = st.columns([1, 2])

with col1:
    st.header('Input Fantallenatori')
    with st.expander("Nome fantallenatori"):
        fantallenatori = {}
        for i in range(1, numero_giocatori + 1):
            nome_fantallenatore = st.text_input(f'Nome del Fantallenatore {i}', value=f'Fantallenatore {i}')
            fantallenatori[f'Giocatore {i}'] = nome_fantallenatore

    st.header('Formazioni e Budget Speso')
    teams = {}
    for i in range(1, numero_giocatori + 1):
        st.subheader(f'{fantallenatori[f"Giocatore {i}"]}')
        with st.expander(f'Acquisti {fantallenatori[f"Giocatore {i}"]}'):
            available_players = [p for p in df['Nome'].unique().tolist() if p not in acquistati]
            giocatori_acquistati = st.multiselect(f'Seleziona i calciatori per {fantallenatori[f"Giocatore {i}"]}',
                                                  available_players)

            totale_speso = 0
            squadra = []

            for giocatore in giocatori_acquistati:
                prezzo = st.number_input(f'Prezzo di {giocatore} ({fantallenatori[f"Giocatore {i}"]})', min_value=1,
                                         value=1)
                totale_speso += prezzo
                ruolo = df.loc[df.Nome == giocatore, 'Ruolo'].values[0]
                fanta_media = df.loc[df.Nome == giocatore, 'Punteggio FantaCalcioPedia'].values[0]
                goal_previsti = df.loc[df.Nome == giocatore, 'Gol previsti'].values[0]
                assist_previsti = df.loc[df.Nome == giocatore, 'Assist previsti'].values[0]
                attributi = df.loc[df.Nome == giocatore, 'Attributi'].values[0]
                squadra.append({'Nome': giocatore, 'Prezzo': prezzo, 'Ruolo': ruolo, 'FantaMedia': fanta_media, 'Gol previsti':goal_previsti, 'Assist previsti':assist_previsti,'Attributi':attributi})

                # Aggiungi il giocatore alla lista degli acquistati
                acquistati.add(giocatore)

            budget_rimanente = budget - totale_speso
            teams[f'Giocatore {i}'] = {'Squadra': squadra, 'Totale Speso': totale_speso,
                                       'Budget Rimanente': budget_rimanente,
                                       'FantaMedia': sum(player['FantaMedia'] for player in squadra) / len(
                                           squadra) if len(squadra) != 0 else 0,
                                       'Goal previsti': sum(player['Gol previsti'] for player in squadra) / len(
                                           squadra) if len(squadra) != 0 else 0
                                       }
with col2:
    for giocatore, dati in teams.items():
        df_squadra = pd.DataFrame(dati['Squadra'])
        st.subheader(fantallenatori[giocatore])
        st.write(f"Totale Speso: {dati['Totale Speso']} crediti")
        st.write(f"Budget Rimanente: {dati['Budget Rimanente']} crediti")
        st.write(f"FantaMedia team intero: {dati['FantaMedia']:.2f} punti")
        st.write(f"Gaol previsti team intero: {dati['Goal previsti']/36:.2f} punti")
        st.table(df_squadra)
