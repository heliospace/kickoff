from flask import Flask, render_template, request, redirect
from datetime import datetime

app = Flask(__name__)

matches = []

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/create_match", methods=["POST"])
def create_match():
    location = request.form.get("location")
    time = request.form.get("time")
    players = request.form.get("players")

    match = {
        "id": len(matches) + 1,
        "location": location,
        "time": time,
        "players": players,
        "joined": [],
        "created": datetime.now()
    }

    matches.append(match)

    return redirect("/matches")


@app.route("/matches")
def view_matches():
    return render_template("matches.html", matches=matches)


@app.route("/join/<int:match_id>", methods=["POST"])
def join_match(match_id):
    name = request.form.get("name")

    for match in matches:
        if match["id"] == match_id:
            match["joined"].append(name)

    return redirect("/matches")


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/stats")
def stats():
    return render_template("stats.html")


if __name__ == "__main__":
    app.run(debug=True)