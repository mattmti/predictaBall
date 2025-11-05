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
        print('\n' + equipe1 + " vs " + equipe2)

        url2 = "https://www.flashscore.fr/football/europe/ligue-des-champions/classement/#/UiRZST3U/classements/global/"

        page2 = browser.new_page()

        page2.goto(url2)

        page2.wait_for_timeout(5000)

        html = page2.content()

        soup2 = BeautifulSoup(html, "html.parser")
        
        # On cherche ici les prochains matchs
        forme_equipe1 = soup2.find_all("a", class_="tableCellParticipant__name")

        if forme_equipe1:
            i = 0
            classement_equipe1 = 1
            classement_equipe2 = 1
            while i < 36:
                if forme_equipe1[i] == equipe1:
                    classement_equipe1 += i
                elif forme_equipe1[i] == equipe2:
                    classement_equipe2 += i
                i += 1
            print("Classement " + equipe1 + " : " + str(classement_equipe1) + '\n' + "Classement " + equipe2 + " : " + str(classement_equipe2))





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