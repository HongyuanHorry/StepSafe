import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# -------------------------
# Paths
# -------------------------
DATA_PATH = "backend/ml/data/scam_messages_train_v2.csv"
ARTIFACT_DIR = "backend/ml/artifacts"

os.makedirs(ARTIFACT_DIR, exist_ok=True)

# -------------------------
# Columns
# -------------------------
FEATURE_COLS = [
    "text",
    "message_type",
    "platform",
    "job_type",
    "contains_link",
    "contains_email",
    "has_payment_request",
    "asks_personal_info",
]

LABEL_COL = "label"
TYPE_COL = "scam_type"


def load_data():
    df = pd.read_csv(DATA_PATH)

    print("Dataset shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nLabel distribution:")
    print(df[LABEL_COL].value_counts())

    print("\nScam type distribution:")
    print(df[TYPE_COL].value_counts())

    # Optional: remove message_id from training entirely
    keep_cols = FEATURE_COLS + [LABEL_COL, TYPE_COL]
    df = df[keep_cols].copy()

    return df


def build_preprocessor():
    text_col = "text"
    cat_cols = ["message_type", "platform", "job_type"]
    bin_cols = ["contains_link", "contains_email", "has_payment_request", "asks_personal_info"]

    return ColumnTransformer([
        ("text", TfidfVectorizer(max_features=5000, ngram_range=(1, 2)), text_col),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ("bin", "passthrough", bin_cols),
    ])


def train_label_model(df):
    X = df[FEATURE_COLS]
    y = df[LABEL_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = Pipeline([
        ("prep", build_preprocessor()),
        ("clf", LogisticRegression(max_iter=1000))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("\n" + "=" * 60)
    print("LABEL MODEL RESULTS")
    print("=" * 60)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    save_path = os.path.join(ARTIFACT_DIR, "label_model_v2.pkl")
    joblib.dump(model, save_path)
    print(f"\nSaved label model to: {save_path}")


def train_type_model(df):
    X = df[FEATURE_COLS]
    y = df[TYPE_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = Pipeline([
        ("prep", build_preprocessor()),
        ("clf", LogisticRegression(max_iter=1000))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("\n" + "=" * 60)
    print("TYPE MODEL RESULTS")
    print("=" * 60)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    save_path = os.path.join(ARTIFACT_DIR, "type_model_v2.pkl")
    joblib.dump(model, save_path)
    print(f"\nSaved type model to: {save_path}")


def main():
    df = load_data()
    train_label_model(df)
    train_type_model(df)


if __name__ == "__main__":
    main()