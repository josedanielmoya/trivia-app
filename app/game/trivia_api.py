import requests
import html
import json
import os
import random

class TriviaAPI:
    BASE_URL = "https://opentdb.com/api.php"
    # Path to the backup JSON file
    BACKUP_FILE = os.path.join(os.path.dirname(__file__), "questions_backup.json")

    @staticmethod
    def fetch_questions(amount=10, difficulty="medium"):
        """Fetches questions from the API. Falls back to local JSON if it fails."""
        try:
            # Request API with a timeout to prevent the app from hanging
            response = requests.get(
                TriviaAPI.BASE_URL,
                params={"amount": amount, "difficulty": difficulty, "type": "multiple"},
                timeout=5
            )
            response.raise_for_status()  # Raises an HTTPError if the response was unsuccessful
            data = response.json()
            
            if data.get("response_code") == 0:
                return TriviaAPI._clean_data(data["results"])
            else:
                return TriviaAPI._get_backup_questions(amount, difficulty)
                
        except (requests.RequestException, ValueError):
            print("⚠️ Error connecting to Trivia API. Using backup file.")
            return TriviaAPI._get_backup_questions(amount, difficulty)

    @staticmethod
    def _clean_data(results):
        """Cleans HTML entities (e.g., &quot;) and shuffles answers."""
        clean_results = []
        for q in results:
            clean_q = {
                "category": html.unescape(q["category"]),
                "question": html.unescape(q["question"]),
                "correct_answer": html.unescape(q["correct_answer"]),
                "incorrect_answers": [html.unescape(ans) for ans in q["incorrect_answers"]]
            }
            # Pre-shuffle correct and incorrect options for the frontend
            options = clean_q["incorrect_answers"] + [clean_q["correct_answer"]]
            random.shuffle(options)
            clean_q["all_answers"] = options
            
            clean_results.append(clean_q)
        return clean_results

    @staticmethod
    def _get_backup_questions(amount, difficulty):
        """Reads the local JSON file. Fulfills the file handling requirement!"""
        try:
            with open(TriviaAPI.BACKUP_FILE, "r", encoding="utf-8") as f:
                all_questions = json.load(f)
            
            # Filter by difficulty if possible
            filtered = [q for q in all_questions if q.get("difficulty") == difficulty]
            if len(filtered) < amount:
                filtered = all_questions # If not enough, use all available
            
            # Pick random questions
            selected = random.sample(filtered, min(amount, len(filtered)))
            return TriviaAPI._clean_data(selected)
            
        except (FileNotFoundError, json.JSONDecodeError):
            print("❌ Error: Backup file not found or corrupted.")
            return []