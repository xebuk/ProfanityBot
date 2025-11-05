import logging
import joblib
import pandas as pd

from data_processing import extract_features_from_word

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./data/log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Text Management")

class ProfanityClassifier:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        try:
            self.model = joblib.load('./data/profanity_model.joblib')
            logger.info("Модель классификации загружена")
        except FileNotFoundError as e:
            logger.warning("Модель классификации не найдена. Прекращение работы.")
            raise e

    def predict_profanity(self, word):
        if self.model is None:
            return False, 0.0

        try:
            features = pd.DataFrame([extract_features_from_word(word)])
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
            elif probability >= 0.3:
                warnings.add(word)
                flag_warning = True

        if flag_shot:
            logger.info(f"{user.name} использовал {word} - матерное слово - {probability}.")
        elif flag_warning:
            logger.info(f"{user.name} использовал {word} - подозрение на матерное слово - {probability}.")
        else:
            logger.info(f"{user.name} использовал {word} - {probability}.")
    return curses, warnings