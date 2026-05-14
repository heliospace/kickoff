from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from datetime import datetime

app = Flask(__name__)

# =========================
# CONFIG
# =========================
app.config["SECRET_KEY"] = "kickoff_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kickoff.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# LOGIN
# =========================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =========================
# USER MODEL (WITH AVATAR)
# =========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # avatar system
    avatar = db.Column(db.String(100), default="barca.png")


# =========================
# MATCH MODEL
# =========================
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)
    players = db.Column(db.Integer, nullable=False)
    joined = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


# =========================
# PARTICIPATION MODEL
# =========================
class MatchParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"))


# =========================
# DB INIT
# =========================
with app.app_context():
    db.create_all()


# =========================
# USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# =========================
# HOME
# =========================
@app.route("/")
@login_required
def home():

    matches = Match.query.order_by(
        Match.created.desc()
    ).limit(3).all()

    return render_template(
        "home.html",
        user=current_user,
        matches=matches
    )


# =========================
# CREATE OPTIONS
# =========================
@app.route("/create")
@login_required
def create():
    return render_template("create.html")


# =========================
# CREATE MATCH
# =========================
@app.route("/create_match", methods=["GET", "POST"])
@login_required
def create_match():

    if request.method == "POST":

        match_time = request.form.get("time")

        formatted_time = datetime.strptime(
            match_time,
            "%Y-%m-%dT%H:%M"
        ).strftime("%d %b • %I:%M %p")

        new_match = Match(
            location=request.form.get("location"),
            time=formatted_time,
            players=int(request.form.get("players")),
            user_id=current_user.id
        )

        db.session.add(new_match)
        db.session.commit()

        return redirect("/matches")

    return render_template("create_match.html")


# =========================
# CREATE SCREENING
# =========================
@app.route("/create_screening", methods=["GET", "POST"])
@login_required
def create_screening():

    if request.method == "POST":

        return redirect("/")

    return render_template("create_screening.html")


# =========================
# MATCH FEED
# =========================
@app.route("/matches")
@login_required
def view_matches():

    matches = Match.query.order_by(Match.created.desc()).all()
    participants = MatchParticipant.query.all()
    users = User.query.all()

    return render_template(
        "matches.html",
        matches=matches,
        participants=participants,
        users=users
    )


# =========================
# JOIN MATCH
# =========================
@app.route("/join/<int:match_id>", methods=["POST"])
@login_required
def join_match(match_id):

    match = db.session.get(Match, match_id)

    if not match:
        return redirect("/matches")

    exists = MatchParticipant.query.filter_by(
        user_id=current_user.id,
        match_id=match_id
    ).first()

    if not exists and match.joined < match.players:
        db.session.add(MatchParticipant(
            user_id=current_user.id,
            match_id=match_id
        ))
        match.joined += 1
        db.session.commit()

    return redirect("/matches")


# =========================
# PROFILE
# =========================
@app.route("/profile")
@login_required
def profile():

    user_matches = Match.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "profile.html",
        user=current_user,
        user_matches=user_matches
    )


# =========================
# UPDATE AVATAR
# =========================
@app.route("/update_avatar", methods=["POST"])
@login_required
def update_avatar():

    selected = request.form.get("avatar")

    if selected:
        current_user.avatar = selected
        db.session.commit()

    return redirect("/profile")


# =========================
# STATS
# =========================
@app.route("/stats")
@login_required
def stats():

    total_matches = Match.query.count()

    user_matches = MatchParticipant.query.filter_by(
        user_id=current_user.id
    ).count()

    return render_template(
        "stats.html",
        user=current_user,
        total_matches=total_matches,
        user_matches=user_matches
    )


# =========================
# SIGNUP
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":

        username = request.form.get("username")

        if User.query.filter_by(username=username).first():
            return "Username already exists"

        new_user = User(
            username=username,
            password=request.form.get("password"),
            avatar="barca.png"
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect("/")

    return render_template("signup.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":

        user = User.query.filter_by(
            username=request.form.get("username"),
            password=request.form.get("password")
        ).first()

        if user:
            login_user(user)
            return redirect("/")

        return "Invalid login"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True, port=5002)
