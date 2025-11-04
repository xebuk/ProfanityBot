import re
import logging

import pandas as pd

import joblib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Text Management")

vowels = "аеёиоуыэюя"
consonants = "бвгджзйклмнпрстфхцчшщ"
special_chars = "ъь"

profanity_ngrams = ["бля", "ху", "пиз", "пез", "еб",
                    "гонд", "ганд", "сук", "cуч", "пид",
                    "блан", "своло", "убл", "мраз", "пед"]

def extract_features(word):
    features = {
        "length": len(word),
        "vowel_count": sum(word.count(c) for c in vowels),
        "consonant_count": sum(word.count(c) for c in consonants),
        "special_char_count": sum(word.count(c) for c in special_chars),
        "has_repeating_chars": int(bool(re.search(r"(.)\1{2,}", word))),
        "consonant_clusters": len(re.findall(rf"[{consonants}]{3,}", word)),
        "vowel_clusters": len(re.findall(rf"[{vowels}]{3,}", word)),
        "starts_with_consonant": int(word[0] in consonants) if word else 0,
        "ends_with_vowel": int(word[-1] in vowels) if word else 0,
        "ends_with_special_char": int(word[-1] in special_chars) if word else 0,
        "contains_common_profanity_ngrams": int(any(ngram in word for ngram in profanity_ngrams))
    }
    return pd.DataFrame([features])


class ProfanityClassifier:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        try:
            self.model = joblib.load('data/profanity_model.joblib')
            logger.info("Модель классификации загружена")
        except FileNotFoundError as e:
            logger.warning("Модель классификации не найдена. Прекращение работы.")
            raise e

    def predict_profanity(self, word):
        if self.model is None:
            return False, 0.0

        try:
            features = extract_features(word)
            probability = self.model.predict_proba(features)[0][1]
            return True, probability
        except Exception as e:
            logger.error(f"Ошибка предсказания для '{word}': {e}")
            return False, 0.0

detector = ProfanityClassifier()
russifier = "".maketrans({
    "a" : "а",
    "b" : "б",
    "c" : "к",
    "d" : "д",
    "e" : "е",
    "f" : "ф",
    "g" : "г",
    "h" : "х",
    "i" : "и",
    "j" : "ж",
    "k" : "к",
    "l" : "л",
    "m" : "м",
    "n" : "н",
    "o" : "о",
    "p" : "п",
    "q" : "ку",
    "r" : "р",
    "s" : "с",
    "t" : "т",
    "u" : "у",
    "v" : "в",
    "w" : "в",
    "x" : "х",
    "y" : "у",
    "z" : "з"
})

def split_and_clean(text):
    words = text.split()
    cleaned_words = list()
    for word in words:
        buffer = (word.lower()
                  .translate(russifier)
                  .strip('.,!?;:"()[]{}<>«»—_-'))
        if buffer:
            cleaned_words.append(buffer)
    return cleaned_words

def analyse_message(user, text) -> tuple[int, set[str]]:
    if not text:
        return 0, set()

    line = split_and_clean(text)
    curses = 0
    warnings = set()
    for word in line:
        flag_shot = False
        flag_warning = False
        if len(word) <= 2:
            continue
        checked, probability = detector.predict_profanity(word)
        if not checked:
            warnings.add(word)
        else:
            if probability >= 0.69:
                curses += 1
                flag_shot = True
            if probability >= 0.3:
                warnings.add(word)
                flag_warning = True

        if flag_shot:
            logger.info(f"{user.name} использовал {word} - матерное слово - {probability}.")
        elif flag_warning:
            logger.info(f"{user.name} использовал {word} - подозрение на матерное слово - {probability}.")
        else:
            logger.info(f"{user.name} использовал {word} - {probability}.")
    return curses, warnings