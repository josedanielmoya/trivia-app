from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships
    hosted_games = db.relationship("Game", foreign_keys="Game.host_id", backref="host", lazy="dynamic")
    guest_games = db.relationship("Game", foreign_keys="Game.guest_id", backref="guest", lazy="dynamic")
    answers = db.relationship("Answer", backref="user", lazy="dynamic")
    stats = db.relationship("UserStats", backref="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_total_games(self):
        return self.hosted_games.count() + self.guest_games.count()

    def get_wins(self):
        return Game.query.filter(
            Game.winner_id == self.id,
            Game.status == "done"
        ).count()

    def __repr__(self):
        return f"<User {self.username}>"


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    host_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    difficulty = db.Column(db.String(10), nullable=False, default="medium")  # easy/medium/hard
    num_questions = db.Column(db.Integer, nullable=False, default=10)
    time_per_question = db.Column(db.Integer, nullable=False, default=30)    # seconds
    category_id = db.Column(db.Integer, nullable=True)    # Open Trivia DB category ID (None = any)
    category_name = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(10), nullable=False, default="waiting")  # waiting/playing/done
    winner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    host_score = db.Column(db.Integer, default=0)
    guest_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    questions = db.relationship("Question", backref="game", lazy="dynamic", cascade="all, delete-orphan")
    answers = db.relationship("Answer", backref="game", lazy="dynamic", cascade="all, delete-orphan")
    winner = db.relationship("User", foreign_keys=[winner_id])

    def is_full(self):
        return self.guest_id is not None

    def both_finished(self):
        return self.status == "done"

    def __repr__(self):
        return f"<Game {self.code} [{self.status}]>"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    order = db.Column(db.Integer, nullable=False)           # position in the game (0-based)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=True)
    difficulty = db.Column(db.String(10), nullable=True)
    correct_answer = db.Column(db.String(256), nullable=False)
    wrong_answers = db.Column(db.Text, nullable=False)      # JSON array stored as string

    def get_all_answers_shuffled(self):
        """Returns a shuffled list of all answer options (correct + wrong)."""
        import json
        import random
        options = json.loads(self.wrong_answers) + [self.correct_answer]
        random.shuffle(options)
        return options

    def __repr__(self):
        return f"<Question {self.id} game={self.game_id} order={self.order}>"


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    given_answer = db.Column(db.String(256), nullable=True)   # None if time ran out
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    time_taken = db.Column(db.Float, nullable=False, default=0.0)  # seconds

    question = db.relationship("Question")

    def __repr__(self):
        return f"<Answer user={self.user_id} q={self.question_id} correct={self.is_correct}>"


class UserStats(db.Model):
    """Aggregated stats per user — updated at the end of each game."""
    __tablename__ = "user_stats"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    total_games = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)
    total_correct = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    max_streak = db.Column(db.Integer, default=0)

    def accuracy(self):
        if self.total_questions == 0:
            return 0.0
        return round(self.total_correct / self.total_questions * 100, 1)

    def win_rate(self):
        if self.total_games == 0:
            return 0.0
        return round(self.total_wins / self.total_games * 100, 1)

    def __repr__(self):
        return f"<UserStats user={self.user_id} wins={self.total_wins}>"
