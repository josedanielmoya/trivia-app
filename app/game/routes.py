import random
import string
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.models import db, Game, Answer
from app.game.trivia_api import TriviaAPI

game_bp = Blueprint("game", __name__)

def update_stats_after_game(game):
    """
    Calculates the winner and updates UserStats for ALL players
    at the end of a finished game.
    """
    from app.models import UserStats

    def get_or_create_stats(user_id):
        s = UserStats.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserStats(user_id=user_id)
            db.session.add(s)
        return s

    player_scores = {}
    
    # Calculate score for each player
    for player in game.players:
        player_answers = Answer.query.filter_by(game_id=game.id, user_id=player.id).all()
        correct_count = sum(1 for a in player_answers if a.is_correct)
        player_scores[player.id] = {
            "answers": player_answers,
            "score": correct_count
        }

    # Determine winner (the one with the highest score)
    max_score = -1
    winners = []
    for pid, data in player_scores.items():
        if data["score"] > max_score:
            max_score = data["score"]
            winners = [pid]
        elif data["score"] == max_score:
            winners.append(pid)

    # If there is a tie, nobody gets the "win" stat, or you can assign it to the first one.
    # We will assign it only if there is a single clear winner with > 0 points.
    if len(winners) == 1 and max_score > 0:
        game.winner_id = winners[0]
    else:
        game.winner_id = None

    game.status = "done"

    # Update stats for all players
    for pid, data in player_scores.items():
        s = get_or_create_stats(pid)
        s.total_games += 1
        s.total_correct += data["score"]
        s.total_questions += len(data["answers"])
        if game.winner_id == pid:
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
    difficulty = request.form.get("difficulty", "medium")
    num_questions = int(request.form.get("num_questions", 10))
    time_per_q = int(request.form.get("time_per_q", 30))
    
    code = generate_room_code()
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
    new_game.players.append(current_user)
    db.session.add(new_game)
    db.session.commit()
    
    flash(f"Room created! Invite your friends with code: {code}", "success")
    return redirect(url_for("game.lobby", code=code))

@game_bp.route("/join", methods=["POST"])
@login_required
def join():
    code = request.form.get("code", "").upper().strip()
    game = Game.query.filter_by(code=code).first()

    if not game:
        flash("Invalid room code.", "danger")
        return redirect(url_for("index"))

    if game.status != "waiting":
        flash("Game has already started or finished.", "warning")
        return redirect(url_for("index"))

    if current_user not in game.players:
        if game.is_full():
            flash("Room is full. Max 10 players.", "warning")
            return redirect(url_for("index"))
            
        game.players.append(current_user)
        db.session.commit()
        flash("Successfully joined the lobby!", "success")

    return redirect(url_for("game.lobby", code=code))

@game_bp.route("/lobby/<code>")
@login_required
def lobby(code):
    game = Game.query.filter_by(code=code).first_or_404()
    
    if game.status == "playing":
        return redirect(url_for("game.play", code=code))
        
    return render_template("game/lobby.html", game=game, players=game.players)

@game_bp.route("/start/<code>", methods=["POST"])
@login_required
def start_game(code):
    game = Game.query.filter_by(code=code).first_or_404()
    
    if current_user.id == game.host_id and len(game.players) >= 2:
        game.status = "playing"
        db.session.commit()
        
    return redirect(url_for("game.play", code=code))

@game_bp.route("/play/<code>")
@login_required
def play(code):
    game = Game.query.filter_by(code=code).first_or_404()
    
    if current_user not in game.players:
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
    Step 5: Show final results and multiplayer leaderboard.
    Triggers winner calculation and stats update the first time ALL players finish.
    """
    game = Game.query.filter_by(code=code).first_or_404()

    all_finished = True
    player_scores = []

    # Check answers for all players in the game
    for player in game.players:
        ans_count = Answer.query.filter_by(game_id=game.id, user_id=player.id).count()
        if ans_count < game.num_questions:
            all_finished = False

        score = Answer.query.filter_by(game_id=game.id, user_id=player.id, is_correct=True).count()
        player_scores.append({
            "username": player.username,
            "score": score,
            "is_host": player.id == game.host_id
        })

    # Sort the leaderboard by score (highest first)
    player_scores.sort(key=lambda x: x["score"], reverse=True)

    # Only update stats once, when the game transitions to "done"
    if all_finished and game.status != "done":
        update_stats_after_game(game)

    return render_template("game/result.html", game=game,
                           all_finished=all_finished,
                           player_scores=player_scores)