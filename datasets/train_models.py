import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# -------------------------
# 1. Load dataset
# -------------------------
df_train = pd.read_csv("scam_messages_train.csv")
df_test = pd.read_csv("scam_messages_test.csv")

# -------------------------
# 2. Choose features
# -------------------------
feature_cols = [
    "text",
    "message_type",
    "platform",
    "job_type",
    "contains_link",
    "contains_email",
    "has_payment_request",
    "asks_personal_info"
]

X_train = df_train[feature_cols]
y_train_label = df_train["label"]
y_train_type = df_train["scam_type"]

X_test = df_test[feature_cols]
y_test_label = df_test["label"]
y_test_type = df_test["scam_type"]

# -------------------------
# 4. Build preprocessors
# -------------------------
text_col = "text"
cat_cols = ["message_type", "platform", "job_type"]
bin_cols = ["contains_link", "contains_email", "has_payment_request", "asks_personal_info"]

preprocessor_label = ColumnTransformer([
    ("text", TfidfVectorizer(max_features=5000, ngram_range=(1, 2)), text_col),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ("bin", "passthrough", bin_cols)
])

preprocessor_type = ColumnTransformer([
    ("text", TfidfVectorizer(max_features=5000, ngram_range=(1, 2)), text_col),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ("bin", "passthrough", bin_cols)
])

# -------------------------
# 5. Build models
# -------------------------
label_model = Pipeline([
    ("prep", preprocessor_label),
    ("clf", LogisticRegression(max_iter=1000))
])

type_model = Pipeline([
    ("prep", preprocessor_type),
    ("clf", LogisticRegression(max_iter=1000))
])

# -------------------------
# 6. Train models
# -------------------------
label_model.fit(X_train, y_train_label)
type_model.fit(X_train, y_train_type)

# -------------------------
# 7. Evaluate models
# -------------------------
y_pred_label = label_model.predict(X_test)
y_pred_type = type_model.predict(X_test)

print("Label model accuracy:", accuracy_score(y_test_label, y_pred_label))
print("Type model accuracy:", accuracy_score(y_test_type, y_pred_type))

# -------------------------
# 8. Save models
# -------------------------
joblib.dump(label_model, "label_model.pkl")
joblib.dump(type_model, "type_model.pkl")

print("Models saved successfully:")
print("- label_model.pkl")
print("- type_model.pkl")