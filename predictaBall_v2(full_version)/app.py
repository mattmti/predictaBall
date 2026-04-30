from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests
import time
import traceback
import random
import io
from datetime import datetime

# --- ReportLab imports ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

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
    print(f"[BLESSURES] Mode démo pour {team_name}")
    return generer_blessures_demo()

def generer_blessures_demo():
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
    print(f"[STATS AVANCÉES] Mode démo pour {team_name}")
    return generer_stats_demo()

def generer_stats_demo():
    return {
        "xg_for": round(random.uniform(1.2, 2.5), 2),
        "xg_against": round(random.uniform(0.8, 2.0), 2),
        "yellow_cards": random.randint(20, 50),
        "red_cards": random.randint(0, 5)
    }

def calculer_importance_match(home_pos, away_pos, home_points, away_points, competition_stage=None):
    importance = "Moyenne"
    score_importance = 5
    if competition_stage and competition_stage in ["FINAL", "SEMI_FINALS", "QUARTER_FINALS", "ROUND_OF_16", "LAST_16"]:
        stage_importance = {
            "FINAL": ("FINALE - Enjeu maximum", 15),
            "SEMI_FINALS": ("DEMI-FINALE - Enjeu très élevé", 12),
            "QUARTER_FINALS": ("QUART DE FINALE - Enjeu élevé", 10),
            "ROUND_OF_16": ("HUITIÈME DE FINALE - Enjeu élevé", 10),
            "LAST_16": ("HUITIÈME DE FINALE - Enjeu élevé", 10)
        }
        return stage_importance.get(competition_stage, ("Match à élimination directe", 8))
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
    import unicodedata
    nom = unicodedata.normalize('NFD', nom).encode('ascii', 'ignore').decode('utf-8')
    nom = nom.lower()
    mots_a_retirer = ['fc', 'cf', 'ac', 'afc', 'bfc', 'rc', 'as', 'sporting', 'club', 'united', 'city']
    mots = nom.split()
    mots_filtres = [m for m in mots if m not in mots_a_retirer]
    return ' '.join(mots_filtres) if mots_filtres else nom

def trouver_match_odds(home_team, away_team, odds_data):
    home_normalized = normaliser_nom_equipe(home_team)
    away_normalized = normaliser_nom_equipe(away_team)
    for match in odds_data:
        match_home = normaliser_nom_equipe(match.get("home_team", ""))
        match_away = normaliser_nom_equipe(match.get("away_team", ""))
        if match_home == home_normalized and match_away == away_normalized:
            return match
        home_mots = set(home_normalized.split())
        away_mots = set(away_normalized.split())
        match_home_mots = set(match_home.split())
        match_away_mots = set(match_away.split())
        if (home_mots & match_home_mots) and (away_mots & match_away_mots):
            return match
    return None

def obtenir_cotes(home_team, away_team, odds_sport):
    if ODDS_API_KEY == "VOTRE_CLE_ODDS_API_ICI":
        return generer_cotes_demo()
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{odds_sport}/odds"
        params = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        match = trouver_match_odds(home_team, away_team, data)
        if match:
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
            if best_odds["home"] > 0:
                return best_odds, bookmakers
    except Exception as e:
        print(f"[CÔTES] Erreur: {e}")
    return generer_cotes_demo()

def generer_cotes_demo():
    bookmakers_list = ["Betclic", "Unibet", "Winamax", "Parions Sport"]
    prob_home = random.uniform(0.25, 0.55)
    prob_draw = random.uniform(0.20, 0.30)
    prob_away = 1 - prob_home - prob_draw
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
    home_buts_forme = home_forme["buts_marques"] / max(home_forme["nb_matchs"], 1)
    away_buts_forme = away_forme["buts_marques"] / max(away_forme["nb_matchs"], 1)
    home_def = home_forme["buts_encaisses"] / max(home_forme["nb_matchs"], 1)
    away_def = away_forme["buts_encaisses"] / max(away_forme["nb_matchs"], 1)
    try:
        home_xg = float(home_advanced['xg_for']) if home_advanced['xg_for'] != 'N/A' else home_buts_forme
        away_xg = float(away_advanced['xg_for']) if away_advanced['xg_for'] != 'N/A' else away_buts_forme
    except:
        home_xg = home_buts_forme
        away_xg = away_buts_forme
    home_attaque = (0.4 * home_buts_forme) + (0.4 * home_xg) + (0.2 * home_stats.get("goalsFor", 0) / 18)
    away_attaque = (0.4 * away_buts_forme) + (0.4 * away_xg) + (0.2 * away_stats.get("goalsFor", 0) / 18)
    buts_home = (home_attaque + away_def) / 2 + 0.2
    buts_away = (away_attaque + home_def) / 2 - 0.1
    if home_forme["forme_str"].count("V") >= 3: buts_home *= 1.1
    if away_forme["forme_str"].count("V") >= 3: buts_away *= 1.1
    if home_forme["forme_str"].count("D") >= 3: buts_home *= 0.9
    if away_forme["forme_str"].count("D") >= 3: buts_away *= 0.9
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
        competition_stage = match.get("stage", None)
        classement = {}; crests = {}
        home_stats = {}; away_stats = {}
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
        home_injuries = obtenir_blessures(home_team, rapid_league_id)
        away_injuries = obtenir_blessures(away_team, rapid_league_id)
        home_advanced = obtenir_statistiques_avancees(home_team, rapid_league_id)
        away_advanced = obtenir_statistiques_avancees(away_team, rapid_league_id)
        home_pos = home_stats.get("position", None)
        away_pos = away_stats.get("position", None)
        home_points = home_stats.get("points", None)
        away_points = away_stats.get("points", None)
        importance, score_importance = calculer_importance_match(
            home_pos, away_pos, home_points, away_points, competition_stage
        )
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
        score_home = 50; score_away = 50; score_draw = 30
        score_home += 10
        if home_points is not None and away_points is not None:
            hp = home_points; ap = away_points
            score_home += hp * 0.5; score_away += ap * 0.5
            if home_pos and away_pos:
                hpos = home_pos; apos = away_pos
                score_home += (21 - hpos) * 2; score_away += (21 - apos) * 2
        hdiff = home_stats.get("goalDifference", 0); adiff = away_stats.get("goalDifference", 0)
        score_home += hdiff * 0.8; score_away += adiff * 0.8
        score_home += home_forme["points"] * 2; score_away += away_forme["points"] * 2
        if home_forme["forme_str"].count("V") >= 3: score_home += 8
        if away_forme["forme_str"].count("V") >= 3: score_away += 8
        if home_forme["forme_str"].count("D") >= 3: score_home -= 5
        if away_forme["forme_str"].count("D") >= 3: score_away -= 5
        try:
            home_xg = float(home_advanced['xg_for']) if home_advanced['xg_for'] != 'N/A' else 1.5
            away_xg = float(away_advanced['xg_for']) if away_advanced['xg_for'] != 'N/A' else 1.5
            score_home += home_xg * 3
            score_away += away_xg * 3
        except:
            pass
        score_home -= len(home_injuries) * 2
        score_away -= len(away_injuries) * 2
        try:
            home_cards = int(home_advanced['yellow_cards']) + int(home_advanced['red_cards']) * 3
            away_cards = int(away_advanced['yellow_cards']) + int(away_advanced['red_cards']) * 3
            score_home -= home_cards / 20
            score_away -= away_cards / 20
        except:
            pass
        if score_home > score_away:
            score_home += score_importance / 10
        else:
            score_away += score_importance / 10
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


# ─────────────────────────────────────────────────────────────
#  NOUVEAU : Génération du rapport PDF
# ─────────────────────────────────────────────────────────────

# Palette de couleurs
C_BG        = colors.HexColor("#080c0f")
C_GREEN     = colors.HexColor("#00ff87")
C_GREEN2    = colors.HexColor("#00c96b")
C_BLUE      = colors.HexColor("#4db8ff")
C_YELLOW    = colors.HexColor("#ffd700")
C_RED       = colors.HexColor("#ff3e5b")
C_TEXT      = colors.HexColor("#e8f0f5")
C_MUTED     = colors.HexColor("#5a7080")
C_CARD      = colors.HexColor("#111820")
C_BORDER    = colors.HexColor("#1e2d38")
C_DARK2     = colors.HexColor("#0d1318")
C_WHITE     = colors.white

def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles['title_main'] = ParagraphStyle(
        'title_main', parent=base['Normal'],
        fontName='Helvetica-Bold', fontSize=28, textColor=C_TEXT,
        spaceAfter=4, alignment=TA_CENTER, leading=34
    )
    styles['subtitle'] = ParagraphStyle(
        'subtitle', parent=base['Normal'],
        fontName='Helvetica', fontSize=11, textColor=C_GREEN,
        spaceAfter=2, alignment=TA_CENTER, leading=14
    )
    styles['label'] = ParagraphStyle(
        'label', parent=base['Normal'],
        fontName='Helvetica', fontSize=7, textColor=C_MUTED,
        spaceAfter=2, alignment=TA_CENTER, leading=9, letterSpacing=1.5
    )
    styles['section_header'] = ParagraphStyle(
        'section_header', parent=base['Normal'],
        fontName='Helvetica-Bold', fontSize=9, textColor=C_GREEN,
        spaceBefore=6, spaceAfter=6, leading=11
    )
    styles['body'] = ParagraphStyle(
        'body', parent=base['Normal'],
        fontName='Helvetica', fontSize=9, textColor=C_TEXT,
        spaceAfter=4, leading=13
    )
    styles['mono'] = ParagraphStyle(
        'mono', parent=base['Normal'],
        fontName='Helvetica', fontSize=8, textColor=C_MUTED,
        spaceAfter=2, leading=11
    )
    styles['team_name'] = ParagraphStyle(
        'team_name', parent=base['Normal'],
        fontName='Helvetica-Bold', fontSize=16, textColor=C_TEXT,
        alignment=TA_CENTER, leading=20, spaceAfter=2
    )
    styles['team_label'] = ParagraphStyle(
        'team_label', parent=base['Normal'],
        fontName='Helvetica', fontSize=7, textColor=C_MUTED,
        alignment=TA_CENTER, leading=9
    )
    styles['big_prob'] = ParagraphStyle(
        'big_prob', parent=base['Normal'],
        fontName='Helvetica-Bold', fontSize=22, textColor=C_GREEN,
        alignment=TA_CENTER, leading=26
    )
    styles['big_prob_draw'] = ParagraphStyle(
        'big_prob_draw', parent=base['Normal'],
        fontName='Helvetica-Bold', fontSize=16, textColor=C_YELLOW,
        alignment=TA_CENTER, leading=20
    )
    styles['big_prob_away'] = ParagraphStyle(
        'big_prob_away', parent=base['Normal'],
        fontName='Helvetica-Bold', fontSize=22, textColor=C_BLUE,
        alignment=TA_CENTER, leading=26
    )
    styles['rec_main'] = ParagraphStyle(
        'rec_main', parent=base['Normal'],
        fontName='Helvetica-Bold', fontSize=14, textColor=C_GREEN,
        alignment=TA_CENTER, leading=18, spaceBefore=4, spaceAfter=4
    )
    styles['footer'] = ParagraphStyle(
        'footer', parent=base['Normal'],
        fontName='Helvetica', fontSize=7, textColor=C_MUTED,
        alignment=TA_CENTER, leading=10
    )
    return styles


def forme_str_to_text(forme_str):
    """Convertit 'VVD NV' en texte lisible"""
    mapping = {"V": "Vic", "N": "Nul", "D": "Def"}
    parts = [mapping.get(c, c) for c in forme_str]
    return "  |  ".join(parts)


def table_style_dark(extra=None):
    base = [
        ('BACKGROUND', (0, 0), (-1, 0), C_DARK2),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_GREEN),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), C_TEXT),
        ('BACKGROUND', (0, 1), (-1, -1), C_CARD),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_CARD, colors.HexColor("#141d24")]),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 0), (-1, 0), [C_DARK2]),
    ]
    if extra:
        base.extend(extra)
    return TableStyle(base)


def generate_pdf_report(data: dict) -> bytes:
    buffer = io.BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN = 18 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f"PredictaBall — {data['home_team']} vs {data['away_team']}",
        author="PredictaBall"
    )

    s = build_styles()
    story = []
    content_width = PAGE_W - 2 * MARGIN

    # ── Fonction utilitaire background de page ──────────────────────────────
    def add_page_bg(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFillColor(C_BG)
        canvas_obj.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Ligne verte en haut
        canvas_obj.setFillColor(C_GREEN)
        canvas_obj.rect(0, PAGE_H - 3, PAGE_W, 3, fill=1, stroke=0)
        canvas_obj.restoreState()

    # ── HEADER ───────────────────────────────────────────────────────────────
    story.append(Paragraph("PREDICTABALL", s['title_main']))
    story.append(Paragraph("RAPPORT D'ANALYSE PREDICTIVE", s['subtitle']))
    story.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %Hh%M')}",
        s['label']
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_GREEN, spaceAfter=6 * mm))

    # ── IMPORTANCE ───────────────────────────────────────────────────────────
    if data.get("match_importance"):
        imp_table = Table(
            [[Paragraph("IMPORTANCE DU MATCH", s['label']),
              Paragraph(f"⚡ {data['match_importance']}", s['subtitle'])]],
            colWidths=[content_width * 0.35, content_width * 0.65]
        )
        imp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0a1a0f")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#00ff8740")),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(imp_table)
        story.append(Spacer(1, 5 * mm))

    # ── ÉQUIPES & PROBABILITÉS ───────────────────────────────────────────────
    home = data['home_team']
    away = data['away_team']
    prob_h = data['probabilities']['home']
    prob_d = data['probabilities']['draw']
    prob_a = data['probabilities']['away']
    match_date = data.get('match_date', '')

    col = content_width / 3

    teams_data = [[
        Paragraph(home, s['team_name']),
        Paragraph("VS", ParagraphStyle('vs', parent=s['subtitle'], fontSize=20, textColor=C_BORDER, alignment=TA_CENTER)),
        Paragraph(away, s['team_name']),
    ], [
        Paragraph("DOMICILE", s['team_label']),
        Paragraph(match_date, s['label']),
        Paragraph("EXTERIEUR", s['team_label']),
    ]]
    teams_table = Table(teams_data, colWidths=[col, col, col])
    teams_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_CARD),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(teams_table)
    story.append(Spacer(1, 4 * mm))

    # Barres de probabilités
    prob_data = [[
        Paragraph(f"{prob_h}%", s['big_prob']),
        Paragraph(f"NUL\n{prob_d}%", s['big_prob_draw']),
        Paragraph(f"{prob_a}%", s['big_prob_away']),
    ], [
        Paragraph(home, s['label']),
        Paragraph("", s['label']),
        Paragraph(away, s['label']),
    ]]
    prob_table = Table(prob_data, colWidths=[col, col, col])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0a1520")),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEAFTER', (0, 0), (1, -1), 0.5, C_BORDER),
    ]))
    story.append(prob_table)
    story.append(Spacer(1, 4 * mm))

    # ── PRONOSTIC ────────────────────────────────────────────────────────────
    conf = data.get('confidence', '')
    conf_color = {'Elevee': C_GREEN, 'Moyenne': C_YELLOW, 'Faible': C_RED}.get(conf, C_TEXT)
    conf_label = {'Elevee': 'CONFIANCE ELEVEE', 'Moyenne': 'CONFIANCE MOYENNE', 'Faible': 'CONFIANCE FAIBLE'}.get(conf, conf)

    rec_data = [[
        Paragraph(f"PRONOSTIC : {data['recommendation']}", s['rec_main']),
        Paragraph(conf_label, ParagraphStyle('conf', parent=s['label'], textColor=conf_color, alignment=TA_CENTER, fontSize=8)),
    ]]
    rec_table = Table(rec_data, colWidths=[content_width * 0.7, content_width * 0.3])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0a1a0f")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#00ff8760")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(rec_table)

    # Avertissement match serré
    if data.get('tight_match'):
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            "⚠ Probabilités serrées — match incertain, jouer avec prudence",
            ParagraphStyle('warn', parent=s['mono'], textColor=C_YELLOW, alignment=TA_CENTER)
        ))

    story.append(Spacer(1, 5 * mm))

    # ── MEILLEURES CÔTES ─────────────────────────────────────────────────────
    if data.get('best_odds'):
        story.append(Paragraph("MEILLEURES COTES DES BOOKMAKERS", s['section_header']))
        bo = data['best_odds']
        bm = data.get('bookmakers', {})
        odds_data = [
            ['VICTOIRE ' + home.upper(), 'MATCH NUL', 'VICTOIRE ' + away.upper()],
            [str(bo.get('home', '-')), str(bo.get('draw', '-')), str(bo.get('away', '-'))],
            [bm.get('home', ''), bm.get('draw', ''), bm.get('away', '')],
        ]
        odds_table = Table(odds_data, colWidths=[col, col, col])
        odds_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_DARK2),
            ('TEXTCOLOR', (0, 0), (-1, 0), C_MUTED),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BACKGROUND', (0, 1), (-1, 1), C_CARD),
            ('TEXTCOLOR', (0, 1), (-1, 1), C_TEXT),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'), ('FONTSIZE', (0, 1), (-1, 1), 20),
            ('BACKGROUND', (0, 2), (-1, 2), C_CARD),
            ('TEXTCOLOR', (0, 2), (-1, 2), C_GREEN),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'), ('FONTSIZE', (0, 2), (-1, 2), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(odds_table)
        story.append(Spacer(1, 5 * mm))

    # ── INSIGHTS OVER/UNDER & BTTS ───────────────────────────────────────────
    story.append(Paragraph("PREDICTIONS COMPLEMENTAIRES", s['section_header']))
    avg = data.get('avg_goals', {})
    over = data.get('over_2_5', False)
    btts = data.get('btts', False)

    insights_data = [
        ['INDICATEUR', 'PREDICTION', 'DETAIL'],
        ['Plus de 2.5 buts', 'OUI' if over else 'NON', f"{avg.get('total', '?')} buts estimés"],
        ['Les deux equipes marquent (BTTS)', 'OUI' if btts else 'NON',
         f"Dom: {avg.get('home','?')} but(s) | Ext: {avg.get('away','?')} but(s)"],
    ]
    ins_table = Table(insights_data, colWidths=[content_width * 0.45, content_width * 0.2, content_width * 0.35])
    ins_extra = [
        ('TEXTCOLOR', (1, 1), (1, 1), C_GREEN if over else C_RED),
        ('TEXTCOLOR', (1, 2), (1, 2), C_GREEN if btts else C_RED),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
    ]
    ins_table.setStyle(table_style_dark(ins_extra))
    story.append(ins_table)
    story.append(Spacer(1, 5 * mm))

    # ── CLASSEMENT & FORME ───────────────────────────────────────────────────
    story.append(Paragraph("CLASSEMENT & FORME RECENTE", s['section_header']))
    hs = data.get('home_stats', {})
    as_ = data.get('away_stats', {})
    hf = data.get('home_forme', {})
    af = data.get('away_forme', {})

    stats_rows = [
        ['STATISTIQUE', home, away],
        ['Position', f"#{hs.get('position', '-')}", f"#{as_.get('position', '-')}"],
        ['Points', str(hs.get('points', '-')), str(as_.get('points', '-'))],
        ['Buts marqués', str(hs.get('goalsFor', '-')), str(as_.get('goalsFor', '-'))],
        ['Buts encaissés', str(hs.get('goalsAgainst', '-')), str(as_.get('goalsAgainst', '-'))],
        ['Diff. buts', str(hs.get('goalDifference', '-')), str(as_.get('goalDifference', '-'))],
        ['V / N / D', f"{hs.get('wins','-')}V {hs.get('draws','-')}N {hs.get('losses','-')}D",
                      f"{as_.get('wins','-')}V {as_.get('draws','-')}N {as_.get('losses','-')}D"],
        ['Forme récente (5 matchs)', forme_str_to_text(hf.get('forme_str', '')), forme_str_to_text(af.get('forme_str', ''))],
        ['Buts marqués (forme)', str(hf.get('buts_marques', '-')), str(af.get('buts_marques', '-'))],
        ['Buts encaissés (forme)', str(hf.get('buts_encaisses', '-')), str(af.get('buts_encaisses', '-'))],
    ]
    col1 = content_width * 0.40
    col2 = (content_width - col1) / 2
    stats_table = Table(stats_rows, colWidths=[col1, col2, col2])
    stats_table.setStyle(table_style_dark([
        ('FONTNAME', (1, 0), (2, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), C_GREEN),
        ('TEXTCOLOR', (2, 0), (2, 0), C_BLUE),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 5 * mm))

    # ── STATS AVANCÉES ───────────────────────────────────────────────────────
    ha = data.get('home_advanced', {})
    aa = data.get('away_advanced', {})
    if ha or aa:
        story.append(Paragraph("STATISTIQUES AVANCEES (xG & DISCIPLINE)", s['section_header']))
        adv_rows = [
            ['INDICATEUR', home, away],
            ['xG moyen (pour)', str(ha.get('xg_for', '-')), str(aa.get('xg_for', '-'))],
            ['xG moyen (contre)', str(ha.get('xg_against', '-')), str(aa.get('xg_against', '-'))],
            ['Cartons jaunes (saison)', str(ha.get('yellow_cards', '-')), str(aa.get('yellow_cards', '-'))],
            ['Cartons rouges (saison)', str(ha.get('red_cards', '-')), str(aa.get('red_cards', '-'))],
        ]
        adv_table = Table(adv_rows, colWidths=[col1, col2, col2])
        adv_table.setStyle(table_style_dark([
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (1, 0), (1, 0), C_GREEN),
            ('TEXTCOLOR', (2, 0), (2, 0), C_BLUE),
        ]))
        story.append(adv_table)
        story.append(Spacer(1, 5 * mm))

    # ── BLESSURES ────────────────────────────────────────────────────────────
    hi = data.get('home_injuries', [])
    ai = data.get('away_injuries', [])
    story.append(Paragraph("BLESSURES CONNUES", s['section_header']))
    inj_rows = [['EQUIPE', 'JOUEUR', 'TYPE']]
    for inj in hi:
        inj_rows.append([home, inj.get('player', '-'), inj.get('type', '-')])
    for inj in ai:
        inj_rows.append([away, inj.get('player', '-'), inj.get('type', '-')])
    if len(inj_rows) == 1:
        inj_rows.append(['—', 'Aucune blessure majeure connue', '—'])
    inj_table = Table(inj_rows, colWidths=[col2, col1, col2])
    inj_extra = []
    for i, row in enumerate(inj_rows[1:], 1):
        if row[0] == home:
            inj_extra.append(('TEXTCOLOR', (0, i), (0, i), C_GREEN))
        elif row[0] == away:
            inj_extra.append(('TEXTCOLOR', (0, i), (0, i), C_BLUE))
    inj_table.setStyle(table_style_dark(inj_extra))
    story.append(inj_table)
    story.append(Spacer(1, 5 * mm))

    # ── H2H ──────────────────────────────────────────────────────────────────
    h2h = data.get('h2h')
    if h2h:
        story.append(Paragraph("CONFRONTATIONS DIRECTES (5 DERNIERS MATCHS)", s['section_header']))

        # Score global H2H
        h2h_score_data = [[
            Paragraph(str(h2h['victoires_home']), s['big_prob']),
            Paragraph(f"V — {h2h['nuls']} N — ", s['big_prob_draw']),
            Paragraph(str(h2h['victoires_away']), s['big_prob_away']),
        ]]
        h2h_score_table = Table(h2h_score_data, colWidths=[col, col, col])
        h2h_score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_CARD),
            ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(h2h_score_table)
        story.append(Spacer(1, 2 * mm))

        # Liste des matchs H2H
        h2h_rows = [['DATE', 'DOMICILE', 'SCORE', 'EXTERIEUR', 'RESULTAT']]
        for m in h2h.get('matchs', []):
            h2h_rows.append([
                m.get('date', ''),
                m.get('home', ''),
                m.get('score', ''),
                m.get('away', ''),
                m.get('resultat', ''),
            ])
        if len(h2h_rows) > 1:
            cw = content_width / 5
            h2h_table = Table(h2h_rows, colWidths=[cw * 0.8, cw * 1.4, cw * 0.6, cw * 1.4, cw * 0.8])
            h2h_table.setStyle(table_style_dark([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            story.append(h2h_table)
        story.append(Spacer(1, 5 * mm))

    # ── TOP BUTEURS ──────────────────────────────────────────────────────────
    home_scorers = data.get('home_scorers', [])
    away_scorers = data.get('away_scorers', [])
    if home_scorers or away_scorers:
        story.append(Paragraph("TOP BUTEURS", s['section_header']))
        scorer_rows = [['#', 'JOUEUR', 'EQUIPE', 'BUTS', 'PASSES DEC.']]
        for i, sc in enumerate(home_scorers, 1):
            scorer_rows.append([str(i), sc.get('name', ''), home, str(sc.get('goals', 0)), str(sc.get('assists', 0))])
        for i, sc in enumerate(away_scorers, 1):
            scorer_rows.append([str(i), sc.get('name', ''), away, str(sc.get('goals', 0)), str(sc.get('assists', 0))])
        if len(scorer_rows) > 1:
            cw2 = content_width / 5
            sc_table = Table(scorer_rows, colWidths=[cw2 * 0.4, cw2 * 1.6, cw2 * 1.4, cw2 * 0.8, cw2 * 0.8])
            sc_table.setStyle(table_style_dark([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            story.append(sc_table)
        story.append(Spacer(1, 5 * mm))

    # ── DISCLAIMER ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=4 * mm, spaceAfter=4 * mm))
    story.append(Paragraph(
        "Ce rapport est généré automatiquement par PredictaBall à des fins d'analyse uniquement. "
        "Les probabilités sont basées sur des données statistiques et ne constituent pas des conseils de paris. "
        "Les données de blessures et xG sont en mode démonstration.",
        s['footer']
    ))
    story.append(Paragraph("PredictaBall — by Matteo Monti", s['footer']))

    doc.build(story, onFirstPage=add_page_bg, onLaterPages=add_page_bg)
    buffer.seek(0)
    return buffer.read()


@app.route("/api/report/<int:match_id>/<league_code>")
def generate_report(match_id, league_code):
    """Génère et retourne un rapport PDF pour le match donné"""
    try:
        # Récupérer les données d'analyse (réutilisation de la logique predict)
        predict_response = predict_match(match_id, league_code)

        # Extraire le JSON de la réponse Flask
        if predict_response.status_code != 200:
            return predict_response

        analysis_data = predict_response.get_json()

        # Générer le PDF
        pdf_bytes = generate_pdf_report(analysis_data)

        home = analysis_data.get('home_team', 'home').replace(' ', '_')
        away = analysis_data.get('away_team', 'away').replace(' ', '_')
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"PredictaBall_{home}_vs_{away}_{date_str}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erreur génération PDF : {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)