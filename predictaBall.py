from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def nextMatchesLDC():
    url = "https://www.flashscore.fr/football/europe/ligue-des-champions/calendrier/"
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)

        page.wait_for_timeout(5000)  # On attend 5 secondes pour que le JavaScript charge le contenu

        html = page.content()

        soup = BeautifulSoup(html, "html.parser")
        
        # On cherche ici les prochains matchs
        teams = soup.find_all("span", class_="wcl-simpleText_2t3pL wcl-scores-simple-text-01_8lVyp wcl-name_jjfMf")

        matchs = []
        i = 0
        j = 1
        if teams:
            while i < 36:
                match1 = (teams[i].text, teams[i+1].text)
                matchs.append(match1)
                print(str(j) + ". " + teams[i].text + " vs " + teams[i+1].text) # On affiche les prochains matchs
                i += 2
                j += 1
        
        match_choisi = int(input("Choisissez un match : "))
        equipe1 = matchs[match_choisi - 1][0]
        equipe2 = matchs[match_choisi - 1][1]
        print('\n' + equipe1 + " (H) vs " + equipe2 + " (A) " + '\n')

        url_match = ""
        o = 0
        place_equipe_liste = 0

        while o < 36:
            if equipe1 == teams[o].text:
                place_equipe_liste = o // 2
            o += 1

        matches = soup.find_all("a", class_="eventRowLink")
        print(matches[place_equipe_liste]["href"]) # On vient récupérer ici l'url de la page du match
        

        url2 = "https://www.flashscore.fr/football/europe/ligue-des-champions/classement/#/UiRZST3U/classements/global/"

        page2 = browser.new_page()

        page2.goto(url2)

        page2.wait_for_timeout(5000)

        html = page2.content()

        soup2 = BeautifulSoup(html, "html.parser")
        
        # On cherche ici tous les participants dans l'ordre du classement
        participants = soup2.find_all("a", class_="tableCellParticipant__name")

        classement_equipe1 = 1
        classement_equipe2 = 1

        if participants:
            i = 0
            while i < 36:
                if participants[i].text == equipe1: # Si le participant correspond à l'équipe 1 alors on met à jour son classement
                    classement_equipe1 += i
                elif participants[i].text == equipe2: # Pareil pour l'équipe 2
                    classement_equipe2 += i
                i += 1
            print("Classement " + equipe1 + " : " + str(classement_equipe1) + '\n' + "Classement " + equipe2 + " : " + str(classement_equipe2))

        
        soup3 = BeautifulSoup(html, "html.parser")

        forme_equipes = soup3.find_all("span", class_="wcl-simpleText_2t3pL wcl-scores-simple-text-01_8lVyp") # On récupère les 5 derniers matchs de tous les participants
        forme_equipe1 = []
        forme_equipe2 = []

        j = classement_equipe1 * 5 - 5 # Chaque équipe possède 5 matchs donc on multiplie le classement par 5 puis on retire 5 pour avoir le premier match de l'équipe voulue
        while j < classement_equipe1 * 5:
            if (forme_equipes[j].text != "?"): # Si un match n'a pas encore été joué on ne l'ajoute pas
                forme_equipe1.append(forme_equipes[j].text) # On ajoute les matchs de l'équipe choisie dans notre tableau
            j += 1

        k = classement_equipe2 * 5 - 5
        while k < classement_equipe2 * 5:
            if (forme_equipes[k].text != "?"):
                forme_equipe2.append(forme_equipes[k].text)
            k += 1
        
        print("\nForme " + equipe1 + " : ")
        for element in forme_equipe1:
            print(element)

        print("\nForme " + equipe2 + " : ")
        for element in forme_equipe2:
            print(element)


        url3 = "https://www.lequipe.fr/Football/ligue-des-champions/page-classement-equipes/general"

        page3 = browser.new_page()

        page3.goto(url3)

        page3.wait_for_timeout(5000)

        html2 = page3.content()

        soup3 = BeautifulSoup(html2, "html.parser")
        
        # On cherche ici les buts marqués et encaissés par tous les participants
        buts_marques = soup3.find_all("td", class_="table__col min--tablet")
        
        numero_equipe1_liste = classement_equipe1 * 2 - 2 # Grâce à un petit calcul on retrouve les valeurs qui nous intéressent dans la liste
        numero_equipe2_liste = classement_equipe2 * 2 - 2

        if buts_marques: # Si on a des valeurs alors on affiche les buts marqués/encaissés et la différence de buts des deux équipes
            print('\n' + equipe1 + " :")
            print("Buts marqués : " + buts_marques[numero_equipe1_liste].text)
            print("Buts encaissés : " + buts_marques[numero_equipe1_liste + 1].text)
            difference_buts_equipe1 = int(buts_marques[numero_equipe1_liste].text) - int(buts_marques[numero_equipe1_liste + 1].text)
            print("Différence de buts : " + str(difference_buts_equipe1) + '\n')

            print(equipe2 + " :")
            print("Buts marqués : " + buts_marques[numero_equipe2_liste].text)
            print("Buts encaissés : " + buts_marques[numero_equipe2_liste + 1].text)
            difference_buts_equipe1 = int(buts_marques[numero_equipe2_liste].text) - int(buts_marques[numero_equipe2_liste + 1].text)
            print("Différence de buts : " + str(difference_buts_equipe1) + '\n')
        

        lien_equipes = soup2.find_all("a", class_="tableCellParticipant__name")
        lien_equipe1 = ""
        lien_equipe2 = ""

        # Comme les liens vers les pages des équipes ne sont jamais sous la même forme (exemple : https://www.flashscore.fr/equipe)
        # On vient récupérer directement les url sur les balises <a> en utilisant l'attribut href (celui que l'on veut retrouver)

        if lien_equipes:
            lien_equipe1 = "https://www.flashscore.fr" + lien_equipes[classement_equipe1 - 1]["href"]
            print("Equipe 1 : " + lien_equipe1)
            lien_equipe2 = "https://www.flashscore.fr" + lien_equipes[classement_equipe2 - 1]["href"]
            print("Equipe 2 : " + lien_equipe2)



        # On Ferme le navigateur
        browser.close()



def nextMatchesPL():
    url = "https://www.flashscore.fr/football/angleterre/premier-league/calendrier/"
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        
        page.wait_for_timeout(5000)

        html = page.content()
        
        soup = BeautifulSoup(html, "html.parser")
        
        teams = soup.find_all("span", class_="wcl-simpleText_2t3pL wcl-scores-simple-text-01_8lVyp wcl-name_jjfMf")

        i = 0
        j = 1
        if teams:
            while i < 20:
                print(str(j) + ". " + teams[i].text + " vs " + teams[i+1].text)
                i += 2
                j += 1

        browser.close()




def nextMatchesLigue1():
    url = "https://www.flashscore.fr/football/france/ligue-1/calendrier/"
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url)
        
        page.wait_for_timeout(5000)
        
        html = page.content()
        
        soup = BeautifulSoup(html, "html.parser")
        
        teams = soup.find_all("span", class_="wcl-simpleText_2t3pL wcl-scores-simple-text-01_8lVyp wcl-name_jjfMf")

        i = 0
        j = 1
        if teams:
            while i < 20:
                print(str(j) + ". " + teams[i].text + " vs " + teams[i+1].text)
                i += 2
                j += 1


        browser.close()





def nextMatchesLiga():
    url = "https://www.flashscore.fr/football/espagne/laliga/calendrier/"
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url)
        
        page.wait_for_timeout(5000)
        
        html = page.content()
        
        soup = BeautifulSoup(html, "html.parser")
        
        teams = soup.find_all("span", class_="wcl-simpleText_2t3pL wcl-scores-simple-text-01_8lVyp wcl-name_jjfMf")

        i = 0
        j = 1
        if teams:
            while i < 20:
                print(str(j) + ". " + teams[i].text + " vs " + teams[i+1].text)
                i += 2
                j += 1


        browser.close()





def nextMatchesSerieA():
    url = "https://www.flashscore.fr/football/italie/serie-a/calendrier/"
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url)
        
        page.wait_for_timeout(5000)
        
        html = page.content()
        
        soup = BeautifulSoup(html, "html.parser")
        
        teams = soup.find_all("span", class_="wcl-simpleText_2t3pL wcl-scores-simple-text-01_8lVyp wcl-name_jjfMf")

        i = 0
        j = 1
        if teams:
            while i < 20:
                print(str(j) + ". " + teams[i].text + " vs " + teams[i+1].text)
                i += 2
                j += 1


        browser.close()





def nextMatchesBundesliga():
    url = "https://www.flashscore.fr/football/allemagne/bundesliga/calendrier/"
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url)
        
        page.wait_for_timeout(5000)
        
        html = page.content()
        
        soup = BeautifulSoup(html, "html.parser")
        
        teams = soup.find_all("span", class_="wcl-simpleText_2t3pL wcl-scores-simple-text-01_8lVyp wcl-name_jjfMf")

        i = 0
        j = 1
        if teams:
            while i < 20:
                print(str(j) + ". " + teams[i].text + " vs " + teams[i+1].text)
                i += 2
                j += 1


        browser.close()












championnat_choisi = 0
print("1. Ligue des champions\n2. Premier League\n3. Ligue 1\n4. La Liga\n5. Serie A\n6. Bundesliga\n")
while int(championnat_choisi) < 1 or int(championnat_choisi) > 6:
    championnat_choisi = input("Veuillez choisir un championnat (indiquez le numéro) : ")

if int(championnat_choisi) == 1:
    nextMatchesLDC()

if int(championnat_choisi) == 2:
    nextMatchesPL()

if int(championnat_choisi) == 3:
    nextMatchesLigue1()

if int(championnat_choisi) == 4:
    nextMatchesLiga()

if int(championnat_choisi) == 5:
    nextMatchesSerieA()

if int(championnat_choisi) == 6:
    nextMatchesBundesliga()