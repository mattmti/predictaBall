import requests
from datetime import datetime
import json

class FootballPredictor:
    def __init__(self):
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {
            "X-Auth-Token": "5bce38997bd948849ceb02b50334bc6f"
        }
        
        # Codes des championnats principaux
        self.leagues = {
            "1": {"name": "Ligue 1", "code": "FL1"},
            "2": {"name": "Premier League", "code": "PL"},
            "3": {"name": "La Liga", "code": "PD"},
            "4": {"name": "Bundesliga", "code": "BL1"},
            "5": {"name": "Serie A", "code": "SA"},
            "6": {"name": "Ligue des Champions", "code": "CL"}
        }
    
    def afficher_championnats(self):
        """Affiche les championnats disponibles"""
        print("\n=== CHAMPIONNATS DISPONIBLES ===")
        for key, league in self.leagues.items():
            print(f"{key}. {league['name']}")
        print("================================\n")
    
    def obtenir_prochains_matchs(self, league_code):
        """Récupère les prochains matchs du championnat"""
        url = f"{self.base_url}/competitions/{league_code}/matches"
        params = {"status": "SCHEDULED"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("matches", [])[:5]  # 5 prochains matchs
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des matchs: {e}")
            return []
    
    def obtenir_classement(self, league_code):
        """Récupère le classement du championnat"""
        url = f"{self.base_url}/competitions/{league_code}/standings"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            standings = data.get("standings", [])
            if standings:
                return {team["team"]["name"]: {
                    "position": team["position"],
                    "points": team["points"],
                    "wins": team["won"],
                    "draws": team["draw"],
                    "losses": team["lost"],
                    "goalsFor": team["goalsFor"],
                    "goalsAgainst": team["goalsAgainst"],
                    "goalDifference": team["goalDifference"],
                    "form": team.get("form", "N/A"),
                    "team_id": team["team"]["id"]
                } for team in standings[0]["table"]}
            return {}
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération du classement: {e}")
            return {}
    
    def obtenir_historique_equipe(self, team_id):
        """Récupère les derniers matchs d'une équipe"""
        url = f"{self.base_url}/teams/{team_id}/matches"
        params = {"status": "FINISHED", "limit": 5}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("matches", [])
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def calculer_forme_detaillee(self, matchs, team_name):
        """Calcule la forme récente détaillée d'une équipe"""
        points = 0
        forme_str = ""
        buts_marques = 0
        buts_encaisses = 0
        victoires = 0
        nuls = 0
        defaites = 0
        
        for match in matchs[:5]:
            home_team = match["homeTeam"]["name"]
            away_team = match["awayTeam"]["name"]
            home_score = match["score"]["fullTime"]["home"]
            away_score = match["score"]["fullTime"]["away"]
            
            if home_team == team_name:
                buts_marques += home_score
                buts_encaisses += away_score
                if home_score > away_score:
                    points += 3
                    forme_str += "V"
                    victoires += 1
                elif home_score == away_score:
                    points += 1
                    forme_str += "N"
                    nuls += 1
                else:
                    forme_str += "D"
                    defaites += 1
                    
            elif away_team == team_name:
                buts_marques += away_score
                buts_encaisses += home_score
                if away_score > home_score:
                    points += 3
                    forme_str += "V"
                    victoires += 1
                elif away_score == home_score:
                    points += 1
                    forme_str += "N"
                    nuls += 1
                else:
                    forme_str += "D"
                    defaites += 1
        
        return {
            "points": points,
            "forme_str": forme_str,
            "buts_marques": buts_marques,
            "buts_encaisses": buts_encaisses,
            "victoires": victoires,
            "nuls": nuls,
            "defaites": defaites,
            "nb_matchs": len(matchs[:5])
        }
    
    def analyser_match(self, match, classement):
        """Analyse un match et calcule les pronostics"""
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        home_team_id = match["homeTeam"]["id"]
        away_team_id = match["awayTeam"]["id"]
        
        # Récupération des statistiques
        home_stats = classement.get(home_team, {})
        away_stats = classement.get(away_team, {})
        
        print(f"\n{'='*60}")
        print(f"ANALYSE DU MATCH: {home_team} vs {away_team}")
        print(f"Date: {match['utcDate'][:10]}")
        print(f"{'='*60}\n")
        
        # Récupération de la forme réelle via l'API
        print("Récupération de l'historique des équipes...")
        home_matchs = self.obtenir_historique_equipe(home_team_id)
        away_matchs = self.obtenir_historique_equipe(away_team_id)
        
        home_forme = self.calculer_forme_detaillee(home_matchs, home_team)
        away_forme = self.calculer_forme_detaillee(away_matchs, away_team)
        
        # Affichage des statistiques
        print(f"\n--- {home_team} (Domicile) ---")
        print(f"Position: {home_stats.get('position', 'N/A')}")
        print(f"Points totaux: {home_stats.get('points', 'N/A')}")
        print(f"Buts marqués: {home_stats.get('goalsFor', 'N/A')}")
        print(f"Buts encaissés: {home_stats.get('goalsAgainst', 'N/A')}")
        print(f"Différence de buts: {home_stats.get('goalDifference', 'N/A')}")
        print(f"\nForme récente (5 derniers matchs):")
        print(f"  Bilan: {home_forme['victoires']}V - {home_forme['nuls']}N - {home_forme['defaites']}D")
        print(f"  Buts: {home_forme['buts_marques']} marqués - {home_forme['buts_encaisses']} encaissés")
        print(f"  Points: {home_forme['points']}")

        print(f"\n{'='*60}")

        print(f"\n--- {away_team} (Extérieur) ---")
        print(f"Position: {away_stats.get('position', 'N/A')}")
        print(f"Points totaux: {away_stats.get('points', 'N/A')}")
        print(f"Buts marqués: {away_stats.get('goalsFor', 'N/A')}")
        print(f"Buts encaissés: {away_stats.get('goalsAgainst', 'N/A')}")
        print(f"Différence de buts: {away_stats.get('goalDifference', 'N/A')}")
        print(f"\nForme récente (5 derniers matchs):")
        print(f"  Bilan: {away_forme['victoires']}V - {away_forme['nuls']}N - {away_forme['defaites']}D")
        print(f"  Buts: {away_forme['buts_marques']} marqués - {away_forme['buts_encaisses']} encaissés")
        print(f"  Points: {away_forme['points']}")

        # Calcul du pronostic amélioré
        score_home = 0
        score_away = 0
        
        # Bonus domicile
        score_home += 5
        
        # Points au classement
        score_home += home_stats.get('points', 0) / 10
        score_away += away_stats.get('points', 0) / 10
        
        # Position au classement (inversé)
        score_home += (21 - home_stats.get('position', 10)) / 2
        score_away += (21 - away_stats.get('position', 10)) / 2
        
        # Différence de buts
        score_home += home_stats.get('goalDifference', 0) / 5
        score_away += away_stats.get('goalDifference', 0) / 5
        
        # Forme récente réelle (pondération importante)
        score_home += home_forme['points'] * 1.5  # Coefficient augmenté
        score_away += away_forme['points'] * 1.5
        
        # Bonus pour série de victoires
        if home_forme['forme_str'].count('V') >= 3:
            score_home += 3
        if away_forme['forme_str'].count('V') >= 3:
            score_away += 3
        
        # Malus pour série de défaites
        if home_forme['forme_str'].count('D') >= 3:
            score_home -= 2
        if away_forme['forme_str'].count('D') >= 3:
            score_away -= 2
        
        # Calcul des probabilités
        total = score_home + score_away
        prob_home = (score_home / total * 100) if total > 0 else 33.33
        prob_away = (score_away / total * 100) if total > 0 else 33.33
        prob_draw = 100 - prob_home - prob_away
        
        print(f"\n{'='*60}")
        print("PRONOSTICS")
        print(f"{'='*60}")
        print(f"Victoire {home_team}: {prob_home:.1f}%")
        print(f"Match nul: {prob_draw:.1f}%")
        print(f"Victoire {away_team}: {prob_away:.1f}%")
        
        # Recommandation
        print(f"\n{'='*60}")
        print("RECOMMANDATION")
        print(f"{'='*60}")
        
        if prob_home > 50:
            confiance = 'Élevée' if prob_home > 60 else 'Moyenne'
            print(f"✓ Victoire de {home_team} (Confiance: {confiance})")
        elif prob_away > 50:
            confiance = 'Élevée' if prob_away > 60 else 'Moyenne'
            print(f"✓ Victoire de {away_team} (Confiance: {confiance})")
        else:
            print(f"✓ Match serré - Match nul possible ou victoire courte")
        
        # Pronostic buts basé sur la forme récente
        avg_goals_home = home_forme['buts_marques'] / max(home_forme['nb_matchs'], 1)
        avg_goals_away = away_forme['buts_marques'] / max(away_forme['nb_matchs'], 1)
        avg_goals_total = avg_goals_home + avg_goals_away
        
        print(f"\nPronostic buts:")
        print(f"  Moyenne buts {home_team} (forme récente): {avg_goals_home:.1f}/match")
        print(f"  Moyenne buts {away_team} (forme récente): {avg_goals_away:.1f}/match")
        
        if avg_goals_total > 2.5:
            print(f"✓ Plus de 2.5 buts attendus ({avg_goals_total:.1f} buts estimés)")
        else:
            print(f"✓ Moins de 2.5 buts attendus ({avg_goals_total:.1f} buts estimés)")
        
        # BTTS (Both Teams To Score)
        if avg_goals_home >= 1 and avg_goals_away >= 1:
            print(f"✓ Les deux équipes devraient marquer (BTTS: Oui)")
        else:
            print(f"✓ BTTS: Peu probable")
        
        print(f"{'='*60}\n")
    
    def executer(self):
        """Fonction principale"""
        print("\n" + "="*60)
        print("ANALYSEUR DE MATCHS ET PRONOSTICS FOOTBALL")
        print("Version 3.0 - Avec forme réelle des équipes")
        print("="*60)
        
        self.afficher_championnats()
        
        choix = input("Choisissez un championnat (1-6): ")
        
        if choix not in self.leagues:
            print("Choix invalide!")
            return
        
        league = self.leagues[choix]
        print(f"\nChampionnat sélectionné: {league['name']}")
        
        # Récupération des matchs
        print("\nRécupération des prochains matchs...")
        matchs = self.obtenir_prochains_matchs(league['code'])
        
        if not matchs:
            print("Aucun match trouvé ou erreur API.")
            return
        
        # Affichage des matchs
        print(f"\n{'='*60}")
        print(f"PROCHAINS MATCHS - {league['name']}")
        print(f"{'='*60}")
        for i, match in enumerate(matchs, 1):
            date = match['utcDate'][:10]
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            print(f"{i}. {date} - {home} vs {away}")
        
        # Choix du match
        match_choix = input(f"\nChoisissez un match à analyser (1-{len(matchs)}): ")
        
        try:
            match_idx = int(match_choix) - 1
            if match_idx < 0 or match_idx >= len(matchs):
                print("Choix invalide!")
                return
        except ValueError:
            print("Choix invalide!")
            return
        
        # Récupération du classement
        print("\nRécupération du classement...")
        classement = self.obtenir_classement(league['code'])
        
        # Analyse du match
        self.analyser_match(matchs[match_idx], classement)


if __name__ == "__main__":
    predictor = FootballPredictor()
    predictor.executer()