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
        
    def obtenir_buteurs_competition(self, league_code, team_name, limit=3):
        """Récupère les meilleurs buteurs d'une équipe via les stats de la compétition"""
        url = f"{self.base_url}/competitions/{league_code}/scorers"
        params = {"limit": 50}  # On récupère le top 50 pour être sûr d'avoir les joueurs de l'équipe
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            scorers = data.get("scorers", [])
            
            # Filtrer les buteurs de l'équipe concernée
            team_scorers = []
            for scorer in scorers:
                if scorer["team"]["name"] == team_name:
                    team_scorers.append({
                        "name": scorer["player"]["name"],
                        "goals": scorer["goals"],
                        "assists": scorer.get("assists", 0),
                        "penalties": scorer.get("penalties", 0)
                    })
                    
                    if len(team_scorers) >= limit:
                        break
            
            return team_scorers if team_scorers else None
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des buteurs: {e}")
            return None
        

    def analyser_h2h(self, match_id, home_team, away_team):
        #Analyse les confrontations directes entre deux équipes
        url = f"{self.base_url}/matches/{match_id}/head2head"
        params = {"limit": 10}  # On récupère les 10 dernières confrontations
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            h2h_matches = data.get("matches", [])
            
            if not h2h_matches:
                return None
            
            # Limiter aux 5 dernières confrontations
            h2h_matches = h2h_matches[:5]
            
            # Analyser les résultats
            stats = {
                "victoires_home": 0,
                "victoires_away": 0,
                "nuls": 0,
                "buts_home": 0,
                "buts_away": 0,
                "matchs": []
            }
            
            for match in h2h_matches:
                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]
                home_score = match["score"]["fullTime"]["home"]
                away_score = match["score"]["fullTime"]["away"]
                date = match["utcDate"][:10]
                competition = match["competition"]["name"]
                
                # Déterminer le résultat du point de vue de home_team (l'équipe à domicile du match analysé)
                if home == home_team:
                    stats["buts_home"] += home_score
                    stats["buts_away"] += away_score
                    if home_score > away_score:
                        stats["victoires_home"] += 1
                        resultat = f"✓ {home_team}"
                    elif home_score < away_score:
                        stats["victoires_away"] += 1
                        resultat = f"✓ {away_team}"
                    else:
                        stats["nuls"] += 1
                        resultat = "Match nul"
                    
                    stats["matchs"].append({
                        "date": date,
                        "competition": competition,
                        "home": home,
                        "away": away,
                        "score": f"{home_score}-{away_score}",
                        "resultat": resultat
                    })
                else:  # away == home_team (inversion des équipes)
                    stats["buts_home"] += away_score
                    stats["buts_away"] += home_score
                    if away_score > home_score:
                        stats["victoires_home"] += 1
                        resultat = f"✓ {home_team}"
                    elif away_score < home_score:
                        stats["victoires_away"] += 1
                        resultat = f"✓ {away_team}"
                    else:
                        stats["nuls"] += 1
                        resultat = "Match nul"
                    
                    stats["matchs"].append({
                        "date": date,
                        "competition": competition,
                        "home": home,
                        "away": away,
                        "score": f"{home_score}-{away_score}",
                        "resultat": resultat
                    })
            
            return stats
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des confrontations directes: {e}")
            return None     
    
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
    
    def analyser_match(self, match, classement, league_code):
        """Analyse un match et calcule les pronostics"""
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        home_team_id = match["homeTeam"]["id"]
        away_team_id = match["awayTeam"]["id"]
        match_id = match["id"]
        
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

        h2h_stats = self.analyser_h2h(match_id, home_team, away_team)

        if h2h_stats:
            print(f"\n{'='*60}")
            print("CONFRONTATIONS DIRECTES (5 derniers matchs)")
            print(f"{'='*60}\n")
            print(f"Bilan: {home_team} {h2h_stats['victoires_home']}V - {h2h_stats['nuls']}N - {h2h_stats['victoires_away']}V {away_team}")
            print(f"Buts totaux: {home_team} {h2h_stats['buts_home']} - {h2h_stats['buts_away']} {away_team}")
            print(f"Moyenne buts/match: {(h2h_stats['buts_home'] + h2h_stats['buts_away']) / len(h2h_stats['matchs']):.1f}")
            print(f"\nHistorique des matchs:")
            for m in h2h_stats['matchs']:
                print(f"    {m['home']} {m['score']} {m['away']}")
        else:
            print(f"\n{'='*60}")
            print("CONFRONTATIONS DIRECTES")
            print(f"{'='*60}\n")
            print("Aucune confrontation récente trouvée entre ces équipes")

        home_scorers = self.obtenir_buteurs_competition(league_code, home_team, limit=3)
        away_scorers = self.obtenir_buteurs_competition(league_code, away_team, limit=3)
        
        if home_scorers:
            print(f"\n{'='*60}")
            print("MEILLEURS BUTEURS PAR EQUIPE :")
            print(f"{'='*60}\n")
            for i, scorer in enumerate(home_scorers, 1):
                penalties = scorer.get('penalties') or 0
                assists = scorer.get('assists') or 0
                penalties_info = f" ({penalties} pen.)" if penalties > 0 else ""
                assists_info = f" - {assists} passes" if assists > 0 else ""
                print(f"  {i}. {scorer['name']}: {scorer['goals']} buts{penalties_info}{assists_info}")

        if away_scorers:
            print("\n")
            for i, scorer in enumerate(away_scorers, 1):
                penalties = scorer.get('penalties') or 0
                assists = scorer.get('assists') or 0
                penalties_info = f" ({penalties} pen.)" if penalties > 0 else ""
                assists_info = f" - {assists} passes" if assists > 0 else ""
                print(f"  {i}. {scorer['name']}: {scorer['goals']} buts{penalties_info}{assists_info}")

        score_home = 50  # Base de 50 points pour chaque équipe
        score_away = 50
        score_draw = 30  # Base pour le match nul
        
        # 1. BONUS DOMICILE
        score_home += 10
        
        # 2. POINTS AU CLASSEMENT (impact modéré)
        home_points = home_stats.get('points', 0)
        away_points = away_stats.get('points', 0)
        score_home += home_points * 0.5
        score_away += away_points * 0.5
        
        # 3. POSITION AU CLASSEMENT
        home_pos = home_stats.get('position', 10)
        away_pos = away_stats.get('position', 10)
        score_home += (21 - home_pos) * 2
        score_away += (21 - away_pos) * 2
        
        # 4. DIFFÉRENCE DE BUTS (force offensive/défensive)
        home_diff = home_stats.get('goalDifference', 0)
        away_diff = away_stats.get('goalDifference', 0)
        score_home += home_diff * 0.8
        score_away += away_diff * 0.8
        
        # 5. FORME RÉCENTE (très important)
        score_home += home_forme['points'] * 2
        score_away += away_forme['points'] * 2
        
        # Bonus/malus pour séries
        if home_forme['forme_str'].count('V') >= 3:
            score_home += 8
        if away_forme['forme_str'].count('V') >= 3:
            score_away += 8
        
        if home_forme['forme_str'].count('D') >= 3:
            score_home -= 5
        if away_forme['forme_str'].count('D') >= 3:
            score_away -= 5
        
        # Bonus pour les matchs nuls récents (augmente prob de nul)
        home_draws = home_forme['forme_str'].count('N')
        away_draws = away_forme['forme_str'].count('N')
        score_draw += (home_draws + away_draws) * 3
        
        # 6. ÉCART ENTRE LES ÉQUIPES
        # Si les équipes sont proches au classement ou en forme, augmenter prob de nul
        diff_position = abs(home_pos - away_pos)
        diff_points = abs(home_points - away_points)
        
        if diff_position <= 3:  # Équipes très proches au classement
            score_draw += 10
        elif diff_position <= 6:  # Équipes assez proches
            score_draw += 5
        
        if diff_points <= 5:  # Écart de points faible
            score_draw += 8
        elif diff_points <= 10:
            score_draw += 4
        
        # Si les formes sont similaires
        if abs(home_forme['points'] - away_forme['points']) <= 3:
            score_draw += 6
        
        # 7. HISTORIQUE DES CONFRONTATIONS DIRECTES
        # (Si disponible - sera ajouté plus tard dans le code)
        
        # 8. AJUSTEMENT SELON LA QUALITÉ DES ÉQUIPES
        # Les meilleures équipes ont plus de mal à se départager
        avg_position = (home_pos + away_pos) / 2
        if avg_position <= 5:  # Top 5
            score_draw += 5
        
        # 9. NORMALISATION ET CALCUL DES PROBABILITÉS
        total = score_home + score_away + score_draw
        prob_home = (score_home / total * 100)
        prob_away = (score_away / total * 100)
        prob_draw = (score_draw / total * 100)
        
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
        
        max_prob = max(prob_home, prob_draw, prob_away)
        
        if max_prob == prob_home:
            confiance = 'Élevée' if prob_home > 50 else 'Moyenne' if prob_home > 40 else 'Faible'
            print(f"✓ Victoire de {home_team} (Confiance: {confiance})")
        elif max_prob == prob_away:
            confiance = 'Élevée' if prob_away > 50 else 'Moyenne' if prob_away > 40 else 'Faible'
            print(f"✓ Victoire de {away_team} (Confiance: {confiance})")
        else:
            confiance = 'Élevée' if prob_draw > 40 else 'Moyenne' if prob_draw > 33 else 'Faible'
            print(f"✓ Match nul probable (Confiance: {confiance})")
        
        # Analyser l'écart entre les probabilités
        probs_sorted = sorted([prob_home, prob_draw, prob_away], reverse=True)
        if probs_sorted[0] - probs_sorted[1] < 10:
            print(f"  ⚠ Les probabilités sont très serrées - match incertain")
        
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
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            print(f"{i}. {home} vs {away}")
        
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
        self.analyser_match(matchs[match_idx], classement, league['code'])


if __name__ == "__main__":
    predictor = FootballPredictor()
    predictor.executer()