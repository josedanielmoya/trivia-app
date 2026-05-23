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


@stats_bp.route("/profile")
@login_required
def profile():
    stats = get_or_create_stats(current_user.id)

    # Last 10 finished games where the current user participated
    recent_games = (
        Game.query
        .filter(
            (Game.host_id == current_user.id) | (Game.guest_id == current_user.id),
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