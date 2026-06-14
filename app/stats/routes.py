import io
from flask import Blueprint, render_template, send_file, make_response
from flask_login import login_required, current_user

from app.models import db, User, Game, Answer, UserStats
from app.stats.charts import generate_category_chart

stats_bp = Blueprint("stats", __name__)


def get_or_create_stats(user_id):
    """Returns the UserStats row for a user, creating it if it doesn't exist."""
    stats = UserStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = UserStats(user_id=user_id)
        db.session.add(stats)
        db.session.commit()
    return stats


@stats_bp.route("/ranking")
@login_required
def ranking():
    # Fetch all UserStats ordered by wins, then total correct answers as tiebreaker
    all_stats = (
        UserStats.query
        .join(User, UserStats.user_id == User.id)
        .order_by(UserStats.total_wins.desc(), UserStats.total_correct.desc())
        .all()
    )
    return render_template("stats/ranking.html", all_stats=all_stats)


import random
import string
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, UserStats
from app.auth.forms import RegisterForm, LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        # Create empty stats record on registration
        stats = UserStats(user_id=user.id)
        db.session.add(stats)
        db.session.commit()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(next_page or url_for("index"))
        flash("Invalid username or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/guest", methods=["POST"])
def guest_login():
    """Generates a random guest account and logs them in automatically."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
        
    # Generate random guest credentials
    random_suffix = ''.join(random.choices(string.digits, k=4))
    username = f"Guest_{random_suffix}"
    email = f"guest_{random_suffix}@trivia.local"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Ensure username is unique just in case
    while User.query.filter_by(username=username).first():
        random_suffix = ''.join(random.choices(string.digits, k=4))
        username = f"Guest_{random_suffix}"
        email = f"guest_{random_suffix}@trivia.local"
        
    # Create and save the guest user
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    
    # Create empty stats record
    stats = UserStats(user_id=user.id)
    db.session.add(stats)
    db.session.commit()
    
    # Log them in automatically
    login_user(user)
    flash(f"Playing as {username}. Have fun!", "success")
    return redirect(url_for("index"))

@stats_bp.route("/profile")
@login_required
def profile():
    stats = get_or_create_stats(current_user.id)

    # Last 10 finished games where the current user participated (as host or player)
    recent_games = (
        Game.query
        .filter(
            Game.players.any(User.id == current_user.id),
            Game.status == "done",
        )
        .order_by(Game.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template("stats/profile.html", stats=stats, recent_games=recent_games)



@stats_bp.route("/chart/categories.png")
@login_required
def category_chart():
    """Serves the category accuracy chart as a PNG image."""
    answers = Answer.query.filter_by(user_id=current_user.id).all()
    img_bytes = generate_category_chart(answers)
    return send_file(io.BytesIO(img_bytes), mimetype="image/png")


@stats_bp.route("/export/csv")
@login_required
def export_csv():
    """Exports the current user's full answer history as a downloadable CSV file."""
    answers = Answer.query.filter_by(user_id=current_user.id).all()
    csv_content = _build_csv(answers)
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = "attachment; filename=my_trivia_history.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


def _build_csv(answers) -> str:
    """Builds the CSV string from a list of Answer objects."""
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Game", "Category", "Question", "Your Answer",
                     "Correct Answer", "Correct?", "Time (s)"])
    for a in answers:
        writer.writerow([
            a.game_id,
            a.category or "—",
            a.question_text,
            a.given_answer or "—",
            a.correct_answer,
            "Yes" if a.is_correct else "No",
            f"{a.time_taken:.1f}",
        ])
    return output.getvalue()