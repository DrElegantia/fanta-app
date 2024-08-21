from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd

# Lista dei ruoli
rolePlayers = ['Portieri', 'Difensori', 'Centrocampisti', 'Trequartisti', 'Attaccanti']

# Carica il file Excel con i dati dei calciatori
df = pd.read_excel(
    '/Quotazioni_Fantacalcio_Stagione_2024_25.xlsx', skiprows=1)
listName = df['Nome']
df.set_index("Nome", inplace=True)


def extract_evolution_tags(soup):
    """Estrae tutte le categorie dalla sezione mc_hookEvolution."""
    evolution_section = soup.find("div", class_="col_full center mc_hookEvolution")
    tags = {
        "Ultimi Arrivi": "", "In Crescita": "", "Rischiosi": "", "Fuoriclasse": "", "Outsider": "",
        "Titolari": "", "Economici": "", "Giovani": "", "Infortunati": "", "Buona Media": "",
        "Goleador": "", "Assistman": "", "Rigorista": "", "Sp. Piazzati": ""
    }

    if evolution_section:
        divs = evolution_section.find_all("div", class_="col_one_fourth")
        for div in divs:
            span_text = div.find("span", class_="stickdanpic").text.strip()
            if span_text in tags:
                tags[span_text] = span_text

    return tags


def extract_predicted_stats(soup):
    """Estrae le statistiche previste (presenze, gol, assist) dalla sezione col_one_third col_last."""
    stats_section = soup.find("div", class_="col_one_third col_last")
    stats = {
        "Presenze previste": "",
        "Gol previsti": "",
        "Assist previsti": ""
    }

    if stats_section:
        labels = stats_section.find_all("div", class_="label12")
        for label in labels:
            strong_texts = label.find_all("strong")
            spans = label.find_all("span", class_="stickdan")
            for strong, span in zip(strong_texts, spans):
                stat_name = strong.text.strip().rstrip(':')
                if stat_name in stats:
                    stats[stat_name] = span.text.strip()

    return stats


for role in rolePlayers:
    print(role)
    page = requests.get("https://www.fantacalciopedia.com/lista-calciatori-serie-a/" + role.lower() + "/")
    soup = BeautifulSoup(page.content, 'html.parser')

    mydivs = soup.find_all("div", {"class": "col_full giocatore"})

    if role != 'Attaccanti':
        dictPlayer = {}

    for playersPage in mydivs:
        meanSkill = 0
        hrefPlay = playersPage.find_all("a", {"class": "label label-default fondoindaco"})[0]['href']
        ruoloSite = role[0]
        if ruoloSite == 'T':
            ruoloSite = 'A'

        namePlay = playersPage.find("h3", {"class": "tit_calc"})
        newPage = requests.get(hrefPlay)
        soupInfo = BeautifulSoup(newPage.content, 'html.parser')
        values = soupInfo.find_all("div", {"class": "label12"})
        appVal = str(values[4].text).split(":")
        teamSite = appVal[len(appVal) - 1].replace("\n", "").replace(" ", "")

        skillsPlayer = soupInfo.find_all("ul", {"class": "skills"})
        skill_values = []
        for skillsUl in skillsPlayer:
            skillsLi = skillsUl.find_all("li")
            for skillLi in skillsLi:
                skillsDiv = skillLi.find_all("div", {"class": "counter counter-inherit counter-instant"})
                for skillDiv in skillsDiv:
                    skillsSpan = skillDiv.find_all("span")
                    for skill in skillsSpan:
                        meanSkill += int(skill.text)
                        skill_values.append(int(skill.text))

        evolution_tags = extract_evolution_tags(soupInfo)
        predicted_stats = extract_predicted_stats(soupInfo)

        dictPlayer[namePlay.text.lower()] = {
            "Media": meanSkill / 4,
            "Ruolo": ruoloSite,
            "Squadra": teamSite,
            "ALG FCP": skill_values[0],
            "Punteggio FantaCalcioPedia": skill_values[1],
            "Solidità fantainvestimento": skill_values[2],
            "Resistenza infortuni": skill_values[3],
            **evolution_tags,  # Aggiungi tutte le categorie estratte
            **predicted_stats  # Aggiungi le statistiche previste
        }

    if role != 'Trequartisti':
        dictPlayer = sorted(dictPlayer.items(), key=lambda x: x[1]['Media'], reverse=True)
        if role == 'Trequartisti':
            role = 'Attaccanti'

        with open('meanSkill' + role + '.csv', 'a+', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Nome', 'Squadra', 'Ruolo', 'Media', 'ALG FCP', 'Punteggio FantaCalcioPedia',
                             'Solidità fantainvestimento', 'Resistenza infortuni'] +
                            list(evolution_tags.keys()) +
                            ['Presenze previste', 'Gol previsti', 'Assist previsti'])
            for key, value in dictPlayer:
                flag = 0
                for name in listName:
                    namePlayer = str(name).replace('.', '').replace('-', ' ').lower()
                    team = df.loc[name, 'Squadra']
                    ruolo = df.loc[name, 'R']
                    ruoloSite = value['Ruolo']
                    teamSite = value["Squadra"]
                    if namePlayer in key and ruolo == ruoloSite and team == teamSite:
                        writer.writerow(
                            [name, team, ruolo, value['Media'], value['ALG FCP'], value['Punteggio FantaCalcioPedia'],
                             value['Solidità fantainvestimento'], value['Resistenza infortuni']] +
                            [value[category] for category in evolution_tags.keys()] +
                            [value['Presenze previste'], value['Gol previsti'], value['Assist previsti']]
                        )
                        flag = 1
                        break
                if flag == 0:
                    writer.writerow(
                        [key.upper(), teamSite, ruoloSite, value['Media'], value['ALG FCP'],
                         value['Punteggio FantaCalcioPedia'], value['Solidità fantainvestimento'],
                         value['Resistenza infortuni']] +
                        [value[category] for category in evolution_tags.keys()] +
                        [value['Presenze previste'], value['Gol previsti'], value['Assist previsti']]
                    )
