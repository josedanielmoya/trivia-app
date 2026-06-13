import random
import string
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.models import db, Game, Answer
from app.game.trivia_api import TriviaAPI

game_bp = Blueprint("game", __name__)

def update_stats_after_game(game):
    """
    Calculates the winner and updates UserStats for both players
    at the end of a finished game.
    Called once when both players have answered all questions.
    """
    from app.models import UserStats

    def get_or_create_stats(user_id):
        s = UserStats.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserStats(user_id=user_id)
            db.session.add(s)
        return s

    host_answers = Answer.query.filter_by(game_id=game.id, user_id=game.host_id).all()
    guest_answers = Answer.query.filter_by(game_id=game.id, user_id=game.guest_id).all()

    host_score = sum(1 for a in host_answers if a.is_correct)
    guest_score = sum(1 for a in guest_answers if a.is_correct)

    # Determine winner (winner_id stays None on a draw)
    if host_score > guest_score:
        game.winner_id = game.host_id
    elif guest_score > host_score:
        game.winner_id = game.guest_id

    game.status = "done"

    # Update stats for both players
    for user_id, answers, won in [
        (game.host_id, host_answers, game.winner_id == game.host_id),
        (game.guest_id, guest_answers, game.winner_id == game.guest_id),
    ]:
        s = get_or_create_stats(user_id)
        s.total_games += 1
        s.total_correct += sum(1 for a in answers if a.is_correct)
        s.total_questions += len(answers)
        if won:
            s.total_wins += 1
            s.current_streak += 1
            s.max_streak = max(s.max_streak, s.current_streak)
        else:
            s.current_streak = 0  # Reset streak on loss or draw

    db.session.commit()

def generate_room_code():
    """Generates a random 6-character uppercase alphanumeric code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@game_bp.route("/create", methods=["POST"])
@login_required
def create():
    """Step 1: Player A creates a room."""
    difficulty = request.form.get("difficulty", "medium")
    num_questions = int(request.form.get("num_questions", 10))
    time_per_q = int(request.form.get("time_per_q", 30))
    
    code = generate_room_code()
    # Ensure code is unique
    while Game.query.filter_by(code=code).first():
        code = generate_room_code()

    import json
    questions = TriviaAPI.fetch_questions(amount=num_questions, difficulty=difficulty)

    new_game = Game(
        code=code,
        host_id=current_user.id,
        difficulty=difficulty,
        num_questions=len(questions),
        time_per_q=time_per_q,
        status="waiting",
        questions_json=json.dumps(questions)
    )
    db.session.add(new_game)
    db.session.commit()
    
    flash(f"Room created! Invite your friend with code: {code}", "success")
    return redirect(url_for("game.lobby", code=code))

@game_bp.route("/join", methods=["POST"])
@login_required
def join():
    """Step 2: Player B joins the lobby."""
    code = request.form.get("code", "").upper().strip()
    game = Game.query.filter_by(code=code).first()

    if not game:
        flash("Invalid room code.", "danger")
        return redirect(url_for("index"))
    
    if game.host_id == current_user.id:
        return redirect(url_for("game.lobby", code=code))

    if game.status != "waiting":
        flash("Game has already started or finished.", "warning")
        return redirect(url_for("index"))

    if game.is_full() and game.guest_id != current_user.id:
        flash("Room is full.", "warning")
        return redirect(url_for("index"))

    if not game.is_full():
        game.guest_id = current_user.id
        db.session.commit()
    
    flash("Successfully joined the lobby!", "success")
    return redirect(url_for("game.lobby", code=code))


@game_bp.route("/lobby/<code>")
@login_required
def lobby(code):
    """Waiting area before the game starts."""
    game = Game.query.filter_by(code=code).first_or_404()
    
    # If the host has started the game, redirect everyone to play area
    if game.status == "playing":
        return redirect(url_for("game.play", code=code))
        
    # Get the guest's username if someone joined
    guest_name = None
    if game.guest_id:
        from app.models import User
        guest = db.session.get(User, game.guest_id)
        if guest:
            guest_name = guest.username

    return render_template("game/lobby.html", game=game, guest_name=guest_name)


@game_bp.route("/start/<code>", methods=["POST"])
@login_required
def start_game(code):
    """Step 2.5: Host manually starts the game."""
    game = Game.query.filter_by(code=code).first_or_404()
    
    if current_user.id == game.host_id and game.is_full():
        game.status = "playing"
        db.session.commit()
        
    return redirect(url_for("game.play", code=code))

@game_bp.route("/play/<code>")
@login_required
def play(code):
    game = Game.query.filter_by(code=code).first_or_404()
    
    if current_user.id not in [game.host_id, game.guest_id]:
        flash("You are not part of this game.", "danger")
        return redirect(url_for("index"))

    import json
    questions = json.loads(game.questions_json) if game.questions_json else []
    
    answers_given = Answer.query.filter_by(game_id=game.id, user_id=current_user.id).count()
    
    if answers_given >= len(questions):
        return redirect(url_for("game.result", code=code))

    current_question = questions[answers_given]
    
    return render_template("game/play.html", game=game, question=current_question, q_num=answers_given + 1)

@game_bp.route("/answer/<code>", methods=["POST"])
@login_required
def submit_answer(code):
    game = Game.query.filter_by(code=code).first_or_404()
    
    # LEEMOS LAS PREGUNTAS DE LA BASE DE DATOS
    import json
    questions = json.loads(game.questions_json) if game.questions_json else []
    
    answers_given = Answer.query.filter_by(game_id=game.id, user_id=current_user.id).count()
    
    if answers_given < len(questions):
        current_question = questions[answers_given]
        given_answer = request.form.get("answer")
        time_taken = float(request.form.get("time_taken", game.time_per_q))
        
        is_correct = (given_answer == current_question["correct_answer"])
        
        new_answer = Answer(
            game_id=game.id,
            user_id=current_user.id,
            question_text=current_question["question"],
            category=current_question["category"],
            correct_answer=current_question["correct_answer"],
            given_answer=given_answer,
            is_correct=is_correct,
            time_taken=time_taken
        )
        db.session.add(new_answer)
        db.session.commit()
        
    return redirect(url_for("game.play", code=code))

@game_bp.route("/result/<code>")
@login_required
def result(code):
    """
    Step 5: Show final results.
    Triggers winner calculation and stats update the first time both players finish.
    """
    game = Game.query.filter_by(code=code).first_or_404()

    host_answers = Answer.query.filter_by(game_id=game.id, user_id=game.host_id).count()
    guest_answers = (
        Answer.query.filter_by(game_id=game.id, user_id=game.guest_id).count()
        if game.guest_id else 0
    )

    both_finished = (host_answers >= game.num_questions and guest_answers >= game.num_questions)

    # Only update stats once, when the game transitions to "done"
    if both_finished and game.status != "done":
        update_stats_after_game(game)

    host_score = Answer.query.filter_by(
        game_id=game.id, user_id=game.host_id, is_correct=True).count()
    guest_score = Answer.query.filter_by(
        game_id=game.id, user_id=game.guest_id, is_correct=True).count() if game.guest_id else 0

    return render_template("game/result.html", game=game,
                           both_finished=both_finished,
                           host_score=host_score,
                           guest_score=guest_score)