# TriviaApp 🎮

A turn-based multiplayer trivia web application built with Flask and SQLite for the **Scripting Languages (Python)** course project.

## Description

Two players compete on the same device, answering the same trivia questions fetched from the public [Open Trivia DB](https://opentdb.com/) API. Player 1 answers first, then Player 2. The player with the highest score (accuracy + speed) wins.

## System Requirements

- Python 3.8+
- pip

## Installation & Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd trivia_app

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up environment variables
cp .env.example .env
# Edit .env and set your SECRET_KEY

# 5. Run the application
python run.py
```

Visit: http://127.0.0.1:5000

The database (`instance/trivia.db`) is created automatically on first run.

## Project Structure (Role 1 — Auth & Base)

```
trivia_app/
├── run.py                  ← entry point
├── config.py               ← dev/prod configuration
├── requirements.txt        ← dependencies
├── .env.example            ← environment variable template
├── app/
│   ├── __init__.py         ← Flask app factory, blueprints, error handlers
│   ├── models.py           ← User, Game, Question, Answer, UserStats (SQLAlchemy)
│   ├── auth/
│   │   ├── routes.py       ← /auth/register, /auth/login, /auth/logout
│   │   └── forms.py        ← WTForms with full validation
│   ├── templates/
│   │   ├── base.html       ← arcade-style base layout with navbar
│   │   ├── auth/           ← login.html, register.html
│   │   └── errors/         ← 404.html, 500.html
│   └── static/
│       └── css/style.css   ← arcade color theme
```

## Tech Stack

| Component | Library |
|---|---|
| Web framework | Flask 3.0 |
| Authentication | Flask-Login |
| Form validation | Flask-WTF + WTForms |
| Database ORM | SQLAlchemy + SQLite |
| Password hashing | Werkzeug |
| Charts | matplotlib (Role 4) |
| Trivia API | Open Trivia DB (Role 2) |

## Roles & Responsibilities

| Role | Responsibilities |
|---|---|
| **Role 1 (this)** | Project setup, models, authentication, base layout |
| Role 2 | Game logic, Trivia API integration, game routes |
| Role 3 | All frontend templates, CSS arcade style, JS timer |
| Role 4 | Stats, ranking, charts, admin panel, CSV export |

## Git Workflow

Each team member works on their own branch and opens a Pull Request to `main`:

```
main
├── feat/auth-and-models      ← Role 1
├── feat/game-logic           ← Role 2
├── feat/frontend-templates   ← Role 3
└── feat/stats-and-admin      ← Role 4
```

To enable other roles, uncomment the blueprint imports in `app/__init__.py`.
