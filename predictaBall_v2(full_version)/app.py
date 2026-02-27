from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
import time
import traceback

app = Flask(__name__, static_folder='../frontend')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": "5bce38997bd948849ceb02b50334bc6f"}

LEAGUES = {
    "1": {"name": "Ligue 1", "code": "FL1"},
    "2": {"name": "Premier League", "code": "PL"},
    "3": {"name": "La Liga", "code": "PD"},
    "4": {"name": "Bundesliga", "code": "BL1"},
    "5": {"name": "Serie A", "code": "SA"},
    "6": {"name": "Ligue des Champions", "code": "CL"}
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
        hp = home_stats.get("points", 0); ap = away_stats.get("points", 0)
        score_home += hp * 0.5; score_away += ap * 0.5
        hpos = home_stats.get("position", 10); apos = away_stats.get("position", 10)
        score_home += (21 - hpos) * 2; score_away += (21 - apos) * 2
        hdiff = home_stats.get("goalDifference", 0); adiff = away_stats.get("goalDifference", 0)
        score_home += hdiff * 0.8; score_away += adiff * 0.8
        score_home += home_forme["points"] * 2; score_away += away_forme["points"] * 2
        if home_forme["forme_str"].count("V") >= 3: score_home += 8
        if away_forme["forme_str"].count("V") >= 3: score_away += 8
        if home_forme["forme_str"].count("D") >= 3: score_home -= 5
        if away_forme["forme_str"].count("D") >= 3: score_away -= 5
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
        elif max_prob == prob_away:
            rec = f"Victoire {away_team}"
            conf = "Elevee" if prob_away > 50 else "Moyenne" if prob_away > 40 else "Faible"
        else:
            rec = "Match nul"
            conf = "Elevee" if prob_draw > 40 else "Moyenne" if prob_draw > 33 else "Faible"

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