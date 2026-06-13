from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

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
    answers = db.relationship("Answer", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    stats = db.relationship("UserStats", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

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
    time_per_q = db.Column(db.Integer, nullable=False, default=30)           # seconds
    status = db.Column(db.String(10), nullable=False, default="waiting")     # waiting/playing/done
    questions_json = db.Column(db.Text, nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones
    answers = db.relationship("Answer", backref="game", lazy="dynamic", cascade="all, delete-orphan")
    winner = db.relationship("User", foreign_keys=[winner_id])

    def is_full(self):
        return self.guest_id is not None

    def both_finished(self):
        return self.status == "done"


class Round(db.Model):
    """One player's session within a game — groups their answers together."""
    __tablename__ = "rounds"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    finished = db.Column(db.Boolean, default=False)

    # Relationships
    answers = db.relationship("Answer", backref="round", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Round game={self.game_id} user={self.user_id} finished={self.finished}>"


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"), nullable=True)
    
    # Nuevos campos guardados directamente en la respuesta
    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=True)
    correct_answer = db.Column(db.String(256), nullable=False)
    
    given_answer = db.Column(db.String(256), nullable=True)   # None si el tiempo se agotó
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    time_taken = db.Column(db.Float, nullable=False, default=0.0)  # seconds

    def __repr__(self):
        return f"<Answer user={self.user_id} correct={self.is_correct}>"


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
