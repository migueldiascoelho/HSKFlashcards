from datetime import datetime


class ScoreManager:
    def __init__(self, file_path="scores.txt"):
        self.file_path = file_path

    def write_scores(self, name, score):
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        with open(self.file_path, 'a') as file:
            file.write(f'USER: {name} -> SCORE: {score} --> DATE: {dt_string}\n')
