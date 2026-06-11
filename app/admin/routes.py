from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.models import db, User, Game, Answer, UserStats

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    """Decorator that restricts access to admin users only."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    games = Game.query.order_by(Game.created_at.desc()).limit(30).all()
    total_answers = db.session.execute(
        db.select(db.func.count()).select_from(Answer)
    ).scalar()
    return render_template("admin/dashboard.html",
                           users=users, games=games, total_answers=total_answers)


@admin_bp.route("/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Deletes a user and all their associated data (CRUD - Delete)."""
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.dashboard"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/user/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    """Promotes or demotes a user to/from admin (CRUD - Update)."""
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot change your own admin status.", "warning")
        return redirect(url_for("admin.dashboard"))
    user.is_admin = not user.is_admin
    db.session.commit()
    role = "admin" if user.is_admin else "regular user"
    flash(f"'{user.username}' is now {role}.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/game/<int:game_id>/delete", methods=["POST"])
@admin_required
def delete_game(game_id):
    """Deletes a game and all its answers (CRUD - Delete)."""
    game = db.session.get(Game, game_id)
    if game is None:
        abort(404)
    db.session.delete(game)
    db.session.commit()
    flash(f"Game '{game.code}' deleted.", "success")
    return redirect(url_for("admin.dashboard"))