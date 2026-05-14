from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from datetime import datetime, timedelta
from urllib.parse import urlparse

app = Flask(__name__)

# =========================
# CONFIG
# =========================
app.config["SECRET_KEY"] = "kickoff_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kickoff.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

LINEUP_FORMATIONS = {
    "4-3-3": [
        {"key": "gk", "label": "GK", "x": 50, "y": 86},
        {"key": "lb", "label": "LB", "x": 18, "y": 66},
        {"key": "cb1", "label": "CB", "x": 39, "y": 69},
        {"key": "cb2", "label": "CB", "x": 61, "y": 69},
        {"key": "rb", "label": "RB", "x": 82, "y": 66},
        {"key": "cm1", "label": "CM", "x": 28, "y": 45},
        {"key": "cm2", "label": "CM", "x": 50, "y": 50},
        {"key": "cm3", "label": "CM", "x": 72, "y": 45},
        {"key": "lw", "label": "LW", "x": 22, "y": 22},
        {"key": "st", "label": "ST", "x": 50, "y": 17},
        {"key": "rw", "label": "RW", "x": 78, "y": 22}
    ],
    "4-4-2": [
        {"key": "gk", "label": "GK", "x": 50, "y": 86},
        {"key": "lb", "label": "LB", "x": 18, "y": 66},
        {"key": "cb1", "label": "CB", "x": 39, "y": 69},
        {"key": "cb2", "label": "CB", "x": 61, "y": 69},
        {"key": "rb", "label": "RB", "x": 82, "y": 66},
        {"key": "lm", "label": "LM", "x": 18, "y": 43},
        {"key": "cm1", "label": "CM", "x": 39, "y": 48},
        {"key": "cm2", "label": "CM", "x": 61, "y": 48},
        {"key": "rm", "label": "RM", "x": 82, "y": 43},
        {"key": "st1", "label": "ST", "x": 40, "y": 18},
        {"key": "st2", "label": "ST", "x": 60, "y": 18}
    ],
    "3-5-2": [
        {"key": "gk", "label": "GK", "x": 50, "y": 86},
        {"key": "cb1", "label": "CB", "x": 30, "y": 68},
        {"key": "cb2", "label": "CB", "x": 50, "y": 72},
        {"key": "cb3", "label": "CB", "x": 70, "y": 68},
        {"key": "lm", "label": "LM", "x": 16, "y": 46},
        {"key": "cm1", "label": "CM", "x": 36, "y": 49},
        {"key": "cm2", "label": "CM", "x": 50, "y": 42},
        {"key": "cm3", "label": "CM", "x": 64, "y": 49},
        {"key": "rm", "label": "RM", "x": 84, "y": 46},
        {"key": "st1", "label": "ST", "x": 40, "y": 18},
        {"key": "st2", "label": "ST", "x": 60, "y": 18}
    ]
}

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
    name = db.Column(db.String(100), default="")
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), default="")
    location = db.Column(db.String(100), default="")
    favorite_club = db.Column(db.String(100), default="")
    fan_label = db.Column(db.String(100), default="")
    player_level = db.Column(db.String(100), default="")

    # avatar system
    avatar = db.Column(db.String(100), default="barca.png")

    matches_created = db.relationship("Match", back_populates="creator")
    screenings_hosted = db.relationship("Screening", back_populates="creator")
    match_participations = db.relationship("MatchParticipant", back_populates="user")
    joined_matches = db.relationship(
        "Match",
        secondary="match_participant",
        primaryjoin="User.id == MatchParticipant.user_id",
        secondaryjoin="Match.id == MatchParticipant.match_id",
        viewonly=True
    )


# =========================
# MATCH MODEL
# =========================
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)
    starts_at = db.Column(db.DateTime)
    formation = db.Column(db.String(20), default="4-3-3")
    players = db.Column(db.Integer, nullable=False)
    joined = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    creator = db.relationship("User", back_populates="matches_created")
    participants = db.relationship("MatchParticipant", back_populates="match")
    lineup_slots = db.relationship("LineupSlot", back_populates="match")
    joined_users = db.relationship(
        "User",
        secondary="match_participant",
        primaryjoin="Match.id == MatchParticipant.match_id",
        secondaryjoin="User.id == MatchParticipant.user_id",
        viewonly=True
    )

    @property
    def display_time(self):
        if self.starts_at:
            return self.starts_at.strftime("%d %b, %I:%M %p")

        return self.time


# =========================
# SCREENING MODEL
# =========================
class Screening(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)
    starts_at = db.Column(db.DateTime)
    seats = db.Column(db.Integer, nullable=False)
    entry_type = db.Column(db.String(50), default="")
    price = db.Column(db.String(50), default="")
    booking_link = db.Column(db.String(300), default="")
    created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    creator = db.relationship("User", back_populates="screenings_hosted")

    @property
    def display_time(self):
        if self.starts_at:
            return self.starts_at.strftime("%d %b, %I:%M %p")

        return self.time


# =========================
# PARTICIPATION MODEL
# =========================
class MatchParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"))

    user = db.relationship("User", back_populates="match_participations")
    match = db.relationship("Match", back_populates="participants")


# =========================
# LINEUP SLOT MODEL
# =========================
class LineupSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    slot_key = db.Column(db.String(20), nullable=False)

    match = db.relationship("Match", back_populates="lineup_slots")
    user = db.relationship("User")


# =========================
# DB INIT
# =========================
def add_column_if_missing(table_name, column_name, column_definition):
    safe_table = table_name.replace('"', '""')
    safe_column = column_name.replace('"', '""')
    existing_columns = [
        row[1]
        for row in db.session.execute(
            db.text(f'PRAGMA table_info("{safe_table}")')
        )
    ]

    if column_name not in existing_columns:
        db.session.execute(
            db.text(
                f'ALTER TABLE "{safe_table}" '
                f'ADD COLUMN "{safe_column}" {column_definition}'
            )
        )
        db.session.commit()


with app.app_context():
    db.create_all()
    add_column_if_missing("user", "name", "VARCHAR(100) DEFAULT ''")
    add_column_if_missing("user", "position", "VARCHAR(100) DEFAULT ''")
    add_column_if_missing("user", "location", "VARCHAR(100) DEFAULT ''")
    add_column_if_missing("user", "favorite_club", "VARCHAR(100) DEFAULT ''")
    add_column_if_missing("user", "fan_label", "VARCHAR(100) DEFAULT ''")
    add_column_if_missing("user", "player_level", "VARCHAR(100) DEFAULT ''")
    add_column_if_missing("match", "starts_at", "DATETIME")
    add_column_if_missing("match", "formation", "VARCHAR(20) DEFAULT '4-3-3'")
    add_column_if_missing("screening", "starts_at", "DATETIME")


# =========================
# USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def parse_form_datetime(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


def format_event_time(value):
    return value.strftime("%d %b, %I:%M %p")


def is_valid_optional_url(value):
    if not value:
        return True

    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def can_edit_lineup(match):
    if match.user_id != current_user.id:
        return False

    if not match.starts_at:
        return False

    return datetime.now() >= match.starts_at - timedelta(minutes=15)


def get_lineup_players(match):
    users = {}

    if match.creator:
        users[match.creator.id] = match.creator

    for participant in match.participants:
        if participant.user:
            users[participant.user.id] = participant.user

    return list(users.values())


def get_lineup_assignments(match):
    return {
        slot.slot_key: slot.user_id
        for slot in match.lineup_slots
    }


def get_match_feed_context(matches):
    match_ids = [match.id for match in matches]
    participants = []

    if match_ids:
        participants = MatchParticipant.query.filter(
            MatchParticipant.match_id.in_(match_ids)
        ).all()

    users = {
        user.id: user
        for user in User.query.filter(
            User.id.in_([participant.user_id for participant in participants])
        ).all()
    } if participants else {}

    participant_names = {match.id: [] for match in matches}
    joined_match_ids = set()

    seen_pairs = set()

    for participant in participants:
        pair = (participant.match_id, participant.user_id)

        if pair in seen_pairs:
            continue

        seen_pairs.add(pair)
        user = users.get(participant.user_id)

        if user:
            participant_names.setdefault(participant.match_id, []).append(user.username)

        if participant.user_id == current_user.id:
            joined_match_ids.add(participant.match_id)

    for match in matches:
        match.joined = len(participant_names.get(match.id, []))

    return {
        "matches": matches,
        "participant_names": participant_names,
        "joined_match_ids": joined_match_ids
    }


def get_screening_hostnames(screenings):
    host_ids = {screening.user_id for screening in screenings if screening.user_id}

    if not host_ids:
        return {}

    return {
        user.id: user.username
        for user in User.query.filter(User.id.in_(host_ids)).all()
    }


def get_event_feed_context(matches, screenings):
    events = [
        {"type": "match", "item": match}
        for match in matches
    ] + [
        {"type": "screening", "item": screening}
        for screening in screenings
    ]

    events.sort(
        key=lambda event: event["item"].created or datetime.min,
        reverse=True
    )

    return {
        **get_match_feed_context(matches),
        "screenings": screenings,
        "screening_hostnames": get_screening_hostnames(screenings),
        "events": events
    }


# =========================
# HOME
# =========================
@app.route("/")
@login_required
def home():

    matches = Match.query.order_by(
        Match.created.desc()
    ).limit(5).all()

    screenings = Screening.query.order_by(
        Screening.created.desc()
    ).limit(5).all()

    feed_context = get_event_feed_context(matches, screenings)
    feed_context["events"] = feed_context["events"][:5]

    live_scores = [
        {
            "status": "LIVE",
            "minute": "72'",
            "home": "Arsenal",
            "away": "Chelsea",
            "home_score": 2,
            "away_score": 1
        },
        {
            "status": "HT",
            "minute": "45'",
            "home": "Barcelona",
            "away": "Real Madrid",
            "home_score": 0,
            "away_score": 0
        },
        {
            "status": "LIVE",
            "minute": "64'",
            "home": "Inter",
            "away": "Milan",
            "home_score": 1,
            "away_score": 2
        },
        {
            "status": "FT",
            "minute": "90'",
            "home": "Dortmund",
            "away": "Bayern",
            "home_score": 3,
            "away_score": 1
        },
        {
            "status": "UPCOMING",
            "minute": "20:30",
            "home": "PSG",
            "away": "Marseille",
            "home_score": "-",
            "away_score": "-"
        }
    ]

    return render_template(
        "home.html",
        user=current_user,
        live_scores=live_scores,
        **feed_context
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

        location = request.form.get("location", "").strip()
        match_time = request.form.get("time", "").strip()
        players_value = request.form.get("players", "").strip()

        if not location:
            flash("Location is required.", "error")
            return redirect("/create_match")

        if not match_time:
            flash("Time cannot be empty.", "error")
            return redirect("/create_match")

        try:
            players = int(players_value)
        except ValueError:
            flash("Max players must be a number.", "error")
            return redirect("/create_match")

        if players <= 0:
            flash("Max players must be greater than 0.", "error")
            return redirect("/create_match")

        try:
            starts_at = parse_form_datetime(match_time)
        except ValueError:
            flash("Choose a valid date and time.", "error")
            return redirect("/create_match")

        new_match = Match(
            location=location,
            time=format_event_time(starts_at),
            starts_at=starts_at,
            players=players,
            user_id=current_user.id
        )

        db.session.add(new_match)
        db.session.commit()

        flash("Match created.", "success")
        return redirect("/matches")

    return render_template("create_match.html")


# =========================
# CREATE SCREENING
# =========================
@app.route("/create_screening", methods=["GET", "POST"])
@login_required
def create_screening():

    if request.method == "POST":

        match_name = request.form.get("screening_match", "").strip()
        location = request.form.get("location", "").strip()
        screening_time = request.form.get("time", "").strip()
        seats_value = request.form.get("seats", "").strip()
        booking_link = request.form.get("booking_link", "").strip()

        if not match_name:
            flash("Match name is required.", "error")
            return redirect("/create_screening")

        if not location:
            flash("Location is required.", "error")
            return redirect("/create_screening")

        if not screening_time:
            flash("Time cannot be empty.", "error")
            return redirect("/create_screening")

        try:
            seats = int(seats_value)
        except ValueError:
            flash("Max seats must be a number.", "error")
            return redirect("/create_screening")

        if seats <= 0:
            flash("Max seats must be greater than 0.", "error")
            return redirect("/create_screening")

        if not is_valid_optional_url(booking_link):
            flash("Booking link must start with http:// or https://.", "error")
            return redirect("/create_screening")

        try:
            starts_at = parse_form_datetime(screening_time)
        except ValueError:
            flash("Choose a valid date and time.", "error")
            return redirect("/create_screening")

        new_screening = Screening(
            match_name=match_name,
            location=location,
            time=format_event_time(starts_at),
            starts_at=starts_at,
            seats=seats,
            entry_type=request.form.get("entry", "").strip(),
            price=request.form.get("price", ""),
            booking_link=booking_link,
            user_id=current_user.id
        )

        db.session.add(new_screening)
        db.session.commit()

        flash("Screening created.", "success")
        return redirect("/matches")

    return render_template("create_screening.html")


# =========================
# MATCH FEED
# =========================
@app.route("/matches")
@login_required
def view_matches():

    matches = Match.query.order_by(Match.created.desc()).all()
    screenings = Screening.query.order_by(Screening.created.desc()).all()

    return render_template(
        "matches.html",
        **get_event_feed_context(matches, screenings)
    )


# =========================
# JOIN MATCH
# =========================
@app.route("/join/<int:match_id>", methods=["POST"])
@login_required
def join_match(match_id):

    match = db.session.get(Match, match_id)

    if not match:
        flash("Match not found.", "error")
        return redirect("/matches")

    exists = MatchParticipant.query.filter_by(
        user_id=current_user.id,
        match_id=match_id
    ).first()

    if exists:
        flash("You already joined this match.", "info")
        return redirect("/matches")

    match_participants = MatchParticipant.query.filter_by(match_id=match_id).all()
    joined_count = len({
        participant.user_id
        for participant in match_participants
    })

    if joined_count < match.players:
        db.session.add(MatchParticipant(
            user_id=current_user.id,
            match_id=match_id
        ))
        match.joined = joined_count + 1
        db.session.commit()
        flash("You joined this match.", "success")
    else:
        flash("This match is full.", "error")

    return redirect("/matches")


# =========================
# MATCH LINEUP
# =========================
@app.route("/match/<int:match_id>/lineup")
@login_required
def view_lineup(match_id):

    match = db.session.get(Match, match_id)

    if not match:
        flash("Match not found.", "error")
        return redirect("/matches")

    formation = match.formation or "4-3-3"

    if formation not in LINEUP_FORMATIONS:
        formation = "4-3-3"

    unlock_time = None

    if match.starts_at:
        unlock_time = format_event_time(match.starts_at - timedelta(minutes=15))

    return render_template(
        "lineup.html",
        match=match,
        formation=formation,
        formations=LINEUP_FORMATIONS,
        lineup_slots=LINEUP_FORMATIONS[formation],
        assignments=get_lineup_assignments(match),
        lineup_players=get_lineup_players(match),
        can_edit=can_edit_lineup(match),
        is_host=match.user_id == current_user.id,
        unlock_time=unlock_time
    )


@app.route("/match/<int:match_id>/lineup", methods=["POST"])
@login_required
def update_lineup(match_id):

    match = db.session.get(Match, match_id)

    if not match:
        flash("Match not found.", "error")
        return redirect("/matches")

    if match.user_id != current_user.id:
        flash("Only the host can edit the lineup.", "error")
        return redirect(f"/match/{match.id}/lineup")

    if not can_edit_lineup(match):
        flash("Lineup editing unlocks 15 minutes before kickoff.", "info")
        return redirect(f"/match/{match.id}/lineup")

    formation = request.form.get("formation", "4-3-3")

    if formation not in LINEUP_FORMATIONS:
        flash("Choose a valid formation.", "error")
        return redirect(f"/match/{match.id}/lineup")

    eligible_players = {
        player.id
        for player in get_lineup_players(match)
    }

    existing_slots = {
        slot.slot_key: slot
        for slot in match.lineup_slots
    }

    match.formation = formation
    used_user_ids = set()

    for slot in LINEUP_FORMATIONS[formation]:
        selected_user_id = request.form.get(f"slot_{slot['key']}", "").strip()
        user_id = None

        if selected_user_id:
            try:
                user_id = int(selected_user_id)
            except ValueError:
                flash("Invalid player selection.", "error")
                return redirect(f"/match/{match.id}/lineup")

            if user_id not in eligible_players:
                flash("Only joined players can be placed in the lineup.", "error")
                return redirect(f"/match/{match.id}/lineup")

            if user_id in used_user_ids:
                flash("A player can only be assigned to one slot.", "error")
                return redirect(f"/match/{match.id}/lineup")

            used_user_ids.add(user_id)

        lineup_slot = existing_slots.get(slot["key"])

        if not lineup_slot:
            lineup_slot = LineupSlot(
                match_id=match.id,
                slot_key=slot["key"]
            )
            db.session.add(lineup_slot)

        lineup_slot.user_id = user_id

    db.session.commit()
    flash("Lineup saved.", "success")

    return redirect(f"/match/{match.id}/lineup")


# =========================
# PROFILE
# =========================
@app.route("/profile")
@login_required
def profile():

    user_matches = Match.query.filter_by(user_id=current_user.id).all()
    hosted_screenings = Screening.query.filter_by(user_id=current_user.id).all()

    joined_participants = MatchParticipant.query.filter_by(
        user_id=current_user.id
    ).all()
    joined_match_ids = list({
        participant.match_id
        for participant in joined_participants
    })
    joined_matches = []

    if joined_match_ids:
        joined_matches = Match.query.filter(Match.id.in_(joined_match_ids)).all()

    return render_template(
        "profile.html",
        user=current_user,
        user_matches=user_matches,
        joined_matches=joined_matches,
        hosted_screenings=hosted_screenings
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

    matches_created = Match.query.filter_by(user_id=current_user.id).count()
    matches_joined = MatchParticipant.query.filter_by(
        user_id=current_user.id
    ).count()
    screenings_hosted = Screening.query.filter_by(user_id=current_user.id).count()
    total_events_attended = matches_joined

    created_matches = Match.query.filter_by(user_id=current_user.id).all()
    available_spots_filled = sum(match.joined for match in created_matches)

    xp = (
        matches_created * 20
        + matches_joined * 10
        + screenings_hosted * 20
    )
    level = (xp // 100) + 1
    level_progress = xp % 100

    rating = min(
        99,
        50
        + matches_created * 4
        + matches_joined * 3
        + screenings_hosted * 4
        + available_spots_filled
    )

    playmaking = min(99, 55 + matches_created * 5 + screenings_hosted * 2)
    community = min(99, 50 + matches_joined * 5 + available_spots_filled * 2)
    hosting = min(99, 50 + screenings_hosted * 7 + matches_created * 3)
    activity = min(99, 50 + total_events_attended * 4 + matches_created * 3)
    pace = min(99, 55 + matches_joined * 4 + total_events_attended * 2)
    shooting = min(99, 52 + matches_created * 4 + available_spots_filled)
    passing = playmaking
    dribbling = min(99, 55 + total_events_attended * 3 + matches_joined * 2)
    defending = min(99, 50 + available_spots_filled * 2 + matches_created)
    physical = min(99, 55 + activity // 3 + matches_joined)

    return render_template(
        "stats.html",
        user=current_user,
        total_matches=total_matches,
        matches_created=matches_created,
        matches_joined=matches_joined,
        screenings_hosted=screenings_hosted,
        total_events_attended=total_events_attended,
        available_spots_filled=available_spots_filled,
        xp=xp,
        level=level,
        level_progress=level_progress,
        rating=rating,
        playmaking=playmaking,
        community=community,
        hosting=hosting,
        activity=activity,
        pace=pace,
        shooting=shooting,
        passing=passing,
        dribbling=dribbling,
        defending=defending,
        physical=physical
    )


# =========================
# SIGNUP
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect("/signup")

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return redirect("/signup")

        new_user = User(
            name=request.form.get("name", "").strip(),
            username=username,
            password=password,
            avatar="barca.png"
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash("Account created.", "success")
        return redirect("/")

    return render_template("signup.html")


# =========================
# UPDATE PROFILE
# =========================
@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():

    current_user.name = request.form.get("name", "").strip()
    current_user.position = request.form.get("position", "").strip()
    current_user.location = request.form.get("location", "").strip()
    current_user.favorite_club = request.form.get("favorite_club", "").strip()
    current_user.fan_label = request.form.get("fan_label", "").strip()
    current_user.player_level = request.form.get("player_level", "").strip()
    db.session.commit()

    return redirect("/profile")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect("/login")

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            login_user(user)
            flash("Welcome back.", "success")
            return redirect("/")

        flash("Invalid login.", "error")
        return redirect("/login")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect("/login")


# =========================
# ERRORS
# =========================
@app.errorhandler(404)
def not_found(error):
    return render_template(
        "error.html",
        title="Page not found",
        message="That page is not on the pitch.",
        action_url="/",
        action_label="Go Home"
    ), 404


@app.errorhandler(500)
def server_error(error):
    return render_template(
        "error.html",
        title="Something went wrong",
        message="Kickoff hit a rough patch. Try again in a moment.",
        action_url="/",
        action_label="Go Home"
    ), 500


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
