import re
import joblib

from logs import text_log, curses, warnings, normal_words

def to_dense(x):
    if hasattr(x, "toarray"):
        return x.toarray()
    return x

class ProfanityClassifierPipeline:
    def __init__(self):
        self.pipeline = None
        self.load_pipeline()

    def load_pipeline(self):
        try:
            import __main__
            __main__.to_dense = to_dense

            self.pipeline = joblib.load("./data/profanity_pipeline.joblib")
            text_log.info("Конвейер классификации загружен")
        except FileNotFoundError as e:
            text_log.warning("Конвейер классификации не найден. Прекращение работы.")
            raise e

    def predict_profanity(self, word):
        if self.pipeline is None:
            return False, 0.0

        try:
            probability = self.pipeline.predict_proba([word])[0][1]
            return True, probability
        except Exception as e:
            text_log.error(f"Ошибка предсказания для '{word}': {e}")
            return False, 0.0

detector = ProfanityClassifierPipeline()
russifier1 = "".maketrans({
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
    "z" : "з",
    "'" : "ь"
})
russifier2 = {
    "ch" : "ч",
    "ya" : "я",
    "oo" : "у",
    "shk" : "чк"
}

def split_and_clean(text: str) -> list[str]:
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    words = re.split(r"\W+", text)
    cleaned_words = list()
    for word in words:
        buffer = word.lower()
        for i in russifier2.keys():
            buffer = buffer.replace(i, russifier2[i])
        buffer = (buffer.translate(russifier1)
                  .strip('.,!?;:"()[]{}<>«»—_-'))
        if buffer:
            cleaned_words.append(buffer)
    return cleaned_words

def analyse_message(user, text, privacy) -> int:
    if not text:
        return 0

    cursed = 0
    for word in text:
        flag_shot = False
        flag_warning = False
        if len(word) <= 2:
            continue
        checked, probability = detector.predict_profanity(word)
        if not checked:
            warnings.write(f"{word} - Не определен")
        else:
            if probability >= 0.85:
                cursed += 1
                flag_shot = True
            if probability >= 0.4:
                flag_warning = True

        if not privacy:
            if flag_shot:
                text_log.info(f"{user.name} использовал {word} - матерное слово - {probability}.")
                curses.write(f"{word} - {probability}\n")
            elif flag_warning:
                text_log.info(f"{user.name} использовал {word} - подозрение на матерное слово - {probability}.")
                warnings.write(f"{word} - {probability}\n")
            else:
                text_log.info(f"{user.name} использовал {word} - {probability}.")
                normal_words.write(f"{word} - {probability}\n")

    return cursed