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

# API-Football (RapidAPI) pour xG, blessures, discipline
RAPID_API_KEY = "609aaf31f8mshd5507353f83b325p1905c3jsn9e9003baada"
RAPID_HEADERS = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

# The Odds API pour les côtes
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

def obtenir_blessures(team_id, rapid_league_id, saison="2024"):
    """Récupère les blessures via API-Football ou génère des données de démo"""
    if RAPID_API_KEY == "VOTRE_CLE_RAPIDAPI_ICI":
        return generer_blessures_demo()
    
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/injuries"
        params = {"team": team_id, "league": rapid_league_id, "season": saison}
        r = requests.get(url, headers=RAPID_HEADERS, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        injuries = data.get("response", [])
        return [
            {
                "player": injury["player"]["name"],
                "type": injury["player"]["type"],
                "reason": injury["player"]["reason"]
            }
            for injury in injuries if injury["player"]["type"] != "Missing"
        ][:5]  # Max 5 blessures
    except Exception as e:
        print(f"[BLESSURES] Erreur: {e}")
        return generer_blessures_demo()

def generer_blessures_demo():
    """Génère des blessures de démonstration"""
    nb_blessures = random.randint(0, 3)
    types_blessures = ["Blessure musculaire", "Cheville", "Genou", "Ischio-jambiers", "Aine"]
    prenoms = ["Lucas", "Antoine", "Thomas", "Alexandre", "Nicolas", "Pierre", "Julien"]
    noms = ["Martin", "Bernard", "Dubois", "Moreau", "Simon", "Laurent", "Leroy"]
    
    return [
        {
            "player": f"{random.choice(prenoms)} {random.choice(noms)}",
            "type": random.choice(types_blessures),
            "reason": "Blessure"
        }
        for i in range(nb_blessures)
    ]

def obtenir_statistiques_avancees(team_id, rapid_league_id, saison="2024"):
    """Récupère xG et discipline via API-Football ou génère des données de démo"""
    if RAPID_API_KEY == "VOTRE_CLE_RAPIDAPI_ICI":
        return generer_stats_demo()
    
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/teams/statistics"
        params = {"team": team_id, "league": rapid_league_id, "season": saison}
        r = requests.get(url, headers=RAPID_HEADERS, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        stats = data.get("response", {})
        
        return {
            "xg_for": stats.get("goals", {}).get("for", {}).get("average", {}).get("total", "N/A"),
            "xg_against": stats.get("goals", {}).get("against", {}).get("average", {}).get("total", "N/A"),
            "yellow_cards": stats.get("cards", {}).get("yellow", {}).get("0-15", {}).get("total", 0),
            "red_cards": stats.get("cards", {}).get("red", {}).get("0-15", {}).get("total", 0)
        }
    except Exception as e:
        print(f"[STATS AVANCÉES] Erreur: {e}")
        return generer_stats_demo()

def generer_stats_demo():
    """Génère des statistiques de démonstration"""
    return {
        "xg_for": round(random.uniform(1.2, 2.5), 2),
        "xg_against": round(random.uniform(0.8, 2.0), 2),
        "yellow_cards": random.randint(20, 50),
        "red_cards": random.randint(0, 5)
    }

def calculer_importance_match(home_pos, away_pos, home_points, away_points):
    """Calcule l'importance du match"""
    importance = "Moyenne"
    score_importance = 5
    
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

def obtenir_cotes(home_team, away_team, odds_sport):
    """Récupère les meilleures côtes des bookmakers ou génère des données de démo"""
    if ODDS_API_KEY == "VOTRE_CLE_ODDS_API_ICI":
        return generer_cotes_demo()
    
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{odds_sport}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        for match in data:
            if (home_team.lower() in match["home_team"].lower() or 
                away_team.lower() in match["away_team"].lower()):
                
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
                
                return best_odds, bookmakers
        
    except Exception as e:
        print(f"[CÔTES] Erreur: {e}")
    
    return generer_cotes_demo()

def generer_cotes_demo():
    """Génère des côtes de démonstration"""
    bookmakers_list = ["Betclic", "Unibet", "Winamax", "Parions Sport"]
    
    best_odds = {
        "home": round(random.uniform(1.5, 3.5), 2),
        "draw": round(random.uniform(3.0, 4.0), 2),
        "away": round(random.uniform(1.8, 4.5), 2)
    }
    
    bookmakers = {
        "home": random.choice(bookmakers_list),
        "draw": random.choice(bookmakers_list),
        "away": random.choice(bookmakers_list)
    }
    
    return best_odds, bookmakers

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

        classement = {}; crests = {}
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

        # Récupération des blessures
        home_injuries = obtenir_blessures(home_id, rapid_league_id)
        away_injuries = obtenir_blessures(away_id, rapid_league_id)
        
        # Récupération des stats avancées (xG, discipline)
        home_advanced = obtenir_statistiques_avancees(home_id, rapid_league_id)
        away_advanced = obtenir_statistiques_avancees(away_id, rapid_league_id)
        
        # Calcul de l'importance du match
        home_pos = home_stats.get("position", 10)
        away_pos = away_stats.get("position", 10)
        home_points = home_stats.get("points", 0)
        away_points = away_stats.get("points", 0)
        importance, score_importance = calculer_importance_match(
            home_pos, away_pos, home_points, away_points
        )
        
        # Récupération des côtes
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
        
        # Classement et points
        hp = home_stats.get("points", 0); ap = away_stats.get("points", 0)
        score_home += hp * 0.5; score_away += ap * 0.5
        hpos = home_stats.get("position", 10); apos = away_stats.get("position", 10)
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
        
        # xG (Expected Goals) - NOUVEAU
        try:
            home_xg = float(home_advanced['xg_for']) if home_advanced['xg_for'] != 'N/A' else 1.5
            away_xg = float(away_advanced['xg_for']) if away_advanced['xg_for'] != 'N/A' else 1.5
            score_home += home_xg * 3
            score_away += away_xg * 3
        except:
            pass
        
        # Blessures - NOUVEAU (impact négatif)
        score_home -= len(home_injuries) * 2
        score_away -= len(away_injuries) * 2
        
        # Discipline - NOUVEAU (pénalité pour équipes indisciplinées)
        try:
            home_cards = int(home_advanced['yellow_cards']) + int(home_advanced['red_cards']) * 3
            away_cards = int(away_advanced['yellow_cards']) + int(away_advanced['red_cards']) * 3
            score_home -= home_cards / 20
            score_away -= away_cards / 20
        except:
            pass
        
        # Importance du match - NOUVEAU
        if score_home > score_away:
            score_home += score_importance / 10
        else:
            score_away += score_importance / 10
        
        # Calcul match nul
        score_draw += (home_forme["forme_str"].count("N") + away_forme["forme_str"].count("N")) * 3
        diff_pos = abs(hpos - apos); diff_pts = abs(hp - ap)
        if diff_pos <= 3: score_draw += 10
        elif diff_pos <= 6: score_draw += 5
        if diff_pts <= 5: score_draw += 8
        elif diff_pts <= 10: score_draw += 4
        if abs(home_forme["points"] - away_forme["points"]) <= 3: score_draw += 6
        if (hpos + apos) / 2 <= 5: score_draw += 5

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

        avg_gh = home_forme["buts_marques"] / max(home_forme["nb_matchs"], 1)
        avg_ga = away_forme["buts_marques"] / max(away_forme["nb_matchs"], 1)
        avg_total = avg_gh + avg_ga

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
            "over_2_5": avg_total > 2.5,
            "btts": avg_gh >= 1 and avg_ga >= 1,
            "avg_goals": {"home": round(avg_gh, 1), "away": round(avg_ga, 1), "total": round(avg_total, 1)}
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)