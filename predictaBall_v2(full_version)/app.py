from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
import time
import traceback
import random

app = Flask(__name__, static_folder='../frontend')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": "5bce38997bd948849ceb02b50334bc6f"}

RAPID_API_KEY = "609aaf31f8mshd5507353f83b325p1905c3jsn9e9003baada"
RAPID_HEADERS = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

ODDS_API_KEY = "f5b6789547836224ae8b1d471b95134f"

LEAGUES = {
    "1": {"name": "Ligue 1", "code": "FL1", "rapid_id": 61, "odds_sport": "soccer_france_ligue_one"},
    "2": {"name": "Premier League", "code": "PL", "rapid_id": 39, "odds_sport": "soccer_epl"},
    "3": {"name": "La Liga", "code": "PD", "rapid_id": 140, "odds_sport": "soccer_spain_la_liga"},
    "4": {"name": "Bundesliga", "code": "BL1", "rapid_id": 78, "odds_sport": "soccer_germany_bundesliga"},
    "5": {"name": "Serie A", "code": "SA", "rapid_id": 135, "odds_sport": "soccer_italy_serie_a"},
    "6": {"name": "Ligue des Champions", "code": "CL", "rapid_id": 2, "odds_sport": "soccer_uefa_champs_league"}
}

def api_get(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=15)
        if r.status_code == 429:
            print(f"[RATE LIMIT] {path} - attente 7s puis retry")
            time.sleep(7)
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=15)
        if not r.ok:
            print(f"[HTTP {r.status_code}] {path}")
            return None
        return r.json()
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {path}")
        return None
    except Exception as e:
        print(f"[ERROR] {path} - {e}")
        return None

def obtenir_blessures(team_name, rapid_league_id, saison="2024"):
    """
    Récupère les blessures via API-Football en mode démo
    Note: L'API gratuite a des limites strictes, donc on utilise des données de démo
    Pour une version production, il faudrait une clé API payante
    """
    print(f"[BLESSURES] Mode démo pour {team_name}")
    return generer_blessures_demo()

def generer_blessures_demo():
    """Génère des blessures de démonstration"""
    nb_blessures = random.randint(0, 3)
    types_blessures = ["Blessure musculaire", "Cheville", "Genou", "Ischio-jambiers", "Aine", "Dos"]
    prenoms = ["Lucas", "Antoine", "Thomas", "Alexandre", "Nicolas", "Pierre", "Julien", "Maxime", "Hugo", "Louis"]
    noms = ["Martin", "Bernard", "Dubois", "Moreau", "Simon", "Laurent", "Leroy", "Petit", "Garcia", "Roux"]
    
    return [
        {
            "player": f"{random.choice(prenoms)} {random.choice(noms)}",
            "type": random.choice(types_blessures),
            "reason": "Blessure"
        }
        for i in range(nb_blessures)
    ]

def obtenir_statistiques_avancees(team_name, rapid_league_id, saison="2024"):
    """
    Récupère xG et discipline via des données de démonstration
    Note: Pour des vraies données, il faudrait une API payante
    """
    print(f"[STATS AVANCÉES] Mode démo pour {team_name}")
    return generer_stats_demo()

def generer_stats_demo():
    """Génère des statistiques avancées de démonstration"""
    return {
        "xg_for": round(random.uniform(1.2, 2.5), 2),
        "xg_against": round(random.uniform(0.8, 2.0), 2),
        "yellow_cards": random.randint(20, 50),
        "red_cards": random.randint(0, 5)
    }

def calculer_importance_match(home_pos, away_pos, home_points, away_points, competition_stage=None):
    """
    Calcule l'importance du match
    Gère les compétitions à élimination directe (Ligue des Champions)
    """
    importance = "Moyenne"
    score_importance = 5
    
    # Pour les matchs à élimination directe (pas de classement)
    if competition_stage and competition_stage in ["FINAL", "SEMI_FINALS", "QUARTER_FINALS", "ROUND_OF_16", "LAST_16"]:
        stage_importance = {
            "FINAL": ("FINALE - Enjeu maximum", 15),
            "SEMI_FINALS": ("DEMI-FINALE - Enjeu très élevé", 12),
            "QUARTER_FINALS": ("QUART DE FINALE - Enjeu élevé", 10),
            "ROUND_OF_16": ("HUITIÈME DE FINALE - Enjeu élevé", 10),
            "LAST_16": ("HUITIÈME DE FINALE - Enjeu élevé", 10)
        }
        return stage_importance.get(competition_stage, ("Match à élimination directe", 8))
    
    # Pour les compétitions avec classement
    if home_pos and away_pos and home_points is not None and away_points is not None:
        if home_pos <= 4 and away_pos <= 4:
            importance = "Très élevée - Lutte pour le titre/Europe"
            score_importance = 10
        elif home_pos >= 16 and away_pos >= 16:
            importance = "Élevée - Match de maintien"
            score_importance = 8
        elif abs(home_points - away_points) <= 3:
            importance = "Élevée - Match serré au classement"
            score_importance = 7
        elif (home_pos <= 4 and away_pos >= 16) or (away_pos <= 4 and home_pos >= 16):
            importance = "Moyenne - Écart de niveau"
            score_importance = 4
    
    return importance, score_importance

def normaliser_nom_equipe(nom):
    """Normalise le nom d'une équipe pour faciliter la correspondance"""
    # Supprime les accents, met en minuscule, retire les mots communs
    import unicodedata
    nom = unicodedata.normalize('NFD', nom).encode('ascii', 'ignore').decode('utf-8')
    nom = nom.lower()
    # Retire les mots communs
    mots_a_retirer = ['fc', 'cf', 'ac', 'afc', 'bfc', 'rc', 'as', 'sporting', 'club', 'united', 'city']
    mots = nom.split()
    mots_filtres = [m for m in mots if m not in mots_a_retirer]
    return ' '.join(mots_filtres) if mots_filtres else nom

def trouver_match_odds(home_team, away_team, odds_data):
    """
    Trouve le match correspondant dans les données de côtes
    Utilise une correspondance flexible pour gérer les différences de noms
    """
    home_normalized = normaliser_nom_equipe(home_team)
    away_normalized = normaliser_nom_equipe(away_team)
    
    for match in odds_data:
        match_home = normaliser_nom_equipe(match.get("home_team", ""))
        match_away = normaliser_nom_equipe(match.get("away_team", ""))
        
        # Correspondance exacte
        if match_home == home_normalized and match_away == away_normalized:
            return match
        
        # Correspondance partielle (un des mots clés correspond)
        home_mots = set(home_normalized.split())
        away_mots = set(away_normalized.split())
        match_home_mots = set(match_home.split())
        match_away_mots = set(match_away.split())
        
        if (home_mots & match_home_mots) and (away_mots & match_away_mots):
            return match
    
    return None

def obtenir_cotes(home_team, away_team, odds_sport):
    """Récupère les meilleures côtes des bookmakers"""
    # Mode démo si pas de clé API
    if ODDS_API_KEY == "VOTRE_CLE_ODDS_API_ICI":
        print(f"[CÔTES] Mode démo pour {home_team} vs {away_team}")
        return generer_cotes_demo()
    
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{odds_sport}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        
        print(f"[CÔTES] Requête API pour {odds_sport}")
        r = requests.get(url, params=params, timeout=10)
        
        # Vérifier le nombre de requêtes restantes
        remaining = r.headers.get('x-requests-remaining', 'N/A')
        print(f"[CÔTES] Requêtes restantes: {remaining}")
        
        r.raise_for_status()
        data = r.json()
        
        # Chercher le match correspondant avec correspondance flexible
        match = trouver_match_odds(home_team, away_team, data)
        
        if match:
            print(f"[CÔTES] Match trouvé: {match['home_team']} vs {match['away_team']}")
            
            best_odds = {"home": 0, "draw": 0, "away": 0}
            bookmakers = {"home": "", "draw": "", "away": ""}
            
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market["outcomes"]:
                            if outcome["name"] == match["home_team"]:
                                if outcome["price"] > best_odds["home"]:
                                    best_odds["home"] = outcome["price"]
                                    bookmakers["home"] = bookmaker["title"]
                            elif outcome["name"] == match["away_team"]:
                                if outcome["price"] > best_odds["away"]:
                                    best_odds["away"] = outcome["price"]
                                    bookmakers["away"] = bookmaker["title"]
                            elif outcome["name"] == "Draw":
                                if outcome["price"] > best_odds["draw"]:
                                    best_odds["draw"] = outcome["price"]
                                    bookmakers["draw"] = bookmaker["title"]
            
            if best_odds["home"] > 0:  # Si on a trouvé des côtes
                return best_odds, bookmakers
        
        print(f"[CÔTES] Aucun match trouvé dans les données API")
        
    except Exception as e:
        print(f"[CÔTES] Erreur: {e}")
    
    # Fallback vers mode démo
    return generer_cotes_demo()

def generer_cotes_demo():
    """Génère des côtes de démonstration réalistes"""
    bookmakers_list = ["Betclic", "Unibet", "Winamax", "Parions Sport"]
    
    # Génère des côtes cohérentes (la somme des probabilités implicites ~ 100%)
    # Probabilités réalistes
    prob_home = random.uniform(0.25, 0.55)
    prob_draw = random.uniform(0.20, 0.30)
    prob_away = 1 - prob_home - prob_draw
    
    # Conversion en côtes avec marge bookmaker (~5-10%)
    marge = random.uniform(1.05, 1.10)
    
    best_odds = {
        "home": round(marge / prob_home, 2),
        "draw": round(marge / prob_draw, 2),
        "away": round(marge / prob_away, 2)
    }
    
    bookmakers = {
        "home": random.choice(bookmakers_list),
        "draw": random.choice(bookmakers_list),
        "away": random.choice(bookmakers_list)
    }
    
    return best_odds, bookmakers

def calculer_buts_probables(home_forme, away_forme, home_stats, away_stats, home_advanced, away_advanced):
    """
    Calcule une estimation plus précise du nombre de buts
    Prend en compte: forme récente, stats défensives, xG, domicile/extérieur
    """
    # Buts moyens sur la forme récente (5 derniers matchs)
    home_buts_forme = home_forme["buts_marques"] / max(home_forme["nb_matchs"], 1)
    away_buts_forme = away_forme["buts_marques"] / max(away_forme["nb_matchs"], 1)
    
    # Buts encaissés moyens (défense)
    home_def = home_forme["buts_encaisses"] / max(home_forme["nb_matchs"], 1)
    away_def = away_forme["buts_encaisses"] / max(away_forme["nb_matchs"], 1)
    
    # xG si disponible (plus fiable que les buts réels)
    try:
        home_xg = float(home_advanced['xg_for']) if home_advanced['xg_for'] != 'N/A' else home_buts_forme
        away_xg = float(away_advanced['xg_for']) if away_advanced['xg_for'] != 'N/A' else away_buts_forme
    except:
        home_xg = home_buts_forme
        away_xg = away_buts_forme
    
    # Calcul hybride: 
    # - L'attaque de l'équipe domicile contre la défense de l'extérieur
    # - L'attaque de l'équipe extérieure contre la défense du domicile
    # - Bonus domicile (+0.2 buts)
    
    # Pondération: 40% forme récente, 40% xG, 20% stats générales
    home_attaque = (0.4 * home_buts_forme) + (0.4 * home_xg) + (0.2 * home_stats.get("goalsFor", 0) / 18)
    away_attaque = (0.4 * away_buts_forme) + (0.4 * away_xg) + (0.2 * away_stats.get("goalsFor", 0) / 18)
    
    # Buts attendus pour le match
    buts_home = (home_attaque + away_def) / 2 + 0.2  # Bonus domicile
    buts_away = (away_attaque + home_def) / 2 - 0.1  # Malus extérieur
    
    # Ajustements selon la forme
    if home_forme["forme_str"].count("V") >= 3:
        buts_home *= 1.1
    if away_forme["forme_str"].count("V") >= 3:
        buts_away *= 1.1
    
    if home_forme["forme_str"].count("D") >= 3:
        buts_home *= 0.9
    if away_forme["forme_str"].count("D") >= 3:
        buts_away *= 0.9
    
    total = buts_home + buts_away
    
    return {
        "home": round(max(0.5, buts_home), 1),
        "away": round(max(0.5, buts_away), 1),
        "total": round(max(1.0, total), 1)
    }

@app.route("/api/leagues")
def get_leagues():
    return jsonify(LEAGUES)

@app.route("/api/matches/<league_code>")
def get_matches(league_code):
    try:
        data = api_get(f"/competitions/{league_code}/matches", {"status": "SCHEDULED"})
        if data is None:
            return jsonify({"error": "Impossible de recuperer les matchs"}), 502
        return jsonify(data.get("matches", [])[:5])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculer_forme(matchs, team_name):
    points = 0; forme = ""; bm = 0; be = 0; v = 0; n = 0; d = 0
    for m in matchs[:5]:
        try:
            ht = m["homeTeam"]["name"]; at = m["awayTeam"]["name"]
            hs = m["score"]["fullTime"]["home"] or 0
            as_ = m["score"]["fullTime"]["away"] or 0
            if ht == team_name:
                bm += hs; be += as_
                if hs > as_: points += 3; forme += "V"; v += 1
                elif hs == as_: points += 1; forme += "N"; n += 1
                else: forme += "D"; d += 1
            elif at == team_name:
                bm += as_; be += hs
                if as_ > hs: points += 3; forme += "V"; v += 1
                elif as_ == hs: points += 1; forme += "N"; n += 1
                else: forme += "D"; d += 1
        except Exception:
            continue
    return {"points": points, "forme_str": forme, "buts_marques": bm, "buts_encaisses": be,
            "victoires": v, "nuls": n, "defaites": d, "nb_matchs": len(matchs[:5])}

@app.route("/api/predict/<int:match_id>/<league_code>")
def predict_match(match_id, league_code):
    try:
        # Récupération des infos du championnat
        league_info = None
        for lid, ldata in LEAGUES.items():
            if ldata["code"] == league_code:
                league_info = ldata
                break
        
        if not league_info:
            return jsonify({"error": "Championnat non trouvé"}), 404
        
        rapid_league_id = league_info["rapid_id"]
        odds_sport = league_info["odds_sport"]
        
        data = api_get(f"/matches/{match_id}")
        if data is None:
            return jsonify({"error": "Impossible de recuperer les donnees du match"}), 502
        match = data.get("match", data)
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        home_id = match["homeTeam"]["id"]
        away_id = match["awayTeam"]["id"]
        
        # Récupérer la phase de la compétition (pour Ligue des Champions)
        competition_stage = match.get("stage", None)
        print(f"[MATCH] Stage: {competition_stage}")

        classement = {}; crests = {}
        home_stats = {}; away_stats = {}
        
        # Tentative de récupération du classement (peut échouer pour matchs éliminatoires)
        standings_data = api_get(f"/competitions/{league_code}/standings")
        if standings_data:
            standings_raw = standings_data.get("standings", [])
            if standings_raw:
                for t in standings_raw[0]["table"]:
                    classement[t["team"]["name"]] = {
                        "position": t["position"], "points": t["points"],
                        "wins": t["won"], "draws": t["draw"], "losses": t["lost"],
                        "goalsFor": t["goalsFor"], "goalsAgainst": t["goalsAgainst"],
                        "goalDifference": t["goalDifference"]
                    }
                    crests[t["team"]["name"]] = t["team"].get("crest", "")
        
        home_stats = classement.get(home_team, {})
        away_stats = classement.get(away_team, {})

        # Récupération des blessures (mode démo)
        home_injuries = obtenir_blessures(home_team, rapid_league_id)
        away_injuries = obtenir_blessures(away_team, rapid_league_id)
        
        # Récupération des stats avancées (mode démo)
        home_advanced = obtenir_statistiques_avancees(home_team, rapid_league_id)
        away_advanced = obtenir_statistiques_avancees(away_team, rapid_league_id)
        
        # Calcul de l'importance du match (adapté pour les éliminations directes)
        home_pos = home_stats.get("position", None)
        away_pos = away_stats.get("position", None)
        home_points = home_stats.get("points", None)
        away_points = away_stats.get("points", None)
        
        importance, score_importance = calculer_importance_match(
            home_pos, away_pos, home_points, away_points, competition_stage
        )
        
        # Récupération des côtes (avec correspondance améliorée)
        best_odds, bookmakers = obtenir_cotes(home_team, away_team, odds_sport)

        hm_data = api_get(f"/teams/{home_id}/matches", {"status": "FINISHED", "limit": 5})
        am_data = api_get(f"/teams/{away_id}/matches", {"status": "FINISHED", "limit": 5})
        hm = hm_data.get("matches", []) if hm_data else []
        am = am_data.get("matches", []) if am_data else []
        home_forme = calculer_forme(hm, home_team)
        away_forme = calculer_forme(am, away_team)

        h2h_stats = None
        h2h_data = api_get(f"/matches/{match_id}/head2head", {"limit": 10})
        if h2h_data:
            h2h_matches = h2h_data.get("matches", [])[:5]
            if h2h_matches:
                stats = {"victoires_home": 0, "victoires_away": 0, "nuls": 0,
                         "buts_home": 0, "buts_away": 0, "matchs": []}
                for m in h2h_matches:
                    try:
                        ht = m["homeTeam"]["name"]; at = m["awayTeam"]["name"]
                        hs = m["score"]["fullTime"]["home"] or 0
                        as_ = m["score"]["fullTime"]["away"] or 0
                        if ht == home_team:
                            stats["buts_home"] += hs; stats["buts_away"] += as_
                            if hs > as_: stats["victoires_home"] += 1; res = f"OK {home_team}"
                            elif hs < as_: stats["victoires_away"] += 1; res = f"OK {away_team}"
                            else: stats["nuls"] += 1; res = "Nul"
                        else:
                            stats["buts_home"] += as_; stats["buts_away"] += hs
                            if as_ > hs: stats["victoires_home"] += 1; res = f"OK {home_team}"
                            elif as_ < hs: stats["victoires_away"] += 1; res = f"OK {away_team}"
                            else: stats["nuls"] += 1; res = "Nul"
                        stats["matchs"].append({
                            "date": m["utcDate"][:10],
                            "competition": m["competition"]["name"],
                            "home": ht, "away": at,
                            "score": f"{hs}-{as_}", "resultat": res
                        })
                    except Exception:
                        continue
                h2h_stats = stats

        home_scorers = []; away_scorers = []
        sc_data = api_get(f"/competitions/{league_code}/scorers", {"limit": 50})
        if sc_data:
            for s in sc_data.get("scorers", []):
                try:
                    sname = s["team"]["name"]
                    entry = {
                        "name": s["player"]["name"],
                        "goals": s["goals"],
                        "assists": s.get("assists") or 0,
                        "penalties": s.get("penalties") or 0
                    }
                    if sname == home_team and len(home_scorers) < 3:
                        home_scorers.append(entry)
                    elif sname == away_team and len(away_scorers) < 3:
                        away_scorers.append(entry)
                except Exception:
                    continue

        # ALGORITHME DE PRÉDICTION AMÉLIORÉ
        score_home = 50; score_away = 50; score_draw = 30
        
        # Bonus domicile
        score_home += 10
        
        # Classement et points (si disponibles)
        if home_points is not None and away_points is not None:
            hp = home_points; ap = away_points
            score_home += hp * 0.5; score_away += ap * 0.5
            if home_pos and away_pos:
                hpos = home_pos; apos = away_pos
                score_home += (21 - hpos) * 2; score_away += (21 - apos) * 2
        
        # Différence de buts
        hdiff = home_stats.get("goalDifference", 0); adiff = away_stats.get("goalDifference", 0)
        score_home += hdiff * 0.8; score_away += adiff * 0.8
        
        # Forme récente
        score_home += home_forme["points"] * 2; score_away += away_forme["points"] * 2
        if home_forme["forme_str"].count("V") >= 3: score_home += 8
        if away_forme["forme_str"].count("V") >= 3: score_away += 8
        if home_forme["forme_str"].count("D") >= 3: score_home -= 5
        if away_forme["forme_str"].count("D") >= 3: score_away -= 5
        
        # xG (Expected Goals)
        try:
            home_xg = float(home_advanced['xg_for']) if home_advanced['xg_for'] != 'N/A' else 1.5
            away_xg = float(away_advanced['xg_for']) if away_advanced['xg_for'] != 'N/A' else 1.5
            score_home += home_xg * 3
            score_away += away_xg * 3
        except:
            pass
        
        # Blessures (impact négatif)
        score_home -= len(home_injuries) * 2
        score_away -= len(away_injuries) * 2
        
        # Discipline (pénalité pour équipes indisciplinées)
        try:
            home_cards = int(home_advanced['yellow_cards']) + int(home_advanced['red_cards']) * 3
            away_cards = int(away_advanced['yellow_cards']) + int(away_advanced['red_cards']) * 3
            score_home -= home_cards / 20
            score_away -= away_cards / 20
        except:
            pass
        
        # Importance du match
        if score_home > score_away:
            score_home += score_importance / 10
        else:
            score_away += score_importance / 10
        
        # Calcul match nul
        score_draw += (home_forme["forme_str"].count("N") + away_forme["forme_str"].count("N")) * 3
        
        if home_pos and away_pos and home_points is not None and away_points is not None:
            diff_pos = abs(home_pos - away_pos)
            diff_pts = abs(home_points - away_points)
            if diff_pos <= 3: score_draw += 10
            elif diff_pos <= 6: score_draw += 5
            if diff_pts <= 5: score_draw += 8
            elif diff_pts <= 10: score_draw += 4
            if abs(home_forme["points"] - away_forme["points"]) <= 3: score_draw += 6
            if (home_pos + away_pos) / 2 <= 5: score_draw += 5

        total = score_home + score_away + score_draw
        prob_home = round(score_home / total * 100, 1)
        prob_away = round(score_away / total * 100, 1)
        prob_draw = round(score_draw / total * 100, 1)

        max_prob = max(prob_home, prob_draw, prob_away)
        if max_prob == prob_home:
            rec = f"Victoire {home_team}"
            conf = "Elevee" if prob_home > 50 else "Moyenne" if prob_home > 40 else "Faible"
            best_odd = best_odds["home"]
            best_bookmaker = bookmakers["home"]
        elif max_prob == prob_away:
            rec = f"Victoire {away_team}"
            conf = "Elevee" if prob_away > 50 else "Moyenne" if prob_away > 40 else "Faible"
            best_odd = best_odds["away"]
            best_bookmaker = bookmakers["away"]
        else:
            rec = "Match nul"
            conf = "Elevee" if prob_draw > 40 else "Moyenne" if prob_draw > 33 else "Faible"
            best_odd = best_odds["draw"]
            best_bookmaker = bookmakers["draw"]

        probs_sorted = sorted([prob_home, prob_draw, prob_away], reverse=True)
        tight = probs_sorted[0] - probs_sorted[1] < 10

        # NOUVEAU - Calcul amélioré du nombre de buts
        avg_goals = calculer_buts_probables(
            home_forme, away_forme, home_stats, away_stats, home_advanced, away_advanced
        )

        return jsonify({
            "home_team": home_team,
            "away_team": away_team,
            "home_crest": crests.get(home_team, ""),
            "away_crest": crests.get(away_team, ""),
            "match_date": match.get("utcDate", "")[:10],
            "home_stats": home_stats,
            "away_stats": away_stats,
            "home_forme": home_forme,
            "away_forme": away_forme,
            
            # NOUVELLES DONNÉES
            "home_injuries": home_injuries,
            "away_injuries": away_injuries,
            "home_advanced": home_advanced,
            "away_advanced": away_advanced,
            "match_importance": importance,
            "best_odds": best_odds,
            "bookmakers": bookmakers,
            "recommended_odd": best_odd,
            "recommended_bookmaker": best_bookmaker,
            
            "h2h": h2h_stats,
            "home_scorers": home_scorers,
            "away_scorers": away_scorers,
            "probabilities": {"home": prob_home, "draw": prob_draw, "away": prob_away},
            "recommendation": rec,
            "confidence": conf,
            "tight_match": tight,
            "over_2_5": avg_goals["total"] > 2.5,
            "btts": avg_goals["home"] >= 1 and avg_goals["away"] >= 1,
            "avg_goals": avg_goals
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)