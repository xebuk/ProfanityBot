import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import FunctionTransformer
from sklearn.ensemble import HistGradientBoostingClassifier

from sklearn.pipeline import Pipeline

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

tr1 = "".maketrans({"е" : "ё"})
tr2 = "".maketrans({"е" : "я"})

def to_dense(x):
    if hasattr(x, "toarray"):
        return x.toarray()
    return x

def fit_pipeline():
    profane_words = open("../safe/Тёмная сторона.txt", "r", encoding="utf8")
    normal_words = open("../safe/Великий Могучий - nx.txt", "r", encoding="utf8")

    data = list()
    for word in profane_words:
        data.append({"word": word.strip(), "label": 1})
        data.append({"word": word.translate(tr1).strip(), "label": 1})
        data.append({"word": word.translate(tr2).strip(), "label": 1})
    for word in normal_words:
        data.append({"word": word.strip(), "label": 0})

    profane_words.close()
    normal_words.close()

    df = pd.DataFrame(data)
    X = df['word'].values
    y = df['label'].values

    print(f"Размер данных: {X.shape}")
    print(f"Мат: {sum(y)}, Не мат: {len(y) - sum(y)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 4),
            max_features=10000,
            lowercase=True,
            min_df=2,
            max_df=0.9,
            sublinear_tf=True
        )),
        ('transformer', FunctionTransformer(
            to_dense,
            accept_sparse=True
        )),
        ("classifier", HistGradientBoostingClassifier(
            max_iter=200,
            learning_rate=0.1,
            max_depth=10,
            class_weight='balanced',
            random_state=42
        ))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    print("\nРезультаты классификации:")
    print(classification_report(y_test, y_pred))

    # Сохранение модели
    joblib.dump(pipeline, "../data/profanity_pipeline.joblib")
    print("Конвейер сохранен в data/profanity_pipeline.joblib")


if __name__ == "__main__":
    fit_pipeline()