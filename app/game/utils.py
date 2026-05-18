import csv
import os
from datetime import datetime
from flask import Response

def export_game_to_csv(game):
    """
    Generates a CSV file with the game's answers.
    Fulfills the 'CSV file handling' requirement.
    """
    # Create an in-memory CSV string generator
    def generate():
        # Header row
        yield "User ID,Question,Category,Correct Answer,Given Answer,Is Correct,Time Taken (s)\n"
        
        # Data rows
        for answer in game.answers:
            row = [
                str(answer.user_id),
                f'"{answer.question_text}"',  # Quotes to handle commas in questions
                f'"{answer.category}"',
                f'"{answer.correct_answer}"',
                f'"{answer.given_answer if answer.given_answer else "Timeout"}"',
                str(answer.is_correct),
                str(round(answer.time_taken, 2))
            ]
            yield ",".join(row) + "\n"

    filename = f"trivia_game_{game.code}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )