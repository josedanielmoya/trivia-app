import os
from flask import Flask, redirect, url_for, render_template, render_template_string
from flask_login import LoginManager, login_required, current_user
from app.models import db, User
from config import config

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "warning"


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Create required directories
    os.makedirs(app.config.get("CHARTS_DIR", "app/static/charts"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Other blueprints — uncomment when each role adds their files
    from app.game.routes import game_bp
    app.register_blueprint(game_bp, url_prefix="/game")
    from app.stats.routes import stats_bp
    app.register_blueprint(stats_bp, url_prefix="/stats")
    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Root route
    @app.route("/")
    @login_required
    def index():
        return render_template("index.html")

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
