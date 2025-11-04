import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import re

vowels = "аеёиоуыэюя"
consonants = "бвгджзйклмнпрстфхцчшщ"
special_chars = "ъь"

profanity_ngrams = ["бля", "ху", "пиз", "пез", "еб",
                    "гонд", "ганд", "сук", "cуч", "пид",
                    "блан", "своло", "убл", "мраз", "пед"]

def prepare_training_data():
    profane_words = open("safe/Тёмная сторона.txt", "r", encoding="utf8")
    normal_words = open("safe/Великий могучий.txt", "r", encoding="utf8")

    data = []
    for word in set(profane_words):
        data.append({"word": word, "label": 1})
    for word in list(set(normal_words))[:3000]:
        data.append({"word": word, "label": 0})

    profane_words.close()
    normal_words.close()

    return pd.DataFrame(data)


def extract_features(words):
    features = []

    for word in words:
        word = word.lower().strip()
        feature_dict = {
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
        features.append(feature_dict)

    return pd.DataFrame(features)


def train_model():
    df = prepare_training_data()

    X = extract_features(df['word'].values)
    y = df['label'].values

    print(f"Размер данных: {X.shape}")
    print(f"Мат: {sum(y)}, Не мат: {len(y) - sum(y)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\nРезультаты классификации:")
    print(classification_report(y_test, y_pred))

    # Сохранение модели
    joblib.dump(model, 'data/profanity_model.joblib')
    print("Модель сохранена в data/profanity_model.joblib")

    return model


if __name__ == "__main__":
    train_model()