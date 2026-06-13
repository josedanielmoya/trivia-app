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