import os
import csv
import json
from datetime import datetime

def count_words_per_level(flashcard_files):
    words_per_level = {}
    for i, file_name in enumerate(flashcard_files, start=1):
        with open(file_name, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            word_count = sum(1 for row in reader) - 1  # Minus 1 to exclude header row
            words_per_level[i] = word_count

    return words_per_level

def calculate_hsk_completion(file_path='learned_status.json', flashcard_files=["hsk1_vocabulary_only.csv", "hsk2_vocabulary_only.csv", "hsk3_vocabulary_only.csv", "hsk4_vocabulary_only.csv", "hsk5_vocabulary_only.csv", "hsk6_vocabulary_only.csv"]):
    # Check if the file is empty
    if os.path.getsize(file_path) > 0:
        # Load the learned status data
        with open(file_path, 'r', encoding='utf-8') as file:
            learned_status = json.load(file)

        # Count words per HSK level
        words_count = count_words_per_level(flashcard_files)

        hsk_levels = {1: {"discovered": 0, "mastered": 0}, 2: {"discovered": 0, "mastered": 0}, 3: {"discovered": 0, "mastered": 0}, 4: {"discovered": 0, "mastered": 0}, 5: {"discovered": 0, "mastered": 0}, 6: {"discovered": 0, "mastered": 0}}

        # Calculate the discovered and mastered words for each HSK level
        for word, data in learned_status.items():
            hsk_level = data.get('hsk_level', 0)
            value = data.get('value', 0)
            last_interaction = datetime.strptime(data.get('last_interaction'), "%Y-%m-%d %H:%M:%S")

            if hsk_level in hsk_levels:
                if value >= 1:
                    hsk_levels[hsk_level]["discovered"] += 1
                if value >= 4 and (datetime.now() - last_interaction).days < 7:
                    hsk_levels[hsk_level]["mastered"] += 1

        percentages = {}  # A dictionary to store proficiency percentages

        for level in hsk_levels:
            discovered_words = hsk_levels[level]["discovered"]
            mastered_words = hsk_levels[level]["mastered"]
            total_words = words_count[level]


            # Calculate percentages only if there are words in the level
            if total_words > 0:
                discovered_percentage = (discovered_words / total_words) * 100
                mastered_percentage = (mastered_words / total_words) * 100
                total_percentage = (discovered_percentage + mastered_percentage) / 2
                percentages[level] = round(total_percentage, 1)


        return percentages

    else:
        # If the file is empty, return 0 for all levels
        return {level: 0.0 for level in range(1, 7)}


def calculate_user_level():
    percentages = calculate_hsk_completion()
    level = int(round(((1 + percentages[1]*0.165 + percentages[2]*0.165 + percentages[3]*0.165 + percentages[4]*0.165 + percentages[5]*0.165 + percentages[6]*0.165)/2),0))
    return level


if __name__ == "__main":
    calculate_hsk_completion()
