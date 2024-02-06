import json
from datetime import datetime

class LearnedStatusManager:
    def __init__(self, file_path='learned_status.json'):
        self.file_path = file_path
        self.learned_status = self.load_learned_status()

    def load_learned_status(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                data = file.read()
                if data:
                    return json.loads(data)
                else:
                    return {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_learned_status(self):
        sorted_status = dict(sorted(self.learned_status.items(), key=lambda item: item[1]['value'], reverse=True))

        with open(self.file_path, 'w', encoding='utf-8') as file:
            json.dump(sorted_status, file, ensure_ascii=False, indent=2)

    def update_status(self, chinese_word, increment, hsk_level):
        if chinese_word in self.learned_status:
            self.learned_status[chinese_word]["value"] += increment
            self.learned_status[chinese_word]["last_interaction"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.learned_status[chinese_word] = {
                "value": increment,
                "last_interaction": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hsk_level": hsk_level
            }

        self.save_learned_status()



    def get_learned_words(self):
        return list(self.learned_status.keys())


    def get_learned_words_count(self):
        return len(self.learned_status)


    def get_mastered_words_count(self):
        mastered_words = []
        for word, data in self.learned_status.items():
            if data["value"] >= 4:
                mastered_words.append(word)
        return len(mastered_words)
