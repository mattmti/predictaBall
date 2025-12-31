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
                    "form": team.get("form", "N/A")
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
    
    def calculer_forme(self, matchs, team_name):
        """Calcule la forme récente d'une équipe (points sur les 5 derniers matchs)"""
        points = 0
        for match in matchs[:5]:
            home_team = match["homeTeam"]["name"]
            away_team = match["awayTeam"]["name"]
            home_score = match["score"]["fullTime"]["home"]
            away_score = match["score"]["fullTime"]["away"]
            
            if home_team == team_name:
                if home_score > away_score:
                    points += 3
                elif home_score == away_score:
                    points += 1
            elif away_team == team_name:
                if away_score > home_score:
                    points += 3
                elif away_score == home_score:
                    points += 1
        
        return points
    
    def analyser_match(self, match, classement):
        """Analyse un match et calcule les pronostics"""
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        
        # Récupération des statistiques
        home_stats = classement.get(home_team, {})
        away_stats = classement.get(away_team, {})
        
        print(f"\n{'='*60}")
        print(f"ANALYSE DU MATCH: {home_team} vs {away_team}")
        print(f"Date: {match['utcDate'][:10]}")
        print(f"{'='*60}\n")
        
        # Affichage des statistiques
        print(f"--- {home_team} (Domicile) ---")
        print(f"Position: {home_stats.get('position', 'N/A')}")
        print(f"Points: {home_stats.get('points', 'N/A')}")
        print(f"Forme: {home_stats.get('form', 'N/A')}")
        print(f"Buts marqués: {home_stats.get('goalsFor', 'N/A')}")
        print(f"Buts encaissés: {home_stats.get('goalsAgainst', 'N/A')}")
        print(f"Différence de buts: {home_stats.get('goalDifference', 'N/A')}")
        
        print(f"\n--- {away_team} (Extérieur) ---")
        print(f"Position: {away_stats.get('position', 'N/A')}")
        print(f"Points: {away_stats.get('points', 'N/A')}")
        print(f"Forme: {away_stats.get('form', 'N/A')}")
        print(f"Buts marqués: {away_stats.get('goalsFor', 'N/A')}")
        print(f"Buts encaissés: {away_stats.get('goalsAgainst', 'N/A')}")
        print(f"Différence de buts: {away_stats.get('goalDifference', 'N/A')}")
        
        # Calcul du pronostic
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
        
        # Forme récente
        home_form = home_stats.get('form', '') or ''
        away_form = away_stats.get('form', '') or ''
        
        for result in home_form:
            if result == 'W':
                score_home += 2
            elif result == 'D':
                score_home += 1
        
        for result in away_form:
            if result == 'W':
                score_away += 2
            elif result == 'D':
                score_away += 1
        
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
            print(f"✓ Victoire de {home_team} (Confiance: {'Élevée' if prob_home > 60 else 'Moyenne'})")
        elif prob_away > 50:
            print(f"✓ Victoire de {away_team} (Confiance: {'Élevée' if prob_away > 60 else 'Moyenne'})")
        else:
            print(f"✓ Match serré - Match nul possible ou victoire courte")
        
        # Pronostic buts
        avg_goals = (home_stats.get('goalsFor', 0) + away_stats.get('goalsFor', 0)) / 10
        if avg_goals > 2.5:
            print(f"✓ Plus de 2.5 buts attendus")
        else:
            print(f"✓ Moins de 2.5 buts attendus")
        
        print(f"{'='*60}\n")
    
    def executer(self):
        """Fonction principale"""
        print("\n" + "="*60)
        print("ANALYSEUR DE MATCHS ET PRONOSTICS FOOTBALL")
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
            print("\nNote: Cette version utilise l'API football-data.org")
            print("Pour l'utiliser, inscrivez-vous sur https://www.football-data.org/")
            print("et remplacez 'VOTRE_CLE_API_ICI' par votre clé gratuite.")
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