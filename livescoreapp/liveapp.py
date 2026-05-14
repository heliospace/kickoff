import os

from flask import Flask, render_template
import requests

app = Flask(__name__)

API_KEY = os.environ.get("API_FOOTBALL_KEY", "29af64a95867774d1287f1f542d16589")
API_BASE_URL = "https://v3.football.api-sports.io"
SEASON = 2025
LEAGUES = [
    {"id": 39, "name": "Premier League"},
    {"id": 140, "name": "La Liga"},
    {"id": 135, "name": "Serie A"},
    {"id": 78, "name": "Bundesliga"},
]

headers = {
    "x-apisports-key": API_KEY
}

def fetch_fixtures(params):
    response = requests.get(
        f"{API_BASE_URL}/fixtures",
        headers=headers,
        params=params,
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    if data.get("errors"):
        raise RuntimeError(data["errors"])

    return data.get("response", [])


def get_league_matches():
    if not API_KEY:
        return [], "Missing API_FOOTBALL_KEY."

    try:
        live_matches = fetch_fixtures({"live": "all"})
        live_by_league = {
            league["id"]: [
                match for match in live_matches
                if match.get("league", {}).get("id") == league["id"]
            ]
            for league in LEAGUES
        }

        has_live_matches = any(live_by_league.values())
        league_sections = []

        for league in LEAGUES:
            matches = live_by_league[league["id"]]
            message = None

            if not matches:
                matches = fetch_fixtures({
                    "league": league["id"],
                    "season": SEASON,
                    "next": 5
                })

                if has_live_matches:
                    message = "No live matches in this league. Showing upcoming fixtures."
                else:
                    message = "No live matches right now. Showing upcoming fixtures."

            league_sections.append({
                "name": league["name"],
                "matches": matches,
                "message": message
            })

        return league_sections, None

    except requests.exceptions.RequestException as exc:
        return [], f"Could not reach the football API: {exc}"
    except ValueError:
        return [], "Football API returned an invalid response."
    except RuntimeError as exc:
        return [], f"Football API error: {exc}"

@app.route("/")
def home():
    league_sections, message = get_league_matches()
    return render_template(
        "index.html",
        league_sections=league_sections,
        message=message
    )

if __name__ == "__main__":
    app.run(debug=True, port=5001)
