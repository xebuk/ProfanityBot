from joblib import dump
from pandas import DataFrame

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import FunctionTransformer
from sklearn.ensemble import HistGradientBoostingClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from whisper import load_model, available_models

def to_dense(x):
    if hasattr(x, "toarray"):
        return x.toarray()
    return x

def fit_pipeline():
    profane_words = open("../../safe/Тёмная сторона - nx.txt", "r", encoding="utf8")
    profane_words_addendum = open("../../safe/Тёмная сторона - Личный набор.txt", "r", encoding="utf8")
    normal_words = open("../../safe/Великий Могучий - nx.txt", "r", encoding="utf8")
    normal_words_addendum = open("../../safe/Великий Могучий - Личный Набор.txt", "r", encoding="utf8")

    data = list()
    for word in profane_words:
        data.append({"word": word.strip(), "label": 1})
    for word in set(profane_words_addendum):
        data.append({"word": word.strip(), "label": 1})
    for word in normal_words:
        data.append({"word": word.strip(), "label": 0})
    for word in set(normal_words_addendum):
        data.append({"word": word.strip(), "label": 0})

    profane_words.close()
    profane_words_addendum.close()
    normal_words.close()
    normal_words_addendum.close()

    df = DataFrame(data)
    X = df['word'].values
    y = df['label'].values

    print(f"Размер данных: {X.shape}")
    print(f"Мат: {sum(y)}, Не мат: {len(y) - sum(y)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=69420
    )

    pipeline = ImbPipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 5),
            max_features=50000,
            max_df=0.8,
            min_df=0.0,
            lowercase=True,
            sublinear_tf=True
        )),
        ('transformer', FunctionTransformer(
            to_dense,
            accept_sparse=True
        )),
        ('smote', SMOTE(
            random_state=69420,
            sampling_strategy="auto",
            k_neighbors=7
        )),
        ("classifier", HistGradientBoostingClassifier(
            max_iter=400,
            learning_rate=0.1,
            max_depth=600,
            class_weight='balanced',
            random_state=69420
        ))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    print("\nРезультаты классификации:")
    report = classification_report(y_test, y_pred)
    print(report)
    with open("profanity_pipeline/profanity_pipeline_data_new.txt", "w", encoding="utf8") as new_pipeline:
        new_pipeline.write(report)

    # Сохранение модели
    dump(pipeline, "profanity_pipeline/profanity_pipeline_new.joblib")
    print("Конвейер сохранен в profanity_pipeline_new.joblib")

def change_whisper_model():
    available_model_list = available_models()
    print(f"""Доступные модели:
{available_model_list}
Введите название нужной модели. При некорректном вводе программа закончит работу.""")
    model = input()
    if model in available_model_list:
        load_model(model, download_root="whisper")

if __name__ == "__main__":
    fit_pipeline()