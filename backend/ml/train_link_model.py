import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

DATA_PATH = "backend/ml/data/train_links.csv"
ARTIFACT_DIR = "backend/ml/artifacts"

os.makedirs(ARTIFACT_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(DATA_PATH)

    print("Dataset shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nLabel distribution:")
    print(df["label"].value_counts())

    if "link" not in df.columns or "label" not in df.columns:
        raise ValueError("train_links.csv must contain 'link' and 'label' columns")

    df["link"] = df["link"].fillna("").astype(str).str.strip()
    df["label"] = df["label"].fillna(0).astype(int)

    df = df[df["link"].str.len() > 0].copy()
    return df


def main():
    df = load_data()

    X = df["link"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=10000)),
        ("clf", LogisticRegression(max_iter=1000))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("\n" + "=" * 60)
    print("LINK MODEL RESULTS")
    print("=" * 60)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    save_path = os.path.join(ARTIFACT_DIR, "link_model_v1.pkl")
    joblib.dump(model, save_path)
    print(f"\nSaved link model to: {save_path}")


if __name__ == "__main__":
    main()