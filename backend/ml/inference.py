import os
import joblib
import pandas as pd

# -------------------------
# Load model paths
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LABEL_MODEL_PATH = os.path.join(BASE_DIR, "label_model.pkl")
TYPE_MODEL_PATH = os.path.join(BASE_DIR, "type_model.pkl")

# -------------------------
# Load trained models once
# -------------------------
label_model = joblib.load(LABEL_MODEL_PATH)
type_model = joblib.load(TYPE_MODEL_PATH)


def extract_features_from_text(text: str):
    """
    Create simple structured features from raw text.
    These must match the columns used during training.
    """
    text_lower = text.lower()

    return {
        "text": text,
        "message_type": "Email",   # default value
        "platform": "Unknown",     # default value
        "job_type": "Unknown",     # default value
        "contains_link": 1 if "http" in text_lower or "www." in text_lower else 0,
        "contains_email": 1 if "@" in text else 0,
        "has_payment_request": 1 if any(word in text_lower for word in [
            "pay", "payment", "fee", "deposit", "transfer", "refundable"
        ]) else 0,
        "asks_personal_info": 1 if any(word in text_lower for word in [
            "bank details", "paypal", "id", "account number", "passport", "ssn"
        ]) else 0
    }


def normalize_input(payload: dict):
    """
    Convert incoming request payload into the exact feature structure
    expected by the trained models.
    """
    text = payload.get("text", "").strip()

    if not text:
        raise ValueError("Text input is empty.")

    text_lower = text.lower()

    contains_link = payload.get("contains_link")
    if contains_link is None:
        contains_link = 1 if "http" in text_lower or "www." in text_lower else 0

    contains_email = payload.get("contains_email")
    if contains_email is None:
        contains_email = 1 if "@" in text else 0

    has_payment_request = payload.get("has_payment_request")
    if has_payment_request is None:
        has_payment_request = 1 if any(word in text_lower for word in [
            "pay", "payment", "fee", "deposit", "transfer", "refundable"
        ]) else 0

    asks_personal_info = payload.get("asks_personal_info")
    if asks_personal_info is None:
        asks_personal_info = 1 if any(word in text_lower for word in [
            "bank details", "paypal", "id", "account number", "passport", "ssn"
        ]) else 0

    row = {
        "text": text,
        "message_type": payload.get("message_type") or "Email",
        "platform": payload.get("platform") or "Gmail",
        "job_type": payload.get("job_type") or "Remote",
        "contains_link": int(contains_link),
        "contains_email": int(contains_email),
        "has_payment_request": int(has_payment_request),
        "asks_personal_info": int(asks_personal_info),
    }

    return row


def predict_message(payload: dict):
    """
    Run both ML models on one message.
    Returns:
    - row: normalized feature dictionary
    - scam_pred: 0 or 1
    - scam_prob: probability of scam
    - type_pred: predicted scam type
    """
    row = normalize_input(payload)
    input_df = pd.DataFrame([row])

    scam_pred = label_model.predict(input_df)[0]
    scam_prob = float(label_model.predict_proba(input_df)[0][1])
    type_pred = type_model.predict(input_df)[0]

    if scam_pred == 0:
        type_pred = "Legitimate"

    return row, scam_pred, scam_prob, type_pred