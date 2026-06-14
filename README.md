# 🎮 TriviaApp: Real-Time Multiplayer Trivia 

A robust, turn-based and real-time multiplayer trivia web application built with Python, Flask, and SQLite. 

This repository serves as the final project and technical memory for the **Scripting Languages (Python)** course.

## 👥 Team Members (The Developers)
This project was collaboratively designed, developed, and tested by:
* **Jose Daniel Moya Moreno**
* **Gonzalo Morte Gomez**
* **Arturo Hernandez Martinez**
* **Alvaro Rivera Moreno**

---

## 📖 1. Project Overview & Objective

TriviaApp was conceived to provide an engaging, arcade-style trivia experience where friends can compete against each other in real-time. 

Initially designed for a simple 1v1 on a single device, the project rapidly evolved during development into a **LAN-capable massive multiplayer game** supporting up to 10 simultaneous players per room. It seamlessly integrates external REST APIs, relational databases, asynchronous-feeling frontend interactions (via polling), and data visualization.

---

## 🏗️ 2. Architectural & Design Decisions (Project Memory)

To build a stable and scalable application, our team made several critical engineering decisions:

### A. Multiplayer Synchronization & Database Evolution
* **The Challenge:** Moving from a 2-player system to a 10-player system.
* **The Solution:** We dropped the rigid `host_id` and `guest_id` columns in favor of a **Many-to-Many relationship** (`game_players` association table). This allowed any number of users to join a `Game` instance.
* **Real-Time Feel:** Instead of overcomplicating the stack with WebSockets (which require external dependencies like Redis/SocketIO), we implemented **JS Polling**. The Lobby and Results pages auto-refresh seamlessly using `setTimeout()`, keeping players synchronized when waiting for the host to start or for opponents to finish their questions.

### B. API Integration & Rate Limiting Strategy
* **The Challenge:** The public *Open Trivia DB API* enforces strict rate limits (1 request per 5 seconds). Initially, each player fetching questions caused the game to crash or fall back to local files prematurely.
* **The Solution:** We implemented a "Fetch Once, Read Many" architecture. When the Host creates a room, the server fetches the questions from the API once and stores them as a serialized string in the `questions_json` column of the database. All joining players read from this database column, ensuring zero API bottlenecks and guaranteeing that all competitors answer the exact same questions.
* **Failsafe:** If the API is entirely down, the system catches the `requests.exceptions.RequestException` and safely loads a local file (`questions_backup.json`).

### C. UX: The "Play as Guest" System
* **The Challenge:** Forcing users to fill out a registration form on their phones just to play a quick 2-minute game creates high friction.
* **The Solution:** We developed a frictionless `/guest` route. Clicking the button generates a temporary username (`Guest_XXXX`), a random secure password, and an empty stats profile, logging the user in automatically. This hooks perfectly into our existing database structure without requiring a separate "anonymous user" logic flow.

### D. Security Measures
* **Password Hashing:** Plain-text passwords are never stored. We implemented `Flask-Bcrypt` to salt and hash all user credentials.
* **CSRF Protection:** Enabled globally via `Flask-WTF`'s `CSRFProtect`. Every single POST form (including pure HTML forms) requires a valid `csrf_token` to prevent Cross-Site Request Forgery attacks.

---

## 🎓 3. Course Requirements Fulfilled

This project rigorously implements all core requirements established in the course syllabus:

1.  **Object-Oriented Programming (OOP):** Deep use of classes for SQLAlchemy models (`User`, `Game`, `Answer`, `UserStats`), API Handlers (`TriviaAPI`), and JS Controllers (`GameTimer`).
2.  **File Handling (I/O):**
    * **JSON Handling:** Reading fallback data securely.
    * **CSV Generation:** The `/export/csv` route builds an in-memory CSV file using `io.StringIO` mapping all of a user's historical answers, allowing them to download it instantly.
3.  **External API Integration:** Leveraging the `requests` library to fetch categorized trivia queries dynamically based on user-selected difficulty.
4.  **External Libraries:** `Flask`, `SQLAlchemy`, `Flask-Login`, `Flask-WTF`, `Flask-Bcrypt`, `Requests`, and `Matplotlib`.
5.  **Relational Database & Admin CRUD:** * Complex relational models with foreign keys and cascade deletions.
    * A protected **Admin Dashboard** (`/admin/dashboard`) where users with `is_admin=True` can perform full CRUD operations: Read database states, Update roles, and Delete users/games.
6.  **Data Visualization:** Player profiles include a dynamically generated `.png` pie chart showing accuracy across different trivia categories, generated entirely backend-side using `Matplotlib`.

---

## 🚀 4. Core Features summary

* 🎮 **Up to 10 Players per Room** (LAN/Wi-Fi ready).
* ⏱️ **Dynamic JS Timer:** Auto-selects a random answer and auto-submits if the user runs out of time.
* 🏆 **Real-Time Leaderboard:** Ranks players automatically based on correct answers and assigns 🥇🥈🥉 medals.
* 🕵️ **Guest Mode:** Instant 1-click accounts.
* 📊 **Analytics:** Win streaks, win rates, and visual category charts.
* 🛠️ **Admin Panel:** Complete oversight of the application.

---

## ⚙️ 5. Installation & Setup Guide

### Requirements
* Python 3.8+
* `pip`

### Step-by-Step Setup

**1. Clone the repository**
```bash
git clone <repo-url>
cd trivia_app
