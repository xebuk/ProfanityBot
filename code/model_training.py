import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

from data_processing import extract_features_from_word

tr1 = "".maketrans({"е" : "ё"})

def prepare_training_data():
    profane_words = open("../safe/Тёмная сторона.txt", "r", encoding="utf8")
    normal_words = open("../safe/Великий Могучий.txt", "r", encoding="utf8")

    data = []
    for word in profane_words:
        data.append({"word": word, "label": 1})
        data.append({"word": word.translate(tr1), "label": 1})
    for word in normal_words:
        data.append({"word": word, "label": 0})

    profane_words.close()
    normal_words.close()

    return pd.DataFrame(data)


def extract_features(words):
    return pd.DataFrame([extract_features_from_word(word.lower().strip()) for word in words])


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
    joblib.dump(model, '../data/profanity_model.joblib')
    print("Модель сохранена в data/profanity_model.joblib")

    return model


if __name__ == "__main__":
    train_model()