import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LINK_MODEL_PATH = os.path.join(BASE_DIR, "artifacts", "link_model_v1.pkl")

link_model = joblib.load(LINK_MODEL_PATH)


def predict_link(link: str):
    pred = link_model.predict([link])[0]
    prob = float(link_model.predict_proba([link])[0][1])
    return pred, prob
